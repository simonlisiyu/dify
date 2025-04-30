import logging

from core.tools.entities.api_entities import ToolProviderTypeApiLiteral
from core.tools.tool_manager import ToolManager
from services.tools.tools_transform_service import ToolTransformService

logger = logging.getLogger(__name__)


class ToolCommonService:
    # [Starry] directory tool
    @staticmethod
    def list_tool_providers(user_id: str, tenant_id: str, typ: ToolProviderTypeApiLiteral = None,
                            directory_id=None, created_start=None, created_end=None, account_id=None, order_by=None):
        """
        list tool providers

        :return: the list of tool providers
        """
        providers = ToolManager.list_providers_from_api(user_id, tenant_id, typ,
                                                    directory_id, created_start, created_end, account_id, order_by)
        logger.info(f"providers.size = {len(providers)}")

        # add icon
        for provider in providers:
            ToolTransformService.repack_provider(tenant_id=tenant_id, provider=provider)
        logger.info(f"finish repack providers.size = {len(providers)}")

        result = [provider.to_dict() for provider in providers]
        logger.info(f"result.size = {len(result)}")

        return result
