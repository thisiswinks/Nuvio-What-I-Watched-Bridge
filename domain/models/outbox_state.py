from dataclasses import dataclass
from typing import Optional

@dataclass
class ProviderOutboxState:
    status: str = "pending"  # Options: pending, synced, error, unmatched, skipped
    last_synced_at: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
