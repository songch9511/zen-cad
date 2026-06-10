from __future__ import annotations

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
PACKAGER = ROOT / "tools" / "package_text_to_cad_bundle.py"
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


class Phase100IntegrationTest(unittest.TestCase):
    def test_text_to_cad_pipeline_generates_review_and_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package"
            review_out = root / "review"
            detail_out = root / "detail"
            approval = root / "proceed_approval.json"
            package.mkdir()
            write_contract_package(package)

            review = run_tool(RUNNER, "--package", str(package), "--out", str(review_out), "--target-harness", "text-to-cad")
            self.assertEqual(0, review.returncode, review.stderr)
            self.assertTrue((review_out / "review_bundle.json").exists())

            gate = load_json(review_out / "proceed_gate.json")
            self.assertIn("source_lock_summary", gate["extensions"])
            self.assertEqual(["motor_proxy"], gate["extensions"]["source_lock_summary"]["final_blockers"])

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
                "text-to-cad",
                "--approval",
                str(approval),
            )
            self.assertEqual(0, detail.returncode, detail.stderr)
            self.assertTrue((detail_out / "detail_handoff.json").exists())
            self.assertTrue((detail_out / "text_to_cad_bundle" / "text_to_cad_prompt.md").exists())

            prompt = (detail_out / "text_to_cad_bundle" / "text_to_cad_prompt.md").read_text(encoding="utf-8")
            self.assertIn("CAD Skills/text-to-cad", prompt)
            self.assertIn("motor_axis_locked", prompt)
            self.assertIn("Do not treat viewer links or screenshots as substitutes", prompt)

            summary = load_json(detail_out / "pipeline_run.json")
            self.assertEqual("completed", summary["status"])
            self.assertEqual("package_text_to_cad_bundle", summary["steps"][-1]["step_id"])
            self.assertEqual(str(detail_out / "text_to_cad_bundle"), summary["artifacts"]["text_to_cad_bundle"])

            validation = run_tool(VALIDATOR, "--package-only", "--package", str(detail_out))
            self.assertEqual(0, validation.returncode, validation.stderr)

    def test_text_to_cad_prompt_rejects_non_text_to_cad_handoff(self) -> None:
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
            approved = run_tool(APPROVER, "--proceed-gate", str(review_out / "proceed_gate.json"), "--out", str(approval))
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

            result = run_tool(
                PACKAGER,
                "--handoff",
                str(detail_out / "detail_handoff.json"),
                "--out",
                str(root / "bad_bundle"),
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("target_harness text-to-cad", result.stderr)


if __name__ == "__main__":
    unittest.main()
