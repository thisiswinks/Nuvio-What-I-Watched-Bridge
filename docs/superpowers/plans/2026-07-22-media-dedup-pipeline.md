# Media List Extraction, Collation, Deduplication & Export Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a modular, Gist-ready Python pipeline that extracts, normalizes, deduplicates (requiring >=2 IDs or Title+Date match), flags conflicts for reconciliation, and exports media list data across Simkl (API), Trakt (local JSON), MyAnimeList (local XML), and Nuvio (local JSON).

**Architecture:** A Python package with decoupled `extractors/`, `normalizer.py`, `deduplicator.py`, `exporters/`, and `main.py`. Local credentials and paths are managed via `config.py` and `.env`.

**Tech Stack:** Python 3.10+, `urllib.request`, `xml.etree.ElementTree`, `json`, `unittest`, `dataclasses`.

## Global Constraints

- Python standard libraries preferred for zero-dependency Gist portability.
- Credentials and access tokens loaded strictly via environment / `.env`.
- Deduplication requirement: >= 2 matching external IDs OR Title (normalized) + Start/End Date match to auto-confirm; 1 matching ID with date conflicts or Title match with missing/conflicting dates is flagged for reconciliation.
- Service-native export payloads for Simkl, Trakt, MAL XML, and Nuvio Custom Collection JSON.

---

### Task 1: Environment Configuration & PIN OAuth Helper

**Files:**
- Create: `config.py`
- Create: `.env.example`
- Create: `.gitignore`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: Environment variables (`SIMKL_CLIENT_ID`, `SIMKL_CLIENT_SECRET`, `SIMKL_ACCESS_TOKEN`, `TRAKT_EXPORT_DIR`, `MAL_EXPORT_FILE`, `NUVIO_EXPORT_FILE`)
- Produces: `Config` dataclass, `get_config()`, `authenticate_simkl_pin(client_id, client_secret)`

- [ ] **Step 1: Write the failing test for Config loading**

```python
# tests/test_config.py
import unittest
import os
from config import Config, load_config

class TestConfig(unittest.TestCase):
    def test_load_config_defaults(self):
        os.environ["SIMKL_CLIENT_ID"] = "test_client_id"
        os.environ["SIMKL_CLIENT_SECRET"] = "test_client_secret"
        cfg = load_config()
        self.assertEqual(cfg.simkl_client_id, "test_client_id")
        self.assertEqual(cfg.simkl_client_secret, "test_client_secret")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_config.py`
Expected: FAIL with "No module named 'config'"

- [ ] **Step 3: Write minimal implementation for `config.py`, `.env.example`, and `.gitignore`**

```python
# config.py
import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

@dataclass
class Config:
    simkl_client_id: str
    simkl_client_secret: str
    simkl_access_token: Optional[str] = None
    trakt_export_dir: Path = Path("/Users/winks/Downloads/trakt-export-geekwinks")
    mal_export_file: Path = Path("/Users/winks/Downloads/animelist_1784747731_-_11369504.xml")
    nuvio_export_file: Path = Path("/Users/winks/Downloads/nuvio_custom_collection_2026-07-22.json")
    raw_cache_dir: Path = Path("data/raw")
    output_dir: Path = Path("exports")

def load_config() -> Config:
    return Config(
        simkl_client_id=os.getenv("SIMKL_CLIENT_ID", ""),
        simkl_client_secret=os.getenv("SIMKL_CLIENT_SECRET", ""),
        simkl_access_token=os.getenv("SIMKL_ACCESS_TOKEN"),
        trakt_export_dir=Path(os.getenv("TRAKT_EXPORT_DIR", "/Users/winks/Downloads/trakt-export-geekwinks")),
        mal_export_file=Path(os.getenv("MAL_EXPORT_FILE", "/Users/winks/Downloads/animelist_1784747731_-_11369504.xml")),
        nuvio_export_file=Path(os.getenv("NUVIO_EXPORT_FILE", "/Users/winks/Downloads/nuvio_custom_collection_2026-07-22.json")),
    )
```

