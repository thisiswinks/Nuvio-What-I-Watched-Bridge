import unittest
from exporters.mal_sync import MALSyncAdapter
from exporters.simkl_sync import SimklSyncAdapter
from infrastructure.api_clients.nuvio_supabase import NuvioSupabaseAdapter

class TestSyncAdapters(unittest.TestCase):
    def test_mal_adapter_initialization(self):
        adapter = MALSyncAdapter(access_token="test_mal_token")
        self.assertEqual(adapter.access_token, "test_mal_token")
        self.assertEqual(adapter.rate_delay_ms, 600)

    def test_simkl_adapter_initialization(self):
        adapter = SimklSyncAdapter(client_id="test_client_id", access_token="test_simkl_token")
        self.assertEqual(adapter.client_id, "test_client_id")
        self.assertEqual(adapter.batch_size, 100)

    def test_nuvio_supabase_adapter_initialization(self):
        adapter = NuvioSupabaseAdapter(api_key="test_key", bearer_token="test_bearer")
        self.assertEqual(adapter.api_key, "test_key")
        self.assertEqual(adapter.bearer_token, "test_bearer")

if __name__ == "__main__":
    unittest.main()
