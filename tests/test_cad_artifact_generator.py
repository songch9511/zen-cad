from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "tools" / "generate_cad_artifact.py"
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


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


class CadArtifactGeneratorTest(unittest.TestCase):
    @unittest.skipUnless(BUILD123D_AVAILABLE, "build123d is required for in-repo CAD generation")
    def test_generates_step_and_inspection_report_from_build123d_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "simple_layout.py"
            manifest = root / "cad_source_manifest.json"
            step = root / "simple_layout.step"
            report = root / "cad_generation.inspection_report.json"

            source.write_text(
                "\n".join(
                    [
                        "from build123d import Box",
                        "",
                        "def gen_step():",
                        "    shape = Box(12, 8, 4)",
                        "    shape.label = 'simple_layout_box'",
                        "    return shape",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            write_json(
                manifest,
                {
                    "schema_version": "0.8.0",
                    "kind": "cad_source_manifest",
                    "id": "simple_layout.build123d_manifest",
                    "source_scene_id": "simple_layout.layout_proxy_scene",
                    "target_harness": "build123d",
                    "source_path": str(source),
                    "expected_primary_artifact": str(step),
                    "generated_files": [str(source), str(manifest)],
                    "primitives": ["simple_layout.box"],
                    "locked_layout_facts": ["box_size_locked"],
                    "inspection_targets": ["check_step_bbox"],
                    "source_of_truth": {
                        "scene": "layout_proxy.scene.json",
                        "package": "package",
                    },
                    "extensions": {},
                },
            )

            result = run_tool(GENERATOR, "--source", str(source), "--manifest", str(manifest), "--out", str(step), "--report", str(report))
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue(step.exists())
            self.assertGreater(step.stat().st_size, 0)
            self.assertTrue(report.exists())

            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual("inspection_report", data["kind"])
            self.assertEqual("passed", data["status"])
            statuses = {check["check_id"]: check["status"] for check in data["checks"]}
            self.assertEqual("passed", statuses["step_export_succeeds"])
            self.assertEqual("passed", statuses["step_import_succeeds"])
            self.assertEqual("passed", statuses["step_bbox_nonzero"])

            validation = run_tool(VALIDATOR, "--package-only", "--package", str(report))
            self.assertEqual(0, validation.returncode, validation.stderr)


if __name__ == "__main__":
    unittest.main()