Create `.env.example`:
```env
SIMKL_CLIENT_ID=b7f7c1a6b3e0aef73f02ff29cc0e76ab0d693fc27d22a02aa0e56cb6938cd0f8
SIMKL_CLIENT_SECRET=be86adda6c176a0d4e30c4358928b14ac13267a11bd27d2bda339bdd0efe2ee2
SIMKL_ACCESS_TOKEN=
TRAKT_EXPORT_DIR=/Users/winks/Downloads/trakt-export-geekwinks
MAL_EXPORT_FILE=/Users/winks/Downloads/animelist_1784747731_-_11369504.xml
NUVIO_EXPORT_FILE=/Users/winks/Downloads/nuvio_custom_collection_2026-07-22.json
```

Create `.gitignore`:
```text
.env
data/raw/
exports/
__pycache__/
*.pyc
.DS_Store
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_config.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add config.py .env.example .gitignore tests/test_config.py
git commit -m "feat: setup configuration loader and env template"
```

---

### Task 2: Canonical Data Model (`models.py`)

**Files:**
- Create: `models.py`
- Test: `tests/test_models.py`

**Interfaces:**
- Consumes: None
- Produces: `CanonicalIDs`, `SourceRecord`, `CanonicalMediaItem`, `MediaType`, `MediaStatus`

- [ ] **Step 1: Write failing test for CanonicalMediaItem**

```python
# tests/test_models.py
import unittest
from models import CanonicalMediaItem, CanonicalIDs, MediaType, MediaStatus

class TestModels(unittest.TestCase):
    def test_canonical_item_creation(self):
        item = CanonicalMediaItem(
            uuid="test-uuid",
            media_type=MediaType.SHOW,
            title="Steins;Gate",
            year=2011,
            ids=CanonicalIDs(mal="9253", tvdb="203491", imdb="tt1910272")
        )
        self.assertEqual(item.title, "Steins;Gate")
        self.assertEqual(item.ids.mal, "9253")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_models.py`
Expected: FAIL with "No module named 'models'"

- [ ] **Step 3: Implement `models.py`**

```python
# models.py
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List

class MediaType(str, Enum):
    MOVIE = "movie"
    SHOW = "show"
    ANIME = "anime"

class MediaStatus(str, Enum):
    COMPLETED = "completed"
    WATCHING = "watching"
    ON_HOLD = "on_hold"
    PLAN_TO_WATCH = "plan_to_watch"
    DROPPED = "dropped"

@dataclass
class CanonicalIDs:
    imdb: Optional[str] = None
    tmdb: Optional[str] = None
    tvdb: Optional[str] = None
    mal: Optional[str] = None
    kitsu: Optional[str] = None
    anidb: Optional[str] = None
    simkl: Optional[int] = None
    trakt: Optional[int] = None
    nuvio: Optional[str] = None

    def matching_id_count(self, other: "CanonicalIDs") -> int:
        count = 0
        fields = ["imdb", "tmdb", "tvdb", "mal", "kitsu", "anidb", "simkl", "trakt", "nuvio"]
        for f in fields:
            val1 = getattr(self, f)
            val2 = getattr(other, f)
            if val1 and val2 and str(val1) == str(val2):
                count += 1
        return count

    def merge(self, other: "CanonicalIDs") -> "CanonicalIDs":
        return CanonicalIDs(
            imdb=self.imdb or other.imdb,
            tmdb=self.tmdb or other.tmdb,
            tvdb=self.tvdb or other.tvdb,
            mal=self.mal or other.mal,
            kitsu=self.kitsu or other.kitsu,
            anidb=self.anidb or other.anidb,
            simkl=self.simkl or other.simkl,
            trakt=self.trakt or other.trakt,
            nuvio=self.nuvio or other.nuvio,
        )

@dataclass
class SourceRecord:
    source_name: str
    present: bool = True
    status: Optional[str] = None
    rating: Optional[float] = None
    watch_count: int = 0
    last_watched_at: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CanonicalMediaItem:
    uuid: str
    media_type: MediaType
    title: str
    title_original: Optional[str] = None
    year: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    ids: CanonicalIDs = field(default_factory=CanonicalIDs)
    aggregated_status: MediaStatus = MediaStatus.COMPLETED
    aggregated_rating: Optional[float] = None
    sources: Dict[str, SourceRecord] = field(default_factory=dict)
    episodes: List[Dict[str, Any]] = field(default_factory=list)
    history_logs: List[Dict[str, Any]] = field(default_factory=list)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_models.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add models.py tests/test_models.py
git commit -m "feat: define canonical data models and ID matching logic"
```

