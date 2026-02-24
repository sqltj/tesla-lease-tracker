import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

from .logger import logger

if TYPE_CHECKING:
    from .models import LeaseConfig, MileageReading


class AppData(BaseModel):
    """Root persistence object for JSON storage mode."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    lease_config: "LeaseConfig | None" = None
    readings: list["MileageReading"] = Field(default_factory=list)
    last_sync: datetime | None = None


class DataStore:
    """JSON file-backed persistence for lease data.

    Keeps ~1100 readings max over a 3-year lease — no database needed.
    """

    def __init__(self, path: Path) -> None:
        self._path = path
        self._data = AppData()
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                raw = self._path.read_text()
                self._data = AppData.model_validate_json(raw)
                logger.info(f"Loaded data from {self._path}")
            except Exception as e:
                logger.warning(f"Failed to load data from {self._path}: {e}")
                self._data = AppData()
        else:
            logger.info(f"No data file at {self._path}, starting fresh")

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(self._data.model_dump_json(indent=2))

    @property
    def data(self) -> AppData:
        return self._data


# Rebuild AppData model after imports complete to resolve forward references
def _rebuild_app_data():
    from .models import LeaseConfig, MileageReading
    AppData.model_rebuild()


_rebuild_app_data()
