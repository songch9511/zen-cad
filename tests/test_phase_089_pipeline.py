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
GENERATOR = ROOT / "tools" / "generate_layout_proxy.py"
SCENE_INSPECTOR = ROOT / "tools" / "inspect_layout_proxy.py"
SOURCE_EXPORTER = ROOT / "tools" / "export_cad_source.py"
SOURCE_INSPECTOR = ROOT / "tools" / "inspect_cad_source.py"
PROCEED_PACKAGER = ROOT / "tools" / "package_proceed_gate.py"
PROCEED_APPROVER = ROOT / "tools" / "approve_proceed_gate.py"
DETAIL_HANDOFF = ROOT / "tools" / "generate_detail_handoff.py"
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


def run_pipeline(root: Path) -> tuple[Path, Path, Path, Path, Path, Path, Path]:
    package = root / "package"
    scene_out = root / "scene"
    source_out = root / "source"
    package.mkdir()
    write_contract_package(package)

    generated = run_tool(GENERATOR, "--package", str(package), "--out", str(scene_out))
    assert generated.returncode == 0, generated.stderr
    scene = scene_out / "layout_proxy.scene.json"

    scene_report = scene_out / "locked_facts.inspection_report.json"
    scene_inspected = run_tool(SCENE_INSPECTOR, "--package", str(package), "--scene", str(scene), "--out", str(scene_report))
    assert scene_inspected.returncode == 0, scene_inspected.stderr

    exported = run_tool(SOURCE_EXPORTER, "--package", str(package), "--scene", str(scene), "--out", str(source_out))
    assert exported.returncode == 0, exported.stderr
    source = source_out / "layout_proxy_build123d.py"
    manifest = source_out / "cad_source_manifest.json"

    source_report = source_out / "source.inspection_report.json"
    source_inspected = run_tool(
        SOURCE_INSPECTOR,
        "--scene",
        str(scene),
        "--manifest",
        str(manifest),
        "--source",
        str(source),
        "--out",
        str(source_report),
    )
    assert source_inspected.returncode == 0, source_inspected.stderr

    proceed = root / "proceed_gate.json"
    packaged = run_tool(
        PROCEED_PACKAGER,
        "--package",
        str(package),
        "--artifact",
        str(scene),
        "--artifact",
        str(source),
        "--report",
        str(scene_report),
        "--report",
        str(source_report),
        "--out",
        str(proceed),
    )
    assert packaged.returncode == 0, packaged.stderr

    approval = root / "proceed_approval.json"
    approved = run_tool(
        PROCEED_APPROVER,
        "--proceed-gate",
        str(proceed),
        "--out",
        str(approval),
        "--approver",
        "test_user",
    )
    assert approved.returncode == 0, approved.stderr

    handoff = root / "detail_handoff.json"
    detail = run_tool(
        DETAIL_HANDOFF,
        "--package",
        str(package),
        "--proceed-gate",
        str(proceed),
        "--approval",
        str(approval),
        "--out",
        str(handoff),
        "--target-harness",
        "build123d",
    )
    assert detail.returncode == 0, detail.stderr
    return package, scene, source, source_report, proceed, approval, handoff


