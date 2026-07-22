import json
from pathlib import Path
from typing import List, Dict, Any, Union


def export_reconciliation(flagged: List[Dict[str, Any]], out_dir: Union[str, Path]) -> None:
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    with open(out_path / "reconciliation_flagged.json", "w", encoding="utf-8") as f:
        json.dump(flagged, f, indent=2)

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
            item1 = item.get("item1", "Item 1")
            item2 = item.get("item2", "Item 2")
            reason = item.get("reason", "N/A")
            md_lines.append(f"### {idx}. {item1} vs {item2}")
            md_lines.append(f"- **Reason**: {reason}")
            if "year1" in item or "year2" in item:
                md_lines.append(f"- **Years**: {item.get('year1')} vs {item.get('year2')}")
            md_lines.append("")

    with open(out_path / "reconciliation.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")
