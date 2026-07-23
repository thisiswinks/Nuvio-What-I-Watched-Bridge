"""Backward-compatible re-export shim.

The Simkl sync adapter now lives in ``infrastructure/api_clients/simkl.py``
(AGENTS.md layer boundaries). This module is kept so existing imports keep
working; new code should import from the infrastructure package.
"""
from infrastructure.api_clients.simkl import (  # noqa: F401
    SimklSyncAdapter,
    SimklSyncResult,
    SIMKL_HISTORY_URL,
)

__all__ = ["SimklSyncAdapter", "SimklSyncResult", "SIMKL_HISTORY_URL"]
