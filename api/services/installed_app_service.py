# [Starry] directory installed app
# __author__ "lisiyu"
# date 2024/8/21

import logging
from collections import Counter, defaultdict

from flask_login import current_user
from flask_sqlalchemy.pagination import Pagination

from extensions.ext_database import db
from models.model import App, Conversation, InstalledApp, InstalledAppFavourite, Message
from models.workflow import WorkflowAppLog


class InstalledAppService:
    def get_paginate_installed_apps(self, apps: list[App], args: dict) -> Pagination | None:
        """
        Get app list with pagination
        :param tenant_id: tenant id or account id
        :param args: request args
        :return:
        """
        # app ids
        app_id_map = {app.id: app for app in apps}
        app_ids = list(app_id_map.keys())
        logging.info(f"app_ids={app_ids}")

        # get favourite_apps, cal distinct(account) per app_id, my_account is_favourite
        favouriteFilters = [
            InstalledAppFavourite.app_id.in_(app_ids)
        ]
        installed_app_favourite = db.session.query(InstalledAppFavourite).filter(*favouriteFilters).all()
        favourite_app_map = {}
        favourite_app_distinct_account_count = defaultdict(set)
        for favourite in installed_app_favourite:
            favourite_app_distinct_account_count[favourite.app_id].add(favourite.account_id)
            if current_user.id == favourite.account_id:
                favourite_app_map[favourite.app_id] = favourite
        # filter my_account favourite
        if args.get('is_favourite'):
            app_ids = list(favourite_app_map.keys())
            logging.info(f"filtered_app_ids={app_ids}")

        # get installed_apps
        filters = [
            InstalledApp.position == 1,
            InstalledApp.app_id.in_(app_ids)
        ]

        installed_apps = db.paginate(
            db.select(InstalledApp).where(*filters).order_by(InstalledApp.created_at.desc()),
            page=args['page'],
            per_page=args['limit'],
            error_out=False
        )
        logging.info(f"installed_apps={installed_apps.total}")

        # cal count(conversation) and distinct(account) per app_id
        conversation_filters = [
            Conversation.app_id.in_(app_ids)
        ]
        conversations = db.session.query(Conversation).filter(*conversation_filters).all()
        app_id_counter = Counter(conv.app_id for conv in conversations)
        # app_id_distinct_account_count = defaultdict(set)
        # for conv in conversations:
        #     app_id_distinct_account_count[conv.app_id].add(conv.from_account_id)

        # cal count(messages) or count(workflow-app-logs) per app_id
        message_filters = [
            Message.app_id.in_(app_ids)
        ]
        messages = db.session.query(Message).filter(*message_filters).all()
        message_counter = Counter(msg.app_id for msg in messages)
        if len(messages) == 0:
            workflow_message_filters = [
                WorkflowAppLog.app_id.in_(app_ids)
            ]
            messages = db.session.query(WorkflowAppLog).filter(*workflow_message_filters).all()
            message_counter = Counter(msg.app_id for msg in messages)

        # 遍历: add mode, replace is_pinned&favourite, count conversation&account
        for installed_app in installed_apps.items:
            installed_app.app = app_id_map[installed_app.app_id]
            installed_app.description = app_id_map[installed_app.app_id].description
            if installed_app.app_id in favourite_app_map:
                installed_app.is_pinned = favourite_app_map[installed_app.app_id].is_pinned
                installed_app.is_favourite = True
            if message_counter[installed_app.app_id]:
                installed_app.conversation_account_count = message_counter[installed_app.app_id]
            if app_id_counter[installed_app.app_id]:
                # installed_app.conversation_account_count = len(app_id_distinct_account_count[installed_app.app_id])
                installed_app.conversation_count = app_id_counter[installed_app.app_id]
            if favourite_app_distinct_account_count[installed_app.app_id]:
                installed_app.favourite_account_count = len(favourite_app_distinct_account_count[installed_app.app_id])

        return installed_apps

    def create_installed_app_favourite(self, installed_app: InstalledApp, account_id: str) -> InstalledAppFavourite:
        """
        Create installed_app_favourite
        :param installed_app: InstalledApp
        :param account_id: account_id
        """
        new_installed_app_favourite = InstalledAppFavourite(
            installed_app_id=installed_app.id,
            app_id=installed_app.app_id,
            account_id=account_id,
            is_pinned=False,
        )
        db.session.add(new_installed_app_favourite)
        db.session.commit()

        return new_installed_app_favourite

    def delete_installed_app_favourite(self, installed_app: InstalledApp, account_id: str) -> None:
        filters = [
            InstalledAppFavourite.account_id == account_id,
            InstalledAppFavourite.installed_app_id == installed_app.id
        ]
        db.session.query(InstalledAppFavourite).filter(*filters).delete(synchronize_session=False)
        db.session.commit()

    def update_installed_app_pinned(self, installed_app: InstalledApp, is_pinned: bool) -> None:
        """
        Update installed_app is_pinned
        :param installed_app: InstalledApp
        :param is_pinned: is_pinned
        """
        installed_app.is_pinned = is_pinned
        db.session.commit()

    def update_installed_app_favourite_pinned(self, installed_app: InstalledApp, is_pinned: bool, account_id: str) -> None:
        """
        Update installed_app is_pinned
        :param installed_app: InstalledApp
        :param is_pinned: is_pinned
        """
        filters = [
            InstalledAppFavourite.account_id == account_id,
            InstalledAppFavourite.installed_app_id == installed_app.id
        ]
        installedAppFavourite = db.session.query(InstalledAppFavourite).filter(*filters).first()
        installedAppFavourite.is_pinned = is_pinned
        db.session.commit()
