from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools" / "generate_layout_proxy.py"
VALIDATOR = ROOT / "tools" / "validate_contract.py"


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


def write_contract_package(package: Path, interface_ref: str = "motor.nema_17.layout") -> None:
    write_json(
        package / "cad_spec.json",
        {
            "schema_version": "0.8.0",
            "kind": "cad_spec",
            "id": "belt_drive_layout",
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
                    "statement": "Motor shaft axis is locked for layout.",
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
            "id": "belt_drive_layout_contract",
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
                    "interface_signature_refs": [interface_ref],
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


class LayoutProxyGeneratorTest(unittest.TestCase):
    def test_generates_scene_and_inspection_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package"
            out = root / "out"
            package.mkdir()
            write_contract_package(package)

            result = run_tool(GENERATOR, "--package", str(package), "--out", str(out))
            self.assertEqual(0, result.returncode, result.stderr)

            scene_path = out / "layout_proxy.scene.json"
            report_path = out / "layout_proxy.inspection_report.json"
            self.assertTrue(scene_path.exists())
            self.assertTrue(report_path.exists())

            scene = json.loads(scene_path.read_text(encoding="utf-8"))
            self.assertEqual("layout_proxy_scene", scene["kind"])
            self.assertEqual("belt_drive_layout", scene["source_spec_id"])
            primitive_ids = {primitive["id"] for primitive in scene["primitives"]}
            self.assertIn("motor_proxy.motor_body", primitive_ids)
            self.assertIn("bearing_proxy.bearing_envelope", primitive_ids)
            self.assertIn("check_motor_axis", {item["check_id"] for item in scene["skipped_checks"]})

            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual("inspection_report", report["kind"])
            self.assertEqual("layout_proxy_scene", report["artifact"]["kind"])
            self.assertEqual("ready_for_layout_generation", report["proceed_recommendation"])

            validation = run_tool(VALIDATOR, "--package-only", "--package", str(out))
            self.assertEqual(0, validation.returncode, validation.stderr)

    def test_unresolved_interface_signature_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package"
            out = root / "out"
            package.mkdir()
            write_contract_package(package, interface_ref="missing.interface.layout")

            result = run_tool(GENERATOR, "--package", str(package), "--out", str(out))
            self.assertNotEqual(0, result.returncode)
            self.assertIn("unresolved interface signature", result.stderr)


if __name__ == "__main__":
    unittest.main()
