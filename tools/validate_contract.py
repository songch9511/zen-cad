#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "0.8.0"

SCHEMA_FILES = {
    "cad_spec.schema.json": "cad_spec",
    "layout_contract.schema.json": "layout_contract",
    "interface_signature.schema.json": "interface_signature",
    "inspection_report.schema.json": "inspection_report",
    "handoff_packet.schema.json": "handoff_packet",
    "layout_proxy_scene.schema.json": "layout_proxy_scene",
}

COMMON_SCHEMA_REQUIRED = {"schema_version", "kind", "extensions"}

INTERFACE_REQUIRED = {
    "schema_version",
    "kind",
    "id",
    "title",
    "units",
    "family",
    "quality_label",
    "trusted_for_layout",
    "source",
    "primary_axes",
    "mounting_datums",
    "critical_dimensions",
    "envelope",
    "validation_targets",
    "proxy_may_simplify",
    "must_confirm_before_final",
    "extensions",
}

FORBIDDEN_REGISTRY_KEYS = {
    "manufacturer",
    "supplier",
    "sku",
    "price",
    "availability",
    "bom_quantity",
    "step_file",
    "cad_file",
    "load_rating",
    "torque_rating",
    "material",
    "certification",
}


@dataclass
class Issue:
    path: str
    message: str


