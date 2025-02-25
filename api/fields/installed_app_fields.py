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
