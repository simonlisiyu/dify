# [Starry] directory
# __author__ "lisiyu"
# date 2024/8/22

import uuid
import logging
from datetime import datetime, timezone

from flask_login import current_user
from flask_restful import Resource, inputs, marshal, marshal_with, reqparse
from werkzeug.exceptions import BadRequest, Forbidden, NotFound, abort

from controllers.console import api
from controllers.console.wraps import account_initialization_required
from controllers.console.workspace.wraps import DirectoryResource
from models.model import Directory
from fields.directory_fields import directory_fields, dir_tree_fields
from libs.login import login_required
from services.directory_service import DirectoryService
from services.account_service import TenantService


def uuid_str(value):
    try:
        return str(uuid.UUID(value))
    except ValueError:
        abort(400, message="Invalid UUID format in parent_id.")


class DirectoryTreeApi(Resource):

    @login_required
    @account_initialization_required
    @marshal_with(dir_tree_fields)
    def get(self):
        """List all directory tree of current tenant."""

        current_user.role = TenantService.get_user_role(current_user, current_user.current_tenant)
        if current_user.role not in ["owner", "admin", "editor"]:
            return {'data': [], 'total': 0, 'page': 1, 'limit': 100, 'has_more': False}

        parser = reqparse.RequestParser()
        parser.add_argument('type', type=str, choices=['app', 'knowledge', 'tool'], default='app', location='args', required=False)
        args = parser.parse_args()

        # get dir tree
        dir_service = DirectoryService()
        dirs = dir_service.get_directory_tree(args)

        return {'dir_tree': dirs}

    @login_required
    @account_initialization_required
    def post(self):
        """Add a directory into tree."""

        current_user.role = TenantService.get_user_role(current_user, current_user.current_tenant)
        if current_user.role not in ["owner", "admin"]:
            return {'result': 'failed', 'message': 'only owner&admin can edit dir'}

        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        parser.add_argument('type', type=str, choices=['app', 'knowledge', 'tool'], required=True, help='only support app/knowledge/tool.')
        # parser.add_argument('level', type=inputs.int_range(0, 2), required=True, help='only support 0-2.')
        parser.add_argument('parent_id', type=uuid_str, location='json', required=False, default=None)
        args = parser.parse_args()
        logging.info(f"args={args}")

        try:
            dir_service = DirectoryService()
            directory = dir_service.create_directory(args)
        except Exception as e:
            logging.info(f"Exception={e}")
            raise BadRequest("create directory failed, please change another directory name.")

        return {'message': f'Directory created successfully',
                'directory_id': directory.id}


class DirectoryApi(DirectoryResource):

    @login_required
    @account_initialization_required
    def delete(self, directory):
        """Delete a directory."""

        current_user.role = TenantService.get_user_role(current_user, current_user.current_tenant)
        if current_user.role not in ["owner", "admin"]:
            return {'result': 'failed', 'message': 'only owner&admin can edit dir'}

        dir_service = DirectoryService()
        dir_service.delete_directory(directory)

        return {'result': 'success', 'message': 'Directory deleted successfully'}

    def patch(self, directory):
        """Update a directory's name."""

        current_user.role = TenantService.get_user_role(current_user, current_user.current_tenant)
        if current_user.role not in ["owner", "admin"]:
            return {'result': 'failed', 'message': 'only owner&admin can edit dir'}

        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True)
        args = parser.parse_args()
        logging.info(f"args={args}")

        try:
            directory_service = DirectoryService()
            directory_service.update_directory(directory, args['name'])
        except Exception as e:
            logging.info(f"Exception={e}")
            raise BadRequest("update directory failed, please change another directory name.")

        return {'result': 'success', 'message': 'Directory updated successfully'}

    @marshal_with(dir_tree_fields)
    def get(self, directory):
        """Detail a directory's subtree."""
        current_user.role = TenantService.get_user_role(current_user, current_user.current_tenant)
        if current_user.role not in ["owner", "admin"]:
            return {'result': 'failed', 'message': 'only owner&admin can edit dir'}

        parser = reqparse.RequestParser()
        parser.add_argument('type', type=str, choices=['app', 'knowledge', 'tool'], location='args', required=True,
                            help='only support app/knowledge/tool.')
        args = parser.parse_args()

        directory_service = DirectoryService()
        directory_with_sub = directory_service.get_directory_sub(args['type'], directory)

        return {'dir_tree': directory_with_sub}

    def put(self, directory):
        """Move a directory to another parent and change level."""

        current_user.role = TenantService.get_user_role(current_user, current_user.current_tenant)
        if current_user.role not in ["owner", "admin"]:
            return {'result': 'failed', 'message': 'only owner&admin can edit dir'}

        parser = reqparse.RequestParser()
        parser.add_argument('parent_id', type=uuid_str, required=True)
        args = parser.parse_args()
        logging.info(f"args={args}")

        directory_service = DirectoryService()
        directory_service.move_directory(directory, args['parent_id'])

        return {'result': 'success', 'message': 'Directory moved successfully'}


class DirectoryBindingCreateApi(Resource):

    @login_required
    @account_initialization_required
    def post(self):
        if not (current_user.is_editor or current_user.is_dataset_editor):
            raise Forbidden()

        parser = reqparse.RequestParser()
        parser.add_argument('target_ids', type=list, nullable=False, required=True, location='json',
                            help='target IDs is required.')
        parser.add_argument('directory_id', type=str, nullable=False, required=True, location='json',
                            help='Directory ID is required.')
        parser.add_argument('type', type=str, location='json',
                            choices=Directory.DIRECTORY_TYPE_LIST,
                            nullable=True,
                            help='Invalid type, only app/dataset/tool.')
        args = parser.parse_args()
        directory_service = DirectoryService()
        directory_service.delete_directory_binding(args['target_ids'], args['type'])
        directory_service.save_directory_binding(args['directory_id'], args['target_ids'], args['type'])

        return 200


class DirectoryBindingDeleteApi(Resource):

    @login_required
    @account_initialization_required
    def post(self):
        # The role of the current user in the ta table must be admin, owner, editor, or dataset_operator
        if not (current_user.is_editor or current_user.is_dataset_editor):
            raise Forbidden()

        parser = reqparse.RequestParser()
        parser.add_argument('target_ids', type=list, nullable=False, required=True,
                            help='Target ID is required.')
        parser.add_argument('type', type=str, location='json',
                            choices=Directory.DIRECTORY_TYPE_LIST,
                            nullable=True,
                            help='Invalid type, only app/dataset/tool.')
        args = parser.parse_args()
        directory_service = DirectoryService()
        directory_service.delete_directory_binding(args['target_ids'], args['type'])

        return 200



api.add_resource(DirectoryTreeApi, '/directory')
api.add_resource(DirectoryApi, '/directory/<uuid:directory_id>')
api.add_resource(DirectoryBindingCreateApi, '/directory-bindings/create')
api.add_resource(DirectoryBindingDeleteApi, '/directory-bindings/remove')
