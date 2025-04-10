# [Starry] directory outer api
# __author__ "lisiyu"
# date 2024/11/30

from flask import Blueprint

from libs.external_api import ExternalApi

from .outer_services import DatasetApi, DatasetAddFileApi
from .sso_services import SSOLoginApi

# Outer
bp = Blueprint("outer_api", __name__, url_prefix="/outer/api")
api = ExternalApi(bp)

api.add_resource(DatasetApi, "/dataset/init")
api.add_resource(DatasetAddFileApi, "/dataset/file/init")

# Outer SSO
api.add_resource(SSOLoginApi, "/sso/login")
