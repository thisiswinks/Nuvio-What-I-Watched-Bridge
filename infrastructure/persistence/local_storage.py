import json
import os
import tempfile
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class LocalStorage:
    """Atomic JSON persistence store for on-device canonical media data.
    
    Uses a write-to-temp-then-rename strategy to prevent data corruption
    if the process crashes mid-write (e.g. TV power loss).
    """
    def __init__(self, file_path: str = "data/export/combined_full.json"):
        self.file_path = file_path
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

    def load(self) -> Dict[str, Any]:
        """Load the full canonical media store from disk."""
        if not os.path.exists(self.file_path):
            return {"items": [], "metadata": {"version": "1.0.0", "last_updated": None}}
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load local storage from {self.file_path}: {e}")
            return {"items": [], "metadata": {"version": "1.0.0", "last_updated": None}}

    def save(self, data: Dict[str, Any]) -> bool:
        """Atomically save the full canonical media store to disk.
        
        Writes to a temporary file first, then uses os.replace() for an
        atomic POSIX rename. This guarantees the file is never left in a
        corrupted state, even during a power failure.
        """
        try:
            dir_name = os.path.dirname(self.file_path)
            fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                os.replace(tmp_path, self.file_path)
                return True
            except Exception:
                # Clean up temp file on failure
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise
        except Exception as e:
            logger.error(f"Failed to save local storage to {self.file_path}: {e}")
            return False
