import unittest

from harvester.classify.period_parser import parse_period


class PeriodParserTests(unittest.TestCase):
    def test_month_name_period_is_canonical(self):
        self.assertEqual(parse_period("Monthly Portfolio June 2026"), "2026-06")

    def test_numeric_period_is_canonical(self):
        self.assertEqual(parse_period("portfolio_2026-06.pdf"), "2026-06")


if __name__ == "__main__":
    unittest.main()
