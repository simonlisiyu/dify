from flask import Blueprint

from libs.external_api import ExternalApi

from .outer_services import DatasetApi, DatasetAddFileApi

bp = Blueprint("outer_api", __name__, url_prefix="/outer/api")
api = ExternalApi(bp)

# Outer
api.add_resource(DatasetApi, "/dataset/init")
api.add_resource(DatasetAddFileApi, "/dataset/file/init")
