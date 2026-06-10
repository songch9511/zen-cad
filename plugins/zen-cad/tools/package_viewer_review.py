#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from validate_contract import ContractValidator, Issue


@dataclass
class ViewerReviewResult:
    brief_path: Path


class ViewerReviewPackager:
    def __init__(
        self,
        repo_root: Path,
        proceed_gate: Path,
        out: Path,
        pipeline_run: Path | None,
        viewer_artifacts: list[Path],
        reviewer: str,
    ) -> None:
        self.repo_root = repo_root
        self.proceed_gate = proceed_gate
        self.out = out
        self.pipeline_run = pipeline_run
        self.viewer_artifacts = viewer_artifacts
        self.reviewer = reviewer
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

    def package(self) -> ViewerReviewResult | None:
        validator = ContractValidator(self.repo_root)
        validator.validate_repo()
        validator.validate_package(self.proceed_gate)
        if self.pipeline_run is not None:
            validator.validate_package(self.pipeline_run)
        if validator.issues:
            self.issues.extend(validator.issues)
            return None

        for artifact in self.viewer_artifacts:
            if not artifact.exists():
                self.error(artifact, "viewer artifact does not exist")
        if self.issues:
            return None

        gate = self.load_json(self.proceed_gate)
        pipeline = self.load_json(self.pipeline_run) if self.pipeline_run is not None else None
        if not isinstance(gate, dict):
            return None
        if gate.get("kind") != "proceed_gate_package":
            self.error(self.proceed_gate, "viewer review requires a proceed_gate_package document")
            return None
        if self.pipeline_run is not None and (not isinstance(pipeline, dict) or pipeline.get("kind") != "pipeline_run"):
            self.error(self.pipeline_run, "optional pipeline run must be a pipeline_run document")
            return None

        markdown = self.render_markdown(gate, pipeline if isinstance(pipeline, dict) else None)
        self.out.parent.mkdir(parents=True, exist_ok=True)
        self.out.write_text(markdown, encoding="utf-8")
        return ViewerReviewResult(brief_path=self.out)

    def render_markdown(self, gate: dict[str, Any], pipeline: dict[str, Any] | None) -> str:
        lines: list[str] = [
            "# Zen CAD Viewer Review Brief",
            "",
            f"- Spec ID: `{gate.get('spec_id', 'unknown')}`",
            f"- Proceed gate: `{self.proceed_gate}`",
            f"- Gate status: `{gate.get('status', 'unknown')}`",
            f"- Reviewer role: `{self.reviewer}`",
        ]
        if pipeline is not None:
            lines.extend(
                [
                    f"- Pipeline run: `{self.pipeline_run}`",
                    f"- Pipeline status: `{pipeline.get('status', 'unknown')}`",
                    f"- Target harness: `{pipeline.get('target_harness', 'unknown')}`",
                ]
            )
        lines.extend(
            [
                "",
                "## Review Objective",
                "",
                "Open the layout/proceed artifacts in a CAD viewer and review visible positioning, interface orientation, assembly structure, and obvious drift against the locked layout facts.",
                "",
                "Screenshots, viewer links, and visual snapshots are review aids only. Do not mark the package complete from screenshots alone; use the proceed gate status, check summary, inspection reports, and downstream geometry measurements as completion evidence.",
                "",
                "## Source Package",
                "",
            ]
        )
        lines.extend(format_artifacts(gate.get("artifacts", [])))
        lines.extend(
            [
                "",
                "## Inspection Reports",
                "",
            ]
        )
        lines.extend(format_reports(gate.get("reports", [])))
        lines.extend(
            [
                "",
                "## Viewer Artifacts",
                "",
            ]
        )
        lines.extend(format_viewer_artifacts(self.viewer_artifacts))
        lines.extend(
            [
                "",
                "## Locked Layout Facts",
                "",
            ]
        )
        lines.extend(format_list(gate.get("locked_layout_facts", []), empty="No locked layout facts were listed. Treat this as a blocker."))
        lines.extend(
            [
                "",
                "## Check Summary",
                "",
            ]
        )
        lines.extend(format_check_summary(gate.get("check_summary", {})))
        lines.extend(
            [
                "",
                "## Known Limitations",
                "",
            ]
        )
        lines.extend(format_list(gate.get("limitations", []), empty="No limitations were recorded in the proceed gate."))
        lines.extend(
            [
                "",
                "## CAD Viewer Tasks",
                "",
                "1. Open the listed layout and source artifacts that the viewer supports.",
                "2. Compare visible axes, frames, part relationships, interface datums, clearances, and motion cues against the locked facts.",
                "3. Cross-check any visual finding against the inspection reports before calling it passed.",
                "4. If a visual concern is not covered by a check, request a distance, axis, frame, mate, or geometry measurement instead of approving by sight.",
                "5. Record skipped viewer steps with the missing tool, unsupported artifact, or unavailable measurement.",
                "",
                "## Decision Guidance",
                "",
            ]
        )
        lines.extend(decision_guidance(gate))
        lines.extend(
            [
                "",
                "## Review Notes Template",
                "",
                "```text",
                "viewer_artifacts_opened:",
                "visible_findings:",
                "measurement_requests:",
                "blockers:",
                "recommended_decision:",
                "```",
                "",
            ]
        )
        return "\n".join(lines)


