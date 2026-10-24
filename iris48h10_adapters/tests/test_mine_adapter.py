import json
import unittest
from pathlib import Path

from adapters.mine_features import normalize_mine_feature

ROOT = Path(__file__).resolve().parents[1]


class MineFeatureAdapterTests(unittest.TestCase):
    def test_fixture_preserves_position_metadata_and_flags_uncertainty(self):
        rows = json.loads((ROOT / "fixtures" / "mine_shaft_fixture.json").read_text(encoding="utf-8"))
        shaft = normalize_mine_feature(rows[0])
        self.assertEqual(shaft.source_identifier, "SYN-SHAFT-001")
        self.assertEqual(shaft.feature_kind, "shaft")
        self.assertEqual(shaft.depth_m, 210)
        self.assertEqual(shaft.uncertainty_m, 75)
        self.assertTrue(shaft.review_required)
        self.assertIn("uncertain_shaft_position", shaft.review_reasons)

    def test_missing_position_is_marked_for_review(self):
        rows = json.loads((ROOT / "fixtures" / "mine_shaft_fixture.json").read_text(encoding="utf-8"))
        row = dict(rows[0], position=None)
        shaft = normalize_mine_feature(row)
        self.assertTrue(shaft.review_required)
        self.assertTrue(any(reason.startswith("invalid_position:") for reason in shaft.review_reasons))


if __name__ == "__main__":
    unittest.main()
