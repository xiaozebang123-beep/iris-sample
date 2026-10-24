import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from adapters.pipeline import run_pipeline

ROOT = Path(__file__).resolve().parents[1]


class GeometryQATests(unittest.TestCase):
    def test_missing_facility_crs_emits_geometry_review_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture_dir = Path(tmp) / "fixtures"
            fixture_dir.mkdir()
            for name in ("wasserbuch_fixture.json", "mine_shaft_fixture.json", "industrial_facilities.json"):
                (fixture_dir / name).write_text(
                    (ROOT / "fixtures" / name).read_text(encoding="utf-8"), encoding="utf-8"
                )
            facilities_path = fixture_dir / "industrial_facilities.json"
            facilities = json.loads(facilities_path.read_text(encoding="utf-8"))
            facilities[0]["crs"] = None
            facilities_path.write_text(json.dumps(facilities), encoding="utf-8")

            output = Path(tmp) / "facility-risk.json"
            result = run_pipeline(fixture_dir, output, as_of=date(2026, 10, 24))
            facility = result["facilities"][0]
            self.assertTrue(any("facility_geometry_qa_failed" in item for item in facility["geometry_qa"]))
            water = facility["risk_layers"]["water_rights"][0]
            mine = facility["risk_layers"]["mine_well_shaft"][0]
            self.assertTrue(any(flag["flag_code"] == "WATER_RIGHT_GEOMETRY_REVIEW" for flag in water["flags"]))
            self.assertTrue(any(flag["flag_code"] == "MINE_FEATURE_GEOMETRY_REVIEW" for flag in mine["flags"]))
            self.assertTrue(all(flag["status"] == "REVIEW_REQUIRED" for flag in water["flags"] + mine["flags"]))


if __name__ == "__main__":
    unittest.main()
