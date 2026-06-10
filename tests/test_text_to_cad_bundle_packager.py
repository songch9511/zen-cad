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


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def write_handoff(path: Path, target_harness: str = "text-to-cad", extensions: dict | None = None) -> None:
    write_json(
        path,
        {
            "schema_version": "0.8.0",
            "kind": "handoff_packet",
            "id": "belt_drive_layout.detail_upgrade_handoff",
            "spec_id": "belt_drive_layout",
            "target_harness": target_harness,
            "target_maturity": "detail_cad",
            "locked_facts": ["motor_axis_locked"],
            "parameter_contract": ["motor_shaft_axis"],
            "artifact_targets": ["detail_cad.step", "detail CAD source", "inspection report"],
            "required_checks": ["check_motor_axis"],
            "repair_loop": "Change the smallest source-level cause, rerun failed checks, and stop if a locked layout fact must change.",
            "stop_conditions": ["Stop if locked layout facts must change."],
            "extensions": extensions or {},
        },
    )


class TextToCadBundlePackagerTest(unittest.TestCase):
    def test_packages_approved_text_to_cad_handoff_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package"
            review_out = root / "review"
            detail_out = root / "detail"
            bundle = root / "bundle"
            approval = root / "proceed_approval.json"
            package.mkdir()
            write_contract_package(package)

            review = run_tool(RUNNER, "--package", str(package), "--out", str(review_out), "--target-harness", "text-to-cad")
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
                "text-to-cad",
                "--approval",
                str(approval),
            )
            self.assertEqual(0, detail.returncode, detail.stderr)

            result = run_tool(PACKAGER, "--handoff", str(detail_out / "detail_handoff.json"), "--out", str(bundle))
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(
                {"adapter_manifest.json", "handoff_packet.json", "text_to_cad_prompt.md"},
                {path.name for path in bundle.iterdir()},
            )

            prompt = (bundle / "text_to_cad_prompt.md").read_text(encoding="utf-8")
            self.assertIn("CAD Skills/text-to-cad", prompt)
            self.assertIn("Zen CAD has not generated CAD source", prompt)
            self.assertIn("motor_axis_locked", prompt)
            self.assertIn("Stop instead of changing locked layout facts", prompt)

            handoff = load_json(bundle / "handoff_packet.json")
            self.assertEqual("text-to-cad", handoff["target_harness"])

            manifest = load_json(bundle / "adapter_manifest.json")
            self.assertEqual("text_to_cad_bundle_manifest", manifest["kind"])
            self.assertEqual("tools/package_text_to_cad_bundle.py", manifest["extensions"]["packager"])
            self.assertEqual(str(detail_out / "detail_handoff.json"), manifest["source_handoff"])
            self.assertEqual("proceed", manifest["approval"]["proceed_decision"])
            self.assertIn("does not generate CAD source", manifest["adapter_contract"]["boundary"])

            validation = run_tool(VALIDATOR, "--package-only", "--package", str(bundle))
            self.assertEqual(0, validation.returncode, validation.stderr)

    def test_rejects_handoff_without_approval_markers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "handoff.json"
            bundle = root / "bundle"
            write_handoff(handoff)

            result = run_tool(PACKAGER, "--handoff", str(handoff), "--out", str(bundle))
            self.assertNotEqual(0, result.returncode)
            self.assertIn("approved handoff is missing approval markers", result.stderr)
            self.assertFalse((bundle / "text_to_cad_prompt.md").exists())

    def test_rejects_non_text_to_cad_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            handoff = root / "handoff.json"
            bundle = root / "bundle"
            write_handoff(
                handoff,
                target_harness="build123d",
                extensions={
                    "proceed_gate": "proceed_gate.json",
                    "proceed_gate_status": "ready_for_user_review",
                    "proceed_approval": "proceed_approval.json",
                    "proceed_decision": "proceed",
                },
            )

            result = run_tool(PACKAGER, "--handoff", str(handoff), "--out", str(bundle))
            self.assertNotEqual(0, result.returncode)
            self.assertIn("target_harness text-to-cad", result.stderr)


if __name__ == "__main__":
    unittest.main()
