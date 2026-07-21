"""
Merge benchmark JSON files by replacing profiles with later file entries.

Usage:
    python scripts/merge_benchmark_results.py benchmark-results.json benchmark-obscura.json -o benchmark-results-merged.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def merge_reports(paths: list[Path]) -> dict[str, Any]:
    if not paths:
        raise ValueError("At least one benchmark JSON file is required")

    merged = json.loads(paths[0].read_text(encoding="utf-8"))
    profiles_by_name = {
        profile["name"]: profile for profile in merged.get("profiles", []) if "name" in profile
    }

    for path in paths[1:]:
        report = json.loads(path.read_text(encoding="utf-8"))
        for profile in report.get("profiles", []):
            name = profile.get("name")
            if name:
                profiles_by_name[name] = profile

        existing_names = set(merged.get("meta", {}).get("profiles", []))
        incoming_names = [profile.get("name") for profile in report.get("profiles", [])]
        merged.setdefault("meta", {})["profiles"] = [
            *[name for name in merged.get("meta", {}).get("profiles", []) if name in profiles_by_name],
            *[name for name in incoming_names if name and name not in existing_names],
        ]

    ordered_names = merged.get("meta", {}).get("profiles", [])
    merged["profiles"] = [
        profiles_by_name[name] for name in ordered_names if name in profiles_by_name
    ]
    known_names = set(ordered_names)
    merged["profiles"].extend(
        profile for name, profile in sorted(profiles_by_name.items()) if name not in known_names
    )
    merged["recommendations"] = [
        {
            "name": profile["name"],
            "available": profile.get("available", False),
            "usable_rate": profile.get("quality", {}).get("usable_rate", 0.0),
            "median_ms": profile.get("performance", {}).get("median_ms", 0.0),
            "throughput_urls_per_second": profile.get("performance", {}).get(
                "throughput_urls_per_second", 0.0
            ),
            "javascript_usable_rate": profile.get("capability", {})
            .get("by_tag", {})
            .get("javascript_required", {})
            .get("usable_rate", 0.0),
            "boilerplate_usable_rate": profile.get("capability", {})
            .get("by_tag", {})
            .get("boilerplate_removal", {})
            .get("usable_rate", 0.0),
        }
        for profile in sorted(
            merged["profiles"],
            key=lambda item: (
                not item.get("available", False),
                -item.get("quality", {}).get("usable_rate", 0.0),
                item.get("performance", {}).get("median_ms", 0.0),
            ),
        )
    ]
    return merged


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", type=Path, nargs="+")
    parser.add_argument("-o", "--output", type=Path, default=Path("benchmark-results-merged.json"))
    args = parser.parse_args()

    merged = merge_reports(args.inputs)
    args.output.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