class Phase089PipelineTest(unittest.TestCase):
    def test_contract_to_detail_handoff_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package, scene, source, source_report, proceed, approval, handoff = run_pipeline(Path(tmp))

            scene_data = load_json(scene)
            self.assertEqual("layout_proxy_scene", scene_data["kind"])

            source_text = source.read_text(encoding="utf-8")
            self.assertIn("def gen_step", source_text)
            self.assertIn("ZEN_CAD_PRIMITIVES", source_text)

            source_report_data = load_json(source_report)
            self.assertEqual("partial", source_report_data["status"])
            statuses = {check["check_id"]: check["status"] for check in source_report_data["checks"]}
            self.assertEqual("passed", statuses["source_primitives_cover_scene"])
            self.assertEqual("passed", statuses["cad_source_layout_facts_carried"])

            proceed_data = load_json(proceed)
            self.assertEqual("proceed_gate_package", proceed_data["kind"])
            self.assertEqual("ready_for_user_review", proceed_data["status"])
            self.assertIn("detail_upgrade", proceed_data["decision_options"])

            approval_data = load_json(approval)
            self.assertEqual("proceed_approval", approval_data["kind"])
            self.assertEqual("proceed", approval_data["decision"])

            handoff_data = load_json(handoff)
            self.assertEqual("handoff_packet", handoff_data["kind"])
            self.assertEqual("detail_cad", handoff_data["target_maturity"])
            self.assertIn("motor_axis_locked", handoff_data["locked_facts"])
            self.assertEqual(str(approval), handoff_data["extensions"]["proceed_approval"])
            self.assertTrue(any("locked layout facts" in item for item in handoff_data["stop_conditions"]))

            for path in [package, scene, source_report, proceed, approval, handoff]:
                validation = run_tool(VALIDATOR, "--package-only", "--package", str(path))
                self.assertEqual(0, validation.returncode, validation.stderr)

    def test_source_locked_step_replaces_matching_proxy_primitives(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package"
            scene_out = root / "scene"
            source_out = root / "source"
            package.mkdir()
            write_contract_package(package)
            sourced_dir = package / "sourced"
            sourced_dir.mkdir()
            bearing_step = sourced_dir / "bearing_608.step"
            bearing_step.write_text("ISO-10303-21; END-ISO-10303-21;", encoding="utf-8")
            write_json(
                package / "bearing_source_lock.json",
                {
                    "schema_version": "0.8.0",
                    "kind": "source_lock_evidence",
                    "id": "belt_drive_layout.bearing_proxy.source_lock",
                    "part_id": "bearing_proxy",
                    "part_role": "catalog_part",
                    "lock_status": "source_locked",
                    "source_identity": {
                        "display_name": "608 bearing sourced STEP",
                        "manufacturer_name": "",
                        "model": "608",
                        "product_url": "",
                        "identity_basis": "user_provided",
                    },
                    "evidence_sources": [
                        {
                            "source_type": "user_provided",
                            "locator": "sourced/bearing_608.step",
                            "artifact_kind": "step",
                            "trusted_for": ["geometry_reference"],
                            "retrieval_status": "provided_file_not_inspected",
                            "observed_at": "2026-06-10",
                            "notes": "Fixture STEP path for source import.",
                        }
                    ],
                    "interface_signature_refs": ["bearing.608.layout"],
                    "interface_signature_role": "layout_reference_only",
                    "claims_made": ["geometry_reference_url"],
                    "required_before_final": [
                        "Import the locked source geometry in the downstream CAD harness.",
                        "Run geometry checks for required datums, axes, interfaces, and clearances.",
                    ],
                    "claims_not_made": [
                        "No rating, load capacity, torque capacity, or safety factor is claimed.",
                        "No certification, compliance, price, inventory, or availability is claimed.",
                    ],
                    "extensions": {},
                },
            )

            generated = run_tool(GENERATOR, "--package", str(package), "--out", str(scene_out))
            self.assertEqual(0, generated.returncode, generated.stderr)
            scene = scene_out / "layout_proxy.scene.json"

            exported = run_tool(SOURCE_EXPORTER, "--package", str(package), "--scene", str(scene), "--out", str(source_out))
            self.assertEqual(0, exported.returncode, exported.stderr)

            source = source_out / "layout_proxy_build123d.py"
            manifest = source_out / "cad_source_manifest.json"
            source_text = source.read_text(encoding="utf-8")
            manifest_data = load_json(manifest)

            self.assertIn("ZEN_CAD_SOURCED_PARTS", source_text)
            self.assertIn("import_step", source_text)
            self.assertIn(str(bearing_step.resolve()), source_text)
            self.assertNotIn("bearing_proxy.bearing_envelope", source_text)
            self.assertEqual("bearing_proxy", manifest_data["sourced_parts"][0]["part_id"])
            self.assertEqual(str(bearing_step.resolve()), manifest_data["sourced_parts"][0]["locator"])

            source_report = source_out / "source.inspection_report.json"
            source_inspected = run_tool(
                SOURCE_INSPECTOR,
                "--scene",
                str(scene),
                "--manifest",
                str(manifest),
                "--source",
                str(source),
                "--out",
                str(source_report),
            )
            self.assertEqual(0, source_inspected.returncode, source_inspected.stderr)
            report_data = load_json(source_report)
            statuses = {check["check_id"]: check["status"] for check in report_data["checks"]}
            self.assertEqual("passed", statuses["source_sourced_parts_cover_manifest"])
            self.assertEqual("passed", statuses["source_imports_sourced_steps"])

    def test_source_inspector_detects_scene_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, scene, source, _, _, _, _ = run_pipeline(root)
            manifest = root / "source" / "cad_source_manifest.json"
            manifest_data = load_json(manifest)
            manifest_data["source_scene_id"] = "wrong_scene"
            broken_manifest = root / "broken_manifest.json"
            write_json(broken_manifest, manifest_data)

            report = root / "broken_source.inspection_report.json"
            result = run_tool(
                SOURCE_INSPECTOR,
                "--scene",
                str(scene),
                "--manifest",
                str(broken_manifest),
                "--source",
                str(source),
                "--out",
                str(report),
            )
            self.assertEqual(0, result.returncode, result.stderr)
            report_data = load_json(report)
            self.assertEqual("failed", report_data["status"])
            failed = {check["check_id"] for check in report_data["checks"] if check["status"] == "failed"}
            self.assertIn("manifest_scene_id_matches", failed)

    def test_detail_handoff_rejects_repair_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package, _, _, _, proceed, approval, _ = run_pipeline(root)
            proceed_data = load_json(proceed)
            proceed_data["status"] = "needs_repair"
            broken_proceed = root / "needs_repair_proceed_gate.json"
            write_json(broken_proceed, proceed_data)
            handoff = root / "should_not_exist.json"

            result = run_tool(
                DETAIL_HANDOFF,
                "--package",
                str(package),
                "--proceed-gate",
                str(broken_proceed),
                "--approval",
                str(approval),
                "--out",
                str(handoff),
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("ready_for_user_review", result.stderr)

    def test_detail_handoff_requires_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package, _, _, _, proceed, _, _ = run_pipeline(root)
            handoff = root / "missing_approval_handoff.json"

            result = run_tool(
                DETAIL_HANDOFF,
                "--package",
                str(package),
                "--proceed-gate",
                str(proceed),
                "--out",
                str(handoff),
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("--approval", result.stderr)


if __name__ == "__main__":
    unittest.main()
