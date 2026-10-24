# Engineering Note — IRIS-48H-10 Prototype

## Design

The implementation separates the two source adapters (`water_rights.py`, `mine_features.py`) from shared spatial risk generation (`spatial_risk.py`) and fixture I/O (`pipeline.py`). Normalized records retain source IDs, source names, source URLs, validity/observation metadata, coordinates/CRS, and review reasons. The output is deterministic JSON and is written by atomic replacement rather than append, so reruns do not duplicate records.

## Spatial method and geometry QA

All geometries are validated for parseability, non-empty geometry, validity, and expected type. Distances are computed only after transforming to EPSG:25832, a metric projected CRS appropriate to this illustrative NRW-area fixture. If the CRS is absent, unrecognized, or conversion fails, the code emits a geometry QA review flag instead of comparing coordinates silently. The prototype does not implement nationwide CRS selection; real deployments must select a suitable local projected CRS for each study area and verify axis/units from the provider.

For uncertain point locations, `conservative_distance_m = max(0, observed_distance_m - uncertainty_m)`. Subtracting the uncertainty radius expands the potential influence area rather than overstating separation. The 1,000 m threshold is explicitly a configurable screening parameter used for this exercise, not an asserted legal or geotechnical threshold.

## Review behavior

Water-right records are marked `REVIEW_REQUIRED` if required fields are missing or invalid, the licence status is not recognized as active/in-force, the licence is expired/not yet valid, or the validity window is inconsistent. Mine features are marked for review if required identifiers/metadata or geometry/CRS are missing/invalid, or the location/reliability is uncertain. Proximity flags also request human review. The output never interprets a missing record as proof that a right does not exist.

## Source provenance, legality, and availability

The fixtures are fully synthetic and use `.invalid` URLs so that they cannot be mistaken for real data sources. No scraping, authentication, CAPTCHA bypass, unauthorized bulk data access, or network requests occur. In a production connector, choose a permitted official endpoint or dataset, obey licence and rate-limit terms, store retrieval timestamps and source versions, and document coverage gaps. A provider that is inaccessible or has no matching record must be represented as unavailable/unknown rather than as a negative legal finding.

## Limitations and next steps

This is a narrow vertical slice with one synthetic record per source and one facility. It does not establish legal rights, engineering safety, database integration, or complete state-level coverage. Before production use, confirm the real source schema/licence, improve per-source parsing and provenance, define operationally approved distance thresholds, add provider-specific coverage metadata, and subject CRS and geometry assumptions to domain review.
