import json
import unittest
from datetime import date
from pathlib import Path

from adapters.water_rights import normalize_water_right

ROOT = Path(__file__).resolve().parents[1]


class WaterRightAdapterTests(unittest.TestCase):
    def test_fixture_is_normalized_and_missing_or_expired_values_require_review(self):
        rows = json.loads((ROOT / "fixtures" / "wasserbuch_fixture.json").read_text(encoding="utf-8"))
        right = normalize_water_right(rows[0], as_of=date(2026, 10, 24))
        self.assertEqual(right.right_id, "SYN-WR-001")
        self.assertEqual(right.permitted_unit, "m3/day")
        self.assertTrue(right.review_required)
        self.assertIn("licence_expired", right.review_reasons)
        self.assertIn("missing_permitted_quantity", right.review_reasons)
        self.assertEqual(right.facility_aoi.geom_type, "Polygon")

    def test_active_complete_record_does_not_get_data_review_flag(self):
        rows = json.loads((ROOT / "fixtures" / "wasserbuch_fixture.json").read_text(encoding="utf-8"))
        row = dict(rows[0], valid_to="2027-12-31", permitted_quantity=1000)
        right = normalize_water_right(row, as_of=date(2026, 10, 24))
        self.assertFalse(right.review_required)
        self.assertEqual(right.review_reasons, ())


if __name__ == "__main__":
    unittest.main()
