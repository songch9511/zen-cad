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
class ReviewBundleResult:
    bundle_path: Path


class ReviewBundlePackager:
    def __init__(self, repo_root: Path, proceed_gate: Path, out: Path) -> None:
        self.repo_root = repo_root
        self.proceed_gate = proceed_gate
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

    def package_bundle(self) -> ReviewBundleResult | None:
        validator = ContractValidator(self.repo_root)
        validator.validate_repo()
        validator.validate_package(self.proceed_gate)
        if validator.issues:
            self.issues.extend(validator.issues)
            return None
        gate = self.load_json(self.proceed_gate)
        if not isinstance(gate, dict):
            return None
        if gate.get("kind") != "proceed_gate_package":
            self.error(self.proceed_gate, "review bundle requires a proceed_gate_package document")
            return None

        bundle = self.build_bundle(gate)
        self.out.parent.mkdir(parents=True, exist_ok=True)
        write_json(self.out, bundle)

        output_validator = ContractValidator(self.repo_root)
        output_validator.validate_package(self.out)
        if output_validator.issues:
            self.issues.extend(output_validator.issues)
            return None
        return ReviewBundleResult(bundle_path=self.out)

    def build_bundle(self, gate: dict[str, Any]) -> dict[str, Any]:
        artifacts = gate.get("artifacts", [])
        reports = gate.get("reports", [])
        viewer_targets = [
            {
                "path": str(artifact.get("path", "")),
                "viewer_hint": viewer_hint(str(artifact.get("kind", ""))),
                "evidence_role": "review_only",
            }
            for artifact in artifacts
            if artifact.get("kind") in {"layout_proxy_scene", "source", "json", "step", "stp", "viewer", "snapshot"}
        ]
        status = "ready_for_viewer_review" if gate.get("status") == "ready_for_user_review" else str(gate.get("status", "blocked"))
        if status not in {"ready_for_viewer_review", "needs_repair", "blocked"}:
            status = "blocked"
        return {
            "schema_version": SCHEMA_VERSION,
            "kind": "review_bundle",
            "id": f"{gate['spec_id']}.review_bundle",
            "spec_id": gate["spec_id"],
            "status": status,
            "artifacts": artifacts,
            "reports": [
                {"path": str(report.get("path", "")), "kind": "inspection_report"}
                for report in reports
            ],
            "locked_layout_facts": gate.get("locked_layout_facts", []),
            "viewer_targets": viewer_targets,
            "evidence_policy": [
                "Viewer targets are review evidence only.",
                "Geometry measurements, kernel checks, and source-level carry-through remain the stronger completion evidence.",
                "Screenshots or browser previews must not be used as final engineering certification.",
            ],
            "limitations": gate.get("limitations", []),
            "next_actions": [
                "Open viewer targets to inspect layout readability and obvious placement drift.",
                "Approve proceed only if locked layout facts and skipped-check limitations are acceptable.",
                "Run downstream CAD generation and geometry inspection before final readiness claims.",
            ],
            "extensions": {
                "packager": "tools/package_review_bundle.py",
                "proceed_gate": str(self.proceed_gate),
            },
        }


def viewer_hint(kind: str) -> str:
    if kind == "layout_proxy_scene":
        return "Open as layout context if the active viewer supports Zen CAD scene JSON."
    if kind == "source":
        return "Use as source-of-truth context for downstream CAD generation, not as visual evidence."
    if kind in {"step", "stp"}:
        return "Open as the generated CAD model; visual review does not replace geometry checks."
    if kind == "viewer":
        return "Open this local CAD Viewer link when the viewer server is running."
    if kind == "snapshot":
        return "Use this saved viewer snapshot for visual review only; geometry checks remain authoritative."
    return "Review metadata before proceeding."


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package Zen CAD proceed-gate artifacts for viewer-oriented review.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1], help="Zen CAD repository root.")
    parser.add_argument("--proceed-gate", type=Path, required=True, help="Proceed gate package JSON.")
    parser.add_argument("--out", type=Path, required=True, help="Output review bundle JSON path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    packager = ReviewBundlePackager(args.repo_root, args.proceed_gate, args.out)
    result = packager.package_bundle()
    if packager.issues:
        for issue in packager.issues:
            print(f"{issue.path}: {issue.message}", file=sys.stderr)
        return 1
    if result is None:
        print("review bundle packaging failed", file=sys.stderr)
        return 1
    print(f"Review bundle: {result.bundle_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
