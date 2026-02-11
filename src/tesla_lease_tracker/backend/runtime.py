from pathlib import Path

from databricks.sdk import WorkspaceClient

from .config import AppConfig
from .data_store import DataStore


class Runtime:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        data_path = Path(config.data_file_path)
        self._data_store = DataStore(data_path)

    @property
    def ws(self) -> WorkspaceClient:
        # note - this workspace client is usually an SP-based client
        # in development it usually uses the DATABRICKS_CONFIG_PROFILE
        return WorkspaceClient()

    @property
    def data_store(self) -> DataStore:
        return self._data_store
