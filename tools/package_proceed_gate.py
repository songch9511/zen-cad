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
class ProceedGateResult:
    package_path: Path


class ProceedGatePackager:
    def __init__(self, repo_root: Path, package: Path, artifacts: list[Path], reports: list[Path], out: Path) -> None:
        self.repo_root = repo_root
        self.package = package
        self.artifacts = artifacts
        self.reports = reports
        self.out = out
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

    def package_gate(self) -> ProceedGateResult | None:
        validator = ContractValidator(self.repo_root)
        validator.validate_repo()
        validator.validate_package(self.package)
        for report_path in self.reports:
            validator.validate_package(report_path)
        for artifact in self.artifacts:
            if not artifact.exists():
                self.error(artifact, "artifact does not exist")
        if not self.artifacts:
            self.error("<args>", "proceed gate packaging requires at least one artifact")
        if not self.reports:
            self.error("<args>", "proceed gate packaging requires at least one inspection report")
        if validator.issues:
            self.issues.extend(validator.issues)
            return None
        if self.issues:
            return None

        spec = self.load_spec()
        if spec is None:
            return None
        report_docs = [self.load_json(path) for path in self.reports]
        report_docs = [report for report in report_docs if isinstance(report, dict)]
        gate = self.build_gate(spec, report_docs)
        self.out.parent.mkdir(parents=True, exist_ok=True)
        write_json(self.out, gate)

        output_validator = ContractValidator(self.repo_root)
        output_validator.validate_package(self.out)
        if output_validator.issues:
            self.issues.extend(output_validator.issues)
            return None
        return ProceedGateResult(package_path=self.out)

    def load_spec(self) -> dict[str, Any] | None:
        paths = [self.package] if self.package.is_file() else sorted(self.package.rglob("*.json"))
        specs: list[dict[str, Any]] = []
        for path in paths:
            loaded = self.load_json(path)
            if isinstance(loaded, dict) and loaded.get("kind") == "cad_spec":
                specs.append(loaded)
        if len(specs) != 1:
            self.error(self.package, "proceed gate packaging requires exactly one cad_spec document")
            return None
        return specs[0]

    def build_gate(self, spec: dict[str, Any], reports: list[dict[str, Any]]) -> dict[str, Any]:
        summary = summarize_reports(reports)
        status = "needs_repair" if summary["failed"] else "ready_for_user_review"
        decision_options = ["revise_layout"] if summary["failed"] else ["proceed", "revise_layout", "detail_upgrade"]
        recommended = "Repair failed checks before proceed review." if summary["failed"] else "Review layout contract and choose proceed, revise_layout, or detail_upgrade."
        locked = [
            str(fact.get("fact_id", fact))
            for fact in spec.get("locked_layout_facts", [])
            if isinstance(fact, dict) or isinstance(fact, str)
        ]
        limitations = sorted(
            {
                str(item)
                for report in reports
                for item in report.get("limitations", [])
            }
        )
        return {
            "schema_version": SCHEMA_VERSION,
            "kind": "proceed_gate_package",
            "id": f"{spec['id']}.proceed_gate",
            "spec_id": spec["id"],
            "status": status,
            "decision_options": decision_options,
            "recommended_next_step": recommended,
            "artifacts": [{"path": str(path), "kind": artifact_kind(path)} for path in self.artifacts],
            "reports": [
                {
                    "path": str(path),
                    "status": str(report.get("status", "unknown")),
                    "proceed_recommendation": str(report.get("proceed_recommendation", "unknown")),
                }
                for path, report in zip(self.reports, reports)
            ],
            "locked_layout_facts": locked,
            "check_summary": summary,
            "limitations": limitations,
            "extensions": {
                "packager": "tools/package_proceed_gate.py",
            },
        }


def summarize_reports(reports: list[dict[str, Any]]) -> dict[str, int]:
    summary = {"passed": 0, "partial": 0, "failed": 0, "skipped": 0}
    for report in reports:
        status = report.get("status")
        if status in {"passed", "partial", "failed"}:
            summary[str(status)] += 1
        for check in report.get("checks", []):
            if isinstance(check, dict) and check.get("status") in {"passed", "partial", "failed"}:
                summary[str(check["status"])] += 1
        summary["skipped"] += len(report.get("skipped_checks", []))
    return summary


def artifact_kind(path: Path) -> str:
    name = path.name
    if name.endswith(".scene.json"):
        return "layout_proxy_scene"
    if name.endswith(".inspection_report.json") or name.endswith(".report.json"):
        return "inspection_report"
    if name.endswith(".py"):
        return "source"
    if name.endswith(".json"):
        return "json"
    return path.suffix.lstrip(".") or "unknown"


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package Zen CAD proceed-gate artifacts and inspection reports.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1], help="Zen CAD repository root.")
    parser.add_argument("--package", type=Path, required=True, help="Contract package JSON file or directory.")
    parser.add_argument("--artifact", type=Path, action="append", default=[], help="Artifact path to include. Repeatable.")
    parser.add_argument("--report", type=Path, action="append", required=True, help="Inspection report path. Repeatable.")
    parser.add_argument("--out", type=Path, required=True, help="Output proceed gate package path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    packager = ProceedGatePackager(args.repo_root, args.package, args.artifact, args.report, args.out)
    result = packager.package_gate()
    if packager.issues:
        for issue in packager.issues:
            print(f"{issue.path}: {issue.message}", file=sys.stderr)
        return 1
    if result is None:
        print("proceed gate packaging failed", file=sys.stderr)
        return 1
    print(f"Proceed gate package: {result.package_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
