import logging

# [Starry] directory installed app
import uuid
from datetime import UTC, datetime
from typing import Any

from flask_login import current_user  # type: ignore
from flask_restful import Resource, inputs, marshal_with, reqparse  # type: ignore
from sqlalchemy import and_
from werkzeug.exceptions import BadRequest, Forbidden, NotFound, abort

from controllers.console import api
from controllers.console.explore.wraps import InstalledAppResource
from controllers.console.wraps import account_initialization_required, cloud_edition_billing_resource_check
from extensions.ext_database import db

# [Starry] directory installed app
# from fields.installed_app_fields import installed_app_list_fields
from fields.installed_app_fields import installed_app_pagination_fields
from libs.login import login_required
from models import App, InstalledApp, RecommendedApp
from models.model import Tag, TagBinding
from services.account_service import TenantService
from services.app_service import AppService
from services.installed_app_service import InstalledAppService


class InstalledAppsListApi(Resource):
    @login_required
    @account_initialization_required
    @marshal_with(installed_app_pagination_fields)
    def get(self):
        # [Starry] directory installed app
        # app_id = request.args.get("app_id", default=None, type=str)
        current_tenant_id = current_user.current_tenant_id

        def uuid_list(value):
            try:
                return [str(uuid.UUID(v)) for v in value.split(',')]
            except ValueError:
                abort(400, message="Invalid UUID format in tag_ids.")
        parser = reqparse.RequestParser()
        parser.add_argument('page', type=inputs.int_range(1, 99999), required=False, default=1, location='args')
        parser.add_argument('limit', type=inputs.int_range(1, 100), required=False, default=20, location='args')
        parser.add_argument('mode', type=str, choices=['chat', 'completion', 'workflow', 'agent-chat', 'advanced-chat', 'all'], default='all', location='args', required=False)
        parser.add_argument('name', type=str, location='args', required=False)
        parser.add_argument('tag_ids', type=uuid_list, location='args', required=False)
        parser.add_argument('account_id', type=str, location='args', required=False)
        parser.add_argument('is_favourite', type=int, location='args', required=False)
        parser.add_argument('app_id', type=int, location='args', default=None, required=False)
        args = parser.parse_args()

        if args['app_id']:
            installed_app_pagination = (
                db.session.query(InstalledApp)
                .filter(and_(InstalledApp.tenant_id == current_tenant_id, InstalledApp.app_id == args['app_id']))
                .all()
            )
        else:
            # installed_apps = db.session.query(InstalledApp).filter(InstalledApp.tenant_id == current_tenant_id).all()
            # [Starry] directory installed app
            app_service = AppService()
            apps = app_service.get_apps(current_user.current_tenant_id, args)
            if not apps:
                return {'data': [], 'total': 0, 'page': 1, 'limit': 20, 'has_more': False}
            installed_app_service = InstalledAppService()
            installed_app_pagination = installed_app_service.get_paginate_installed_apps(apps, args)
            if not installed_app_pagination:
                return {'data': [], 'total': 0, 'page': 1, 'limit': 20, 'has_more': False}

        # [Starry] directory installed app
        def tags(tenant_id, app_id):
            app_tags = db.session.query(Tag).join(
                TagBinding,
                Tag.id == TagBinding.tag_id
            ).filter(
                TagBinding.target_id == app_id,
                TagBinding.tenant_id == tenant_id,
                Tag.tenant_id == tenant_id,
                Tag.type == 'app'
            ).all()
            return app_tags or []

        current_user.role = TenantService.get_user_role(current_user, current_user.current_tenant)
        installed_app_list: list[dict[str, Any]] = [
            {
                "id": installed_app.id,
                "app": installed_app.app,
                "app_owner_tenant_id": installed_app.app_owner_tenant_id,
                "is_pinned": installed_app.is_pinned,
                "last_used_at": installed_app.last_used_at,
                "editable": current_user.role in {"owner", "admin"},
                "uninstallable": current_tenant_id == installed_app.app_owner_tenant_id,
                # [Starry] directory installed app
                'is_favourite': installed_app.is_favourite,
                'mode': installed_app.mode,
                'conversation_account_count': installed_app.conversation_account_count,
                'conversation_count': installed_app.conversation_count,
                'favourite_account_count': installed_app.favourite_account_count,
                'tags': tags(current_tenant_id, installed_app.app.id),
            }
            for installed_app in installed_app_pagination
            if installed_app.app is not None
        ]
        installed_app_list.sort(
            key=lambda app: (
                -app["is_pinned"],
                app["last_used_at"] is None,
                -app["last_used_at"].timestamp() if app["last_used_at"] is not None else 0,
            )
        )

        # [Starry] directory installed app
        logging.info(len(installed_app_list))
        # return {"installed_apps": installed_app_list}
        return {
            'page': installed_app_pagination.page,
            'limit': args['limit'],
            'total': installed_app_pagination.total,
            'has_more': installed_app_pagination.has_next,
            'data': installed_app_list
        }

    @login_required
    @account_initialization_required
    @cloud_edition_billing_resource_check("apps")
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument("app_id", type=str, required=True, help="Invalid app_id")
        args = parser.parse_args()

        recommended_app = RecommendedApp.query.filter(RecommendedApp.app_id == args["app_id"]).first()
        if recommended_app is None:
            raise NotFound("App not found")

        current_tenant_id = current_user.current_tenant_id
        app = db.session.query(App).filter(App.id == args["app_id"]).first()

        if app is None:
            raise NotFound("App not found")

        if not app.is_public:
            raise Forbidden("You can't install a non-public app")

        installed_app = InstalledApp.query.filter(
            and_(InstalledApp.app_id == args["app_id"], InstalledApp.tenant_id == current_tenant_id)
        ).first()

        if installed_app is None:
            # todo: position
            recommended_app.install_count += 1

            new_installed_app = InstalledApp(
                app_id=args["app_id"],
                tenant_id=current_tenant_id,
                app_owner_tenant_id=app.tenant_id,
                is_pinned=False,
                last_used_at=datetime.now(UTC).replace(tzinfo=None),
            )
            db.session.add(new_installed_app)
            db.session.commit()

        return {"message": "App installed successfully"}


