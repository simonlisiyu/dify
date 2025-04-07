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
        parser.add_argument("output_tb_relation_fields", type=list, default=[], required=False, nullable=True, location="json")
        parser.add_argument("output_tb_name", type=str, required=True, nullable=False, location="json")
        parser.add_argument("output_tb_remark", type=str, required=True, nullable=False, location="json")
        parser.add_argument("folder_from", type=str, required=True, nullable=False, default="", location="json")
        parser.add_argument("mode", type=str, required=True, nullable=False, location="json")
        args = parser.parse_args()
        dmc_request = 0
        if args["from_pro"] == "dmc":
            dmc_request = 1

        opendsClient = OpendsClient()

        if app_model.mode not in [AppMode.COMPLETION.value, AppMode.WORKFLOW.value]:
            raise ValueError("not workflow or completion app")

        if args["mode"] == "test" or args["mode"] == "data":
            responses = []
            input_tb_id = args["input_tb_id"]
            input_tb_fields = args["input_tb_fields"]
            input_tb_field_ids = [field["fid"] for field in input_tb_fields]
            result = opendsClient.tb_data_query(input_tb_id, input_tb_field_ids, 5, dmc_request)
            if result == "":
                raise ValueError("工作表数据查询出错")
            if len(result["data"]) == 0:
                raise ValueError("工作表数据为空")
            if args["mode"] == "test":
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
                responses = []
                for data in result["data"]:
                    inputs = {}
                    for i, input_tb_field in enumerate(input_tb_fields):
                        inputs[input_tb_field["input"]] = data[i]
                    responses.append(inputs)
                return {"result": responses}, 200
        else:
            ds_id = ""
            if args["from_pro"] == "dmc":
                ds_list = opendsClient.ds_list()
                for ds in ds_list["data_source"]:
                    if ds["name"] == dify_config.OPENDS_AI_DS_NAME:
                        ds_id = ds["ds_id"]
                        for table in ds["tables"]:
                            if table[0] == args["output_tb_name"]:
                                raise ValueError("输出数据表名称已存在")
                        break
                else:
                    ds_id = opendsClient.ds_create(dify_config.OPENDS_AI_DS_NAME)["ds_id"]
                dmc_tb_info = opendsClient.dmc_tb_info(args["input_tb_id"])
                if dmc_tb_info["data_count"] == 0:
                    raise ValueError("工作表数据为空,无法运行")
                if dmc_tb_info["data_count"] > dify_config.OPENDS_QUERY_LIMIT:
                    raise ValueError("工作表数据量超过最大限制:%s条" % dify_config.OPENDS_QUERY_LIMIT)
                    # raise ValueError("table count more than %s" % dify_config.OPENDS_QUERY_LIMIT)
            if args["from_pro"] == "etl":
                etl_tb_list = opendsClient.etl_tb_list(args["output_tb_name"])
                if len(etl_tb_list) > 0:
                    raise ValueError("输出数据表名称已存在")
                etl_tb_info = opendsClient.etl_tb_info(args["input_tb_id"])
                if etl_tb_info["data_count"] == 0:
                    raise ValueError("工作表数据为空,无法运行")
                if etl_tb_info["data_count"] > dify_config.OPENDS_QUERY_LIMIT:
                    raise ValueError("工作表数据量超过最大限制:%s条" % dify_config.OPENDS_QUERY_LIMIT)
                    # raise ValueError("table count more than %s" % dify_config.OPENDS_QUERY_LIMIT)
            # 校验重名
            output_tb_fields = args["output_tb_fields"]
            output_tb_relation_fields = args["output_tb_relation_fields"]
            output_tb_relation_names = [field["name"] for field in output_tb_relation_fields]
            output_tb_field_names = [field["name"] for field in output_tb_fields]
            all_output_tb_field_names = output_tb_relation_names + output_tb_field_names
            # all_output_tb_field_names存在重复，并提示重复的字段
            if len(all_output_tb_field_names) != len(set(all_output_tb_field_names)):
                duplicate_fields = [field for field in all_output_tb_field_names if
                                    all_output_tb_field_names.count(field) > 1]
                raise ValueError("输出数据表字段名称重复: %s" % ", ".join(duplicate_fields))

            installed_app_batch_run.delay(args=args, app_id=app_model.id, current_user=current_user.id, ds_id=ds_id)
            # installed_app_batch_run(args, app_model, current_user, ds_id)
            return {"result": "success", "folder_name": dify_config.OPENDS_AI_DS_NAME}, 200


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
        batch_run_records = db.paginate(query, page=args["page"], per_page=args["limit"], error_out=False)
        for batch_run_record in batch_run_records.items:
            if batch_run_record.from_pro == "etl":
                input_tb_url = ""
                batch_run_record.output_tb_url = "%s/doraemon/#/datamodel/data-preview/%s?moduleName=dataPersonal" \
                                                 "&tbName=%s&type=opends&storageType=1&tbType=self&backId=folder_root" \
                                                 % (dify_config.DMC_HOST, batch_run_record.output_tb_id,
                                                    batch_run_record.output_tb_name)
                if batch_run_record.folder_from == "public_database":
                    input_tb_url = "%s/doraemon/#/datamodel/data-preview/%s?moduleName=dataPublish" \
                                                    "&tbName=%s&tbType=access"
                elif batch_run_record.folder_from == "personal_upload_database":
                    input_tb_url = "%s/doraemon/#/datamodel/data-preview/%s?moduleName=dataPersonal" \
                                                    "&tbName=%s&tbType=access"

                elif batch_run_record.folder_from == "dataflow_result_database":
                    input_tb_url = "%s/doraemon/#/datamodel/data-preview/%s?moduleName=dataModel" \
                                                    "&tbName=%s&type=flow"
                if input_tb_url:
                    batch_run_record.input_tb_url = input_tb_url % (
                        dify_config.DMC_HOST, batch_run_record.input_tb_id, batch_run_record.input_tb_name)
                else:
                    batch_run_record.input_tb_url = dify_config.DMC_HOST
            elif batch_run_record.from_pro == "dmc":
                batch_run_record.output_tb_url = "%s/tb-details/%s/data-preview?tbType=RAW" \
                                                 % (dify_config.DMC_HOST, batch_run_record.output_tb_id)
                if batch_run_record.folder_from == "MAP":
                    batch_run_record.input_tb_url = "%s/dmc/#/tb-lib/%s?viewType=preview&moduleName=map&tbName=%s" \
                                                     % (dify_config.DMC_HOST, batch_run_record.input_tb_id,
                                                        batch_run_record.input_tb_name)
                else:
                    batch_run_record.input_tb_url = "%s/tb-details/%s/data-preview?tbType=%s" \
                                                     % (dify_config.DMC_HOST, batch_run_record.input_tb_id,
                                                        batch_run_record.folder_from)

        return batch_run_records


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
        node_dict = {}
        for node in workflow.graph_dict["nodes"]:
            for variable in node["data"].get("variables", []):
                if "type" in variable and variable["type"] != "":
                    if "text-input" == variable["type"] or "paragraph" == variable["type"]:
                        node_dict["%s_%s" % (node["id"], variable["variable"])] = "string"
                    else:
                        node_dict["%s_%s" % (node["id"], variable["variable"])] = variable["type"]
            if "outputs" in node["data"] and type(node["data"]["outputs"]) == dict:
                for output_key, output_value in node["data"].get("outputs", {}).items():
                    if "type" in output_value and output_value["type"] != "":
                        node_dict["%s_%s" % (node["id"], output_key)] = output_value["type"]
        outputs = []
        for node in workflow.graph_dict["nodes"]:
            if node["data"]["type"] == "end":
                for output in node["data"]["outputs"]:
                    node_type = "string"
                    if "_".join(output["value_selector"]) in node_dict:
                        node_type = node_dict["_".join(output["value_selector"])]
                    outputs.append({"node": node["data"]["title"], "output": output["variable"], "type": node_type})
        return {"result": outputs}, 200
