"""Geometry parsing, validation, and transformation helpers.

The prototype uses EPSG:25832 (ETRS89 / UTM zone 32N), a metre-based CRS
suitable for the synthetic NRW test fixture. This is not a blanket CRS choice
for nationwide German data; select a suitable local projected CRS per study area.
"""
from __future__ import annotations

from typing import Any

from pyproj import CRS, Transformer
from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform

ANALYSIS_CRS = "EPSG:25832"


class GeometryError(ValueError):
    """Raised when geometry or CRS cannot be safely interpreted."""


def parse_geometry(raw: Any) -> BaseGeometry:
    if not isinstance(raw, dict):
        raise GeometryError("geometry must be a GeoJSON-like object")
    try:
        geom = shape(raw)
    except Exception as exc:  # shapely may raise several exception types
        raise GeometryError(f"geometry could not be parsed: {exc}") from exc
    if geom.is_empty:
        raise GeometryError("geometry is empty")
    if not geom.is_valid:
        raise GeometryError("geometry is invalid")
    return geom


def to_analysis_crs(geom: BaseGeometry, source_crs: str | None) -> BaseGeometry:
    if not source_crs:
        raise GeometryError("source CRS is missing")
    try:
        src = CRS.from_user_input(source_crs)
        dst = CRS.from_user_input(ANALYSIS_CRS)
    except Exception as exc:
        raise GeometryError(f"CRS could not be interpreted: {source_crs}") from exc
    if src == dst:
        return geom
    try:
        transformer = Transformer.from_crs(src, dst, always_xy=True)
        converted = transform(transformer.transform, geom)
    except Exception as exc:
        raise GeometryError(f"geometry transformation failed: {exc}") from exc
    if converted.is_empty or not converted.is_valid:
        raise GeometryError("transformed geometry is empty or invalid")
    return converted


def geometry_to_geojson(geom: BaseGeometry | None) -> dict[str, Any] | None:
    return mapping(geom) if geom is not None else None
