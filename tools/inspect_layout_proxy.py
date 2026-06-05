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
class InspectionResult:
    report_path: Path


class LayoutProxyInspector:
    def __init__(self, repo_root: Path, package: Path, scene_path: Path, out: Path) -> None:
        self.repo_root = repo_root
        self.package = package
        self.scene_path = scene_path
        self.out = out
        self.issues: list[Issue] = []
        self.registry = self.load_registry()

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

    def load_registry(self) -> dict[str, dict[str, Any]]:
        registry_root = self.repo_root / "registry" / "interfaces"
        index = self.load_json(registry_root / "index.json")
        records: dict[str, dict[str, Any]] = {}
        if not isinstance(index, dict):
            return records
        for entry in index.get("entries", []):
            if not isinstance(entry, str):
                continue
            record = self.load_json(registry_root / entry)
            if isinstance(record, dict) and isinstance(record.get("id"), str):
                records[record["id"]] = record
        return records

    def inspect(self) -> InspectionResult | None:
        validator = ContractValidator(self.repo_root)
        validator.validate_repo()
        validator.validate_package(self.package)
        validator.validate_package(self.scene_path)
        if validator.issues:
            self.issues.extend(validator.issues)
            return None

        documents = self.load_package_documents()
        cad_specs = [(path, doc) for path, doc in documents if doc.get("kind") == "cad_spec"]
        if len(cad_specs) != 1:
            self.error(self.package, "layout proxy inspection requires exactly one cad_spec document")
            return None
        spec_path, spec = cad_specs[0]
        layout = self.resolve_layout_contract(documents, spec)
        if not layout:
            self.error(spec_path, "layout proxy inspection requires a layout_contract document or cad_spec.layout_contract object")
            return None
        scene = self.load_json(self.scene_path)
        if not isinstance(scene, dict):
            return None

        package_interfaces = {
            doc["id"]: doc
            for _, doc in documents
            if doc.get("kind") == "interface_signature" and isinstance(doc.get("id"), str)
        }
        report = self.build_report(spec, layout, scene, package_interfaces)
        self.out.parent.mkdir(parents=True, exist_ok=True)
        write_json(self.out, report)

        output_validator = ContractValidator(self.repo_root)
        output_validator.validate_package(self.out)
        if output_validator.issues:
            self.issues.extend(output_validator.issues)
            return None

        return InspectionResult(report_path=self.out)

    def load_package_documents(self) -> list[tuple[Path, dict[str, Any]]]:
        paths = [self.package] if self.package.is_file() else sorted(self.package.rglob("*.json"))
        documents: list[tuple[Path, dict[str, Any]]] = []
        for path in paths:
            loaded = self.load_json(path)
            if isinstance(loaded, dict):
                documents.append((path, loaded))
        return documents

    def resolve_layout_contract(self, documents: list[tuple[Path, dict[str, Any]]], spec: dict[str, Any]) -> dict[str, Any] | None:
        layouts = [doc for _, doc in documents if doc.get("kind") == "layout_contract"]
        if len(layouts) == 1:
            return layouts[0]
        embedded = spec.get("layout_contract")
        if isinstance(embedded, dict):
            return embedded
        return None

    def build_report(
        self,
        spec: dict[str, Any],
        layout: dict[str, Any],
        scene: dict[str, Any],
        package_interfaces: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []
        checks.append(self.check_source_spec(spec, scene))
        checks.append(self.check_maturity(scene))
        checks.append(self.check_parts_have_primitives(layout, scene))
        checks.append(self.check_locked_facts_carried(spec, scene))
        checks.append(self.check_inspection_targets_carried(spec, scene))
        checks.append(self.check_relationships_carried(layout, scene))
        checks.append(self.check_primitives_are_layout_only(scene))
        checks.extend(self.check_interface_signatures(layout, scene, package_interfaces))

        failed = [check for check in checks if check["status"] == "failed"]
        skipped = scene.get("skipped_checks", [])
        status = "failed" if failed else "partial" if skipped else "passed"
        recommendation = "needs_repair" if failed else "ready_for_layout_generation"
        limitations = [
            "Inspection covers kernel-neutral scene contract only.",
            "Downstream CAD geometry checks are still required before proceed review.",
        ]
        if skipped:
            limitations.append("Scene carries skipped geometry checks that require a CAD harness.")

        return {
            "schema_version": SCHEMA_VERSION,
            "kind": "inspection_report",
            "id": f"{spec['id']}.layout_proxy_locked_facts_report",
            "spec_id": spec["id"],
            "artifact": {
                "path": str(self.scene_path),
                "kind": "layout_proxy_scene",
            },
            "status": status,
            "checks": checks,
            "skipped_checks": skipped,
            "repair_attempts": [],
            "proceed_recommendation": recommendation,
            "limitations": limitations,
            "extensions": {
                "inspector": "tools/inspect_layout_proxy.py",
            },
        }

    def check_source_spec(self, spec: dict[str, Any], scene: dict[str, Any]) -> dict[str, Any]:
        expected = spec.get("id")
        actual = scene.get("source_spec_id")
        return check_result(
            "scene_source_spec_matches",
            "label",
            actual == expected,
            f"scene.source_spec_id={actual!r}; cad_spec.id={expected!r}",
        )

    def check_maturity(self, scene: dict[str, Any]) -> dict[str, Any]:
        return check_result(
            "scene_maturity_layout_proxy",
            "label",
            scene.get("maturity_target") == "layout_proxy",
            f"scene.maturity_target={scene.get('maturity_target')!r}",
        )

    def check_parts_have_primitives(self, layout: dict[str, Any], scene: dict[str, Any]) -> dict[str, Any]:
        expected_parts = {
            part.get("part_id")
            for part in layout.get("parts", [])
            if isinstance(part, dict) and isinstance(part.get("part_id"), str)
        }
        primitive_parts = {
            primitive.get("part_id")
            for primitive in scene.get("primitives", [])
            if isinstance(primitive, dict) and isinstance(primitive.get("part_id"), str)
        }
        missing = sorted(expected_parts - primitive_parts)
        return check_result(
            "scene_parts_have_primitives",
            "label",
            not missing,
            f"missing primitive coverage for parts: {', '.join(missing) if missing else 'none'}",
        )

    def check_locked_facts_carried(self, spec: dict[str, Any], scene: dict[str, Any]) -> dict[str, Any]:
        expected = {
            fact.get("fact_id")
            for fact in spec.get("locked_layout_facts", [])
            if isinstance(fact, dict) and isinstance(fact.get("fact_id"), str)
        }
        actual = {str(item) for item in scene.get("locked_layout_facts", [])}
        missing = sorted(expected - actual)
        return check_result(
            "scene_locked_facts_carried",
            "label",
            not missing,
            f"missing locked facts: {', '.join(missing) if missing else 'none'}",
            sorted(expected),
        )

    def check_inspection_targets_carried(self, spec: dict[str, Any], scene: dict[str, Any]) -> dict[str, Any]:
        expected = {
            check.get("check_id")
            for check in spec.get("inspection_plan", [])
            if isinstance(check, dict) and isinstance(check.get("check_id"), str)
        }
        actual = {str(item) for item in scene.get("inspection_targets", [])}
        missing = sorted(expected - actual)
        return check_result(
            "scene_inspection_targets_carried",
            "label",
            not missing,
            f"missing inspection targets: {', '.join(missing) if missing else 'none'}",
        )

    def check_relationships_carried(self, layout: dict[str, Any], scene: dict[str, Any]) -> dict[str, Any]:
        expected: set[str] = set()
        relationships = layout.get("relationships", {})
        if isinstance(relationships, dict):
            for group in ["contacts", "connections", "motion"]:
                for relationship in relationships.get(group, []):
                    if isinstance(relationship, dict) and isinstance(relationship.get("relationship_id"), str):
                        expected.add(relationship["relationship_id"])
        actual = {
            relationship.get("id")
            for relationship in scene.get("relationships", [])
            if isinstance(relationship, dict) and isinstance(relationship.get("id"), str)
        }
        missing = sorted(expected - actual)
        return check_result(
            "scene_relationships_carried",
            "label",
            not missing,
            f"missing relationships: {', '.join(missing) if missing else 'none'}",
        )

    def check_primitives_are_layout_only(self, scene: dict[str, Any]) -> dict[str, Any]:
        bad = [
            str(primitive.get("id", "<unknown>"))
            for primitive in scene.get("primitives", [])
            if isinstance(primitive, dict) and primitive.get("fidelity") != "layout_only"
        ]
        return check_result(
            "scene_primitives_layout_only",
            "label",
            not bad,
            f"non-layout-only primitives: {', '.join(bad) if bad else 'none'}",
        )

    def check_interface_signatures(
        self,
        layout: dict[str, Any],
        scene: dict[str, Any],
        package_interfaces: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        checks: list[dict[str, Any]] = []
        primitive_sources = derived_sources(scene.get("primitives", []))
        datum_sources = derived_sources(scene.get("datums", []))
        for part in layout.get("parts", []):
            if not isinstance(part, dict):
                continue
            part_id = str(part.get("part_id", "unknown_part"))
            refs = [ref for ref in part.get("interface_signature_refs", []) if isinstance(ref, str)]
            for ref in refs:
                signature = package_interfaces.get(ref) or self.registry.get(ref)
                if not signature:
                    checks.append(
                        check_result(
                            f"{part_id}.{ref}.interface_resolved",
                            "label",
                            False,
                            f"unresolved interface signature {ref}",
                        )
                    )
                    continue
                signature_id = str(signature["id"])
                primitive_ok = signature_id in primitive_sources
                datum_ok = signature_id in datum_sources
                checks.append(
                    check_result(
                        f"{part_id}.{signature_id}.proxy_primitives",
                        "label",
                        primitive_ok,
                        f"primitive derived_from includes {signature_id}: {primitive_ok}",
                    )
                )
                checks.append(
                    check_result(
                        f"{part_id}.{signature_id}.datums",
                        "label",
                        datum_ok,
                        f"datum derived_from includes {signature_id}: {datum_ok}",
                    )
                )
        return checks


def derived_sources(items: Any) -> set[str]:
    sources: set[str] = set()
    if not isinstance(items, list):
        return sources
    for item in items:
        if not isinstance(item, dict):
            continue
        for source in item.get("derived_from", []):
            sources.add(str(source))
    return sources


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
    parser = argparse.ArgumentParser(description="Inspect a Zen CAD layout proxy scene against its contract package.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1], help="Zen CAD repository root.")
    parser.add_argument("--package", type=Path, required=True, help="Contract package JSON file or directory.")
    parser.add_argument("--scene", type=Path, required=True, help="layout_proxy.scene.json to inspect.")
    parser.add_argument("--out", type=Path, required=True, help="Output inspection report JSON path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    inspector = LayoutProxyInspector(args.repo_root, args.package, args.scene, args.out)
    result = inspector.inspect()
    if inspector.issues:
        for issue in inspector.issues:
            print(f"{issue.path}: {issue.message}", file=sys.stderr)
        return 1
    if result is None:
        print("layout proxy inspection failed", file=sys.stderr)
        return 1
    print(f"Inspection report: {result.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