class InstalledAppApi(InstalledAppResource):
    """
    update and delete an installed app
    use InstalledAppResource to apply default decorators and get installed_app
    """

    def delete(self, installed_app):
        if installed_app.app_owner_tenant_id == current_user.current_tenant_id:
            raise BadRequest("You can't uninstall an app owned by the current tenant")

        db.session.delete(installed_app)
        db.session.commit()

        return {"result": "success", "message": "App uninstalled successfully"}

    def patch(self, installed_app):
        parser = reqparse.RequestParser()
        parser.add_argument("is_pinned", type=inputs.boolean)
        # [Starry] directory installed app
        parser.add_argument('is_favourite', type=inputs.boolean)
        args = parser.parse_args()

        commit_args = False
        if "is_pinned" in args:
            installed_app.is_pinned = args["is_pinned"]
            commit_args = True
        elif "is_favourite" in args:
            installed_app_service = InstalledAppService()
            current_account_id = current_user.id
            installed_app_service.update_installed_app_favourite_pinned(installed_app, args['is_favourite'], current_account_id)

        if commit_args:
            db.session.commit()

        return {"result": "success", "message": "App info updated successfully"}


# [Starry] directory installed app
class InstalledAppFavouriteApi(InstalledAppResource):
    """
    create and delete an installed app favourite
    """
    def delete(self, installed_app):
        current_account_id = current_user.id
        installed_app_service = InstalledAppService()
        installed_app_service.delete_installed_app_favourite(installed_app, current_account_id)

        return {'result': 'success', 'message': 'Installed App Favourite deleted successfully'}

    def post(self, installed_app):
        current_account_id = current_user.id
        installed_app_service = InstalledAppService()
        new_installed_app_favourite = installed_app_service.create_installed_app_favourite(installed_app, current_account_id)

        return {'result': 'success', 'message': f'Installed App Favourite {new_installed_app_favourite.id} created successfully'}


api.add_resource(InstalledAppsListApi, "/installed-apps")
api.add_resource(InstalledAppApi, "/installed-apps/<uuid:installed_app_id>")
api.add_resource(InstalledAppFavouriteApi, '/installed-apps/<uuid:installed_app_id>/favourite')