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
HANDOFF_FILENAME = "handoff_packet.json"
MANIFEST_FILENAME = "adapter_manifest.json"
PROMPT_FILENAME = "text_to_cad_prompt.md"


@dataclass
class TextToCadBundleResult:
    bundle_dir: Path
    handoff_path: Path
    manifest_path: Path
    prompt_path: Path


class TextToCadBundlePackager:
    def __init__(self, repo_root: Path, handoff: Path, out: Path) -> None:
        self.repo_root = repo_root
        self.handoff = handoff
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

    def package(self) -> TextToCadBundleResult | None:
        validator = ContractValidator(self.repo_root)
        validator.validate_repo()
        validator.validate_package(self.handoff)
        if validator.issues:
            self.issues.extend(validator.issues)
            return None

        handoff = self.load_json(self.handoff)
        if not isinstance(handoff, dict):
            return None
        if not self.validate_approved_text_to_cad_handoff(handoff):
            return None

        self.out.mkdir(parents=True, exist_ok=True)
        handoff_path = self.out / HANDOFF_FILENAME
        manifest_path = self.out / MANIFEST_FILENAME
        prompt_path = self.out / PROMPT_FILENAME

        write_json(handoff_path, handoff)
        prompt_path.write_text(self.build_prompt(handoff), encoding="utf-8")
        write_json(manifest_path, self.build_manifest(handoff))

        output_validator = ContractValidator(self.repo_root)
        output_validator.validate_package(self.out)
        if output_validator.issues:
            self.issues.extend(output_validator.issues)
            return None

        return TextToCadBundleResult(
            bundle_dir=self.out,
            handoff_path=handoff_path,
            manifest_path=manifest_path,
            prompt_path=prompt_path,
        )

    def validate_approved_text_to_cad_handoff(self, handoff: dict[str, Any]) -> bool:
        ok = True
        if handoff.get("kind") != "handoff_packet":
            self.error(self.handoff, "text-to-cad bundle requires a handoff_packet document")
            ok = False
        if handoff.get("target_harness") != "text-to-cad":
            self.error(self.handoff, "text-to-cad bundle requires handoff target_harness text-to-cad")
            ok = False
        if handoff.get("target_maturity") != "detail_cad":
            self.error(self.handoff, "text-to-cad bundle requires target_maturity detail_cad")
            ok = False

        extensions = handoff.get("extensions")
        if not isinstance(extensions, dict):
            self.error(self.handoff, "approved handoff must include extensions")
            return False
        required_markers = ["proceed_gate", "proceed_gate_status", "proceed_approval", "proceed_decision"]
        missing = [marker for marker in required_markers if not str(extensions.get(marker, "")).strip()]
        if missing:
            self.error(self.handoff, f"approved handoff is missing approval markers: {', '.join(missing)}")
            ok = False
        if extensions.get("proceed_gate_status") != "ready_for_user_review":
            self.error(self.handoff, "approved handoff must come from a ready_for_user_review proceed gate")
            ok = False
        if extensions.get("proceed_decision") not in {"proceed", "detail_upgrade"}:
            self.error(self.handoff, "approved handoff proceed_decision must be proceed or detail_upgrade")
            ok = False
        return ok

    def build_manifest(self, handoff: dict[str, Any]) -> dict[str, Any]:
        extensions = handoff.get("extensions", {})
        return {
            "schema_version": SCHEMA_VERSION,
            "kind": "text_to_cad_bundle_manifest",
            "id": f"{handoff['id']}.text_to_cad_bundle",
            "spec_id": str(handoff["spec_id"]),
            "source_handoff": str(self.handoff),
            "target_harness": "text-to-cad",
            "entry_prompt": PROMPT_FILENAME,
            "included_files": [
                {
                    "path": HANDOFF_FILENAME,
                    "role": "approved_handoff_packet",
                },
                {
                    "path": PROMPT_FILENAME,
                    "role": "downstream_prompt",
                },
            ],
            "adapter_contract": {
                "zen_cad_role": "Package an approved handoff into downstream text-to-cad instructions only.",
                "boundary": "This adapter does not generate CAD source, STEP/STP files, geometry, snapshots, or viewer links.",
                "downstream_role": "CAD Skills/text-to-cad is responsible for CAD generation, inspection, repair, exports, and viewer handoff.",
                "source_of_truth": HANDOFF_FILENAME,
                "must_preserve": list_of_strings(handoff.get("locked_facts", [])),
                "required_checks": list_of_strings(handoff.get("required_checks", [])),
                "expected_downstream_returns": [
                    "source-of-truth",
                    "generated files",
                    "primary CAD artifact path",
                    "validation actually run",
                    "skipped checks and reasons",
                    "snapshot or viewer evidence when available",
                    "repair attempts",
                    "claims not made",
                ],
            },
            "approval": {
                "proceed_gate": str(extensions.get("proceed_gate", "")),
                "proceed_gate_status": str(extensions.get("proceed_gate_status", "")),
                "proceed_approval": str(extensions.get("proceed_approval", "")),
                "proceed_decision": str(extensions.get("proceed_decision", "")),
                "approver": str(extensions.get("approver", "")),
            },
            "extensions": {
                "packager": "tools/package_text_to_cad_bundle.py",
            },
        }

    def build_prompt(self, handoff: dict[str, Any]) -> str:
        extensions = handoff.get("extensions", {})
        return "\n".join(
            [
                "# CAD Skills / text-to-cad Detail Handoff",
                "",
                "Use the installed CAD Skills/text-to-cad harness (`$cad`) to generate downstream CAD from this approved Zen CAD handoff.",
                "",
                "## Adapter Boundary",
                "",
                "- This bundle is a prompt and adapter contract only.",
                "- Zen CAD has not generated CAD source, STEP/STP, geometry, snapshots, or viewer output in this step.",
                f"- Treat `{HANDOFF_FILENAME}` as the source handoff for locked facts, parameters, checks, repair policy, and stop conditions.",
                "",
                "## Task",
                "",
                "Generate detail CAD from the approved handoff while preserving locked layout facts exactly. Use build123d/Python source when new geometry is needed, then return the generated source path, primary CAD artifact path, checks run, skipped checks, repair attempts, and limitations.",
                "",
                "## Approved Handoff",
                "",
                f"- Handoff id: {handoff.get('id', '')}",
                f"- Spec id: {handoff.get('spec_id', '')}",
                f"- Target maturity: {handoff.get('target_maturity', '')}",
                f"- Target harness: {handoff.get('target_harness', '')}",
                f"- Proceed gate: {extensions.get('proceed_gate', '')}",
                f"- Proceed gate status: {extensions.get('proceed_gate_status', '')}",
                f"- Proceed approval: {extensions.get('proceed_approval', '')}",
                f"- Proceed decision: {extensions.get('proceed_decision', '')}",
                f"- Approver: {extensions.get('approver', '')}",
                "",
                "## Locked Facts",
                "",
                bullet_list(handoff.get("locked_facts", []), "No locked facts were supplied; stop and ask for a corrected handoff."),
                "",
                "## Parameter Contract",
                "",
                bullet_list(handoff.get("parameter_contract", []), "No parameters were supplied; preserve explicit dimensions from the handoff packet."),
                "",
                "## Artifact Targets",
                "",
                bullet_list(handoff.get("artifact_targets", []), "Return source and primary CAD artifact paths produced by text-to-cad."),
                "",
                "## Required Checks",
                "",
                bullet_list(handoff.get("required_checks", []), "No required checks were supplied; stop and ask for a corrected handoff."),
                "",
                "## Repair Loop",
                "",
                str(handoff.get("repair_loop", "")).strip(),
                "",
                "## Stop Conditions",
                "",
                bullet_list(handoff.get("stop_conditions", []), "Stop if locked layout facts may change."),
                "",
                "## Downstream Instructions",
                "",
                "- Use named parameters, datums, labels, and source-level joints where useful.",
                "- Run deterministic geometry inspection before visual review: refs, facts, planes, positioning, targeted measures, frames, mates, or diffs as applicable.",
                "- If visible primary CAD was created or updated and snapshot/viewer tooling is available, return saved snapshots or viewer links. If skipped, state why.",
                "- Do not treat viewer links or screenshots as substitutes for geometry checks.",
                "- Repair the smallest source-level cause of any failed check, then regenerate and rerun dependent checks.",
                "- Hand supported artifacts to a CAD viewer when available.",
                "- Stop instead of changing locked layout facts.",
                "",
                "## Return Format",
                "",
                "- Source-of-truth:",
                "- Generated files:",
                "- Primary CAD artifact:",
                "- Validation actually run:",
                "- Skipped checks and reasons:",
                "- Snapshot/viewer evidence:",
                "- Repair attempts:",
                "- Stop conditions hit:",
                "- Known assumptions:",
                "- Claims not made:",
                "",
            ]
        )


def list_of_strings(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [str(value) for value in values]


def bullet_list(values: Any, fallback: str) -> str:
    items = list_of_strings(values)
    if not items:
        return f"- {fallback}"
    return "\n".join(f"- {item}" for item in items)


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package an approved Zen CAD handoff as a CAD Skills/text-to-cad downstream prompt bundle.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1], help="Zen CAD repository root.")
    parser.add_argument("--handoff", type=Path, required=True, help="Approved handoff_packet JSON targeted at text-to-cad.")
    parser.add_argument("--out", type=Path, required=True, help="Output directory for the text-to-cad prompt bundle.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    packager = TextToCadBundlePackager(args.repo_root, args.handoff, args.out)
    result = packager.package()
    if packager.issues:
        for issue in packager.issues:
            print(f"{issue.path}: {issue.message}", file=sys.stderr)
        return 1
    if result is None:
        print("text-to-cad bundle packaging failed", file=sys.stderr)
        return 1
    print(f"Text-to-CAD bundle: {result.bundle_dir}")
    print(f"Prompt: {result.prompt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
