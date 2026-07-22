import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    simkl_client_id: str = ""
    simkl_client_secret: str = ""
    simkl_access_token: Optional[str] = None
    trakt_export_dir: str = "/Users/winks/Downloads/trakt-export-geekwinks"
    mal_export_file: str = "/Users/winks/Downloads/animelist_1784747731_-_11369504.xml"
    nuvio_export_file: str = "/Users/winks/Downloads/nuvio_custom_collection_2026-07-22.json"
    output_dir: str = "data/export"


def _load_dotenv(dotenv_path: str = ".env") -> None:
    """Helper to load key-value pairs from .env into os.environ if not already set."""
    if not os.path.isfile(dotenv_path):
        return
    try:
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception:
        pass


def load_config() -> Config:
    """Loads configuration settings from environment variables."""
    _load_dotenv()
    token = os.getenv("SIMKL_ACCESS_TOKEN")
    return Config(
        simkl_client_id=os.getenv("SIMKL_CLIENT_ID", ""),
        simkl_client_secret=os.getenv("SIMKL_CLIENT_SECRET", ""),
        simkl_access_token=token if token else None,
        trakt_export_dir=os.getenv("TRAKT_EXPORT_DIR", "/Users/winks/Downloads/trakt-export-geekwinks"),
        mal_export_file=os.getenv("MAL_EXPORT_FILE", "/Users/winks/Downloads/animelist_1784747731_-_11369504.xml"),
        nuvio_export_file=os.getenv("NUVIO_EXPORT_FILE", "/Users/winks/Downloads/nuvio_custom_collection_2026-07-22.json"),
        output_dir=os.getenv("OUTPUT_DIR", "data/export"),
    )