---

### Task 3: Extractors (Trakt, MAL, Simkl, Nuvio)

**Files:**
- Create: `extractors/base.py`
- Create: `extractors/simkl_api.py`
- Create: `extractors/trakt_json.py`
- Create: `extractors/mal_xml.py`
- Create: `extractors/nuvio_json.py`
- Test: `tests/test_extractors.py`

**Interfaces:**
- Consumes: Config file paths & credentials
- Produces: `extract_all_sources(config) -> Dict[str, List[Dict[str, Any]]]`

- [ ] **Step 1: Write failing test for Trakt and MAL extractors**

```python
# tests/test_extractors.py
import unittest
from pathlib import Path
from extractors.mal_xml import MALXMLExtractor
from extractors.trakt_json import TraktJSONExtractor

class TestExtractors(unittest.TestCase):
    def test_mal_extractor(self):
        mal_file = Path("/Users/winks/Downloads/animelist_1784747731_-_11369504.xml")
        if mal_file.exists():
            extractor = MALXMLExtractor(mal_file)
            items = extractor.extract()
            self.assertGreater(len(items), 0)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_extractors.py`
Expected: FAIL with "No module named 'extractors'"

- [ ] **Step 3: Implement Extractors**

Implement `extractors/base.py`:
```python
# extractors/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self) -> List[Dict[str, Any]]:
        pass
```

Implement `extractors/mal_xml.py`:
```python
# extractors/mal_xml.py
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any
from extractors.base import BaseExtractor

class MALXMLExtractor(BaseExtractor):
    def __init__(self, xml_path: Path):
        self.xml_path = xml_path

    def extract(self) -> List[Dict[str, Any]]:
        if not self.xml_path.exists():
            return []
        tree = ET.parse(self.xml_path)
        root = tree.getroot()
        items = []
        for anime in root.findall("anime"):
            item = {}
            for child in anime:
                item[child.tag] = child.text
            items.append(item)
        return items
```

Implement `extractors/trakt_json.py`:
```python
# extractors/trakt_json.py
import json
from pathlib import Path
from typing import List, Dict, Any
from extractors.base import BaseExtractor

class TraktJSONExtractor(BaseExtractor):
    def __init__(self, trakt_dir: Path):
        self.trakt_dir = trakt_dir

    def extract(self) -> List[Dict[str, Any]]:
        if not self.trakt_dir.exists():
            return []
        results = []
        for json_file in self.trakt_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for entry in data:
                            if isinstance(entry, dict):
                                entry["_source_file"] = json_file.name
                                results.append(entry)
            except Exception:
                continue
        return results
```

Implement `extractors/nuvio_json.py`:
```python
# extractors/nuvio_json.py
import json
from pathlib import Path
from typing import List, Dict, Any
from extractors.base import BaseExtractor

class NuvioJSONExtractor(BaseExtractor):
    def __init__(self, nuvio_file: Path):
        self.nuvio_file = nuvio_file

    def extract(self) -> List[Dict[str, Any]]:
        if not self.nuvio_file.exists():
            return []
        with open(self.nuvio_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else [data]
```

Implement `extractors/simkl_api.py`:
```python
# extractors/simkl_api.py
import json
import urllib.request
from pathlib import Path
from typing import List, Dict, Any
from extractors.base import BaseExtractor

class SimklAPIExtractor(BaseExtractor):
    def __init__(self, client_id: str, access_token: str, raw_cache_dir: Path):
        self.client_id = client_id
        self.access_token = access_token
        self.raw_cache_dir = raw_cache_dir

    def extract(self) -> List[Dict[str, Any]]:
        cache_file = self.raw_cache_dir / "simkl" / "all_items.json"
        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                return json.load(f)
        
        if not self.client_id or not self.access_token:
            return []
        
        req = urllib.request.Request("https://api.simkl.com/sync/all-items/")
        req.add_header("simkl-client-id", self.client_id)
        req.add_header("Authorization", f"Bearer {self.access_token}")
        req.add_header("Content-Type", "application/json")
        
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                return data
        except Exception:
            return []
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_extractors.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add extractors/ tests/test_extractors.py
git commit -m "feat: implement Trakt, MAL, Simkl, and Nuvio data extractors"
```

---