def format_artifacts(artifacts: Any) -> list[str]:
    if not isinstance(artifacts, list) or not artifacts:
        return ["- No proceed artifacts were listed. Treat this as a blocker."]
    rows = []
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            rows.append(f"- `{artifact}`")
            continue
        rows.append(f"- `{artifact.get('kind', 'artifact')}`: `{artifact.get('path', 'unknown')}`")
    return rows


def format_reports(reports: Any) -> list[str]:
    if not isinstance(reports, list) or not reports:
        return ["- No inspection reports were listed. Treat this as a blocker."]
    rows = []
    for report in reports:
        if not isinstance(report, dict):
            rows.append(f"- `{report}`")
            continue
        rows.append(
            f"- `{report.get('path', 'unknown')}`: status `{report.get('status', 'unknown')}`, proceed `{report.get('proceed_recommendation', 'unknown')}`"
        )
    return rows


def format_viewer_artifacts(paths: list[Path]) -> list[str]:
    if not paths:
        return ["- None provided. The downstream reviewer should open the source package artifacts directly."]
    return [f"- `{viewer_artifact_kind(path)}`: `{path}`" for path in paths]


def format_list(items: Any, empty: str) -> list[str]:
    if not isinstance(items, list) or not items:
        return [f"- {empty}"]
    return [f"- `{item}`" for item in items]


def format_check_summary(summary: Any) -> list[str]:
    if not isinstance(summary, dict):
        return ["- Check summary is missing or malformed. Treat this as a blocker."]
    return [
        f"- Passed: `{int(summary.get('passed', 0))}`",
        f"- Partial: `{int(summary.get('partial', 0))}`",
        f"- Failed: `{int(summary.get('failed', 0))}`",
        f"- Skipped: `{int(summary.get('skipped', 0))}`",
    ]


def decision_guidance(gate: dict[str, Any]) -> list[str]:
    status = str(gate.get("status", "unknown"))
    summary = gate.get("check_summary", {})
    failed = int(summary.get("failed", 0)) if isinstance(summary, dict) else 0
    options = ", ".join(str(option) for option in gate.get("decision_options", [])) or "none"
    rows = [f"- Available proceed gate decisions: `{options}`."]
    if status != "ready_for_user_review":
        rows.append("- Do not proceed to detail handoff. Return to layout repair or unblock the proceed gate first.")
    elif failed:
        rows.append("- Do not proceed while failed checks are present. Repair and regenerate the proceed gate.")
    else:
        rows.append("- The viewer may recommend proceed only if visible review finds no drift and inspection evidence still supports the locked facts.")
    rows.append("- Detail CAD handoff still requires an explicit proceed approval artifact.")
    rows.append("- Final CAD readiness requires downstream geometry checks beyond this viewer brief.")
    return rows


def viewer_artifact_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return "viewer_snapshot"
    if suffix in {".html", ".htm"}:
        return "viewer_page"
    if suffix in {".glb", ".gltf", ".stl", ".3mf"}:
        return "viewer_model"
    if suffix == ".json":
        return "viewer_data"
    return suffix.lstrip(".") or "viewer_artifact"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package a viewer-oriented Zen CAD proceed review brief.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1], help="Zen CAD repository root.")
    parser.add_argument("--proceed-gate", type=Path, required=True, help="Proceed gate package JSON.")
    parser.add_argument("--pipeline-run", type=Path, help="Optional pipeline_run JSON for run context.")
    parser.add_argument("--viewer-artifact", type=Path, action="append", default=[], help="Optional viewer snapshot, page, model, or report path. Repeatable.")
    parser.add_argument("--out", type=Path, required=True, help="Output Markdown review brief path.")
    parser.add_argument("--reviewer", default="cad-viewer", help="Reviewer role label.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    packager = ViewerReviewPackager(
        args.repo_root,
        args.proceed_gate,
        args.out,
        args.pipeline_run,
        args.viewer_artifact,
        args.reviewer,
    )
    result = packager.package()
    if packager.issues:
        for issue in packager.issues:
            print(f"{issue.path}: {issue.message}", file=sys.stderr)
        return 1
    if result is None:
        print("viewer review packaging failed", file=sys.stderr)
        return 1
    print(f"Viewer review brief: {result.brief_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
