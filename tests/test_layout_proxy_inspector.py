from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_layout_proxy_generator import write_contract_package


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools" / "generate_layout_proxy.py"
INSPECTOR = ROOT / "tools" / "inspect_layout_proxy.py"
VALIDATOR = ROOT / "tools" / "validate_contract.py"


def run_tool(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


class LayoutProxyInspectorTest(unittest.TestCase):
    def test_inspects_generated_scene_against_locked_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package"
            out = root / "out"
            package.mkdir()
            write_contract_package(package)

            generated = run_tool(GENERATOR, "--package", str(package), "--out", str(out))
            self.assertEqual(0, generated.returncode, generated.stderr)

            report_path = out / "locked_facts.inspection_report.json"
            inspected = run_tool(
                INSPECTOR,
                "--package",
                str(package),
                "--scene",
                str(out / "layout_proxy.scene.json"),
                "--out",
                str(report_path),
            )
            self.assertEqual(0, inspected.returncode, inspected.stderr)

            report = load_json(report_path)
            self.assertEqual("inspection_report", report["kind"])
            self.assertEqual("partial", report["status"])
            self.assertEqual("ready_for_layout_generation", report["proceed_recommendation"])
            statuses = {check["check_id"]: check["status"] for check in report["checks"]}
            self.assertEqual("passed", statuses["scene_locked_facts_carried"])
            self.assertEqual("passed", statuses["scene_parts_have_primitives"])
            self.assertGreaterEqual(len(report["skipped_checks"]), 1)

            validation = run_tool(VALIDATOR, "--package-only", "--package", str(report_path))
            self.assertEqual(0, validation.returncode, validation.stderr)

    def test_reports_missing_locked_fact_as_failed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package"
            out = root / "out"
            package.mkdir()
            write_contract_package(package)

            generated = run_tool(GENERATOR, "--package", str(package), "--out", str(out))
            self.assertEqual(0, generated.returncode, generated.stderr)
            scene_path = out / "layout_proxy.scene.json"
            scene = load_json(scene_path)
            scene["locked_layout_facts"] = []
            broken_scene = out / "broken.scene.json"
            write_json(broken_scene, scene)

            report_path = out / "broken.inspection_report.json"
            inspected = run_tool(
                INSPECTOR,
                "--package",
                str(package),
                "--scene",
                str(broken_scene),
                "--out",
                str(report_path),
            )
            self.assertEqual(0, inspected.returncode, inspected.stderr)

            report = load_json(report_path)
            self.assertEqual("failed", report["status"])
            self.assertEqual("needs_repair", report["proceed_recommendation"])
            failed = {check["check_id"] for check in report["checks"] if check["status"] == "failed"}
            self.assertIn("scene_locked_facts_carried", failed)


if __name__ == "__main__":
    unittest.main()
