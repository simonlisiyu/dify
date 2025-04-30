import logging

from flask_restful import (
    Resource,
    reqparse,  # type: ignore
)

from controllers.console import api
from controllers.console.wraps import account_initialization_required
from core.opends.client import OpendsClient
from libs.login import login_required

logger = logging.getLogger(__name__)


class OpendsDmcFolderTreeApi(Resource):
    @login_required
    @account_initialization_required
    def post(self):
        opendsClient = OpendsClient()
        response = opendsClient.dmc_folder_tree()
        return response


class OpendsDmcTbInfoApi(Resource):
    @login_required
    @account_initialization_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("tb_id", type=str, required=True, nullable=False, location="json")
        args = parser.parse_args()
        opendsClient = OpendsClient()
        response = opendsClient.dmc_tb_info(args.get("tb_id"))
        return response


class OpendsEtlFolderGetEtlTreeWithTbListApi(Resource):
    @login_required
    @account_initialization_required
    def post(self):
        opendsClient = OpendsClient()
        response = opendsClient.get_etl_tree_with_tblist()
        return response


class OpendsEtlFolderEtlListOnlyTbApi(Resource):
    @login_required
    @account_initialization_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("filter_tree", type=str, required=True, nullable=False, location="json")
        parser.add_argument("folder_id", type=str, required=True, nullable=False, location="json")
        args = parser.parse_args()
        opendsClient = OpendsClient()
        response = opendsClient.etl_list_only_tb(args.get("filter_tree"), args.get("folder_id"))
        return response


class OpendsEtlFilterApi(Resource):
    @login_required
    @account_initialization_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("filter_str", type=str, required=True, nullable=False, location="json")
        args = parser.parse_args()
        opendsClient = OpendsClient()
        response = opendsClient.etl_filter(args.get("filter_str"))
        return response


class OpendsEtlTbInfoApi(Resource):
    @login_required
    @account_initialization_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("tb_id", type=str, required=True, nullable=False, location="json")
        args = parser.parse_args()
        opendsClient = OpendsClient()
        response = opendsClient.etl_tb_info(args.get("tb_id"))
        return response


api.add_resource(OpendsDmcFolderTreeApi, "/opends/dmc/folder/tree")
api.add_resource(OpendsDmcTbInfoApi, "/opends/dmc/tb/info")
api.add_resource(OpendsEtlFolderGetEtlTreeWithTbListApi, "/opends/etl/folder/get_etl_tree_with_tblist")
api.add_resource(OpendsEtlFolderEtlListOnlyTbApi, "/opends/etl/folder/etl_list_only_tb")
api.add_resource(OpendsEtlFilterApi, "/opends/etl/folder/etl_filter")
api.add_resource(OpendsEtlTbInfoApi, "/opends/etl/tb/info")
