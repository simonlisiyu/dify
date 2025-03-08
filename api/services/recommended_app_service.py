from typing import Optional

from configs import dify_config
from services.recommend_app.recommend_app_factory import RecommendAppRetrievalFactory
# [Starry] directory app
from extensions.ext_database import db
from models.model import AppMode, TemplateApp
import logging
import yaml
logger = logging.getLogger(__name__)


class RecommendedAppService:
    @classmethod
    def get_recommended_apps_and_categories(cls, language: str) -> dict:
        """
        Get recommended apps and categories.
        :param language: language
        :return:
        """
        mode = dify_config.HOSTED_FETCH_APP_TEMPLATES_MODE
        retrieval_instance = RecommendAppRetrievalFactory.get_recommend_app_factory(mode)()
        result = retrieval_instance.get_recommended_apps_and_categories(language)
        if not result.get("recommended_apps") and language != "en-US":
            result = (
                RecommendAppRetrievalFactory.get_buildin_recommend_app_retrieval().fetch_recommended_apps_from_builtin(
                    "en-US"
                )
            )

        return result

    @classmethod
    def get_recommend_app_detail(cls, app_id: str) -> Optional[dict]:
        """
        Get recommend app detail.
        :param app_id: app id
        :return:
        """
        mode = dify_config.HOSTED_FETCH_APP_TEMPLATES_MODE
        retrieval_instance = RecommendAppRetrievalFactory.get_recommend_app_factory(mode)()
        result: dict = retrieval_instance.get_recommend_app_detail(app_id)
        return result

    # [Starry] directory app
    @classmethod
    def _check_or_fix_dsl(cls, import_data: dict) -> dict:
        """
        Check or fix dsl

        :param import_data: import data
        """
        if not import_data.get('version'):
            import_data['version'] = "0.1.0"

        if not import_data.get('kind') or import_data.get('kind') != "app":
            import_data['kind'] = "app"

        # if import_data.get('version') != current_dsl_version:
        #     # Currently only one DSL version, so no difference checks or compatibility fixes will be performed.
        #     logger.warning(f"DSL version {import_data.get('version')} is not compatible "
        #                    f"with current version {current_dsl_version}, related to "
        #                    f"Starry version {dsl_to_strayy_version_mapping.get(current_dsl_version)}.")

        return import_data

    # [Starry] directory app
    @classmethod
    def create_template_app(cls, tenant_id: str, data: str, args: dict) -> TemplateApp:
        """
        Import from app dsl export data, create a new template
        :param tenant_id: tenant id
        :param data: import data
        :param args: request args
        """
        logger.info(f"data={data}")
        try:
            import_data = yaml.safe_load(data)
        except yaml.YAMLError:
            raise ValueError("Invalid YAML format in data argument.")

        # check or repair dsl version
        import_data = cls._check_or_fix_dsl(import_data)

        app_data = import_data.get('app')
        logger.info(f"app_data={app_data}")
        if not app_data:
            raise ValueError("Missing app in data argument")

        # get app basic info
        name = args.get("name") if args.get("name") else app_data.get('name')
        description = args.get("description") if args.get("description") else app_data.get('description', '')
        icon = args.get("icon") if args.get("icon") else app_data.get('icon')
        icon_background = args.get("icon_background") if args.get("icon_background") \
            else app_data.get('icon_background')
        category = args.get("category")
        app_mode = AppMode.value_of(app_data.get("mode"))

        # create recommended app
        template_app = TemplateApp(
            tenant_id=tenant_id,
            name=name,
            mode=app_mode.value,
            category=category,
            description=description,
            icon=icon,
            icon_background=icon_background,
            export_data=data
        )

        try:
            db.session.add(template_app)
            db.session.commit()
        except Exception:
            raise ValueError("import template failed, please change another template name.")

        return template_app

    # [Starry] directory recommend app
    @classmethod
    def get_template_app_detail(cls, app_id: str) -> Optional[dict]:
        """
        Get template app detail.
        :param app_id: app id
        :return:
        """
        # is in public recommended list
        recommended_app = db.session.query(TemplateApp).filter(
            TemplateApp.is_listed == True,
            TemplateApp.id == app_id
        ).first()

        if not recommended_app:
            return None

        return {
            'id': recommended_app.id,
            'name': recommended_app.name,
            'icon': recommended_app.icon,
            'icon_background': recommended_app.icon_background,
            'mode': recommended_app.mode,
            'export_data': recommended_app.export_data
        }

    # [Starry] directory recommend app
    @classmethod
    def get_template_apps_and_categories(cls, language: str) -> dict:
        """
        Fetch recommended apps from db template_apps table.
        :param language: language
        :return:
        """
        recommended_apps = db.session.query(TemplateApp).filter(
            TemplateApp.is_listed == True,
            TemplateApp.language == language
        ).all()

        categories = set()
        recommended_apps_result = []
        for recommended_app in recommended_apps:
            recommended_app_result = {
                'id': recommended_app.id,
                'app': {
                    'id': recommended_app.id,
                    'name': recommended_app.name,
                    'mode': recommended_app.mode,
                    'icon': recommended_app.icon,
                    'icon_background': recommended_app.icon_background
                },
                'app_id': recommended_app.id,
                'description': recommended_app.description,
                'copyright': recommended_app.copyright,
                'privacy_policy': recommended_app.privacy_policy,
                'custom_disclaimer': '',
                'category': recommended_app.category,
                'position': recommended_app.position,
                'is_listed': recommended_app.is_listed
            }
            recommended_apps_result.append(recommended_app_result)
            categories.add(recommended_app.category)  # add category to categories

        return {'recommended_apps': recommended_apps_result, 'categories': sorted(categories)}