#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from validate_contract import ContractValidator, Issue


SCHEMA_VERSION = "0.8.0"


@dataclass
class DetailHandoffResult:
    handoff_path: Path


class DetailHandoffGenerator:
    def __init__(self, repo_root: Path, package: Path, proceed_gate: Path, out: Path, target_harness: str) -> None:
        self.repo_root = repo_root
        self.package = package
        self.proceed_gate = proceed_gate
        self.out = out
        self.target_harness = target_harness
        self.issues: list[Issue] = []

    def error(self, path: Path | str, message: str) -> None:
        self.issues.append(Issue(str(path), message))

    def load_json(self, path: Path) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self.error(path, "file does not exist")
        except json.JSONDecodeError as exc:
            self.error(path, f"invalid JSON: {exc}")
        return None

    def generate(self) -> DetailHandoffResult | None:
        validator = ContractValidator(self.repo_root)
        validator.validate_repo()
        validator.validate_package(self.package)
        validator.validate_package(self.proceed_gate)
        if validator.issues:
            self.issues.extend(validator.issues)
            return None
        gate = self.load_json(self.proceed_gate)
        spec = self.load_spec()
        if not isinstance(gate, dict) or spec is None:
            return None
        if gate.get("status") != "ready_for_user_review":
            self.error(self.proceed_gate, "detail handoff requires proceed gate status ready_for_user_review")
            return None

        handoff = self.build_handoff(spec, gate)
        self.out.parent.mkdir(parents=True, exist_ok=True)
        write_json(self.out, handoff)

        output_validator = ContractValidator(self.repo_root)
        output_validator.validate_package(self.out)
        if output_validator.issues:
            self.issues.extend(output_validator.issues)
            return None
        return DetailHandoffResult(handoff_path=self.out)

    def load_spec(self) -> dict[str, Any] | None:
        paths = [self.package] if self.package.is_file() else sorted(self.package.rglob("*.json"))
        specs: list[dict[str, Any]] = []
        for path in paths:
            loaded = self.load_json(path)
            if isinstance(loaded, dict) and loaded.get("kind") == "cad_spec":
                specs.append(loaded)
        if len(specs) != 1:
            self.error(self.package, "detail handoff generation requires exactly one cad_spec document")
            return None
        return specs[0]

    def build_handoff(self, spec: dict[str, Any], gate: dict[str, Any]) -> dict[str, Any]:
        locked = [
            str(fact.get("fact_id", fact))
            for fact in spec.get("locked_layout_facts", [])
            if isinstance(fact, dict) or isinstance(fact, str)
        ]
        parameters = [
            str(parameter.get("name", parameter))
            for parameter in spec.get("parameter_contract", [])
            if isinstance(parameter, dict) or isinstance(parameter, str)
        ]
        required_checks = [
            str(check.get("check_id", check))
            for check in spec.get("inspection_plan", [])
            if isinstance(check, dict) or isinstance(check, str)
        ]
        return {
            "schema_version": SCHEMA_VERSION,
            "kind": "handoff_packet",
            "id": f"{spec['id']}.detail_upgrade_handoff",
            "spec_id": spec["id"],
            "target_harness": self.target_harness,
            "target_maturity": "detail_cad",
            "locked_facts": locked,
            "parameter_contract": parameters,
            "artifact_targets": [
                str(spec.get("artifact_targets", {}).get("primary_artifact", "detail_cad.step")),
                "detail CAD source",
                "inspection report",
            ],
            "required_checks": required_checks,
            "repair_loop": "Change the smallest source-level cause, rerun failed checks, and stop if a locked layout fact must change.",
            "stop_conditions": [
                "Stop if locked layout facts must change.",
                "Stop if a required interface datum, axis, center distance, clearance, or motion relationship cannot be preserved.",
                "Stop if downstream geometry checks are unavailable and the user asked for final readiness.",
            ],
            "notes": "Proceed gate approved layout review surface. Upgrade detail without changing locked positioning facts.",
            "extensions": {
                "generator": "tools/generate_detail_handoff.py",
                "proceed_gate": str(self.proceed_gate),
                "proceed_gate_status": gate.get("status"),
            },
        }


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a detail-upgrade handoff packet from a ready proceed gate package.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1], help="Zen CAD repository root.")
    parser.add_argument("--package", type=Path, required=True, help="Contract package JSON file or directory.")
    parser.add_argument("--proceed-gate", type=Path, required=True, help="Proceed gate package JSON.")
    parser.add_argument("--out", type=Path, required=True, help="Output detail handoff JSON path.")
    parser.add_argument("--target-harness", choices=["codex", "text-to-cad", "build123d", "cadquery", "freecad", "unknown"], default="unknown")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    generator = DetailHandoffGenerator(args.repo_root, args.package, args.proceed_gate, args.out, args.target_harness)
    result = generator.generate()
    if generator.issues:
        for issue in generator.issues:
            print(f"{issue.path}: {issue.message}", file=sys.stderr)
        return 1
    if result is None:
        print("detail handoff generation failed", file=sys.stderr)
        return 1
    print(f"Detail handoff: {result.handoff_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
