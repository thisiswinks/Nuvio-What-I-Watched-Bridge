import json
from pathlib import Path
from typing import List, Union
from dataclasses import asdict
from models import CanonicalMediaItem, MediaType


def export_master_files(items: List[CanonicalMediaItem], out_dir: Union[str, Path]) -> None:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    movies = []
    shows = []
    anime = []
    all_items = []

    for item in items:
        item_dict = asdict(item)
        all_items.append(item_dict)
        mtype = item.media_type
        if mtype == MediaType.MOVIE or mtype == "movie":
            movies.append(item_dict)
        elif mtype == MediaType.SHOW or mtype == "show":
            shows.append(item_dict)
        elif mtype == MediaType.ANIME or mtype == "anime":
            anime.append(item_dict)

    with open(out_path / "movies.json", "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=2)
    with open(out_path / "shows.json", "w", encoding="utf-8") as f:
        json.dump(shows, f, indent=2)
    with open(out_path / "anime.json", "w", encoding="utf-8") as f:
        json.dump(anime, f, indent=2)
    with open(out_path / "combined_full.json", "w", encoding="utf-8") as f:
        json.dump(all_items, f, indent=2)

    source_counts = {}
    for item in items:
        for src_name in item.sources.keys():
            source_counts[src_name] = source_counts.get(src_name, 0) + 1

    summary_lines = [
        "# Media List Sync Pipeline Summary",
        "",
        "## Statistics",
        f"- **Total Combined Items**: {len(items)}",
        f"- **Movies**: {len(movies)}",
        f"- **TV Shows**: {len(shows)}",
        f"- **Anime**: {len(anime)}",
        "",
        "## Source Breakdown",
    ]
    if source_counts:
        for src_name, count in source_counts.items():
            summary_lines.append(f"- **{src_name.upper()}**: {count} items")
    else:
        summary_lines.append("- No sources found")

    with open(out_path / "summary.md", "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines) + "\n")
