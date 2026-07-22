import argparse
import sys
from pathlib import Path
from typing import List, Optional

from config import load_config
from extractors.mal_xml import MALXMLExtractor
from extractors.trakt_json import TraktJSONExtractor
from extractors.simkl_api import SimklAPIExtractor
from normalizer import normalize_all_sources
from deduplicator import deduplicate_items
from exporters.master_exporter import export_master_files
from exporters.reconciliation import export_reconciliation
from exporters.simkl_exporter import export_simkl_payload
from exporters.trakt_exporter import export_trakt_payload
from exporters.mal_exporter import export_mal_payload
from exporters.nuvio_exporter import export_nuvio_payload


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Media List Sync Pipeline - Extract, normalize, deduplicate, and export media lists."
    )
    parser.add_argument(
        "--refresh-api",
        action="store_true",
        help="Force refresh Simkl API cache and fetch fresh data from API",
    )
    return parser.parse_args(args)


def main(cli_args: Optional[List[str]] = None) -> None:
    args = parse_args(cli_args)
    cfg = load_config()

    print("==========================================")
    print("      Media List Sync Pipeline Starting   ")
    print("==========================================")

    # 1. Instantiate Extractors for the 3 specified input sources
    mal_extractor = MALXMLExtractor(cfg.mal_export_file)
    trakt_extractor = TraktJSONExtractor(cfg.trakt_export_dir)
    simkl_extractor = SimklAPIExtractor(
        client_id=cfg.simkl_client_id,
        access_token=cfg.simkl_access_token,
        force_refresh=args.refresh_api,
    )

    # 2. Extract Raw Objects
    print("\n[1/4] Extracting data from input sources (Simkl, Trakt, MyAnimeList)...")
    raw_mal = mal_extractor.extract()
    print(f"  - MAL XML: {len(raw_mal)} items extracted ({cfg.mal_export_file})")

    raw_trakt = trakt_extractor.extract()
    print(f"  - Trakt JSON: {len(raw_trakt)} items extracted ({cfg.trakt_export_dir})")

    raw_simkl = simkl_extractor.extract()
    simkl_count = 0
    if isinstance(raw_simkl, dict):
        simkl_count = sum(len(v) for v in raw_simkl.values() if isinstance(v, list))
    elif isinstance(raw_simkl, list):
        simkl_count = len(raw_simkl)
    print(f"  - Simkl API: {simkl_count} items extracted")

    raw_data = {
        "mal": raw_mal,
        "trakt": raw_trakt,
        "simkl": raw_simkl,
    }

    # 3. Normalize Sources
    print("\n[2/4] Normalizing items into canonical media records...")
    canonical_items = normalize_all_sources(raw_data)
    print(f"  - Total canonical records created: {len(canonical_items)}")

    # 4. Deduplicate & Reconcile
    print("\n[3/4] Running deduplication and reconciliation engine...")
    dedup_result = deduplicate_items(canonical_items)
    print(f"  - Confirmed unique items: {len(dedup_result.confirmed)}")
    print(f"  - Flagged for reconciliation: {len(dedup_result.flagged)}")

    # 5. Export Master Datasets & Reports & Target Payloads
    out_dir = Path(cfg.output_dir)
    print(f"\n[4/4] Exporting master datasets and target service payloads to '{out_dir}'...")

    export_master_files(dedup_result.confirmed, out_dir)
    print("  - Master datasets written (movies.json, shows.json, anime.json, combined_full.json, summary.md)")

    export_reconciliation(dedup_result.flagged, out_dir)
    print("  - Reconciliation reports written (reconciliation_flagged.json, reconciliation.md)")

    export_simkl_payload(dedup_result.confirmed, out_dir)
    print("  - Simkl import payload written (simkl_import.json)")

    export_trakt_payload(dedup_result.confirmed, out_dir)
    print("  - Trakt import payload written (trakt_import.json)")

    export_mal_payload(dedup_result.confirmed, out_dir)
    print("  - MAL import payload written (mal_import.xml)")

    export_nuvio_payload(dedup_result.confirmed, out_dir)
    print("  - Nuvio import payload written (nuvio_custom_collection.json)")

    print("\n==========================================")
    print("     Pipeline Execution Complete!         ")
    print("==========================================")


if __name__ == "__main__":
    main()
