# [Starry] directory
# __author__ "lisiyu"
# date 2024/8/21

import logging
from flask_login import current_user
from flask_sqlalchemy.pagination import Pagination
from sqlalchemy import func
from werkzeug.exceptions import NotFound
from extensions.ext_database import db
from models.dataset import Dataset
from models.model import App, Directory, DirectoryBindings
from models.tools import ApiToolProvider


class DirectoryService:

    def get_sub_directorys(self, type: str, parent_id: str) -> Pagination | None:
        list = Directory.get_sub_dirs(type, parent_id)
        return list

    def get_directory_tree(self, args: dict) -> Pagination | None:
        dirs = Directory.generate_dir_tree(args['type'], None)
        return dirs

    def create_directory(self, args: dict) -> Directory:
        """
        Create directory
        :param args: args
        """
        new_directory = Directory(
            tenant_id=current_user.current_tenant_id,
            name=args['name'],
            type=args['type'],
            # level=args['level'],
            parent_id=args['parent_id']
        )
        db.session.add(new_directory)
        db.session.commit()

        return new_directory

    def get_directory_sub(self, type: str, directory: Directory) -> Directory:
        return Directory.generate_dir_tree(type, directory.id)

    def move_directory(self, directory: Directory, parent_id: str) -> None:
        directory.parent_id = parent_id
        db.session.commit()

    def update_directory(self, directory: Directory, name: str) -> None:
        """
        Update Directory's name
        :param directory: Directory
        :param name: name
        """
        directory.name = name
        db.session.commit()


    def delete_directory(self, directory: Directory) -> Directory:
        filters = [
            Directory.parent_id == directory.id
        ]
        sub_directory_example = db.session.query(Directory).filter(*filters).first()
        if sub_directory_example:
            raise NotFound(f'Directory {directory.id} can not be deleted, there is sub directory.')
        else:
            db.session.delete(directory)
            db.session.commit()

    def save_directory_binding(self, directory_id: str, target_ids: list[str], target_type: str):
        # save directory binding
        for target_id in target_ids:
            if target_type == 'knowledge':
                dataset = db.session.query(Dataset).filter(
                    Dataset.tenant_id == current_user.current_tenant_id,
                    Dataset.id == target_id
                ).first()
                dataset.directory_id = directory_id
                if not dataset:
                    raise NotFound("Dataset not found")
            elif target_type == 'app':
                app = db.session.query(App).filter(
                    App.tenant_id == current_user.current_tenant_id,
                    App.id == target_id
                ).first()
                app.directory_id = directory_id
                if not app:
                    raise NotFound("App not found")
            elif target_type == 'tool':
                tool = db.session.query(ApiToolProvider).filter(
                    ApiToolProvider.tenant_id == current_user.current_tenant_id,
                    ApiToolProvider.id == target_id
                ).first()
                tool.directory_id = directory_id
                if not tool:
                    raise NotFound("Tool not found")

            directory_binding = db.session.query(DirectoryBindings).filter(
                DirectoryBindings.target_id == target_id
            ).first()
            if directory_binding:
                continue
            new_directory_binding = DirectoryBindings(
                directory_id=directory_id,
                target_id=target_id,
                tenant_id=current_user.current_tenant_id,
                created_by=current_user.id
            )
            db.session.add(new_directory_binding)
        db.session.commit()

    def delete_directory_binding(self, target_ids: list[str], target_type: str):
        for target_id in target_ids:
            # check if target exists
            DirectoryService.check_target_exists(target_type, target_id)
            # delete directory binding
            directory_bindings = db.session.query(DirectoryBindings).filter(
                DirectoryBindings.target_id == target_id,
            ).first()
            if directory_bindings:
                db.session.delete(directory_bindings)

        db.session.commit()

    @staticmethod
    def check_target_exists(type: str, target_id: str):
        if type == 'knowledge':
            dataset = db.session.query(Dataset).filter(
                Dataset.tenant_id == current_user.current_tenant_id,
                Dataset.id == target_id
            ).first()
            if not dataset:
                raise NotFound("Dataset not found")
        elif type == 'app':
            app = db.session.query(App).filter(
                App.tenant_id == current_user.current_tenant_id,
                App.id == target_id
            ).first()
            if not app:
                raise NotFound("App not found")
        elif type == 'tool':
            tool = db.session.query(ApiToolProvider).filter(
                ApiToolProvider.tenant_id == current_user.current_tenant_id,
                ApiToolProvider.id == target_id
            ).first()
            if not tool:
                raise NotFound("Tool not found")
        else:
            raise NotFound("Invalid binding type")
