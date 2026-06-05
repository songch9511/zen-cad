from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validate_contract.py"


def run_validator(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")


class ContractValidatorTest(unittest.TestCase):
    def test_repo_contract_surface_validates(self) -> None:
        result = run_validator()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Zen CAD contract validation passed.", result.stdout)

    def test_minimal_cad_spec_package_validates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp)
            write_json(
                package / "cad_spec.json",
                {
                    "schema_version": "0.8.0",
                    "kind": "cad_spec",
                    "id": "layout_test",
                    "parameter_contract": [],
                    "artifact_targets": {},
                    "locked_layout_facts": [
                        {
                            "fact_id": "shaft_axis_locked",
                            "type": "axis",
                            "statement": "Input shaft axis is +X.",
                            "must_preserve": True,
                        }
                    ],
                    "inspection_plan": [
                        {
                            "check_id": "check_shaft_axis",
                            "check_type": "axis",
                            "target": "input_shaft_axis",
                            "expected": "+X world axis",
                            "locked_fact_refs": ["shaft_axis_locked"],
                        }
                    ],
                    "repair_loop": {},
                    "proceed_gate": {},
                    "downstream_handoff": {
                        "locked_facts": ["shaft_axis_locked"],
                        "required_checks": ["check_shaft_axis"],
                        "stop_conditions": ["Stop if locked layout facts must change."],
                    },
                    "extensions": {},
                },
            )

            result = run_validator("--package-only", "--package", str(package))
            self.assertEqual(0, result.returncode, result.stderr)

    def test_inspection_pass_requires_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp)
            write_json(
                package / "inspection_report.json",
                {
                    "schema_version": "0.8.0",
                    "kind": "inspection_report",
                    "id": "bad_report",
                    "checks": [
                        {
                            "check_id": "bbox",
                            "check_type": "bbox",
                            "status": "passed",
                            "evidence": "",
                        }
                    ],
                    "skipped_checks": [],
                    "extensions": {},
                },
            )

            result = run_validator("--package-only", "--package", str(package))
            self.assertNotEqual(0, result.returncode)
            self.assertIn("must include evidence", result.stderr)

    def test_handoff_must_embed_locked_facts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp)
            write_json(
                package / "handoff_packet.json",
                {
                    "schema_version": "0.8.0",
                    "kind": "handoff_packet",
                    "id": "bad_handoff",
                    "required_checks": ["check_axis"],
                    "stop_conditions": ["Stop if locked facts must change."],
                    "extensions": {},
                },
            )

            result = run_validator("--package-only", "--package", str(package))
            self.assertNotEqual(0, result.returncode)
            self.assertIn("must embed locked_facts", result.stderr)


if __name__ == "__main__":
    unittest.main()
