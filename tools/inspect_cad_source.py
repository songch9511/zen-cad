#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from validate_contract import ContractValidator, Issue


SCHEMA_VERSION = "0.8.0"


@dataclass
class SourceInspectionResult:
    report_path: Path


class CadSourceInspector:
    def __init__(self, repo_root: Path, scene_path: Path, manifest_path: Path, source_path: Path, out: Path) -> None:
        self.repo_root = repo_root
        self.scene_path = scene_path
        self.manifest_path = manifest_path
        self.source_path = source_path
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

    def inspect(self) -> SourceInspectionResult | None:
        validator = ContractValidator(self.repo_root)
        validator.validate_repo()
        validator.validate_package(self.scene_path)
        validator.validate_package(self.manifest_path)
        if validator.issues:
            self.issues.extend(validator.issues)
            return None

        scene = self.load_json(self.scene_path)
        manifest = self.load_json(self.manifest_path)
        if not isinstance(scene, dict) or not isinstance(manifest, dict):
            return None
        source_text = self.load_source_text()
        if source_text is None:
            return None

        checks = self.build_checks(scene, manifest, source_text)
        failed = [check for check in checks if check["status"] == "failed"]
        status = "failed" if failed else "partial"
        recommendation = "needs_repair" if failed else "ready_for_proceed_review"
        report = {
            "schema_version": SCHEMA_VERSION,
            "kind": "inspection_report",
            "id": f"{manifest['id']}.source_inspection_report",
            "spec_id": str(scene.get("source_spec_id", "unknown_spec")),
            "artifact": {
                "path": str(self.source_path),
                "kind": "source",
            },
            "status": status,
            "checks": checks,
            "skipped_checks": [
                {
                    "check_id": "step_geometry_export",
                    "reason": "Source-level adapter inspection only; STEP generation requires downstream CAD runtime.",
                },
                {
                    "check_id": "geometry_measurements",
                    "reason": "No CAD kernel geometry was generated in this adapter stage.",
                },
            ],
            "repair_attempts": [],
            "proceed_recommendation": recommendation,
            "limitations": [
                "Inspection verifies source-level carry-through, not generated STEP geometry.",
                "Run downstream CAD generation and geometry inspection before final proceed approval.",
            ],
            "extensions": {
                "inspector": "tools/inspect_cad_source.py",
            },
        }
        self.out.parent.mkdir(parents=True, exist_ok=True)
        write_json(self.out, report)

        output_validator = ContractValidator(self.repo_root)
        output_validator.validate_package(self.out)
        if output_validator.issues:
            self.issues.extend(output_validator.issues)
            return None

        return SourceInspectionResult(report_path=self.out)

    def load_source_text(self) -> str | None:
        try:
            return self.source_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            self.error(self.source_path, "source file does not exist")
        return None

    def build_checks(self, scene: dict[str, Any], manifest: dict[str, Any], source_text: str) -> list[dict[str, Any]]:
        scene_id = str(scene.get("id", ""))
        primitive_ids = [
            str(primitive["id"])
            for primitive in scene.get("primitives", [])
            if isinstance(primitive, dict) and isinstance(primitive.get("id"), str)
        ]
        manifest_primitives = [str(item) for item in manifest.get("primitives", [])]
        source_constants = parse_source_constants(source_text)
        manifest_sourced_parts = [
            str(item.get("part_id"))
            for item in manifest.get("sourced_parts", [])
            if isinstance(item, dict) and item.get("part_id")
        ]
        manifest_feature_plan = {}
        if isinstance(manifest.get("extensions"), dict) and isinstance(manifest["extensions"].get("cad_feature_plan"), dict):
            manifest_feature_plan = manifest["extensions"]["cad_feature_plan"]
        manifest_feature_parts = feature_part_ids(manifest_feature_plan)
        source_sourced_parts = [
            str(item.get("part_id"))
            for item in source_constants.get("ZEN_CAD_SOURCED_PARTS", [])
            if isinstance(item, dict) and item.get("part_id")
        ]
        source_feature_plan = source_constants.get("ZEN_CAD_FEATURE_PLAN", {})
        source_feature_parts = feature_part_ids(source_feature_plan if isinstance(source_feature_plan, dict) else {})
        expected_source_primitive_ids = [
            str(primitive["id"])
            for primitive in scene.get("primitives", [])
            if isinstance(primitive, dict)
            and isinstance(primitive.get("id"), str)
            and str(primitive.get("part_id", "")) not in set(manifest_sourced_parts)
            and str(primitive.get("part_id", "")) not in manifest_feature_parts
        ]
        source_primitive_ids = [
            str(primitive["id"])
            for primitive in source_constants.get("ZEN_CAD_PRIMITIVES", [])
            if isinstance(primitive, dict) and isinstance(primitive.get("id"), str)
        ]
        source_facts = [str(item) for item in source_constants.get("ZEN_CAD_LOCKED_LAYOUT_FACTS", [])]
        source_targets = [str(item) for item in source_constants.get("ZEN_CAD_INSPECTION_TARGETS", [])]
        checks = [
            check_result(
                "manifest_scene_id_matches",
                "label",
                manifest.get("source_scene_id") == scene_id,
                f"manifest.source_scene_id={manifest.get('source_scene_id')!r}; scene.id={scene_id!r}",
            ),
            check_result(
                "source_scene_id_matches",
                "label",
                source_constants.get("ZEN_CAD_SCENE_ID") == scene_id,
                f"source ZEN_CAD_SCENE_ID={source_constants.get('ZEN_CAD_SCENE_ID')!r}; scene.id={scene_id!r}",
            ),
            check_result(
                "manifest_primitives_cover_scene",
                "label",
                set(manifest_primitives) == set(primitive_ids),
                f"manifest primitives={len(manifest_primitives)}; scene primitives={len(primitive_ids)}",
            ),
            check_result(
                "source_primitives_cover_scene",
                "label",
                set(source_primitive_ids) == set(expected_source_primitive_ids),
                f"source proxy primitives={len(source_primitive_ids)}; expected proxy primitives after sourced STEP replacement={len(expected_source_primitive_ids)}",
            ),
            check_result(
                "cad_source_layout_facts_carried",
                "label",
                set(source_facts) == {str(item) for item in scene.get("locked_layout_facts", [])},
                f"source layout facts={len(source_facts)}; scene layout facts={len(scene.get('locked_layout_facts', []))}",
                [str(item) for item in scene.get("locked_layout_facts", [])],
            ),
            check_result(
                "source_inspection_targets_carried",
                "label",
                set(source_targets) == {str(item) for item in scene.get("inspection_targets", [])},
                f"source inspection targets={len(source_targets)}; scene inspection targets={len(scene.get('inspection_targets', []))}",
            ),
            check_result(
                "source_has_gen_step",
                "label",
                "def gen_step" in source_text,
                "source contains gen_step function" if "def gen_step" in source_text else "source missing gen_step function",
            ),
        ]
        if manifest_sourced_parts or source_sourced_parts:
            checks.extend(
                [
                    check_result(
                        "source_sourced_parts_cover_manifest",
                        "label",
                        set(source_sourced_parts) == set(manifest_sourced_parts),
                        f"source sourced parts={len(source_sourced_parts)}; manifest sourced parts={len(manifest_sourced_parts)}",
                    ),
                    check_result(
                        "source_imports_sourced_steps",
                        "label",
                        "import_step" in source_text,
                        "source imports STEP/STP geometry with build123d.import_step"
                        if "import_step" in source_text
                        else "source missing import_step for sourced parts",
                    ),
                ]
            )
        if manifest_feature_parts or source_feature_parts:
            checks.extend(
                [
                    check_result(
                        "source_feature_plan_covers_manifest",
                        "label",
                        source_feature_parts == manifest_feature_parts,
                        f"source feature parts={len(source_feature_parts)}; manifest feature parts={len(manifest_feature_parts)}",
                    ),
                    check_result(
                        "source_feature_runtime_present",
                        "label",
                        "_make_feature_part" in source_text and "ZEN_CAD_FEATURE_PLAN" in source_text,
                        "source contains feature-plan runtime"
                        if "_make_feature_part" in source_text and "ZEN_CAD_FEATURE_PLAN" in source_text
                        else "source missing feature-plan runtime",
                    ),
                ]
            )
        return checks