class ContractValidator:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
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

    def validate_repo(self) -> list[Issue]:
        self.validate_schemas()
        self.validate_registry()
        return self.issues

    def validate_schemas(self) -> None:
        schema_root = self.repo_root / "schemas"
        for filename, kind in SCHEMA_FILES.items():
            path = schema_root / filename
            schema = self.load_json(path)
            if not isinstance(schema, dict):
                continue
            if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                self.error(path, "schema must use JSON Schema Draft 2020-12")
            if schema.get("type") != "object":
                self.error(path, "top-level schema type must be object")
            if schema.get("additionalProperties") is not False:
                self.error(path, "stable schema must set additionalProperties to false")
            required = set(schema.get("required", []))
            missing = sorted(COMMON_SCHEMA_REQUIRED - required)
            if missing:
                self.error(path, f"missing common required fields: {', '.join(missing)}")
            properties = schema.get("properties", {})
            if properties.get("schema_version", {}).get("const") != SCHEMA_VERSION:
                self.error(path, f"schema_version const must be {SCHEMA_VERSION}")
            if properties.get("kind", {}).get("const") != kind:
                self.error(path, f"kind const must be {kind}")

    def validate_registry(self) -> None:
        registry_root = self.repo_root / "registry" / "interfaces"
        index_path = registry_root / "index.json"
        index = self.load_json(index_path)
        if not isinstance(index, dict):
            return
        if index.get("schema_version") != SCHEMA_VERSION:
            self.error(index_path, f"schema_version must be {SCHEMA_VERSION}")
        if index.get("kind") != "interface_registry_index":
            self.error(index_path, "kind must be interface_registry_index")
        entries = index.get("entries")
        if not isinstance(entries, list) or not entries:
            self.error(index_path, "entries must be a non-empty list")
            return
        seen: set[str] = set()
        for entry in entries:
            if not isinstance(entry, str):
                self.error(index_path, "entries must contain only string paths")
                continue
            if entry in seen:
                self.error(index_path, f"duplicate registry entry: {entry}")
            seen.add(entry)
            if entry.startswith("/") or ".." in Path(entry).parts:
                self.error(index_path, f"registry entry must be relative and contained: {entry}")
                continue
            record_path = registry_root / entry
            record = self.load_json(record_path)
            if isinstance(record, dict):
                self.validate_interface_signature(record_path, record)

    def validate_interface_signature(self, path: Path, record: dict[str, Any]) -> None:
        missing = sorted(INTERFACE_REQUIRED - set(record))
        if missing:
            self.error(path, f"missing interface fields: {', '.join(missing)}")
            return
        if record.get("schema_version") != SCHEMA_VERSION:
            self.error(path, f"schema_version must be {SCHEMA_VERSION}")
        if record.get("kind") != "interface_signature":
            self.error(path, "kind must be interface_signature")
        if record.get("units") != "mm":
            self.error(path, "units must be mm")
        if not record.get("trusted_for_layout"):
            self.error(path, "built-in registry records must be trusted_for_layout")
        forbidden = sorted(FORBIDDEN_REGISTRY_KEYS & walk_keys(record))
        if forbidden:
            self.error(path, f"registry record contains procurement or final-claim keys: {', '.join(forbidden)}")
        for field in [
            "primary_axes",
            "mounting_datums",
            "critical_dimensions",
            "validation_targets",
            "proxy_may_simplify",
            "must_confirm_before_final",
        ]:
            if not isinstance(record.get(field), list) or not record[field]:
                self.error(path, f"{field} must be a non-empty list")
        for dimension in record.get("critical_dimensions", []):
            if not isinstance(dimension, dict):
                self.error(path, "critical_dimensions entries must be objects")
                continue
            for field in ["name", "value", "units", "status"]:
                if field not in dimension:
                    self.error(path, f"critical dimension missing {field}")

    def validate_package(self, package: Path) -> list[Issue]:
        documents = self.load_package_documents(package)
        if documents is None:
            return self.issues

        by_kind: dict[str, list[tuple[Path, dict[str, Any]]]] = {}
        ids: set[str] = set()
        for path, document in documents:
            if not isinstance(document, dict):
                self.error(path, "contract document must be a JSON object")
                continue
            kind = document.get("kind")
            doc_id = document.get("id")
            if not isinstance(kind, str):
                self.error(path, "document must have string kind")
                continue
            if not isinstance(doc_id, str) or not doc_id:
                self.error(path, "document must have non-empty string id")
                continue
            if document.get("schema_version") != SCHEMA_VERSION:
                self.error(path, f"schema_version must be {SCHEMA_VERSION}")
            if doc_id in ids:
                self.error(path, f"duplicate document id: {doc_id}")
            ids.add(doc_id)
            by_kind.setdefault(kind, []).append((path, document))

        for path, document in by_kind.get("cad_spec", []):
            self.validate_cad_spec_document(path, document)
        for path, document in by_kind.get("handoff_packet", []):
            self.validate_handoff_document(path, document)
        for path, document in by_kind.get("inspection_report", []):
            self.validate_inspection_document(path, document)
        for path, document in by_kind.get("interface_signature", []):
            self.validate_interface_signature(path, document)
        for path, document in by_kind.get("layout_proxy_scene", []):
            self.validate_layout_proxy_scene_document(path, document)

        return self.issues

    def load_package_documents(self, package: Path) -> list[tuple[Path, Any]] | None:
        if package.is_file():
            return [(package, self.load_json(package))]
        if not package.is_dir():
            self.error(package, "package path must be a JSON file or directory")
            return None
        paths = sorted(path for path in package.rglob("*.json") if path.is_file())
        if not paths:
            self.error(package, "package directory contains no JSON documents")
            return None
        return [(path, self.load_json(path)) for path in paths]

    def validate_cad_spec_document(self, path: Path, document: dict[str, Any]) -> None:
        required = {
            "parameter_contract",
            "artifact_targets",
            "locked_layout_facts",
            "inspection_plan",
            "repair_loop",
            "proceed_gate",
            "downstream_handoff",
        }
        missing = sorted(required - set(document))
        if missing:
            self.error(path, f"cad_spec missing required fields: {', '.join(missing)}")
        locked_facts = document.get("locked_layout_facts", [])
        if not isinstance(locked_facts, list) or not locked_facts:
            self.error(path, "cad_spec locked_layout_facts must be a non-empty list")
        inspection_plan = document.get("inspection_plan", [])
        if not isinstance(inspection_plan, list) or not inspection_plan:
            self.error(path, "cad_spec inspection_plan must be a non-empty list")
        check_ids = {check.get("check_id") for check in inspection_plan if isinstance(check, dict)}
        for fact in locked_facts if isinstance(locked_facts, list) else []:
            if not isinstance(fact, dict):
                self.error(path, "locked layout facts must be objects")
                continue
            if fact.get("must_preserve") is not True:
                self.error(path, f"locked fact {fact.get('fact_id', '<unknown>')} must set must_preserve true")
            if not any(fact.get("fact_id") in check.get("locked_fact_refs", []) for check in inspection_plan if isinstance(check, dict)):
                self.error(path, f"locked fact {fact.get('fact_id', '<unknown>')} has no inspection check")
        handoff = document.get("downstream_handoff")
        if isinstance(handoff, dict):
            required_handoff = {"locked_facts", "required_checks", "stop_conditions"}
            missing_handoff = sorted(required_handoff - set(handoff))
            if missing_handoff:
                self.error(path, f"embedded downstream_handoff missing: {', '.join(missing_handoff)}")
            for check_ref in handoff.get("required_checks", []):
                if check_ref not in check_ids:
                    self.error(path, f"handoff required check not declared in inspection_plan: {check_ref}")

    def validate_handoff_document(self, path: Path, document: dict[str, Any]) -> None:
        if not document.get("locked_facts"):
            self.error(path, "handoff_packet must embed locked_facts")
        if not document.get("required_checks"):
            self.error(path, "handoff_packet must include required_checks")
        if not document.get("stop_conditions"):
            self.error(path, "handoff_packet must include stop_conditions")
        stop_text = " ".join(str(item) for item in document.get("stop_conditions", []))
        if "locked" not in stop_text.lower():
            self.error(path, "handoff_packet stop_conditions must mention locked facts")

    def validate_inspection_document(self, path: Path, document: dict[str, Any]) -> None:
        checks = document.get("checks", [])
        if not isinstance(checks, list):
            self.error(path, "inspection_report checks must be a list")
            return
        for check in checks:
            if not isinstance(check, dict):
                self.error(path, "inspection_report check entries must be objects")
                continue
            if check.get("status") == "passed" and not str(check.get("evidence", "")).strip():
                self.error(path, f"passed check {check.get('check_id', '<unknown>')} must include evidence")
        for skipped in document.get("skipped_checks", []):
            if not isinstance(skipped, dict) or not str(skipped.get("reason", "")).strip():
                self.error(path, "skipped checks must include a reason")

    def validate_layout_proxy_scene_document(self, path: Path, document: dict[str, Any]) -> None:
        primitives = document.get("primitives", [])
        if not isinstance(primitives, list) or not primitives:
            self.error(path, "layout_proxy_scene primitives must be a non-empty list")
        for primitive in primitives if isinstance(primitives, list) else []:
            if not isinstance(primitive, dict):
                self.error(path, "layout_proxy_scene primitive entries must be objects")
                continue
            for field in ["id", "part_id", "type", "frame", "dimensions", "derived_from", "fidelity"]:
                if field not in primitive:
                    self.error(path, f"layout_proxy_scene primitive missing {field}")
            if primitive.get("fidelity") != "layout_only":
                self.error(path, "layout_proxy_scene primitives must use layout_only fidelity")
        for skipped in document.get("skipped_checks", []):
            if not isinstance(skipped, dict) or not str(skipped.get("reason", "")).strip():
                self.error(path, "layout_proxy_scene skipped checks must include a reason")


def walk_keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        keys = set(value)
        for child in value.values():
            keys.update(walk_keys(child))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for child in value:
            keys.update(walk_keys(child))
        return keys
    return set()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Zen CAD contract schemas, registry records, and optional contract packages.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1], help="Zen CAD repository root.")
    parser.add_argument("--package", type=Path, help="Optional JSON file or directory containing contract documents.")
    parser.add_argument("--repo-only", action="store_true", help="Validate only repository schemas and registry.")
    parser.add_argument("--package-only", action="store_true", help="Validate only the package passed with --package.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    validator = ContractValidator(args.repo_root)

    if args.package_only and not args.package:
        validator.error("<args>", "--package-only requires --package")
    if not args.package_only:
        validator.validate_repo()
    if args.package and not args.repo_only:
        validator.validate_package(args.package)

    if validator.issues:
        for issue in validator.issues:
            print(f"{issue.path}: {issue.message}", file=sys.stderr)
        return 1

    print("Zen CAD contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
