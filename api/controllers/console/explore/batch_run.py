import logging

from flask_restful import reqparse, Resource, marshal_with
from flask_restful.inputs import int_range # type: ignore
from werkzeug.exceptions import InternalServerError

from controllers.console.app.error import (
    CompletionRequestError,
    ProviderModelCurrentlyNotSupportError,
    ProviderNotInitializeError,
    ProviderQuotaExceededError,
)
from controllers.console.explore.error import NotWorkflowAppError
from controllers.console.explore.wraps import InstalledAppResource
from core.app.entities.app_invoke_entities import InvokeFrom
from core.errors.error import (
    ModelCurrentlyNotSupportError,
    ProviderTokenNotInitError,
    QuotaExceededError,
)
from controllers.console.wraps import account_initialization_required
from core.model_runtime.errors.invoke import InvokeError
from extensions.ext_database import db
from libs import helper
from libs.login import current_user
from libs.login import login_required
from models.model import AppMode, InstalledApp, InstalledAppBatchRunRecord
from services.app_generate_service import AppGenerateService
from tasks.installed_app_batch_run import installed_app_batch_run
from core.opends.client import OpendsClient
from configs import dify_config

from fields.installed_app_fields import batch_run_record_api_fields
from fields.workflow_fields import workflow_fields
from services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)


class InstalledAppBatchRunApi(InstalledAppResource):
    def post(self, installed_app: InstalledApp):
        """
        Run workflow
        """
        app_model = installed_app.app
        app_mode = AppMode.value_of(app_model.mode)
        if app_mode != AppMode.WORKFLOW and app_mode != AppMode.COMPLETION:
            raise NotWorkflowAppError()

        parser = reqparse.RequestParser()
        parser.add_argument("from_pro", type=str, required=True, nullable=False, location="json")
        parser.add_argument("input_tb_id", type=str, required=True, nullable=False, location="json")
        parser.add_argument("input_tb_name", type=str, required=True, nullable=False, location="json")
        parser.add_argument("input_tb_fields", type=list, required=True, nullable=False, location="json")
        parser.add_argument("output_tb_fields", type=list, required=True, nullable=False, location="json")
        parser.add_argument("output_tb_name", type=str, required=True, nullable=False, location="json")
        parser.add_argument("output_tb_remark", type=str, required=True, nullable=False, location="json")
        parser.add_argument("mode", type=str, required=True, nullable=False, location="json")
        args = parser.parse_args()

        opendsClient = OpendsClient()

        if app_model.mode not in [AppMode.COMPLETION.value, AppMode.WORKFLOW.value]:
            raise ValueError("not workflow or completion app")

        if args["mode"] == "test":
            responses = []
            input_tb_id = args["input_tb_id"]
            input_tb_fields = args["input_tb_fields"]
            input_tb_field_ids = [field["fid"] for field in input_tb_fields]
            result = opendsClient.tb_data_query(input_tb_id, input_tb_field_ids, 5)
            if result == "":
                raise ValueError("table data query error")
            for data in result["data"]:
                inputs = {}
                for i, input_tb_field in enumerate(input_tb_fields):
                    inputs[input_tb_field["input"]] = data[i]
                try:
                    response = AppGenerateService.generate(
                        app_model=app_model, user=current_user, args={"inputs": inputs, "query": ""},
                        invoke_from=InvokeFrom.DEBUGGER, streaming=True
                    )
                    responses.append(response)

                except ProviderTokenNotInitError as ex:
                    raise ProviderNotInitializeError(ex.description)
                except QuotaExceededError:
                    raise ProviderQuotaExceededError()
                except ModelCurrentlyNotSupportError:
                    raise ProviderModelCurrentlyNotSupportError()
                except InvokeError as e:
                    raise CompletionRequestError(e.description)
                except ValueError as e:
                    raise e
                except Exception as e:
                    logging.exception("internal server error.")
                    raise InternalServerError()
            return helper.compact_generate_responses(responses)
        else:
            ds_id = ""
            if args["from_pro"] == "dmc":
                ds_list = opendsClient.ds_list()
                for ds in ds_list["data_source"]:
                    if ds["name"] == dify_config.OPENDS_AI_DS_NAME:
                        ds_id = ds["ds_id"]
                        for table in ds["tables"]:
                            if table[0] == args["output_tb_name"]:
                                raise ValueError("table name already exists")
                        break
                else:
                    ds_id = opendsClient.ds_create(dify_config.OPENDS_AI_DS_NAME)["ds_id"]
                dmc_tb_info = opendsClient.dmc_tb_info(args["input_tb_id"])
                if dmc_tb_info["data_count"] > dify_config.OPENDS_QUERY_LIMIT:
                    raise ValueError("table count more than %s" % dify_config.OPENDS_QUERY_LIMIT)
            if args["from_pro"] == "etl":
                etl_tb_list = opendsClient.etl_tb_list(args["output_tb_name"])
                if len(etl_tb_list) > 0:
                    raise ValueError("table name already exists")
                etl_tb_info = opendsClient.etl_tb_info(args["input_tb_id"])
                if etl_tb_info["data_count"] > dify_config.OPENDS_QUERY_LIMIT:
                    raise ValueError("table count more than %s" % dify_config.OPENDS_QUERY_LIMIT)
            installed_app_batch_run.delay(args=args, app_id=app_model.id, current_user=current_user.id, ds_id=ds_id)
            # installed_app_batch_run(args, app_model, current_user, ds_id)
            return {"result": "success"}


class BatchRunRecordApi(Resource):
    @login_required
    @account_initialization_required
    @marshal_with(batch_run_record_api_fields)
    def post(self):
        """
        Run workflow
        """
        parser = reqparse.RequestParser()
        parser.add_argument("keyword", type=str, location="args")
        parser.add_argument("page", type=int_range(1, 99999), default=1, location="args")
        parser.add_argument("limit", type=int_range(1, 100), default=20, location="args")
        args = parser.parse_args()
        query = db.select(InstalledAppBatchRunRecord)

        if args["keyword"]:
            query = query.filter(InstalledAppBatchRunRecord.app_name.ilike("%{}%".format(args["keyword"])))
        query = query.order_by(InstalledAppBatchRunRecord.created_at.desc())
        batch_run_record = db.paginate(query, page=args["page"], per_page=args["limit"], error_out=False)
        return batch_run_record


class InstalledAppBatchRunOutputApi(InstalledAppResource):
    def post(self, installed_app: InstalledApp):
        """
        Run workflow
        """
        app_model = installed_app.app
        app_mode = AppMode.value_of(app_model.mode)
        if app_mode != AppMode.WORKFLOW and app_mode != AppMode.COMPLETION:
            raise NotWorkflowAppError()
        if app_mode == AppMode.COMPLETION:
            return {"result": [{"node": "结束", "output": "answer"}]}, 200
        workflow_service = WorkflowService()
        workflow = workflow_service.get_draft_workflow(app_model=app_model)
        outputs = []
        for node in workflow.graph_dict["nodes"]:
            if node["data"]["type"] == "end":
                for output in node["data"]["outputs"]:
                    outputs.append({"node": node["data"]["title"], "output": output["variable"]})
        return {"result": outputs}, 200
