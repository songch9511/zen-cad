from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "run_contract_pipeline.py"
VALIDATOR = ROOT / "tools" / "validate_contract.py"
BUILD123D_AVAILABLE = importlib.util.find_spec("build123d") is not None


BENCHMARKS = [
    ROOT / "benchmarks" / "01-rectangular-calibration-block" / "package",
    ROOT / "benchmarks" / "02-circular-flange" / "package",
    ROOT / "benchmarks" / "03-planetary-gear-stage" / "package",
]


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


class ZenNativeBenchmarkTest(unittest.TestCase):
    @unittest.skipUnless(BUILD123D_AVAILABLE, "build123d is required for native benchmark generation")
    def test_native_benchmarks_generate_step_and_viewer_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for package in BENCHMARKS:
                with self.subTest(package=package.name):
                    validation = run_tool(VALIDATOR, "--package-only", "--package", str(package))
                    self.assertEqual(0, validation.returncode, validation.stderr)

                    out = root / package.parent.name
                    result = run_tool(RUNNER, "--package", str(package), "--out", str(out), "--target-harness", "build123d")
                    self.assertEqual(0, result.returncode, result.stderr)

                    step = out / "source" / "layout_proxy_build123d.step"
                    generation_report = out / "source" / "cad_generation.inspection_report.json"
                    proceed_gate = out / "proceed_gate.json"
                    viewer_link = out / "viewer_link.html"
                    self.assertTrue(step.exists(), str(step))
                    self.assertGreater(step.stat().st_size, 0)
                    self.assertTrue(viewer_link.exists(), str(viewer_link))

                    report = load_json(generation_report)
                    self.assertIn(report["status"], {"passed", "partial"})
                    statuses = {check["check_id"]: check["status"] for check in report["checks"]}
                    self.assertEqual("passed", statuses["cad_feature_plan_carried"])
                    self.assertEqual("passed", statuses["cad_feature_types_supported"])
                    self.assertEqual("passed", statuses["step_import_succeeds"])
                    self.assertEqual("passed", statuses["step_bbox_nonzero"])

                    gate = load_json(proceed_gate)
                    self.assertEqual("ready_for_user_review", gate["status"])
                    artifact_kinds = {artifact["kind"] for artifact in gate["artifacts"]}
                    self.assertIn("step", artifact_kinds)
                    self.assertIn("viewer", artifact_kinds)


if __name__ == "__main__":
    unittest.main()
