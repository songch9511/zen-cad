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
GENERATOR = ROOT / "tools" / "generate_source_lock_evidence.py"
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


def valid_source_lock() -> dict[str, object]:
    return {
        "schema_version": "0.8.0",
        "kind": "source_lock_evidence",
        "id": "belt_drive_layout.bearing_proxy.source_lock",
        "part_id": "bearing_proxy",
        "part_role": "catalog_part",
        "lock_status": "source_locked",
        "source_identity": {
            "display_name": "608ZZ ball bearing",
            "manufacturer_name": "",
            "model": "608ZZ",
            "product_url": "https://www.step.parts/parts/bearing_608zz",
            "identity_basis": "step_parts",
        },
        "evidence_sources": [
            {
                "source_type": "step_parts",
                "locator": "https://www.step.parts/parts/bearing_608zz",
                "artifact_kind": "catalog_page",
                "trusted_for": ["source_identity", "review_only"],
                "retrieval_status": "provided_url_not_fetched",
                "observed_at": "2026-06-10",
                "notes": "step.parts part page.",
            },
            {
                "source_type": "other",
                "locator": "https://media.githubusercontent.com/media/example/parts/bearing_608zz.step",
                "artifact_kind": "step",
                "trusted_for": ["geometry_reference"],
                "retrieval_status": "provided_url_not_fetched",
                "observed_at": "2026-06-10",
                "notes": "STEP URL recorded from source evidence.",
            },
        ],
        "interface_signature_refs": ["bearing.608.layout"],
        "interface_signature_role": "layout_reference_only",
        "claims_made": ["geometry_reference_url", "review_reference", "source_identity"],
        "required_before_final": [
            "Import the locked source geometry in the downstream CAD harness.",
            "Run geometry checks for required datums, axes, interfaces, and clearances.",
        ],
        "claims_not_made": [
            "No rating, load capacity, torque capacity, or safety factor is claimed.",
            "No certification, compliance, price, inventory, or availability is claimed.",
        ],
        "extensions": {},
    }


class SourceLockEvidenceTest(unittest.TestCase):
    def test_generator_records_step_parts_and_manufacturer_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package"
            out = root / "bearing_proxy.source_lock.json"
            package.mkdir()
            write_contract_package(package)

            result = run_tool(
                GENERATOR,
                "--package",
                str(package),
                "--part-id",
                "bearing_proxy",
                "--part-role",
                "catalog_part",
                "--name",
                "608ZZ ball bearing",
                "--model",
                "608ZZ",
                "--step-parts-url",
                "https://www.step.parts/parts/bearing_608zz",
                "--step-source-url",
                "https://media.githubusercontent.com/media/example/parts/bearing_608zz.step",
                "--manufacturer-url",
                "https://example-manufacturer.test/catalog/bearing-608zz",
                "--observed-at",
                "2026-06-10",
                "--out",
                str(out),
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue(out.exists())

            evidence = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual("source_lock_evidence", evidence["kind"])
            self.assertEqual("source_locked", evidence["lock_status"])
            self.assertEqual("layout_reference_only", evidence["interface_signature_role"])
            self.assertEqual(["bearing.608.layout"], evidence["interface_signature_refs"])
            self.assertIn("source_identity", evidence["claims_made"])
            self.assertIn("geometry_reference_url", evidence["claims_made"])
            source_types = {source["source_type"] for source in evidence["evidence_sources"]}
            self.assertEqual({"manufacturer", "other", "step_parts"}, source_types)

            validation = run_tool(VALIDATOR, "--package-only", "--package", str(out))
            self.assertEqual(0, validation.returncode, validation.stderr)

    def test_source_locked_cannot_rely_on_layout_signature_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "layout_only_source_lock.json"
            evidence = valid_source_lock()
            evidence["source_identity"] = {
                "display_name": "608 layout proxy",
                "manufacturer_name": "",
                "model": "",
                "product_url": "",
                "identity_basis": "project_file",
            }
            evidence["evidence_sources"] = [
                {
                    "source_type": "project_file",
                    "locator": "registry/interfaces/bearings/608_layout.json",
                    "artifact_kind": "metadata",
                    "trusted_for": ["layout"],
                    "retrieval_status": "provided_file_not_inspected",
                    "observed_at": "2026-06-10",
                    "notes": "Layout signature only.",
                }
            ]
            evidence["claims_made"] = ["review_reference"]
            write_json(path, evidence)

            result = run_tool(VALIDATOR, "--package-only", "--package", str(path))
            self.assertNotEqual(0, result.returncode)
            self.assertIn("cannot rely only on layout", result.stderr)

    def test_source_lock_rejects_rating_or_certification_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad_claim_source_lock.json"
            evidence = valid_source_lock()
            evidence["certification"] = "UL"
            write_json(path, evidence)

            result = run_tool(VALIDATOR, "--package-only", "--package", str(path))
            self.assertNotEqual(0, result.returncode)
            self.assertIn("final-claim keys", result.stderr)

    def test_step_parts_evidence_must_use_step_parts_domain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package"
            out = root / "bad_domain.source_lock.json"
            package.mkdir()
            write_contract_package(package)

            result = run_tool(
                GENERATOR,
                "--package",
                str(package),
                "--part-id",
                "bearing_proxy",
                "--name",
                "608ZZ ball bearing",
                "--step-parts-url",
                "https://example.com/parts/bearing_608zz",
                "--out",
                str(out),
            )
            self.assertNotEqual(0, result.returncode)
            self.assertIn("step_parts evidence locator", result.stderr)

    def test_checksum_recorded_step_requires_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing_checksum.source_lock.json"
            evidence = valid_source_lock()
            evidence["evidence_sources"] = [
                {
                    "source_type": "step_parts",
                    "locator": "https://media.githubusercontent.com/media/earthtojake/step.parts/main/cad/parts/bearing_608zz.step",
                    "artifact_kind": "step",
                    "trusted_for": ["geometry_reference"],
                    "retrieval_status": "checksum_recorded",
                    "observed_at": "2026-06-10",
                    "notes": "Checksum status without a checksum is invalid.",
                }
            ]
            write_json(path, evidence)

            result = run_tool(VALIDATOR, "--package-only", "--package", str(path))
            self.assertNotEqual(0, result.returncode)
            self.assertIn("checksum_recorded STEP/STP evidence must include sha256", result.stderr)

    def test_step_parts_api_and_media_asset_origins_are_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "step_parts_media.source_lock.json"
            evidence = valid_source_lock()
            evidence["evidence_sources"] = [
                {
                    "source_type": "step_parts",
                    "locator": "https://api.step.parts/v1/parts/bearing_608zz",
                    "artifact_kind": "metadata",
                    "trusted_for": ["source_identity", "review_only"],
                    "retrieval_status": "inspected_elsewhere",
                    "observed_at": "2026-06-10",
                    "notes": "API metadata.",
                },
                {
                    "source_type": "step_parts",
                    "locator": "https://media.githubusercontent.com/media/earthtojake/step.parts/main/cad/parts/bearing_608zz.step",
                    "artifact_kind": "step",
                    "trusted_for": ["geometry_reference"],
                    "retrieval_status": "checksum_recorded",
                    "sha256": "a" * 64,
                    "observed_at": "2026-06-10",
                    "notes": "step.parts media asset.",
                },
            ]
            write_json(path, evidence)

            result = run_tool(VALIDATOR, "--package-only", "--package", str(path))
            self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