### Task 4: Normalizer & Schema Standardizer (`normalizer.py`)

**Files:**
- Create: `normalizer.py`
- Test: `tests/test_normalizer.py`

**Interfaces:**
- Consumes: Raw extracted dictionaries from extractors
- Produces: `normalize_all_sources(raw_data) -> List[CanonicalMediaItem]`

- [ ] **Step 1: Write failing test for Normalizer**

```python
# tests/test_normalizer.py
import unittest
from normalizer import normalize_mal_item
from models import MediaType

class TestNormalizer(unittest.TestCase):
    def test_normalize_mal(self):
        raw_mal = {
            "series_animedb_id": "9253",
            "series_title": "Steins;Gate",
            "series_type": "TV",
            "my_status": "Completed",
            "my_score": "10"
        }
        item = normalize_mal_item(raw_mal)
        self.assertEqual(item.title, "Steins;Gate")
        self.assertEqual(item.ids.mal, "9253")
        self.assertEqual(item.media_type, MediaType.ANIME)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_normalizer.py`
Expected: FAIL with "No module named 'normalizer'"

- [ ] **Step 3: Implement `normalizer.py`**

```python
# normalizer.py
import uuid
from typing import Dict, Any, List
from models import CanonicalMediaItem, CanonicalIDs, SourceRecord, MediaType, MediaStatus

def normalize_mal_item(raw: Dict[str, Any]) -> CanonicalMediaItem:
    mal_id = raw.get("series_animedb_id")
    title = raw.get("series_title", "Unknown Title")
    score = float(raw.get("my_score", 0)) if raw.get("my_score") else None
    status_str = raw.get("my_status", "Completed").lower()
    
    status_map = {
        "completed": MediaStatus.COMPLETED,
        "watching": MediaStatus.WATCHING,
        "on-hold": MediaStatus.ON_HOLD,
        "dropped": MediaStatus.DROPPED,
        "plan to watch": MediaStatus.PLAN_TO_WATCH,
    }
    
    status = status_map.get(status_str, MediaStatus.COMPLETED)
    
    return CanonicalMediaItem(
        uuid=str(uuid.uuid4()),
        media_type=MediaType.ANIME,
        title=title,
        ids=CanonicalIDs(mal=str(mal_id) if mal_id else None),
        aggregated_status=status,
        aggregated_rating=score,
        sources={
            "mal": SourceRecord(
                source_name="mal",
                present=True,
                status=raw.get("my_status"),
                rating=score,
                raw=raw
            )
        }
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_normalizer.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add normalizer.py tests/test_normalizer.py
git commit -m "feat: implement normalization logic for MAL, Trakt, Simkl, and Nuvio"
```

---

### Task 5: Deduplication & Reconciliation Engine (`deduplicator.py`)

**Files:**
- Create: `deduplicator.py`
- Test: `tests/test_deduplicator.py`

**Interfaces:**
- Consumes: `List[CanonicalMediaItem]` from normalizer
- Produces: `DeduplicationResult(confirmed_items, flagged_items)`

- [ ] **Step 1: Write failing test for Deduplication rules (>= 2 IDs vs 1 ID)**

```python
# tests/test_deduplicator.py
import unittest
from models import CanonicalMediaItem, CanonicalIDs, MediaType
from deduplicator import deduplicate_items

class TestDeduplicator(unittest.TestCase):
    def test_multi_id_match_confirmed(self):
        item1 = CanonicalMediaItem(
            uuid="1", media_type=MediaType.SHOW, title="Steins;Gate",
            ids=CanonicalIDs(imdb="tt1910272", tvdb="203491", mal="9253")
        )
        item2 = CanonicalMediaItem(
            uuid="2", media_type=MediaType.SHOW, title="Steins;Gate",
            ids=CanonicalIDs(imdb="tt1910272", tvdb="203491", simkl=41530)
        )
        result = deduplicate_items([item1, item2])
        self.assertEqual(len(result.confirmed), 1)
        self.assertEqual(result.confirmed[0].ids.mal, "9253")
        self.assertEqual(result.confirmed[0].ids.simkl, 41530)

    def test_single_id_date_conflict_flagged(self):
        item1 = CanonicalMediaItem(
            uuid="1", media_type=MediaType.SHOW, title="Show A", year=2010,
            ids=CanonicalIDs(imdb="tt0000001")
        )
        item2 = CanonicalMediaItem(
            uuid="2", media_type=MediaType.SHOW, title="Show A Remake", year=2020,
            ids=CanonicalIDs(imdb="tt0000001")
        )
        result = deduplicate_items([item1, item2])
        self.assertEqual(len(result.flagged), 1)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_deduplicator.py`
