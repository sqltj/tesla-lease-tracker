from importlib import resources
from pathlib import Path
from typing import ClassVar, Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .._metadata import app_name, app_slug

# project root is the parent of the src folder
project_root = Path(__file__).parent.parent.parent.parent
env_file = project_root / ".env"

if env_file.exists():
    load_dotenv(dotenv_path=env_file)


class DatabaseConfig(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(extra="ignore")
    port: int = Field(default=5432, validation_alias="PGPORT")
    database_name: str = Field(default="databricks_postgres")
    instance_name: str = Field(
        default="tesla-lease-tracker", validation_alias="PGAPPNAME"
    )


class AppConfig(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        env_file=env_file,
        env_prefix=f"{app_slug.upper()}_",
        extra="ignore",
        env_nested_delimiter="__",
    )
    app_name: str = Field(default=app_name)

    # Tesla API secrets (stored in Databricks secret scope)
    tesla_secret_scope: str = Field(default="tesla-lease-tracker")
    tesla_client_id_key: str = Field(default="tesla-client-id")
    tesla_client_secret_key: str = Field(default="tesla-client-secret")
    tesla_refresh_token_key: str = Field(default="tesla-refresh-token")
    tesla_api_region: str = Field(default="na")

    # Data persistence
    data_file_path: str = Field(default="data/app_data.json")
    storage_mode: Literal["database", "json"] = Field(default="database")

    # Database (Lakebase)
    db: DatabaseConfig = DatabaseConfig()

    # Zerobus Ingest
    zerobus_catalog: str = Field(default="main")
    zerobus_schema: str = Field(default="default")

    # Model Serving (set TESLA_LEASE_TRACKER_FORECAST_ENDPOINT on Databricks)
    forecast_endpoint: str | None = Field(default=None)

    @property
    def static_assets_path(self) -> Path:
        return Path(str(resources.files(app_slug))).joinpath("__dist__")
