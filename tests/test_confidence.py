import unittest

from harvester.classify.confidence import score_document


class ConfidenceTests(unittest.TestCase):
    def test_conflicting_period_hard_quarantines(self):
        result = score_document(
            amc_from_source=True,
            amc_in_document=True,
            period_from_name_or_link=True,
            period_in_document=True,
            document_type_from_link=True,
            document_type_in_document=True,
            missing_period=False,
            missing_document_type=False,
            conflicting_amc=False,
            conflicting_period=True,
        )
        self.assertTrue(result.hard_conflict)

    def test_score_is_capped_at_100(self):
        result = score_document(
            amc_from_source=True,
            amc_in_document=True,
            period_from_name_or_link=True,
            period_in_document=True,
            document_type_from_link=True,
            document_type_in_document=True,
            missing_period=False,
            missing_document_type=False,
            conflicting_amc=False,
            conflicting_period=False,
        )
        self.assertEqual(result.score, 100)


if __name__ == "__main__":
    unittest.main()
