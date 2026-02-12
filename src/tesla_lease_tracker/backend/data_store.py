import json
from pathlib import Path

from .logger import logger
from .models import AppData


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
