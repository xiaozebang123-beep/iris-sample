import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from adapters.pipeline import run_pipeline

ROOT = Path(__file__).resolve().parents[1]


class SpatialRiskPipelineTests(unittest.TestCase):
    def test_one_facility_has_traceable_flags_from_both_layers(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "facility-risk.json"
            result = run_pipeline(ROOT / "fixtures", output, as_of=date(2026, 10, 24))
            self.assertEqual(len(result["facilities"]), 1)
            facility = result["facilities"][0]
            self.assertIn("water_rights", facility["risk_layers"])
            self.assertIn("mine_well_shaft", facility["risk_layers"])
            water = facility["risk_layers"]["water_rights"][0]
            mine = facility["risk_layers"]["mine_well_shaft"][0]
            self.assertTrue(water["review_required"])
            self.assertTrue(mine["review_required"])
            water_review_reasons = {flag["reason"] for flag in water["flags"]}
            mine_review_reasons = {flag["reason"] for flag in mine["flags"]}
            self.assertIn("missing_permitted_quantity", water_review_reasons)
            self.assertIn("licence_expired", water_review_reasons)
            self.assertIn("uncertain_shaft_position", mine_review_reasons)
            self.assertTrue(all(flag["status"] == "REVIEW_REQUIRED" for flag in water["flags"]))
            self.assertTrue(all(flag["status"] == "REVIEW_REQUIRED" for flag in mine["flags"]))
            self.assertTrue(water["source_url"].startswith("https://example.invalid/"))
            self.assertTrue(mine["source_url"].startswith("https://example.invalid/"))
            self.assertLessEqual(mine["conservative_distance_m"], mine["observed_distance_m"])
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["analysis_crs"], "EPSG:25832")
            self.assertIn("A missing record must not be interpreted", " ".join(payload["source_limitations"]))

    def test_rerun_is_byte_for_byte_idempotent_for_same_inputs_and_date(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "facility-risk.json"
            run_pipeline(ROOT / "fixtures", output, as_of=date(2026, 10, 24))
            first = output.read_bytes()
            run_pipeline(ROOT / "fixtures", output, as_of=date(2026, 10, 24))
            second = output.read_bytes()
            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
