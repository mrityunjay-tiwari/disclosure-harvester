import unittest

from harvester.publish.business_key import holding_business_key


class BusinessKeyTests(unittest.TestCase):
    def test_uses_isin_when_present(self):
        self.assertEqual(holding_business_key(" ine040a01034 ", "HDFC Bank Ltd", "equity"), "isin:INE040A01034")

    def test_uses_security_name_for_non_isin_rows(self):
        self.assertEqual(holding_business_key(None, "TREPS", "cash equivalent"), "name:treps|asset:cash equivalent")


if __name__ == "__main__":
    unittest.main()
