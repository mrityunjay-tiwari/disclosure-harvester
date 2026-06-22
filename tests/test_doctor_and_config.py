import unittest
from pathlib import Path

from harvester.config import load_sources
from harvester.doctor import run_doctor
from harvester.main import build_parser


class DoctorAndConfigTests(unittest.TestCase):
    def test_doctor_reports_core_fields(self):
        result = run_doctor()
        self.assertIn("python", result)
        self.assertIn("dependencies", result)
        self.assertIn("ready_for_fixture_demo", result)
        self.assertTrue(any(item["import_name"] == "yaml" for item in result["dependencies"]))

    def test_config_has_dynamic_validated_sources(self):
        sources = load_sources(Path(__file__).resolve().parents[1] / "configs" / "sources.yaml")
        self.assertGreaterEqual(len(sources), 10)
        self.assertTrue(any(source.source_type == "js" for source in sources))
        self.assertTrue(any(source.validated_end_to_end for source in sources))

    def test_only_validated_demo_sources_are_active(self):
        sources = load_sources(Path(__file__).resolve().parents[1] / "configs" / "sources.yaml")
        active_sources = [source for source in sources if source.active]
        self.assertEqual(len(active_sources), 3)
        self.assertTrue(all(source.validated_end_to_end for source in active_sources))

    def test_verbose_flag_is_optional_and_global(self):
        args = build_parser().parse_args(["--verbose", "--warehouse-path", "data/warehouse/check.duckdb", "run-fixtures"])
        self.assertTrue(args.verbose)
        self.assertEqual(args.warehouse_path, "data/warehouse/check.duckdb")
        self.assertEqual(args.command, "run-fixtures")


if __name__ == "__main__":
    unittest.main()
