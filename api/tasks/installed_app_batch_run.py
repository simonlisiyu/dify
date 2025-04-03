import datetime
import json
import logging
import traceback

from collections.abc import Mapping
from typing import Any
from celery import shared_task  # type: ignore
from models.model import Account, App, AppMode, EndUser, BatchRunRecordStatus
from core.app.entities.app_invoke_entities import InvokeFrom
from werkzeug.exceptions import InternalServerError
from core.opends.client import OpendsClient
from services.app_generate_service import AppGenerateService
from configs import dify_config
from extensions.ext_database import db
from models.model import InstalledAppBatchRun, InstalledAppBatchRunRecord


@shared_task(queue="dataset1")
def installed_app_batch_run(args: Mapping[str, Any], app_id: str, current_user: str, ds_id: str):
    app_model = db.session.query(App).filter(App.id == app_id).first()
    current_user = db.session.query(Account).filter(Account.id == current_user).first()
    name = args["output_tb_name"]
    remark = args["output_tb_remark"]
    input_tb_id = args["input_tb_id"]
    input_tb_fields = args["input_tb_fields"]
    folder_from = args["folder_from"]
    output_tb_relation_fields = args["output_tb_relation_fields"]
    input_tb_field_ids = [field["fid"] for field in input_tb_fields]
    output_tb_relation_field_ids = [field["fid"] for field in output_tb_relation_fields]
    all_query_tb_field_ids = output_tb_relation_field_ids + input_tb_field_ids
    dmc_request = 0
    if args["from_pro"] == "dmc":
        dmc_request = 1
    # 创建InstalledAppBatchRun
    installed_app_batch_run_model = db.session.query(InstalledAppBatchRun).filter(
        InstalledAppBatchRun.app_id == app_model.id).first()
    if installed_app_batch_run_model is None:
        installed_app_batch_run_model = InstalledAppBatchRun(app_id=app_model.id,
                                                             tenant_id=app_model.tenant_id,
                                                             created_by=current_user.id,
                                                             meta=json.dumps(args))
        db.session.add(installed_app_batch_run_model)
        db.session.commit()
    else:
        installed_app_batch_run_model.meta = json.dumps(args)
        db.session.add(installed_app_batch_run_model)
        db.session.commit()
    #
    installed_app_batch_run_record_model = InstalledAppBatchRunRecord(
        app_id=app_model.id,
        tenant_id=app_model.tenant_id,
        app_name=app_model.name,
        from_pro=args["from_pro"],
        input_tb_id=input_tb_id,
        input_tb_name=args["input_tb_name"],
        output_tb_id="",
        output_tb_name=name,
        created_by=current_user.id,
        all_data_count=0,
        success_data_count=0,
        fail_data_count=0,
        meta=json.dumps(args),
        status=BatchRunRecordStatus.NEW.value,
        folder_from=folder_from
    )
    db.session.add(installed_app_batch_run_record_model)
    db.session.commit()

    try:
        opendsClient = OpendsClient()
        # 创建工作表
        output_tb_fields = args["output_tb_fields"]
        output_relation_schema = [{
            "name": output_tb_field["name"],
            "type": output_tb_field["type"] if output_tb_field["type"] else "string",
            "remark": output_tb_field["remark"],
            "title": output_tb_field["name"]
        } for output_tb_field in output_tb_relation_fields]
        # input_schema = [{
        #     "name": "input_%s" % input_tb_field["input"],
        #     "type": "string",
        #     "remark": "",
        #     "title": "input_%s" % input_tb_field["input"]
        # } for input_tb_field in input_tb_fields]
        output_schema = [{
            "name": output_tb_field["name"],
            "type": output_tb_field["type"] if output_tb_field["type"] else "string",
            "remark": output_tb_field["remark"],
            "title": output_tb_field["name"]
        } for output_tb_field in output_tb_fields]
        # schema = output_relation_schema + input_schema + output_schema
        schema = output_relation_schema + output_schema
        fields = [field["name"] for field in schema]
        if args["from_pro"] == "dmc":
            output_tb_id = opendsClient.tb_create(name, ds_id, schema, name, remark)["tb_id"]
        else:
            output_tb_id = opendsClient.etl_tb_create(name, schema, name, remark)["tb_id"]

        result = opendsClient.tb_data_query(input_tb_id, all_query_tb_field_ids,
                                            dify_config.OPENDS_QUERY_LIMIT, dmc_request)

        installed_app_batch_run_record_model.output_tb_id = output_tb_id
        db.session.add(installed_app_batch_run_record_model)
        db.session.commit()

        output_datas = []
        success_data_count = 0
        fail_data_count = 0
        opends_tb_commit_limit = dify_config.OPENDS_TB_COMMIT_COUNT
        if result == "" or len(result["data"]) == 0:
            installed_app_batch_run_record_model.all_data_count = 0
            installed_app_batch_run_record_model.fail_data_count = fail_data_count
            installed_app_batch_run_record_model.success_data_count = success_data_count
            installed_app_batch_run_record_model.status = BatchRunRecordStatus.SUCCESS.value
            db.session.add(installed_app_batch_run_record_model)
            db.session.commit()
        else:
            installed_app_batch_run_record_model.all_data_count = result["df_length"]
            installed_app_batch_run_record_model.status = BatchRunRecordStatus.RUNNING.value
            db.session.add(installed_app_batch_run_record_model)
            db.session.commit()
            for i, data in enumerate(result["data"]):
                try:
                    inputs = {}
                    outputs = {}
                    for j, input_tb_field in enumerate(input_tb_fields):
                        inputs[input_tb_field["input"]] = data[len(output_tb_relation_fields) + j]
                    if app_model.mode == AppMode.COMPLETION.value:
                        response = AppGenerateService.generate(
                            app_model=app_model, user=current_user, args={"inputs": inputs, "query": ""},
                            invoke_from=InvokeFrom.EXPLORE.value, streaming=False
                        )
                        insert_data = data[0: len(output_tb_relation_fields)] + [response["answer"]]
                        # data.extend([response["answer"]])
                        output_datas.append(insert_data)
                    else:
                        response = AppGenerateService.generate(
                            app_model=app_model, user=current_user, args={"inputs": inputs, "query": ""},
                            invoke_from=InvokeFrom.DEBUGGER.value, streaming=True
                        )
                        response_list = []
                        while True:
                            try:
                                response_info = next(response)
                                response_list.append(response_info)
                            except StopIteration:
                               break
                        # response = helper.compact_generate_response(response)
                        # response_list = response.data.decode().strip("\n\n").split("\n\n")
                        for response_info in response_list:
                            response_info = json.loads(response_info.replace("data: ", ""))
                            if response_info["event"] == "node_finished" and response_info["data"]["node_type"] == "end" \
                                    and response_info["data"]["outputs"] is not None:
                                for output_key, output_value in response_info["data"]["outputs"].items():
                                    outputs[response_info["data"]["title"] + "_" + output_key] = output_value

                        output_data = []
                        for k, output_tb_field in enumerate(output_tb_fields):
                            output_data.append(outputs.get(output_tb_field["node"] + "_" + output_tb_field["output"], ""))
                        # data.extend(output_data)
                        insert_data = data[0: len(output_tb_relation_fields)] + output_data
                        output_datas.append(insert_data)
                    success_data_count += 1
                except Exception as e:
                    fail_data_count += 1
                    logging.exception("internal server error.")
                    continue
                if (i + 1) % opends_tb_commit_limit == 0:
                    opendsClient.tb_data_insert(output_tb_id, fields, output_datas)
                    installed_app_batch_run_record_model.success_data_count = success_data_count
                    installed_app_batch_run_record_model.fail_data_count = fail_data_count
                    installed_app_batch_run_record_model.status = BatchRunRecordStatus.RUNNING.value
                    db.session.add(installed_app_batch_run_record_model)
                    db.session.commit()
                    output_datas = []
            if len(output_datas) > 0:
                opendsClient.tb_data_insert(output_tb_id, fields, output_datas)
            opendsClient.tb_commit(output_tb_id)
            opendsClient.tb_update([output_tb_id])
            installed_app_batch_run_record_model.success_data_count = success_data_count
            installed_app_batch_run_record_model.fail_data_count = fail_data_count
            installed_app_batch_run_record_model.updated_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
            installed_app_batch_run_record_model.status = BatchRunRecordStatus.SUCCESS.value
            db.session.add(installed_app_batch_run_record_model)
            db.session.commit()
    except Exception as e:
        installed_app_batch_run_record_model.updated_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        installed_app_batch_run_record_model.status = BatchRunRecordStatus.FAIL.value
        installed_app_batch_run_record_model.error_msg = traceback.format_exc()
        db.session.add(installed_app_batch_run_record_model)
        db.session.commit()
