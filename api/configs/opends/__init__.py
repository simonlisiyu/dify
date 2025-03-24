from pydantic import (
    Field
)
from pydantic_settings import BaseSettings


class OpendsConfig(BaseSettings):
    """
    Security-related configurations for the application
    """

    OPENDS_URL: str = Field(
        description="opends url",
        default="",
    )

    OPENDS_ACCESS_TOKEN: str = Field(
        description="opends access token",
        default="",
    )

    OPENDS_AI_DS_NAME: str = Field(
        description="璇玑AI默认的数据源名称",
        default="璇玑AI",
    )

    OPENDS_QUERY_LIMIT: int = Field(
        description="查询OPENDS单表最大数据量",
        default=10000,
    )

    OPENDS_TB_COMMIT_COUNT: int = Field(
        description="OPENDS单次insert的数量",
        default=500,
    )
