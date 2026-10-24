"""Normalize a single Wasserbuch-like water-right record without network access."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
import math
from typing import Any

from shapely.geometry.base import BaseGeometry

from .geometry_utils import GeometryError, geometry_to_geojson, parse_geometry


@dataclass(frozen=True)
class WaterRight:
    right_id: str | None
    holder_alias: str | None
    licence_status: str | None
    valid_from: date | None
    valid_to: date | None
    permitted_quantity: float | None
    permitted_unit: str | None
    facility_aoi: BaseGeometry | None
    facility_aoi_crs: str | None
    source_url: str | None
    source_name: str | None
    review_required: bool
    review_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "right_id": self.right_id,
            "holder_alias": self.holder_alias,
            "licence_status": self.licence_status,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_to": self.valid_to.isoformat() if self.valid_to else None,
            "permitted_quantity": self.permitted_quantity,
            "permitted_unit": self.permitted_unit,
            "facility_aoi": geometry_to_geojson(self.facility_aoi),
            "facility_aoi_crs": self.facility_aoi_crs,
            "source_url": self.source_url,
            "source_name": self.source_name,
            "review_required": self.review_required,
            "review_reasons": list(self.review_reasons),
        }


def _parse_date(value: Any, field_name: str, reasons: list[str]) -> date | None:
    if value in (None, ""):
        reasons.append(f"missing_{field_name}")
        return None
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        reasons.append(f"invalid_{field_name}")
        return None


def normalize_water_right(raw: dict[str, Any], *, as_of: date) -> WaterRight:
    """Convert source-shaped data into a stable schema and conservative flags.

    No web scraping or external requests are performed. Missing, invalid, or
    expired licence data is explicitly routed to manual review.
    """
    reasons: list[str] = []

    def required_text(key: str) -> str | None:
        value = raw.get(key)
        if value is None or not str(value).strip():
            reasons.append(f"missing_{key}")
            return None
        return str(value).strip()

    right_id = required_text("right_id")
    holder_alias = required_text("holder_alias")
    licence_status = required_text("licence_status")
    valid_from = _parse_date(raw.get("valid_from"), "valid_from", reasons)
    valid_to = _parse_date(raw.get("valid_to"), "valid_to", reasons)
    permitted_unit = required_text("permitted_unit")
    source_url = required_text("source_url")
    source_name = str(raw.get("source_name") or "unknown source")
    crs_raw = raw.get("facility_aoi_crs")
    facility_aoi_crs = str(crs_raw).strip() if crs_raw else None
    if not facility_aoi_crs:
        reasons.append("missing_facility_aoi_crs")

    quantity_raw = raw.get("permitted_quantity")
    permitted_quantity: float | None
    if quantity_raw in (None, ""):
        permitted_quantity = None
        reasons.append("missing_permitted_quantity")
    else:
        try:
            permitted_quantity = float(quantity_raw)
            if not math.isfinite(permitted_quantity) or permitted_quantity < 0:
                permitted_quantity = None
                reasons.append("invalid_permitted_quantity")
        except (TypeError, ValueError):
            permitted_quantity = None
            reasons.append("invalid_permitted_quantity")

    aoi: BaseGeometry | None = None
    try:
        aoi = parse_geometry(raw.get("facility_aoi"))
        if aoi.geom_type not in {"Polygon", "MultiPolygon"}:
            reasons.append("facility_aoi_not_polygonal")
            aoi = None
    except GeometryError as exc:
        reasons.append(f"invalid_facility_aoi:{exc}")

    status_normalized = licence_status.casefold() if licence_status else ""
    if status_normalized not in {"active", "valid", "in_force"}:
        reasons.append(f"licence_status_requires_review:{status_normalized or 'missing'}")
    if valid_to and valid_to < as_of:
        reasons.append("licence_expired")
    if valid_from and valid_from > as_of:
        reasons.append("licence_not_yet_valid")
    if valid_from and valid_to and valid_from > valid_to:
        reasons.append("invalid_validity_window")

    # De-duplicate while preserving diagnostic order.
    unique_reasons = tuple(dict.fromkeys(reasons))
    return WaterRight(
        right_id=right_id,
        holder_alias=holder_alias,
        licence_status=licence_status,
        valid_from=valid_from,
        valid_to=valid_to,
        permitted_quantity=permitted_quantity,
        permitted_unit=permitted_unit,
        facility_aoi=aoi,
        facility_aoi_crs=facility_aoi_crs,
        source_url=source_url,
        source_name=source_name,
        review_required=bool(unique_reasons),
        review_reasons=unique_reasons,
    )
