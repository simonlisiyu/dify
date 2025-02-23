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