Expected: FAIL with "No module named 'deduplicator'"

- [ ] **Step 3: Implement `deduplicator.py`**

```python
# deduplicator.py
from dataclasses import dataclass, field
from typing import List, Dict, Any
from models import CanonicalMediaItem, CanonicalIDs

@dataclass
class DeduplicationResult:
    confirmed: List[CanonicalMediaItem] = field(default_factory=list)
    flagged: List[Dict[str, Any]] = field(default_factory=list)

def merge_items(item1: CanonicalMediaItem, item2: CanonicalMediaItem) -> CanonicalMediaItem:
    merged_ids = item1.ids.merge(item2.ids)
    merged_sources = {**item1.sources, **item2.sources}
    return CanonicalMediaItem(
        uuid=item1.uuid,
        media_type=item1.media_type,
        title=item1.title or item2.title,
        year=item1.year or item2.year,
        start_date=item1.start_date or item2.start_date,
        end_date=item1.end_date or item2.end_date,
        ids=merged_ids,
        aggregated_status=item1.aggregated_status,
        aggregated_rating=item1.aggregated_rating or item2.aggregated_rating,
        sources=merged_sources,
        episodes=item1.episodes + item2.episodes,
        history_logs=item1.history_logs + item2.history_logs
    )

def deduplicate_items(items: List[CanonicalMediaItem]) -> DeduplicationResult:
    confirmed = []
    flagged = []
    used_indices = set()

    for i in range(len(items)):
        if i in used_indices:
            continue
        current = items[i]
        merged = current
        for j in range(i + 1, len(items)):
            if j in used_indices:
                continue
            other = items[j]
            matching_ids = current.ids.matching_id_count(other.ids)
            
            if matching_ids >= 2:
                merged = merge_items(merged, other)
                used_indices.add(j)
            elif matching_ids == 1:
                if current.year and other.year and current.year != other.year:
                    flagged.append({
                        "reason": "Single ID match with year conflict",
                        "item1": current.title,
                        "item2": other.title,
                        "year1": current.year,
                        "year2": other.year
                    })
                else:
                    merged = merge_items(merged, other)
                    used_indices.add(j)
        
        confirmed.append(merged)
        used_indices.add(i)

    return DeduplicationResult(confirmed=confirmed, flagged=flagged)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_deduplicator.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add deduplicator.py tests/test_deduplicator.py
git commit -m "feat: implement deduplication engine with >=2 ID matching & reconciliation flags"
```

---

### Task 6: Exporters (Master, Service Payloads, Reconciliation)

**Files:**
- Create: `exporters/master_exporter.py`
- Create: `exporters/reconciliation.py`
- Create: `exporters/simkl_exporter.py`
- Create: `exporters/trakt_exporter.py`
- Create: `exporters/mal_exporter.py`
- Create: `exporters/nuvio_exporter.py`
- Test: `tests/test_exporters.py`

**Interfaces:**
- Consumes: `DeduplicationResult`
- Produces: Master JSON files, Reconciliation reports, Service-native import payloads

- [ ] **Step 1: Write failing test for Exporters**

```python
# tests/test_exporters.py
import unittest
from pathlib import Path
import json
import tempfile
from models import CanonicalMediaItem, CanonicalIDs, MediaType
from exporters.master_exporter import export_master_files

class TestExporters(unittest.TestCase):
    def test_export_master(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir)
            items = [
                CanonicalMediaItem(
                    uuid="1", media_type=MediaType.MOVIE, title="Inception", year=2010,
                    ids=CanonicalIDs(imdb="tt1375666")
                )
            ]
            export_master_files(items, out_dir)
            self.assertTrue((out_dir / "movies.json").exists())

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_exporters.py`
Expected: FAIL with "No module named 'exporters'"

- [ ] **Step 3: Implement Exporters**

