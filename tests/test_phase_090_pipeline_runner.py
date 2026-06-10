from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_layout_proxy_generator import write_contract_package


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "run_contract_pipeline.py"
APPROVER = ROOT / "tools" / "approve_proceed_gate.py"
VALIDATOR = ROOT / "tools" / "validate_contract.py"
BUILD123D_AVAILABLE = importlib.util.find_spec("build123d") is not None


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


class Phase090PipelineRunnerTest(unittest.TestCase):
    @unittest.skipUnless(BUILD123D_AVAILABLE, "build123d is required for in-repo CAD generation")
    def test_runner_executes_review_pipeline_without_detail_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package"
            out = root / "run"
            package.mkdir()
            write_contract_package(package)

            result = run_tool(RUNNER, "--package", str(package), "--out", str(out), "--target-harness", "build123d")
            self.assertEqual(0, result.returncode, result.stderr)

            expected_artifacts = [
                out / "layout" / "layout_proxy.scene.json",
                out / "layout" / "locked_facts.inspection_report.json",
                out / "source" / "layout_proxy_build123d.py",
                out / "source" / "layout_proxy_build123d.step",
                out / "source" / "cad_source_manifest.json",
                out / "source" / "source.inspection_report.json",
                out / "source" / "cad_generation.inspection_report.json",
                out / "viewer_link.html",
                out / "proceed_gate.json",
                out / "pipeline_run.json",
            ]
            for path in expected_artifacts:
                self.assertTrue(path.exists(), str(path))
            self.assertFalse((out / "detail_handoff.json").exists())

            summary = load_json(out / "pipeline_run.json")
            self.assertEqual("pipeline_run", summary["kind"])
            self.assertEqual("ready_for_user_review", summary["status"])
            self.assertEqual("build123d", summary["target_harness"])
            self.assertEqual(
                [
                    "validate_contract",
                    "generate_layout_proxy",
                    "inspect_layout_proxy",
                    "export_cad_source",
                    "inspect_cad_source",
                    "generate_cad_artifact",
                    "package_viewer_link",
                    "package_proceed_gate",
                    "package_review_bundle",
                    "detail_handoff",
                ],
                [step["step_id"] for step in summary["steps"]],
            )
            self.assertEqual(str(out / "source" / "layout_proxy_build123d.step"), summary["artifacts"]["generated_step"])
            self.assertEqual(str(out / "viewer_link.html"), summary["artifacts"]["viewer_link"])
            self.assertEqual("skipped", summary["steps"][-1]["status"])
            self.assertTrue((out / "review_bundle.json").exists())

            validation = run_tool(VALIDATOR, "--package-only", "--package", str(out))
            self.assertEqual(0, validation.returncode, validation.stderr)

    @unittest.skipUnless(BUILD123D_AVAILABLE, "build123d is required for in-repo CAD generation")
    def test_runner_executes_detail_handoff_with_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package"
            review_out = root / "review"
            detail_out = root / "detail"
            approval = root / "proceed_approval.json"
            package.mkdir()
            write_contract_package(package)

            review = run_tool(RUNNER, "--package", str(package), "--out", str(review_out), "--target-harness", "build123d")
            self.assertEqual(0, review.returncode, review.stderr)

            approved = run_tool(
                APPROVER,
                "--proceed-gate",
                str(review_out / "proceed_gate.json"),
                "--out",
                str(approval),
                "--approver",
                "test_user",
            )
            self.assertEqual(0, approved.returncode, approved.stderr)

            detail = run_tool(
                RUNNER,
                "--package",
                str(package),
                "--out",
                str(detail_out),
                "--target-harness",
                "build123d",
                "--approval",
                str(approval),
            )
            self.assertEqual(0, detail.returncode, detail.stderr)
            self.assertTrue((detail_out / "detail_handoff.json").exists())

            summary = load_json(detail_out / "pipeline_run.json")
            self.assertEqual("completed", summary["status"])
            self.assertEqual("generate_detail_handoff", summary["steps"][-1]["step_id"])
            self.assertEqual(str(approval), summary["artifacts"]["proceed_approval"])

    def test_runner_records_failure_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package"
            out = root / "run"
            package.mkdir()
            write_contract_package(package, interface_ref="missing.interface.layout")

            result = run_tool(RUNNER, "--package", str(package), "--out", str(out))
            self.assertNotEqual(0, result.returncode)

            summary_path = out / "pipeline_run.json"
            self.assertTrue(summary_path.exists())
            summary = load_json(summary_path)
            self.assertEqual("failed", summary["status"])
            self.assertEqual("generate_layout_proxy", summary["steps"][-1]["step_id"])
            self.assertEqual("failed", summary["steps"][-1]["status"])
            issue_text = " ".join(issue["message"] for issue in summary["steps"][-1]["issues"])
            self.assertIn("unresolved interface signature", issue_text)

    def test_approval_rejects_non_ready_proceed_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package"
            out = root / "run"
            approval = root / "proceed_approval.json"
            package.mkdir()
            write_contract_package(package)

            result = run_tool(RUNNER, "--package", str(package), "--out", str(out))
            self.assertEqual(0, result.returncode, result.stderr)

            gate = load_json(out / "proceed_gate.json")
            gate["status"] = "needs_repair"
            broken_gate = root / "needs_repair_proceed_gate.json"
            broken_gate.write_text(json.dumps(gate, indent=2, sort_keys=True), encoding="utf-8")

            approved = run_tool(APPROVER, "--proceed-gate", str(broken_gate), "--out", str(approval))
            self.assertNotEqual(0, approved.returncode)
            self.assertIn("ready_for_user_review", approved.stderr)


if __name__ == "__main__":
    unittest.main()
