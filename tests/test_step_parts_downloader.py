from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from download_step_part import StepPartDownloader, parse_args
from test_layout_proxy_generator import write_contract_package


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools" / "generate_layout_proxy.py"
SOURCE_EXPORTER = ROOT / "tools" / "export_cad_source.py"
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


class FakeStepPartDownloader(StepPartDownloader):
    def __init__(self, repo_root: Path, args: Any, record: dict[str, Any], step_bytes: bytes) -> None:
        super().__init__(repo_root, args)
        self.record = record
        self.step_bytes = step_bytes

    def fetch_bytes(self, url: str) -> bytes | None:
        if url.endswith(f"/v1/parts/{self.record['id']}"):
            return json.dumps(self.record).encode("utf-8")
        if url == self.record["stepUrl"]:
            return self.step_bytes
        self.error(url, "unexpected fake step.parts URL")
        return None


def fake_record(step_bytes: bytes, sha256: str | None = None) -> dict[str, Any]:
    digest = sha256 or hashlib.sha256(step_bytes).hexdigest()
    return {
        "id": "bearing_608zz",
        "name": "608ZZ ball bearing",
        "category": "bearings",
        "family": "deep_groove_ball_bearing",
        "standard": {},
        "attributes": {"bore_diameter": "8 mm"},
        "pageUrl": "https://www.step.parts/parts/bearing_608zz",
        "apiUrl": "https://api.step.parts/v1/parts/bearing_608zz",
        "stepUrl": "https://media.githubusercontent.com/media/earthtojake/step.parts/main/cad/parts/bearing_608zz.step",
        "sha256": digest,
        "byteSize": len(step_bytes),
    }


