import unittest

from harvester.validate.drift import detect_drift


class DriftTests(unittest.TestCase):
    def test_missing_expected_header_triggers_drift(self):
        result = detect_drift(
            current_headers={"scheme_name", "security_name"},
            current_row_count=100,
            current_confidence=90,
            expected_headers={"scheme_name", "security_name", "market_value"},
            last_good_row_count=100,
            last_good_confidence_avg=90,
        )
        self.assertTrue(result.drifted)
        self.assertIn("missing_headers:market_value", result.reasons)

    def test_row_count_drop_triggers_drift(self):
        result = detect_drift(
            current_headers={"scheme_name"},
            current_row_count=20,
            current_confidence=90,
            expected_headers={"scheme_name"},
            last_good_row_count=100,
            last_good_confidence_avg=90,
        )
        self.assertTrue(result.drifted)


if __name__ == "__main__":
    unittest.main()
