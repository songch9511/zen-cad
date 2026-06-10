#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from export_cad_source import CadSourceExporter
from generate_detail_handoff import DetailHandoffGenerator
from generate_layout_proxy import LayoutProxyGenerator
from inspect_cad_source import CadSourceInspector
from inspect_layout_proxy import LayoutProxyInspector
from package_proceed_gate import ProceedGatePackager
from package_review_bundle import ReviewBundlePackager
from package_text_to_cad_bundle import TextToCadBundlePackager
from validate_contract import ContractValidator, Issue


SCHEMA_VERSION = "0.8.0"


@dataclass
class PipelineStep:
    step_id: str
    status: str
    outputs: list[Path] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    note: str = ""


class ContractPipelineRunner:
    def __init__(self, repo_root: Path, package: Path, out: Path, target_harness: str, approval: Path | None) -> None:
        self.repo_root = repo_root
        self.package = package
        self.out = out
        self.target_harness = target_harness
        self.approval = approval
        self.steps: list[PipelineStep] = []
        self.artifacts: dict[str, Path] = {}

    def run(self) -> int:
        self.out.mkdir(parents=True, exist_ok=True)

        if not self.validate_contract_package():
            self.write_summary("failed")
            return 1
        if not self.generate_layout_proxy():
            self.write_summary("failed")
            return 1
        if not self.inspect_layout_proxy():
            self.write_summary("failed")
            return 1
        if not self.export_cad_source():
            self.write_summary("failed")
            return 1
        if not self.inspect_cad_source():
            self.write_summary("failed")
            return 1
        if not self.package_proceed_gate():
            self.write_summary("failed")
            return 1
        if not self.package_review_bundle():
            self.write_summary("failed")
            return 1

        gate = self.load_json(self.artifacts["proceed_gate"])
        if isinstance(gate, dict) and gate.get("status") != "ready_for_user_review":
            self.steps.append(
                PipelineStep(
                    step_id="detail_handoff",
                    status="skipped",
                    note="Proceed gate is not ready for detail handoff.",
                )
            )
            self.write_summary("needs_repair")
            return 0

        if self.approval is not None:
            self.artifacts["proceed_approval"] = self.approval
            if not self.generate_detail_handoff():
                self.write_summary("failed")
                return 1
            if self.target_harness == "text-to-cad" and not self.package_text_to_cad_bundle():
                self.write_summary("failed")
                return 1
            self.write_summary("completed")
            return 0

        self.steps.append(
            PipelineStep(
                step_id="detail_handoff",
                status="skipped",
                note="Detail handoff requires an explicit proceed approval artifact.",
            )
        )
        self.write_summary("ready_for_user_review")
        return 0

    def validate_contract_package(self) -> bool:
        validator = ContractValidator(self.repo_root)
        validator.validate_repo()
        validator.validate_package(self.package)
        return self.record_step("validate_contract", validator.issues)

    def generate_layout_proxy(self) -> bool:
        layout_dir = self.out / "layout"
        generator = LayoutProxyGenerator(self.repo_root, self.package, layout_dir)
        result = generator.generate()
        outputs = []
        if result is not None:
            outputs = [result.scene_path, result.report_path]
            self.artifacts["scene"] = result.scene_path
            self.artifacts["layout_generation_report"] = result.report_path
        return self.record_step("generate_layout_proxy", generator.issues, outputs)

    def inspect_layout_proxy(self) -> bool:
        report = self.out / "layout" / "locked_facts.inspection_report.json"
        inspector = LayoutProxyInspector(self.repo_root, self.package, self.artifacts["scene"], report)
        result = inspector.inspect()
        outputs = [result.report_path] if result is not None else []
        if result is not None:
            self.artifacts["layout_report"] = result.report_path
        return self.record_step("inspect_layout_proxy", inspector.issues, outputs)

    def export_cad_source(self) -> bool:
        source_dir = self.out / "source"
        exporter = CadSourceExporter(self.repo_root, self.package, self.artifacts["scene"], source_dir, "build123d")
        result = exporter.export()
        outputs = []
        if result is not None:
            outputs = [result.source_path, result.manifest_path]
            self.artifacts["source"] = result.source_path
            self.artifacts["source_manifest"] = result.manifest_path
        return self.record_step("export_cad_source", exporter.issues, outputs)

    def inspect_cad_source(self) -> bool:
        report = self.out / "source" / "source.inspection_report.json"
        inspector = CadSourceInspector(self.repo_root, self.artifacts["scene"], self.artifacts["source_manifest"], self.artifacts["source"], report)
        result = inspector.inspect()
        outputs = [result.report_path] if result is not None else []
        if result is not None:
            self.artifacts["source_report"] = result.report_path
        return self.record_step("inspect_cad_source", inspector.issues, outputs)

    def package_proceed_gate(self) -> bool:
        proceed_gate = self.out / "proceed_gate.json"
        packager = ProceedGatePackager(
            self.repo_root,
            self.package,
            [self.artifacts["scene"], self.artifacts["source"]],
            [self.artifacts["layout_report"], self.artifacts["source_report"]],
            proceed_gate,
        )
        result = packager.package_gate()
        outputs = [result.package_path] if result is not None else []
        if result is not None:
            self.artifacts["proceed_gate"] = result.package_path
        return self.record_step("package_proceed_gate", packager.issues, outputs)

    def package_review_bundle(self) -> bool:
        review_bundle = self.out / "review_bundle.json"
        packager = ReviewBundlePackager(self.repo_root, self.artifacts["proceed_gate"], review_bundle)
        result = packager.package_bundle()
        outputs = [result.bundle_path] if result is not None else []
        if result is not None:
            self.artifacts["review_bundle"] = result.bundle_path
        return self.record_step("package_review_bundle", packager.issues, outputs)

    def generate_detail_handoff(self) -> bool:
        handoff = self.out / "detail_handoff.json"
        if self.approval is None:
            self.steps.append(
                PipelineStep(
                    step_id="generate_detail_handoff",
                    status="skipped",
                    note="Missing proceed approval artifact.",
                )
            )
            return True
        generator = DetailHandoffGenerator(self.repo_root, self.package, self.artifacts["proceed_gate"], self.approval, handoff, self.target_harness)
        result = generator.generate()
        outputs = [result.handoff_path] if result is not None else []
        if result is not None:
            self.artifacts["detail_handoff"] = result.handoff_path
        return self.record_step("generate_detail_handoff", generator.issues, outputs)

    def package_text_to_cad_bundle(self) -> bool:
        bundle_dir = self.out / "text_to_cad_bundle"
        packager = TextToCadBundlePackager(self.repo_root, self.artifacts["detail_handoff"], bundle_dir)
        result = packager.package()
        outputs = []
        if result is not None:
            outputs = [result.bundle_dir, result.handoff_path, result.manifest_path, result.prompt_path]
            self.artifacts["text_to_cad_bundle"] = result.bundle_dir
            self.artifacts["text_to_cad_prompt"] = result.prompt_path
        return self.record_step("package_text_to_cad_bundle", packager.issues, outputs)

    def record_step(self, step_id: str, issues: list[Issue], outputs: list[Path] | None = None) -> bool:
        status = "failed" if issues else "passed"
        self.steps.append(PipelineStep(step_id=step_id, status=status, outputs=outputs or [], issues=list(issues)))
        return not issues

    def write_summary(self, status: str) -> Path:
        summary_path = self.out / "pipeline_run.json"
        spec_id = self.resolve_spec_id()
        summary = {
            "schema_version": SCHEMA_VERSION,
            "kind": "pipeline_run",
            "id": f"{spec_id}.pipeline_run" if spec_id else "zen_cad.pipeline_run",
            "contract_package": str(self.package),
            "target_harness": self.target_harness,
            "status": status,
            "steps": [
                {
                    "step_id": step.step_id,
                    "status": step.status,
                    "outputs": [str(path) for path in step.outputs],
                    "issues": [{"path": issue.path, "message": issue.message} for issue in step.issues],
                    "note": step.note,
                }
                for step in self.steps
            ],
            "artifacts": {name: str(path) for name, path in sorted(self.artifacts.items())},
            "extensions": {
                "runner": "tools/run_contract_pipeline.py",
            },
        }
        write_json(summary_path, summary)
        return summary_path

    def resolve_spec_id(self) -> str | None:
        paths = [self.package] if self.package.is_file() else sorted(self.package.rglob("*.json"))
        for path in paths:
            document = self.load_json(path)
            if isinstance(document, dict) and document.get("kind") == "cad_spec" and isinstance(document.get("id"), str):
                return document["id"]
        return None

    def load_json(self, path: Path) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return None


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Zen CAD kernel-neutral contract pipeline.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1], help="Zen CAD repository root.")
    parser.add_argument("--package", type=Path, required=True, help="Contract package JSON file or directory.")
    parser.add_argument("--out", type=Path, required=True, help="Output directory for pipeline artifacts.")
    parser.add_argument(
        "--target-harness",
        choices=["codex", "text-to-cad", "build123d", "cadquery", "freecad", "unknown"],
        default="unknown",
        help="Target harness for the generated detail handoff.",
    )
    parser.add_argument("--approval", type=Path, help="Proceed approval JSON. Required to continue into detail handoff.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    runner = ContractPipelineRunner(
        args.repo_root,
        args.package,
        args.out,
        args.target_harness,
        approval=args.approval,
    )
    code = runner.run()
    print(f"Pipeline run: {args.out / 'pipeline_run.json'}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