def parse_source_constants(source_text: str) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    try:
        module = ast.parse(source_text)
    except SyntaxError:
        return parsed
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        name = node.targets[0].id
        if not name.startswith("ZEN_CAD_"):
            continue
        try:
            parsed[name] = ast.literal_eval(node.value)
        except (ValueError, SyntaxError):
            continue
    return parsed


def feature_part_ids(feature_plan: dict[str, Any]) -> set[str]:
    return {
        str(part.get("part_id"))
        for part in feature_plan.get("parts", [])
        if isinstance(part, dict) and part.get("part_id")
    }


def check_result(
    check_id: str,
    check_type: str,
    passed: bool,
    evidence: str,
    locked_fact_refs: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "check_type": check_type,
        "status": "passed" if passed else "failed",
        "evidence": evidence,
        "locked_fact_refs": locked_fact_refs or [],
    }


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect exported Zen CAD source against a layout proxy scene and source manifest.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1], help="Zen CAD repository root.")
    parser.add_argument("--scene", type=Path, required=True, help="layout_proxy.scene.json used for export.")
    parser.add_argument("--manifest", type=Path, required=True, help="cad_source_manifest.json.")
    parser.add_argument("--source", type=Path, required=True, help="Exported CAD source file.")
    parser.add_argument("--out", type=Path, required=True, help="Output inspection report JSON path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    inspector = CadSourceInspector(args.repo_root, args.scene, args.manifest, args.source, args.out)
    result = inspector.inspect()
    if inspector.issues:
        for issue in inspector.issues:
            print(f"{issue.path}: {issue.message}", file=sys.stderr)
        return 1
    if result is None:
        print("CAD source inspection failed", file=sys.stderr)
        return 1
    print(f"Inspection report: {result.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
