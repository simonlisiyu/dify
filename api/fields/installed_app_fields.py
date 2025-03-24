from flask_restful import fields  # type: ignore

from libs.helper import AppIconUrlField, TimestampField

# [Starry] directory installed app
app_fields = {
    "id": fields.String,
    "name": fields.String,
    "mode": fields.String,
    "icon_type": fields.String,
    "icon": fields.String,
    "icon_background": fields.String,
    "icon_url": AppIconUrlField,
    "use_icon_as_answer_icon": fields.Boolean,
    'description': fields.String,
    'account_name': fields.String,
}

tag_fields = {
    'id': fields.String,
    'name': fields.String,
    'type': fields.String
}

installed_app_fields = {
    "id": fields.String,
    "app": fields.Nested(app_fields),
    "app_owner_tenant_id": fields.String,
    "is_pinned": fields.Boolean,
    "last_used_at": TimestampField,
    "editable": fields.Boolean,
    "uninstallable": fields.Boolean,
    'is_favourite': fields.Boolean,
    'mode': fields.String,
    'conversation_account_count': fields.Integer,
    'conversation_count': fields.Integer,
    'favourite_account_count': fields.Integer,
    'tags': fields.List(fields.Nested(tag_fields))
}

installed_app_list_fields = {"installed_apps": fields.List(fields.Nested(installed_app_fields))}

installed_app_pagination_fields = {
    'page': fields.Integer,
    'limit': fields.Integer,
    'total': fields.Integer,
    'has_more': fields.Boolean,
    'data': fields.List(fields.Nested(installed_app_fields))
}

batch_run_record_api_field = {
    "id": fields.String,
    "tenant_id": fields.String,
    "app_id": fields.String,
    "app_name": fields.String,
    "from_pro": fields.String,
    "input_tb_id": fields.String,
    "input_tb_name": fields.String,
    "output_tb_id": fields.String,
    "output_tb_name": fields.String,
    "created_by": fields.String,
    'all_data_count': fields.Integer,
    'success_data_count': fields.Integer,
    'fail_data_count': fields.Integer,
    "created_at": TimestampField,
    "updated_at": TimestampField,
    "status": fields.Integer,
    "error_msg": fields.String
}

batch_run_record_api_fields = {
    "page": fields.Integer,
    "limit": fields.Integer(attribute="per_page"),
    "total": fields.Integer,
    "has_more": fields.Boolean(attribute="has_next"),
    "data": fields.List(fields.Nested(batch_run_record_api_field), attribute="items"),
}