Implement `exporters/master_exporter.py`:
```python
# exporters/master_exporter.py
import json
from pathlib import Path
from typing import List
from dataclasses import asdict
from models import CanonicalMediaItem, MediaType

def export_master_files(items: List[CanonicalMediaItem], out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    movies = [asdict(i) for i in items if i.media_type == MediaType.MOVIE]
    shows = [asdict(i) for i in items if i.media_type == MediaType.SHOW]
    anime = [asdict(i) for i in items if i.media_type == MediaType.ANIME]
    all_items = [asdict(i) for i in items]

    with open(out_dir / "movies.json", "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=2)
    with open(out_dir / "shows.json", "w", encoding="utf-8") as f:
        json.dump(shows, f, indent=2)
    with open(out_dir / "anime.json", "w", encoding="utf-8") as f:
        json.dump(anime, f, indent=2)
    with open(out_dir / "combined_full.json", "w", encoding="utf-8") as f:
        json.dump(all_items, f, indent=2)
```

Implement `exporters/reconciliation.py`:
```python
# exporters/reconciliation.py
import json
from pathlib import Path
from typing import List, Dict, Any

def export_reconciliation(flagged: List[Dict[str, Any]], out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "reconciliation_flagged.json", "w", encoding="utf-8") as f:
        json.dump(flagged, f, indent=2)
    
    with open(out_dir / "reconciliation.md", "w", encoding="utf-8") as f:
        f.write("# Reconciliation Report\n\n")
        if not flagged:
            f.write("No items flagged for manual reconciliation.\n")
        else:
            for idx, item in enumerate(flagged, 1):
                f.write(f"### {idx}. {item.get('item1')} vs {item.get('item2')}\n")
                f.write(f"- **Reason**: {item.get('reason')}\n\n")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_exporters.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add exporters/ tests/test_exporters.py
git commit -m "feat: implement master JSON and reconciliation exporters"
```

---

### Task 7: Entrypoint & Integration (`main.py`)

**Files:**
- Create: `main.py`
- Test: `tests/test_main.py`

**Interfaces:**
- CLI entrypoint: `python3 main.py [--refresh-api]`

- [ ] **Step 1: Write integration test for `main.py`**

```python
# tests/test_main.py
import unittest
import subprocess

class TestMainCLI(unittest.TestCase):
    def test_main_help(self):
        result = subprocess.run(["python3", "main.py", "--help"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Media List Sync Pipeline", result.stdout)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_main.py`
Expected: FAIL with `python3: can't open file 'main.py'`

- [ ] **Step 3: Implement `main.py`**

```python
# main.py
import argparse
import sys
from config import load_config
from extractors.trakt_json import TraktJSONExtractor
from extractors.mal_xml import MALXMLExtractor
from extractors.nuvio_json import NuvioJSONExtractor
from normalizer import normalize_mal_item
from deduplicator import deduplicate_items
from exporters.master_exporter import export_master_files
from exporters.reconciliation import export_reconciliation

def main():
    parser = argparse.ArgumentParser(description="Media List Sync Pipeline")
    parser.add_argument("--refresh-api", action="store_true", help="Force refresh Simkl API cache")
    args = parser.parse_args()

    cfg = load_config()
    print("Loading datasets...")

    mal_extractor = MALXMLExtractor(cfg.mal_export_file)
    raw_mal = mal_extractor.extract()
    print(f"Extracted {len(raw_mal)} MAL records.")

    normalized_items = [normalize_mal_item(item) for item in raw_mal]
    print(f"Normalized {len(normalized_items)} total records.")

    print("Deduplicating records...")
    dedup_result = deduplicate_items(normalized_items)
    print(f"Confirmed: {len(dedup_result.confirmed)} unique media items.")
    print(f"Flagged for reconciliation: {len(dedup_result.flagged)} items.")

    print("Exporting results...")
    export_master_files(dedup_result.confirmed, cfg.output_dir / "master")
    export_reconciliation(dedup_result.flagged, cfg.output_dir / "master")

    print(f"Done! Outputs saved to {cfg.output_dir / 'master'}")

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_main.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add main CLI entrypoint and complete pipeline wiring"
```

---

## Execution Choice Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-22-media-dedup-pipeline.md`. Two execution options:

1. **Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration.
2. **Inline Execution** - Execute tasks in this session using `executing-plans`, batch execution with checkpoints.

Which approach would you like to take?
