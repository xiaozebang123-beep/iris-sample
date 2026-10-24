"""Shared spatial-risk interface for facilities, water rights, and mine features."""
from __future__ import annotations

import math
from typing import Any, Iterable

from shapely.geometry.base import BaseGeometry

from .geometry_utils import ANALYSIS_CRS, GeometryError, parse_geometry, to_analysis_crs
from .mine_features import MineFeature
from .water_rights import WaterRight

DEFAULT_REVIEW_DISTANCE_M = 1000.0


def _facility_geometry(facility: dict[str, Any]) -> tuple[BaseGeometry, list[str]]:
    qa: list[str] = []
    geom = parse_geometry(facility.get("geometry"))
    if geom.geom_type not in {"Polygon", "MultiPolygon"}:
        raise GeometryError("facility geometry must be Polygon or MultiPolygon")
    geom = to_analysis_crs(geom, facility.get("crs"))
    return geom, qa


def _distance_m(geom: BaseGeometry | None, source_crs: str | None,
                facility_geom: BaseGeometry) -> tuple[float | None, str | None]:
    if geom is None:
        return None, "source_geometry_missing"
    try:
        projected = to_analysis_crs(geom, source_crs)
        return float(projected.distance(facility_geom)), None
    except GeometryError as exc:
        return None, f"geometry_qa_failed:{exc}"


def _flag(flag_code: str, reason: str, source_name: str | None,
          source_url: str | None) -> dict[str, Any]:
    return {
        "flag_code": flag_code,
        "status": "REVIEW_REQUIRED",
        "reason": reason,
        "source_name": source_name or "unknown source",
        "source_url": source_url,
    }


def build_facility_risk(
    facilities: Iterable[dict[str, Any]],
    water_rights: Iterable[WaterRight],
    mine_features: Iterable[MineFeature],
    *,
    review_distance_m: float = DEFAULT_REVIEW_DISTANCE_M,
) -> dict[str, Any]:
    """Create deterministic facility-level risk JSON from normalized fixtures.

    Distances are measured after transforming geometries into a metric CRS.
    For uncertain point locations, the uncertainty radius is subtracted from
    the observed distance (floor at zero), producing a conservative proximity
    estimate. The 1 km default is a prototype screening threshold, not a legal
    setback or site-safety determination.
    """
    if not math.isfinite(review_distance_m) or review_distance_m < 0:
        raise ValueError("review_distance_m must be a finite, non-negative number")

    water_rights = list(water_rights)
    mine_features = list(mine_features)
    facility_results: list[dict[str, Any]] = []

    for facility in sorted(facilities, key=lambda item: str(item.get("facility_id", ""))):
        facility_id = str(facility.get("facility_id") or "UNKNOWN_FACILITY")
        facility_qa: list[str] = []
        facility_geom: BaseGeometry | None = None
        try:
            facility_geom, qa = _facility_geometry(facility)
            facility_qa.extend(qa)
        except GeometryError as exc:
            facility_qa.append(f"facility_geometry_qa_failed:{exc}")

        water_layer: list[dict[str, Any]] = []
        for right in sorted(water_rights, key=lambda item: str(item.right_id or "")):
            source_id = right.right_id or "UNKNOWN_WATER_RIGHT"
            distance, distance_issue = (None, "facility_geometry_unavailable")
            if facility_geom is not None:
                distance, distance_issue = _distance_m(
                    right.facility_aoi, right.facility_aoi_crs, facility_geom
                )
            flags = [
                _flag("WATER_RIGHT_DATA_REVIEW", reason, right.source_name, right.source_url)
                for reason in right.review_reasons
            ]
            if distance_issue:
                flags.append(_flag("WATER_RIGHT_GEOMETRY_REVIEW", distance_issue,
                                   right.source_name, right.source_url))
            elif distance is not None and distance <= review_distance_m:
                flags.append(_flag(
                    "WATER_RIGHT_PROXIMITY_REVIEW",
                    f"water-right AOI is within {review_distance_m:.1f} m of facility",
                    right.source_name, right.source_url,
                ))
            water_layer.append({
                "source_id": source_id,
                "source_name": right.source_name,
                "source_url": right.source_url,
                "distance_m": round(distance, 3) if distance is not None else None,
                "review_required": bool(flags),
                "review_reasons": list(right.review_reasons),
                "flags": flags,
            })

        mine_layer: list[dict[str, Any]] = []
        for feature in sorted(mine_features, key=lambda item: str(item.source_identifier or "")):
            source_id = feature.source_identifier or "UNKNOWN_MINE_FEATURE"
            distance, distance_issue = (None, "facility_geometry_unavailable")
            if facility_geom is not None:
                distance, distance_issue = _distance_m(
                    feature.position, feature.position_crs, facility_geom
                )
            conservative_distance = distance
            if distance is not None and feature.uncertainty_m is not None:
                conservative_distance = max(0.0, distance - feature.uncertainty_m)
            flags = [
                _flag("MINE_FEATURE_DATA_REVIEW", reason, feature.source_name, feature.source_url)
                for reason in feature.review_reasons
            ]
            if distance_issue:
                flags.append(_flag("MINE_FEATURE_GEOMETRY_REVIEW", distance_issue,
                                   feature.source_name, feature.source_url))
            elif conservative_distance is not None and conservative_distance <= review_distance_m:
                flags.append(_flag(
                    "MINE_FEATURE_PROXIMITY_REVIEW",
                    f"conservative feature distance is within {review_distance_m:.1f} m of facility",
                    feature.source_name, feature.source_url,
                ))
            mine_layer.append({
                "source_id": source_id,
                "feature_kind": feature.feature_kind,
                "source_name": feature.source_name,
                "source_url": feature.source_url,
                "observed_distance_m": round(distance, 3) if distance is not None else None,
                "uncertainty_m": feature.uncertainty_m,
                "conservative_distance_m": round(conservative_distance, 3)
                    if conservative_distance is not None else None,
                "review_required": bool(flags),
                "review_reasons": list(feature.review_reasons),
                "flags": flags,
            })

        facility_results.append({
            "facility_id": facility_id,
            "facility_name": str(facility.get("name") or facility_id),
            "analysis_crs": ANALYSIS_CRS,
            "geometry_qa": facility_qa,
            "risk_layers": {
                "water_rights": water_layer,
                "mine_well_shaft": mine_layer,
            },
        })

    return {
        "schema_version": "1.0",
        "analysis_crs": ANALYSIS_CRS,
        "review_distance_m": float(review_distance_m),
        "facilities": facility_results,
        "source_limitations": [
            "Fixtures are synthetic and are not real permits, mines, coordinates, or operational records.",
            "A missing record must not be interpreted as proof that no water rights exist.",
            "Flags are screening prompts for human review, not legal or engineering determinations.",
        ],
    }
