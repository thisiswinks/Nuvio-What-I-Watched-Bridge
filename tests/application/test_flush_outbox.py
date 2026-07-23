import unittest

from application.use_cases.flush_outbox import flush_outbox
from domain.models.canonical_ids import CanonicalIDs
from domain.models.canonical_item import CanonicalMediaItem
from infrastructure.api_clients.simkl import SimklSyncResult


class FakeSimkl:
    def __init__(self, result=None, raise_exc=None):
        self.result = result or SimklSyncResult(added=99)
        self.raise_exc = raise_exc
        self.calls = []

    def sync_history(self, routed):
        self.calls.append(routed)
        if self.raise_exc:
            raise self.raise_exc
        return self.result


def anime_item(**kwargs):
    ids = kwargs.pop("ids")
    item = CanonicalMediaItem(
        title=kwargs.pop("title", "Anime"), media_type="anime", is_anime=True, ids=ids
    )
    for k, v in kwargs.items():
        setattr(item, k, v)
    return item


class TestFlushOutboxSimkl(unittest.TestCase):
    def test_native_anime_synced_via_anime_envelope(self):
        item = anime_item(ids=CanonicalIDs(mal="21"), absolute_episode=403)
        simkl = FakeSimkl()
        results = flush_outbox([item], simkl_adapter=simkl)
        self.assertEqual(results["simkl"]["synced"], 1)
        self.assertEqual(item.outbox["simkl"].status, "synced")
        self.assertEqual(len(simkl.calls[0]["anime"]), 1)
        self.assertEqual(simkl.calls[0]["anime"][0]["ids"]["mal"], 21)

    def test_shared_parent_no_coords_quarantined_not_sent(self):
        item = anime_item(ids=CanonicalIDs(tmdb="1429"))
        simkl = FakeSimkl()
        results = flush_outbox([item], simkl_adapter=simkl)
        self.assertEqual(item.outbox["simkl"].status, "unmatched")
        self.assertTrue(item.outbox["simkl"].error_message)
        # Nothing routable -> no HTTP call at all
        self.assertEqual(simkl.calls, [])
        self.assertEqual(results["simkl"]["synced"], 0)

    def test_not_found_echo_marks_only_that_item(self):
        good = anime_item(title="Good", ids=CanonicalIDs(mal="21"), absolute_episode=1)
        bad = anime_item(title="Bad", ids=CanonicalIDs(mal="999"), absolute_episode=1)
        # Simkl echoes the bad one with an INTEGER id (str-vs-int match must work)
        result = SimklSyncResult(added=1, not_found=[{"ids": {"mal": 999}}])
        simkl = FakeSimkl(result=result)
        flush_outbox([good, bad], simkl_adapter=simkl)
        self.assertEqual(good.outbox["simkl"].status, "synced")
        self.assertEqual(bad.outbox["simkl"].status, "error")

    def test_partial_chunk_failure_attributes_to_failed_entries(self):
        a = anime_item(title="A", ids=CanonicalIDs(mal="1"), absolute_episode=1)
        b = anime_item(title="B", ids=CanonicalIDs(mal="2"), absolute_episode=1)
        # Build the result so B's entry is in the failed chunk.
        def sync_history(routed):
            entries = routed["anime"]
            return SimklSyncResult(added=1, errors=[{"reason": "HTTP 503", "entries": [entries[1]]}])
        simkl = FakeSimkl()
        simkl.sync_history = sync_history
        flush_outbox([a, b], simkl_adapter=simkl)
        self.assertEqual(a.outbox["simkl"].status, "synced")
        self.assertEqual(b.outbox["simkl"].status, "error")
        self.assertEqual(b.outbox["simkl"].retry_count, 1)

    def test_adapter_exception_sets_retry_and_message(self):
        item = anime_item(ids=CanonicalIDs(mal="21"), absolute_episode=1)
        simkl = FakeSimkl(raise_exc=RuntimeError("boom"))
        flush_outbox([item], simkl_adapter=simkl)
        self.assertEqual(item.outbox["simkl"].status, "error")
        self.assertEqual(item.outbox["simkl"].retry_count, 1)
        self.assertIn("boom", item.outbox["simkl"].error_message)

    def test_no_simkl_adapter_leaves_outbox_untouched(self):
        item = anime_item(ids=CanonicalIDs(mal="21"), absolute_episode=1)
        flush_outbox([item], simkl_adapter=None)
        self.assertEqual(item.outbox["simkl"].status, "pending")

    def test_already_unmatched_item_not_resent(self):
        item = anime_item(ids=CanonicalIDs(mal="21"), absolute_episode=1)
        item.outbox["simkl"].status = "unmatched"
        simkl = FakeSimkl()
        flush_outbox([item], simkl_adapter=simkl)
        self.assertEqual(simkl.calls, [])

    def test_native_only_mode_quarantines_hybrid_candidate(self):
        item = anime_item(ids=CanonicalIDs(tmdb="1429"), season=3, episode=13)
        simkl = FakeSimkl()
        flush_outbox([item], simkl_adapter=simkl, simkl_anime_mode="native_only")
        self.assertEqual(item.outbox["simkl"].status, "unmatched")
        self.assertEqual(simkl.calls, [])


if __name__ == "__main__":
    unittest.main()
