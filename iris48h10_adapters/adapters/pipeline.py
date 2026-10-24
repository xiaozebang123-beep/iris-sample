"""File-based, fixture-only pipeline. Does not connect to a database or network."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from .mine_features import normalize_mine_feature
from .spatial_risk import DEFAULT_REVIEW_DISTANCE_M, build_facility_risk
from .water_rights import normalize_water_right


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _write_deterministic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    # Write to a temporary sibling then replace, so interrupted runs do not
    # leave a truncated output. A rerun replaces rather than appends to output.
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(path)


def run_pipeline(
    fixtures_dir: str | Path,
    output_path: str | Path,
    *,
    as_of: date,
    review_distance_m: float = DEFAULT_REVIEW_DISTANCE_M,
) -> dict[str, Any]:
    fixture_dir = Path(fixtures_dir)
    rights_raw = _read_json(fixture_dir / "wasserbuch_fixture.json")
    mines_raw = _read_json(fixture_dir / "mine_shaft_fixture.json")
    facilities_raw = _read_json(fixture_dir / "industrial_facilities.json")

    if not isinstance(rights_raw, list) or not isinstance(mines_raw, list) or not isinstance(facilities_raw, list):
        raise ValueError("Each fixture file must contain a JSON array of records")

    rights = [normalize_water_right(item, as_of=as_of) for item in rights_raw]
    mines = [normalize_mine_feature(item) for item in mines_raw]
    risk = build_facility_risk(
        facilities_raw, rights, mines, review_distance_m=review_distance_m
    )
    risk["evaluated_on"] = as_of.isoformat()
    _write_deterministic_json(Path(output_path), risk)
    return risk
