from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "run_contract_pipeline.py"
VIEWER_PACKAGER = ROOT / "tools" / "package_viewer_review.py"


def run_tool(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


def write_viewer_contract_package(package: Path) -> None:
    write_json(
        package / "cad_spec.json",
        {
            "schema_version": "0.8.0",
            "kind": "cad_spec",
            "id": "viewer_drive_layout",
            "units": "mm",
            "parameter_contract": [
                {
                    "name": "motor_shaft_axis",
                    "units": "dimensionless",
                    "value": "+X",
                    "status": "locked",
                    "source": "user",
                    "drives": ["motor_proxy.shaft_axis"],
                    "validation": ["check_motor_axis"],
                }
            ],
            "artifact_targets": {
                "source_intent": "unknown",
                "primary_artifact": "layout_proxy.scene.json",
                "review_artifacts": ["layout_proxy.inspection_report.json"],
            },
            "locked_layout_facts": [
                {
                    "fact_id": "motor_axis_locked",
                    "type": "axis",
                    "statement": "Motor shaft axis is locked for viewer review.",
                    "must_preserve": True,
                }
            ],
            "inspection_plan": [
                {
                    "check_id": "check_motor_axis",
                    "check_type": "axis",
                    "target": "motor_proxy.shaft_axis",
                    "expected": "Preserve motor shaft axis datum.",
                    "locked_fact_refs": ["motor_axis_locked"],
                }
            ],
            "repair_loop": {
                "smallest_source_change": True,
                "rerun_failed_checks": True,
                "locked_fact_change_policy": "Return to proceed gate if locked facts must change.",
            },
            "proceed_gate": {
                "required_user_decision": "approve layout proxy positioning",
                "approved_next_maturity": "detail_cad",
            },
            "downstream_handoff": {
                "locked_facts": ["motor_axis_locked"],
                "required_checks": ["check_motor_axis"],
                "stop_conditions": ["Stop if locked layout facts must change."],
            },
            "extensions": {},
        },
    )
    write_json(
        package / "layout_contract.json",
        {
            "schema_version": "0.8.0",
            "kind": "layout_contract",
            "id": "viewer_drive_layout_contract",
            "root_component": "base_plate",
            "root_frame": {
                "origin": "base footprint center",
                "axes": "XY base plane, +Z up",
            },
            "parts": [
                {
                    "part_id": "motor_proxy",
                    "role": "driver",
                    "local_frame": "motor face center, shaft axis +X",
                    "proxy_policy": "box body plus shaft axis marker",
                    "interface_signature_refs": ["motor.nema_17.layout"],
                },
                {
                    "part_id": "bearing_proxy",
                    "role": "locator",
                    "local_frame": "bearing center, axis +X",
                    "proxy_policy": "cylindrical envelope",
                    "interface_signature_refs": ["bearing.608.layout"],
                },
            ],
            "relationships": {
                "contacts": [],
                "connections": [
                    {
                        "relationship_id": "motor_to_shaft",
                        "type": "coaxial",
                        "parts": ["motor_proxy", "bearing_proxy"],
                        "statement": "Motor shaft and bearing bore remain coaxial.",
                        "locked": True,
                    }
                ],
                "motion": [],
            },
            "locked_facts": ["motor_axis_locked"],
            "inspection_targets": [
                {
                    "target_id": "check_motor_axis",
                    "check_type": "axis",
                    "target": "motor_proxy.shaft_axis",
                    "expected": "Axis marker exists in layout proxy scene.",
                }
            ],
            "extensions": {},
        },
    )


class ViewerReviewPackagerTest(unittest.TestCase):
    def test_generates_viewer_review_brief_from_runner_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package"
            run_out = root / "run"
            brief = root / "viewer_review.md"
            snapshot = root / "viewer_snapshot.png"
            package.mkdir()
            write_viewer_contract_package(package)
            snapshot.write_text("placeholder viewer snapshot", encoding="utf-8")

            pipeline = run_tool(RUNNER, "--package", str(package), "--out", str(run_out), "--target-harness", "build123d")
            self.assertEqual(0, pipeline.returncode, pipeline.stderr)

            result = run_tool(
                VIEWER_PACKAGER,
                "--proceed-gate",
                str(run_out / "proceed_gate.json"),
                "--pipeline-run",
                str(run_out / "pipeline_run.json"),
                "--viewer-artifact",
                str(snapshot),
                "--out",
                str(brief),
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue(brief.exists())

            text = brief.read_text(encoding="utf-8")
            self.assertIn("# Zen CAD Viewer Review Brief", text)
            self.assertIn("Spec ID: `viewer_drive_layout`", text)
            self.assertIn("Gate status: `ready_for_user_review`", text)
            self.assertIn("Pipeline status: `ready_for_user_review`", text)
            self.assertIn("`viewer_snapshot`", text)
            self.assertIn("`motor_axis_locked`", text)
            self.assertIn("Do not mark the package complete from screenshots alone", text)
            self.assertIn("Detail CAD handoff still requires an explicit proceed approval artifact", text)

    def test_rejects_non_proceed_gate_document(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            not_gate = root / "pipeline_run.json"
            brief = root / "viewer_review.md"
            write_json(
                not_gate,
                {
                    "schema_version": "0.8.0",
                    "kind": "pipeline_run",
                    "id": "not_a_gate",
                    "contract_package": "package",
                    "target_harness": "unknown",
                    "status": "failed",
                    "steps": [
                        {
                            "step_id": "validate_contract",
                            "status": "failed",
                            "outputs": [],
                            "issues": [{"path": "package", "message": "fixture"}],
                            "note": "",
                        }
                    ],
                    "artifacts": {},
                    "extensions": {},
                },
            )

            result = run_tool(VIEWER_PACKAGER, "--proceed-gate", str(not_gate), "--out", str(brief))
            self.assertNotEqual(0, result.returncode)
            self.assertIn("viewer review requires a proceed_gate_package document", result.stderr)
            self.assertFalse(brief.exists())


if __name__ == "__main__":
    unittest.main()
