"""CLI entry point: python -m adapters.cli --fixtures-dir fixtures --output outputs/facility-risk.json"""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from .pipeline import run_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the IRIS-48H-10 fixture-only risk adapter prototype")
    parser.add_argument("--fixtures-dir", default="fixtures", help="Directory containing the three synthetic fixture files")
    parser.add_argument("--output", default="outputs/facility-risk.json", help="Output JSON path")
    parser.add_argument("--as-of", default=date.today().isoformat(), help="Evaluation date in YYYY-MM-DD format")
    parser.add_argument("--review-distance-m", default=1000.0, type=float, help="Prototype proximity review threshold in metres")
    args = parser.parse_args()
    as_of = date.fromisoformat(args.as_of)
    result = run_pipeline(
        Path(args.fixtures_dir), Path(args.output),
        as_of=as_of, review_distance_m=args.review_distance_m,
    )
    facility_count = len(result["facilities"])
    print(f"Wrote {args.output} ({facility_count} facility record(s)); evaluated_on={args.as_of}")
    print("No database, credentials, network scraping, or production data were used.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
