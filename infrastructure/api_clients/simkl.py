"""Simkl sync adapter implementing the correct /sync/history write contract.

Sends pre-routed envelopes (``movies``/``shows``/``anime``) produced by
``domain.services.simkl_payload_router``. Parses Simkl's structured
``added``/``not_found`` response, attributes failures to the exact entries that
failed, and retries only on 429 (a rejected request that never wrote), never on
5xx/timeout where the write outcome is unknown.
"""
import json
import logging
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

SIMKL_HISTORY_URL = "https://api.simkl.com/sync/history"
ENVELOPES = ("movies", "shows", "anime")
MAX_RETRIES = 3
MAX_RETRY_AFTER_SECONDS = 60
_MAX_BODY_LOG = 500
_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


@dataclass
class SimklSyncResult:
    added: int = 0
    not_found: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    sent: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors


def _sanitize(text: str) -> str:
    return _CONTROL_CHARS.sub(" ", str(text))[:_MAX_BODY_LOG]


def _parse_retry_after(value: Optional[str]) -> Optional[int]:
    if not value:
        return None
    value = value.strip()
    if value.isdigit():
        return min(int(value), MAX_RETRY_AFTER_SECONDS)
    try:
        when = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    if when is None:
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    delta = (when - datetime.now(timezone.utc)).total_seconds()
    if delta <= 0:
        return 0
    return min(int(delta), MAX_RETRY_AFTER_SECONDS)


class SimklSyncAdapter:
    def __init__(
        self,
        client_id: str,
        access_token: str,
        batch_size: int = 100,
        sleep_fn: Callable[[float], None] = None,
    ):
        self.client_id = client_id
        self.access_token = access_token
        self.batch_size = batch_size
        self.base_url = "https://api.simkl.com"
        self._sleep = sleep_fn or (lambda _s: None)

    # -- public ----------------------------------------------------------

    def sync_history(self, routed: Dict[str, List[Dict[str, Any]]]) -> SimklSyncResult:
        """POST routed envelopes to /sync/history in bounded chunks.

        ``routed`` maps envelope name -> list of entries. Chunks are capped at
        ``batch_size`` entries per request across all envelopes combined.
        """
        result = SimklSyncResult()
        for chunk in self._chunks(routed):
            self._send_chunk(chunk, result)
        return result

    def add_to_history(self, anime_items: List[Dict[str, Any]]) -> bool:
        """Deprecated: legacy shows-only boolean contract. Prefer sync_history."""
        result = self.sync_history({"shows": list(anime_items)})
        return result.ok

    # -- internals -------------------------------------------------------

    def _chunks(self, routed: Dict[str, List[Dict[str, Any]]]):
        current: Dict[str, List[Dict[str, Any]]] = {}
        count = 0
        for envelope in ENVELOPES:
            for entry in routed.get(envelope, []) or []:
                current.setdefault(envelope, []).append(entry)
                count += 1
                if count >= self.batch_size:
                    yield current
                    current, count = {}, 0
        if count:
            yield current

    def _send_chunk(self, chunk: Dict[str, List[Dict[str, Any]]], result: SimklSyncResult) -> None:
        entries = [e for env in ENVELOPES for e in chunk.get(env, [])]
        result.sent += len(entries)
        data = json.dumps(chunk).encode("utf-8")

        attempt = 0
        while True:
            attempt += 1
            req = urllib.request.Request(
                SIMKL_HISTORY_URL,
                data=data,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "simkl-api-key": self.client_id,
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    body = resp.read().decode("utf-8", errors="ignore")
                self._parse_body(body, entries, result)
                return
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < MAX_RETRIES:
                    delay = _parse_retry_after(e.headers.get("Retry-After")) if e.headers else None
                    if delay is None:
                        delay = min(2 ** attempt, MAX_RETRY_AFTER_SECONDS)
                    logger.warning("Simkl 429 rate limited; retry %s after %ss", attempt, delay)
                    self._sleep(delay)
                    continue
                self._fail_chunk(entries, result, self._http_reason(e))
                return
            except Exception as e:  # noqa: BLE001 - network/timeout: unknown outcome
                # 5xx/timeout: the write may have landed. Do NOT retry in-call;
                # surface for outbox-cycle retry so we never double-write.
                self._fail_chunk(entries, result, f"transport error: {_sanitize(e)}")
                return

    @staticmethod
    def _http_reason(e: urllib.error.HTTPError) -> str:
        body = ""
        try:
            body = _sanitize(e.read().decode("utf-8", errors="ignore"))
        except Exception:  # noqa: BLE001
            pass
        if e.code == 401:
            return "Simkl token expired or invalid (401)"
        return f"Simkl HTTP {e.code}: {body}"

    def _parse_body(self, body: str, entries: List[Dict[str, Any]], result: SimklSyncResult) -> None:
        if not body.strip():
            # Empty 200 body: Simkl accepted the write with no echo.
            result.added += len(entries)
            return
        try:
            payload = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            logger.error("Simkl returned non-JSON body: %s", _sanitize(body))
            self._fail_chunk(entries, result, "non-JSON response body")
            return
        added = payload.get("added") or {}
        if isinstance(added, dict):
            result.added += sum(v for v in added.values() if isinstance(v, int))
        not_found = payload.get("not_found") or {}
        rejected = []
        if isinstance(not_found, dict):
            for env in ENVELOPES:
                rejected.extend(not_found.get(env, []) or [])
        elif isinstance(not_found, list):
            rejected = not_found
        result.not_found.extend(rejected)

    @staticmethod
    def _fail_chunk(entries: List[Dict[str, Any]], result: SimklSyncResult, reason: str) -> None:
        logger.error("Simkl chunk failed (%d entries): %s", len(entries), reason)
        result.errors.append({"reason": reason, "entries": entries})
