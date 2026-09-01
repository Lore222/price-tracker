import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

DEFAULT_STATE_FILE = "state.json"


class StateStore:
    """Persistenza semplice su file JSON per lo stato del tracker.

    Usato per ricordare quali offerte sono già state notificate, così da
    evitare alert Telegram duplicati tra esecuzioni diverse (GH Actions ogni
    run parte da un processo nuovo, ma le esecuzioni locali in --loop e le
    run successive condiviscono questo file).
    """

    def __init__(self, state_file: str = DEFAULT_STATE_FILE):
        self.state_file = state_file
        self._data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if not os.path.exists(self.state_file):
            return {}
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                logger.warning("File di stato malformato (%s), riparto da zero", self.state_file)
                return {}
            return data
        except (OSError, ValueError) as e:
            logger.warning("Impossibile leggere lo stato (%s): %s. Riparto da zero.", self.state_file, e)
            return {}

    def save(self) -> None:
        """Salva lo stato su disco con scrittura atomica (tmp + replace)."""
        try:
            tmp = f"{self.state_file}.tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.state_file)
        except OSError as e:
            logger.error("Impossibile salvare lo stato (%s): %s", self.state_file, e)

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value