import json
from pathlib import Path
from typing import List, Dict, Any, Union


def export_reconciliation(flagged: List[Dict[str, Any]], out_dir: Union[str, Path]) -> None:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    serializable_flagged = []
    for item in flagged:
        clean_item = {}
        for k, v in item.items():
            if isinstance(v, (str, int, float, bool)) or v is None:
                clean_item[k] = v
            elif hasattr(v, "title") and isinstance(getattr(v, "title"), str):
                clean_item[k] = getattr(v, "title")
            elif hasattr(v, "__dict__"):
                clean_item[k] = str(v)
            else:
                clean_item[k] = str(v)
        serializable_flagged.append(clean_item)

    with open(out_path / "reconciliation_flagged.json", "w", encoding="utf-8") as f:
        json.dump(serializable_flagged, f, indent=2)
    with open(out_path / "flagged_data.js", "w", encoding="utf-8") as f:
        f.write("window.FLAGGED_MEDIA_DATA = " + json.dumps(serializable_flagged) + ";\n")


    md_lines = [
        "# Reconciliation Report",
        "",
        f"Total items requiring manual reconciliation: **{len(flagged)}**",
        "",
    ]

    if not flagged:
        md_lines.append("No items flagged for manual reconciliation.")
    else:
        for idx, item in enumerate(flagged, 1):
            item1 = item.get("item1_title") or item.get("item1")
            if hasattr(item1, "title") and isinstance(getattr(item1, "title"), str):
                item1 = getattr(item1, "title")
            item2 = item.get("item2_title") or item.get("item2")
            if hasattr(item2, "title") and isinstance(getattr(item2, "title"), str):
                item2 = getattr(item2, "title")
            reason = item.get("reason", "N/A")
            md_lines.append(f"### {idx}. {item1} vs {item2}")
            md_lines.append(f"- **Reason**: {reason}")
            if "year1" in item or "year2" in item:
                md_lines.append(f"- **Years**: {item.get('year1')} vs {item.get('year2')}")
            md_lines.append("")

    with open(out_path / "reconciliation.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

