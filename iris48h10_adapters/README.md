# IRIS-48H-10 — Fixture-Driven Water Rights and Mine/Shaft Adapters

This directory is a focused, file-based vertical slice for the candidate assessment. It normalizes one synthetic Wasserbuch-like record and one synthetic mine-shaft record, overlays them with a synthetic industrial facility polygon, and emits traceable facility-level risk flags.

## Scope and safety

- Uses **synthetic-only** fixtures under `fixtures/`; all links use the reserved `.invalid` domain.
- Does not call external APIs, scrape sites, bypass access controls, read credentials, or connect to any database.
- Does not treat absence of a record as proof that no water right exists.
- The 1,000 m distance threshold is a configurable prototype screening threshold, not a legal setback or operational safety conclusion.
- The test geometry is in EPSG:25832, suitable for the illustrative NRW-area fixture. Nationwide German data requires choosing appropriate local projected CRSs and verifying source metadata.

## Requirements

Python 3.12+; `shapely` and `pyproj` are required. The referenced IRIS sample project's `pyproject.toml` already lists GeoPandas and Shapely, and lists PyProj as a dependency; this small vertical slice does not require a database.

If running in an environment that does not already have the relevant dependencies:

```bash
python -m pip install "shapely>=2.1" "pyproj>=3.7"
```

## Run the prototype

Run commands from this directory:

```bash
python -m adapters.cli --fixtures-dir fixtures --output outputs/facility-risk.json --as-of 2026-10-24
```

The date is explicit so output can be reproduced. Omit `--as-of` to use the current local date. Override the screening threshold with `--review-distance-m 1000`.

## Run tests

The tests use Python's standard `unittest` runner:

```bash
python -m unittest discover -s tests -v
```

The suite covers one fixture-driven ETL test for each source, invalid/missing water-right and position data, a facility receiving traceable flags from both layers, conservative distance handling, and deterministic/idempotent reruns.

## Output contract

`outputs/facility-risk.json` contains:

- `analysis_crs` and `review_distance_m`;
- one entry per industrial facility;
- `risk_layers.water_rights` and `risk_layers.mine_well_shaft`;
- source identifiers, source URLs, raw/conservative distances, review reasons, and explicit `REVIEW_REQUIRED` flags;
- source limitations, including the rule that missing records do not establish absence of water rights.

## Integration note

This is intentionally isolated from the original database-backed pipeline. Before merging it into the supplied repository, inspect the exact target branch and latest tree; add the package in a non-conflicting location and wire it into project conventions only if requested. No production database is modified.
