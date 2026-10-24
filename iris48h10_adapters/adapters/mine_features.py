"""Normalize a single mine/well/shaft feature from fixture data."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import math
from typing import Any

from shapely.geometry.base import BaseGeometry

from .geometry_utils import GeometryError, geometry_to_geojson, parse_geometry


@dataclass(frozen=True)
class MineFeature:
    source_identifier: str | None
    feature_kind: str | None
    position: BaseGeometry | None
    position_crs: str | None
    depth_m: float | None
    observation_date: date | None
    data_reliability: str | None
    uncertainty_m: float | None
    source_url: str | None
    source_name: str | None
    review_required: bool
    review_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_identifier": self.source_identifier,
            "feature_kind": self.feature_kind,
            "position": geometry_to_geojson(self.position),
            "position_crs": self.position_crs,
            "depth_m": self.depth_m,
            "observation_date": self.observation_date.isoformat() if self.observation_date else None,
            "data_reliability": self.data_reliability,
            "uncertainty_m": self.uncertainty_m,
            "source_url": self.source_url,
            "source_name": self.source_name,
            "review_required": self.review_required,
            "review_reasons": list(self.review_reasons),
        }


def normalize_mine_feature(raw: dict[str, Any]) -> MineFeature:
    reasons: list[str] = []

    def required_text(key: str) -> str | None:
        value = raw.get(key)
        if value is None or not str(value).strip():
            reasons.append(f"missing_{key}")
            return None
        return str(value).strip()

    source_identifier = required_text("source_identifier")
    feature_kind = required_text("feature_kind")
    data_reliability = required_text("data_reliability")
    source_url = required_text("source_url")
    source_name = str(raw.get("source_name") or "unknown source")
    position_crs = str(raw.get("position_crs")).strip() if raw.get("position_crs") else None
    if not position_crs:
        reasons.append("missing_position_crs")

    position: BaseGeometry | None = None
    try:
        position = parse_geometry(raw.get("position"))
        if position.geom_type != "Point":
            reasons.append("position_not_point")
            position = None
    except GeometryError as exc:
        reasons.append(f"invalid_position:{exc}")

    observation_date: date | None = None
    if not raw.get("observation_date"):
        reasons.append("missing_observation_date")
    else:
        try:
            observation_date = date.fromisoformat(str(raw["observation_date"]))
        except (TypeError, ValueError):
            reasons.append("invalid_observation_date")

    depth_m: float | None = None
    if raw.get("depth_m") not in (None, ""):
        try:
            depth_m = float(raw["depth_m"])
            if not math.isfinite(depth_m) or depth_m < 0:
                depth_m = None
                reasons.append("invalid_depth_m")
        except (TypeError, ValueError):
            reasons.append("invalid_depth_m")

    uncertainty_m: float | None = None
    if raw.get("uncertainty_m") not in (None, ""):
        try:
            uncertainty_m = float(raw["uncertainty_m"])
            if not math.isfinite(uncertainty_m) or uncertainty_m < 0:
                uncertainty_m = None
                reasons.append("invalid_uncertainty_m")
        except (TypeError, ValueError):
            reasons.append("invalid_uncertainty_m")

    reliability_norm = data_reliability.casefold() if data_reliability else "unknown"
    position_uncertain = bool(raw.get("position_uncertain")) or reliability_norm in {
        "uncertain", "approximate", "low", "unknown", "unverified"
    }
    if position_uncertain:
        reasons.append("uncertain_shaft_position")
        if uncertainty_m is None:
            reasons.append("uncertainty_distance_not_supplied")

    unique_reasons = tuple(dict.fromkeys(reasons))
    return MineFeature(
        source_identifier=source_identifier,
        feature_kind=feature_kind,
        position=position,
        position_crs=position_crs,
        depth_m=depth_m,
        observation_date=observation_date,
        data_reliability=data_reliability,
        uncertainty_m=uncertainty_m,
        source_url=source_url,
        source_name=source_name,
        review_required=bool(unique_reasons),
        review_reasons=unique_reasons,
    )