class StepPartsDownloaderTest(unittest.TestCase):
    def test_download_generates_checksum_source_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package"
            out_dir = package / "sourced_parts" / "step_parts"
            source_lock = package / "bearing_source_lock.json"
            package.mkdir()
            write_contract_package(package)

            step_bytes = b"ISO-10303-21; FAKE STEP; END-ISO-10303-21;"
            args = parse_args(
                [
                    "--id",
                    "bearing_608zz",
                    "--download",
                    "--out-dir",
                    str(out_dir),
                    "--package",
                    str(package),
                    "--part-id",
                    "bearing_proxy",
                    "--part-role",
                    "catalog_part",
                    "--source-lock-out",
                    str(source_lock),
                    "--observed-at",
                    "2026-06-10",
                ]
            )
            downloader = FakeStepPartDownloader(ROOT, args, fake_record(step_bytes), step_bytes)

            payload = downloader.run()
            self.assertFalse(downloader.issues, downloader.issues)
            self.assertIsNotNone(payload)
            self.assertEqual(1, payload["count"])
            self.assertTrue((out_dir / "bearing_608zz.step").exists())
            self.assertTrue(source_lock.exists())

            evidence = json.loads(source_lock.read_text(encoding="utf-8"))
            geometry_sources = [
                source
                for source in evidence["evidence_sources"]
                if source["artifact_kind"] == "step" and "geometry_reference" in source["trusted_for"]
            ]
            self.assertEqual(2, len(geometry_sources))
            self.assertTrue(all(source["retrieval_status"] == "checksum_recorded" for source in geometry_sources))
            self.assertTrue(all(source["sha256"] == hashlib.sha256(step_bytes).hexdigest() for source in geometry_sources))
            self.assertEqual("project_file", geometry_sources[-1]["source_type"])

            validation = run_tool(VALIDATOR, "--package-only", "--package", str(source_lock))
            self.assertEqual(0, validation.returncode, validation.stderr)

    def test_download_rejects_sha256_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "package"
            package.mkdir()
            write_contract_package(package)
            step_bytes = b"ISO-10303-21; BAD CHECKSUM; END-ISO-10303-21;"
            args = parse_args(
                [
                    "--id",
                    "bearing_608zz",
                    "--download",
                    "--out-dir",
                    str(package / "sourced_parts"),
                    "--package",
                    str(package),
                ]
            )
            downloader = FakeStepPartDownloader(ROOT, args, fake_record(step_bytes, sha256="0" * 64), step_bytes)

            self.assertIsNone(downloader.run())
            self.assertTrue(any("sha256 mismatch" in issue.message for issue in downloader.issues))

    def test_existing_file_with_same_checksum_is_reused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "package"
            out_dir = package / "sourced_parts"
            package.mkdir()
            write_contract_package(package)
            step_bytes = b"ISO-10303-21; REUSED STEP; END-ISO-10303-21;"
            out_dir.mkdir()
            (out_dir / "bearing_608zz.step").write_bytes(step_bytes)
            args = parse_args(
                [
                    "--id",
                    "bearing_608zz",
                    "--download",
                    "--out-dir",
                    str(out_dir),
                    "--package",
                    str(package),
                ]
            )
            downloader = FakeStepPartDownloader(ROOT, args, fake_record(step_bytes), step_bytes)

            payload = downloader.run()
            self.assertFalse(downloader.issues, downloader.issues)
            self.assertIsNotNone(payload)
            self.assertEqual(str(out_dir / "bearing_608zz.step"), payload["items"][0]["saved_step"])

    def test_exporter_prefers_checksum_local_step_over_remote_step_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "package"
            scene_out = root / "scene"
            source_out = root / "source"
            package.mkdir()
            write_contract_package(package)
            local_step = package / "sourced_parts" / "step_parts" / "bearing_608zz.step"
            local_step.parent.mkdir(parents=True)
            step_bytes = b"ISO-10303-21; LOCAL SOURCE STEP; END-ISO-10303-21;"
            local_step.write_bytes(step_bytes)
            digest = hashlib.sha256(step_bytes).hexdigest()
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
                        "display_name": "608ZZ ball bearing",
                        "manufacturer_name": "",
                        "model": "bearing_608zz",
                        "product_url": "https://www.step.parts/parts/bearing_608zz",
                        "identity_basis": "step_parts",
                    },
                    "evidence_sources": [
                        {
                            "source_type": "step_parts",
                            "locator": "https://media.githubusercontent.com/media/earthtojake/step.parts/main/cad/parts/bearing_608zz.step",
                            "artifact_kind": "step",
                            "trusted_for": ["geometry_reference"],
                            "retrieval_status": "checksum_recorded",
                            "sha256": digest,
                            "observed_at": "2026-06-10",
                            "notes": "Remote step.parts STEP asset.",
                        },
                        {
                            "source_type": "project_file",
                            "locator": "sourced_parts/step_parts/bearing_608zz.step",
                            "artifact_kind": "step",
                            "trusted_for": ["geometry_reference"],
                            "retrieval_status": "checksum_recorded",
                            "sha256": digest,
                            "observed_at": "2026-06-10",
                            "notes": "Local checksum-verified STEP copy.",
                        },
                    ],
                    "interface_signature_refs": ["bearing.608.layout"],
                    "interface_signature_role": "layout_reference_only",
                    "claims_made": ["geometry_reference_url", "source_identity"],
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
            exported = run_tool(SOURCE_EXPORTER, "--package", str(package), "--scene", str(scene_out / "layout_proxy.scene.json"), "--out", str(source_out))
            self.assertEqual(0, exported.returncode, exported.stderr)

            manifest = json.loads((source_out / "cad_source_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(str(local_step.resolve()), manifest["sourced_parts"][0]["locator"])
            self.assertEqual("project_file", manifest["sourced_parts"][0]["source_type"])
            self.assertEqual("checksum_recorded", manifest["sourced_parts"][0]["retrieval_status"])
            self.assertEqual(digest, manifest["sourced_parts"][0]["sha256"])


if __name__ == "__main__":
    unittest.main()
