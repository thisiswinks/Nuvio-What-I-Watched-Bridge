import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

VALID_ANIME_MODES = (
    "auto_native_preferred",
    "tvdb_hybrid_only",
    "native_only",
)


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


def _load_yaml_settings(path: str = "config.yaml") -> Dict[str, Any]:
    """Minimal strict reader for the config.yaml subset we use.

    Supports two-space-indented nested mappings with scalar values and inline
    ``#`` comments. Not a general YAML parser; lists and multi-line values are
    intentionally unsupported so config.yaml stays the single source of truth
    without adding a third-party dependency (AGENTS.md: stdlib only).
    """
    settings: Dict[str, Any] = {}
    if not os.path.isfile(path):
        return settings
    stack = [(-1, settings)]
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            indent = len(line) - len(line.lstrip(" "))
            key, _, value = line.strip().partition(":")
            key = key.strip()
            value = value.split("#", 1)[0].strip().strip("'\"")
            while stack and indent <= stack[-1][0]:
                stack.pop()
            parent = stack[-1][1]
            if value == "":
                child: Dict[str, Any] = {}
                parent[key] = child
                stack.append((indent, child))
            else:
                parent[key] = value
    return settings


def get_simkl_anime_mode(yaml_path: str = "config.yaml") -> str:
    """Resolve the Simkl anime routing mode.

    Env var ``SIMKL_ANIME_MODE`` overrides config.yaml
    (providers.simkl.anime_mode); default is ``auto_native_preferred``. An
    unknown value fails loud rather than silently defaulting.
    """
    settings = _load_yaml_settings(yaml_path)
    mode = os.getenv("SIMKL_ANIME_MODE")
    if not mode:
        mode = (
            settings.get("providers", {})
            .get("simkl", {})
            .get("anime_mode", "auto_native_preferred")
        )
    mode = str(mode).strip().lower()
    if mode not in VALID_ANIME_MODES:
        raise ValueError(
            f"Invalid Simkl anime_mode {mode!r}; expected one of {list(VALID_ANIME_MODES)}"
        )
    return mode


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
