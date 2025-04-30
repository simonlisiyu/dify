# [Starry] directory
# __author__ "lisiyu"
# date 2024/8/23

from flask_restful import fields

directory_fields = {
    'id': fields.String,
    'name': fields.String,
    'type': fields.String,
    'level': fields.String,
    'parent_id': fields.String,
    'sub_dir': None,
    'binding_count': fields.Integer
}

directory_fields['sub_dir'] = fields.List(fields.Nested(directory_fields))

dir_tree_fields = {
    'dir_tree': fields.List(fields.Nested(directory_fields))
}
