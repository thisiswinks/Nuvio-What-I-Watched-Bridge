import io
import json
import logging
import unittest
import urllib.error
from contextlib import contextmanager
from unittest import mock

from infrastructure.api_clients.simkl import (
    SimklSyncAdapter,
    SimklSyncResult,
    SIMKL_HISTORY_URL,
)


class FakeResponse(io.BytesIO):
    def __init__(self, body: str, status: int = 200):
        super().__init__(body.encode("utf-8"))
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
        return False


def http_error(code, body="", headers=None):
    return urllib.error.HTTPError(
        SIMKL_HISTORY_URL, code, "err",
        headers or {}, io.BytesIO(body.encode("utf-8")),
    )


class TestSimklAdapter(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.adapter = SimklSyncAdapter(
            client_id="cid", access_token="secret-token", sleep_fn=lambda s: None
        )

    @contextmanager
    def patched(self, side_effect):
        def fake_urlopen(req, timeout=None):
            self.calls.append(req)
            result = side_effect.pop(0) if side_effect else FakeResponse("{}")
            if isinstance(result, Exception):
                raise result
            return result
        with mock.patch("urllib.request.urlopen", fake_urlopen):
            yield

    def test_posts_to_history_endpoint_with_envelopes(self):
        with self.patched([FakeResponse(json.dumps({"added": {"anime": 1}}))]):
            result = self.adapter.sync_history({"anime": [{"ids": {"mal": 21}}]})
        self.assertEqual(self.calls[0].full_url, SIMKL_HISTORY_URL)
        sent = json.loads(self.calls[0].data.decode())
        self.assertEqual(sent, {"anime": [{"ids": {"mal": 21}}]})
        self.assertEqual(result.added, 1)
        self.assertTrue(result.ok)

    def test_empty_payload_makes_no_calls(self):
        with self.patched([]):
            result = self.adapter.sync_history({"anime": [], "shows": []})
        self.assertEqual(self.calls, [])
        self.assertTrue(result.ok)
        self.assertEqual(result.sent, 0)

    def test_chunking_across_envelopes(self):
        self.adapter.batch_size = 2
        routed = {"movies": [{"i": 1}], "anime": [{"i": 2}, {"i": 3}]}
        with self.patched([FakeResponse("{}"), FakeResponse("{}")]):
            self.adapter.sync_history(routed)
        self.assertEqual(len(self.calls), 2)
        first = json.loads(self.calls[0].data.decode())
        self.assertEqual(sum(len(v) for v in first.values()), 2)

    def test_not_found_echo_collected(self):
        body = json.dumps({"added": {"anime": 1}, "not_found": {"anime": [{"ids": {"mal": 999}}]}})
        with self.patched([FakeResponse(body)]):
            result = self.adapter.sync_history({"anime": [{"ids": {"mal": 999}}]})
        self.assertEqual(result.not_found, [{"ids": {"mal": 999}}])

    def test_429_retry_after_honored_then_success(self):
        seq = [http_error(429, headers={"Retry-After": "1"}), FakeResponse(json.dumps({"added": {"anime": 1}}))]
        slept = []
        self.adapter._sleep = lambda s: slept.append(s)
        with self.patched(seq):
            result = self.adapter.sync_history({"anime": [{"ids": {"mal": 1}}]})
        self.assertEqual(slept, [1])
        self.assertEqual(result.added, 1)
        self.assertTrue(result.ok)

    def test_429_http_date_retry_after_falls_back_to_backoff(self):
        seq = [http_error(429, headers={"Retry-After": "not-a-number"}),
               FakeResponse(json.dumps({"added": {"anime": 1}}))]
        slept = []
        self.adapter._sleep = lambda s: slept.append(s)
        with self.patched(seq):
            self.adapter.sync_history({"anime": [{"ids": {"mal": 1}}]})
        self.assertTrue(slept and slept[0] > 0)

    def test_429_exhausts_retries_then_errors(self):
        seq = [http_error(429, headers={"Retry-After": "1"}) for _ in range(3)]
        with self.patched(seq):
            result = self.adapter.sync_history({"anime": [{"ids": {"mal": 1}}]})
        self.assertFalse(result.ok)
        self.assertEqual(result.errors[0]["entries"], [{"ids": {"mal": 1}}])

    def test_5xx_not_retried_marks_error(self):
        seq = [http_error(503, body="<html>bad gateway</html>")]
        with self.patched(seq):
            result = self.adapter.sync_history({"anime": [{"ids": {"mal": 1}}]})
        self.assertEqual(len(self.calls), 1)  # no retry
        self.assertFalse(result.ok)

    def test_401_distinct_token_message(self):
        with self.patched([http_error(401)]):
            result = self.adapter.sync_history({"anime": [{"ids": {"mal": 1}}]})
        self.assertIn("token expired", result.errors[0]["reason"])

    def test_timeout_not_retried_marks_error(self):
        seq = [TimeoutError("timed out")]
        with self.patched(seq):
            result = self.adapter.sync_history({"anime": [{"ids": {"mal": 1}}]})
        self.assertEqual(len(self.calls), 1)
        self.assertFalse(result.ok)

    def test_non_json_body_marks_error(self):
        with self.patched([FakeResponse("<html>oops</html>")]):
            result = self.adapter.sync_history({"anime": [{"ids": {"mal": 1}}]})
        self.assertFalse(result.ok)

    def test_empty_body_treated_as_accepted(self):
        with self.patched([FakeResponse("")]):
            result = self.adapter.sync_history({"anime": [{"ids": {"mal": 1}}]})
        self.assertTrue(result.ok)
        self.assertEqual(result.added, 1)

    def test_missing_added_key_tolerated(self):
        with self.patched([FakeResponse(json.dumps({"not_found": {}}))]):
            result = self.adapter.sync_history({"anime": [{"ids": {"mal": 1}}]})
        self.assertTrue(result.ok)

    def test_token_never_logged(self):
        buf = io.StringIO()
        handler = logging.StreamHandler(buf)
        logger = logging.getLogger("infrastructure.api_clients.simkl")
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        try:
            with self.patched([http_error(503, body="upstream unavailable")]):
                self.adapter.sync_history({"anime": [{"ids": {"mal": 1}}]})
        finally:
            logger.removeHandler(handler)
        self.assertNotIn("secret-token", buf.getvalue())

    def test_add_to_history_alias_returns_bool(self):
        with self.patched([FakeResponse(json.dumps({"added": {"shows": 1}}))]):
            ok = self.adapter.add_to_history([{"ids": {"simkl": 5}}])
        self.assertTrue(ok)
        sent = json.loads(self.calls[0].data.decode())
        self.assertIn("shows", sent)


if __name__ == "__main__":
    unittest.main()
