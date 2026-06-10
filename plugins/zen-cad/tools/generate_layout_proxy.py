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
class GenerationResult:
    scene_path: Path
    report_path: Path


class LayoutProxyGenerator:
    def __init__(self, repo_root: Path, package: Path, out_dir: Path) -> None:
        self.repo_root = repo_root
        self.package = package
        self.out_dir = out_dir
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

    def load_package_documents(self) -> list[tuple[Path, dict[str, Any]]]:
        paths = [self.package] if self.package.is_file() else sorted(self.package.rglob("*.json"))
        documents: list[tuple[Path, dict[str, Any]]] = []
        for path in paths:
            loaded = self.load_json(path)
            if isinstance(loaded, dict):
                documents.append((path, loaded))
        return documents

    def generate(self) -> GenerationResult | None:
        validator = ContractValidator(self.repo_root)
        validator.validate_repo()
        validator.validate_package(self.package)
        if validator.issues:
            self.issues.extend(validator.issues)
            return None

        documents = self.load_package_documents()
        cad_specs = [(path, doc) for path, doc in documents if doc.get("kind") == "cad_spec"]
        if len(cad_specs) != 1:
            self.error(self.package, "layout proxy generation requires exactly one cad_spec document")
            return None
        spec_path, spec = cad_specs[0]
        layout = self.resolve_layout_contract(documents, spec)
        if not layout:
            self.error(spec_path, "layout proxy generation requires a layout_contract document or cad_spec.layout_contract object")
            return None

        package_interfaces = {
            doc["id"]: doc
            for _, doc in documents
            if doc.get("kind") == "interface_signature" and isinstance(doc.get("id"), str)
        }

        scene = self.build_scene(spec_path, spec, layout, package_interfaces)
        if self.issues:
            return None

        self.out_dir.mkdir(parents=True, exist_ok=True)
        scene_path = self.out_dir / "layout_proxy.scene.json"
        report_path = self.out_dir / "layout_proxy.inspection_report.json"
        report = self.build_report(spec, scene, scene_path)
        write_json(scene_path, scene)
        write_json(report_path, report)

        output_validator = ContractValidator(self.repo_root)
        output_validator.validate_package(self.out_dir)
        if output_validator.issues:
            self.issues.extend(output_validator.issues)
            return None

        return GenerationResult(scene_path=scene_path, report_path=report_path)

    def resolve_layout_contract(self, documents: list[tuple[Path, dict[str, Any]]], spec: dict[str, Any]) -> dict[str, Any] | None:
        layouts = [doc for _, doc in documents if doc.get("kind") == "layout_contract"]
        if len(layouts) == 1:
            return layouts[0]
        embedded = spec.get("layout_contract")
        if isinstance(embedded, dict):
            return embedded
        return None

    def build_scene(
        self,
        spec_path: Path,
        spec: dict[str, Any],
        layout: dict[str, Any],
        package_interfaces: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        primitives: list[dict[str, Any]] = []
        datums: list[dict[str, Any]] = []
        relationships: list[dict[str, Any]] = []
        parts = layout.get("parts", [])
        if not isinstance(parts, list) or not parts:
            self.error(spec_path, "layout contract must include at least one part")
            parts = []

        for part in parts:
            if not isinstance(part, dict):
                self.error(spec_path, "layout contract parts must be objects")
                continue
            part_id = str(part.get("part_id", "unnamed_part"))
            local_frame = str(part.get("local_frame", "unspecified"))
            refs = [ref for ref in part.get("interface_signature_refs", []) if isinstance(ref, str)]
            signatures = self.resolve_signatures(spec_path, refs, package_interfaces)
            primitives.extend(self.part_primitives(part_id, local_frame, signatures))
            datums.extend(self.part_datums(part_id, signatures))
            if not signatures:
                primitives.append(
                    {
                        "id": f"{part_id}.proxy_envelope",
                        "part_id": part_id,
                        "type": "envelope",
                        "frame": local_frame,
                        "dimensions": {"policy": str(part.get("proxy_policy", "layout envelope from spec"))},
                        "derived_from": ["layout_contract"],
                        "fidelity": "layout_only",
                        "notes": "No interface signature was attached; downstream CAD must use the spec envelope.",
                    }
                )

        for group_name in ["contacts", "connections", "motion"]:
            for relationship in layout.get("relationships", {}).get(group_name, []):
                if not isinstance(relationship, dict):
                    continue
                relationships.append(
                    {
                        "id": str(relationship.get("relationship_id", f"{group_name}_{len(relationships) + 1}")),
                        "type": str(relationship.get("type", group_name)),
                        "parts": [str(part) for part in relationship.get("parts", [])],
                        "statement": str(relationship.get("statement", "")),
                        "locked": bool(relationship.get("locked", False)),
                    }
                )

        inspection_plan = spec.get("inspection_plan", [])
        skipped_checks = [
            {
                "check_id": str(check.get("check_id", "unnamed_check")),
                "reason": "Kernel-neutral layout proxy scene generated; downstream CAD geometry inspection still required.",
            }
            for check in inspection_plan
            if isinstance(check, dict) and check.get("check_type") in {"bbox", "distance", "frame", "mate", "plane", "axis", "motion", "snapshot", "viewer"}
        ]

        return {
            "schema_version": SCHEMA_VERSION,
            "kind": "layout_proxy_scene",
            "id": f"{spec['id']}.layout_proxy_scene",
            "source_spec_id": spec["id"],
            "units": str(spec.get("units", "mm")),
            "maturity_target": "layout_proxy",
            "source_of_truth": {
                "spec": str(spec_path),
                "package": str(self.package),
            },
            "root_frame": layout.get("root_frame", {}),
            "primitives": primitives,
            "datums": datums,
            "relationships": relationships,
            "locked_layout_facts": [str(fact.get("fact_id", fact)) for fact in spec.get("locked_layout_facts", [])],
            "inspection_targets": [str(check.get("check_id", check)) for check in inspection_plan],
            "skipped_checks": skipped_checks,
            "extensions": {
                "generator": "tools/generate_layout_proxy.py",
            },
        }

    def resolve_signatures(
        self,
        path: Path,
        refs: list[str],
        package_interfaces: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        signatures: list[dict[str, Any]] = []
        for ref in refs:
            record = package_interfaces.get(ref) or self.registry.get(ref)
            if not record:
                self.error(path, f"unresolved interface signature: {ref}")
                continue
            signatures.append(record)
        return signatures

    def part_primitives(self, part_id: str, local_frame: str, signatures: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not signatures:
            return []
        primitives: list[dict[str, Any]] = []
        for signature in signatures:
            family = signature.get("family", "custom")
            dimensions = dimensions_by_name(signature)
            base = {
                "part_id": part_id,
                "frame": local_frame,
                "derived_from": [str(signature["id"])],
                "fidelity": "layout_only",
            }
            if family == "motor":
                primitives.append(
                    {
                        **base,
                        "id": f"{part_id}.motor_body",
                        "type": "box",
                        "dimensions": pick_dimensions(dimensions, ["face_size", "body_width", "body_length"]),
                        "notes": "Motor body is a box proxy; shaft and connector details remain confirm-before-final.",
                    }
                )
                primitives.append(axis_primitive(part_id, local_frame, signature, "shaft_axis"))
            elif family == "bearing":
                primitives.append(
                    {
                        **base,
                        "id": f"{part_id}.bearing_envelope",
                        "type": "cylinder",
                        "dimensions": pick_dimensions(dimensions, ["outer_diameter", "bore_diameter", "width"]),
                        "notes": "Bearing proxy preserves bore, outer seat, and axial width.",
                    }
                )
                primitives.append(axis_primitive(part_id, local_frame, signature, "bearing_axis"))
            elif family == "belt":
                primitives.append(
                    {
                        **base,
                        "id": f"{part_id}.belt_mid_plane",
                        "type": "plane",
                        "dimensions": pick_dimensions(dimensions, ["pitch", "belt_width"]),
                        "notes": "Belt proxy preserves pitch and belt mid-plane only.",
                    }
                )
            elif family == "fastener":
                primitives.append(
                    {
                        **base,
                        "id": f"{part_id}.fastener_pattern",
                        "type": "pattern",
                        "dimensions": pick_dimensions(dimensions, ["normal_clearance_diameter"]),
                        "notes": "Fastener proxy marks clearance axes and pattern intent.",
                    }
                )
            elif family == "shaft_bore":
                primitives.append(
                    {
                        **base,
                        "id": f"{part_id}.shaft_or_bore",
                        "type": "cylinder",
                        "dimensions": pick_dimensions(dimensions, ["nominal_diameter"]),
                        "notes": "Shaft/bore proxy preserves nominal coaxial interface.",
                    }
                )
                primitives.append(axis_primitive(part_id, local_frame, signature, "shaft_axis"))
            elif family == "linear_rail":
                primitives.append(
                    {
                        **base,
                        "id": f"{part_id}.rail_envelope",
                        "type": "box",
                        "dimensions": pick_dimensions(dimensions, ["rail_width", "rail_width_envelope"]),
                        "notes": "Rail proxy preserves travel axis and mounting face envelope.",
                    }
                )
                primitives.append(axis_primitive(part_id, local_frame, signature, "travel_axis"))
            else:
                primitives.append(
                    {
                        **base,
                        "id": f"{part_id}.{family}_envelope",
                        "type": "envelope",
                        "dimensions": dimensions,
                        "notes": "Generic interface envelope proxy.",
                    }
                )
        return [primitive for primitive in primitives if primitive]

    def part_datums(self, part_id: str, signatures: list[dict[str, Any]]) -> list[dict[str, Any]]:
        datums: list[dict[str, Any]] = []
        for signature in signatures:
            signature_id = str(signature["id"])
            for axis in signature.get("primary_axes", []):
                if isinstance(axis, dict):
                    datums.append(
                        {
                            "id": f"{part_id}.{axis.get('name', 'axis')}",
                            "part_id": part_id,
                            "kind": "axis",
                            "statement": str(axis.get("statement", "")),
                            "derived_from": [signature_id],
                        }
                    )
            for datum in signature.get("mounting_datums", []):
                if isinstance(datum, dict):
                    datums.append(
                        {
                            "id": f"{part_id}.{datum.get('name', 'datum')}",
                            "part_id": part_id,
                            "kind": "plane",
                            "statement": str(datum.get("statement", "")),
                            "derived_from": [signature_id],
                        }
                    )
        return datums

    def build_report(self, spec: dict[str, Any], scene: dict[str, Any], scene_path: Path) -> dict[str, Any]:
        checks = [
            {
                "check_id": "scene_primitives_present",
                "check_type": "label",
                "status": "passed",
                "evidence": f"{len(scene['primitives'])} layout proxy primitives generated.",
                "locked_fact_refs": [],
            },
            {
                "check_id": "scene_locked_facts_carried",
                "check_type": "label",
                "status": "passed",
                "evidence": f"{len(scene['locked_layout_facts'])} locked layout facts carried into scene.",
                "locked_fact_refs": scene["locked_layout_facts"],
            },
        ]
        return {
            "schema_version": SCHEMA_VERSION,
            "kind": "inspection_report",
            "id": f"{spec['id']}.layout_proxy_scene_report",
            "spec_id": spec["id"],
            "artifact": {
                "path": str(scene_path),
                "kind": "layout_proxy_scene",
            },
            "status": "partial" if scene["skipped_checks"] else "passed",
            "checks": checks,
            "skipped_checks": scene["skipped_checks"],
            "repair_attempts": [],
            "proceed_recommendation": "ready_for_layout_generation",
            "limitations": [
                "This is a kernel-neutral layout proxy scene, not generated CAD geometry.",
                "Downstream CAD generation and geometry inspection are still required before proceed review.",
            ],
            "extensions": {
                "generator": "tools/generate_layout_proxy.py",
            },
        }


def dimensions_by_name(signature: dict[str, Any]) -> dict[str, Any]:
    dimensions: dict[str, Any] = {}
    for group in ["critical_dimensions", "envelope"]:
        for item in signature.get(group, []):
            if isinstance(item, dict) and isinstance(item.get("name"), str):
                dimensions[item["name"]] = {
                    "value": item.get("value"),
                    "units": item.get("units", signature.get("units", "mm")),
                    "status": item.get("status"),
                }
    return dimensions


def pick_dimensions(dimensions: dict[str, Any], names: list[str]) -> dict[str, Any]:
    return {name: dimensions[name] for name in names if name in dimensions}


def axis_primitive(part_id: str, local_frame: str, signature: dict[str, Any], axis_name: str) -> dict[str, Any]:
    return {
        "id": f"{part_id}.{axis_name}",
        "part_id": part_id,
        "type": "axis",
        "frame": local_frame,
        "dimensions": {},
        "derived_from": [str(signature["id"])],
        "fidelity": "layout_only",
        "notes": f"{axis_name} datum marker.",
    }


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a kernel-neutral Zen CAD layout proxy scene from a validated contract package.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1], help="Zen CAD repository root.")
    parser.add_argument("--package", type=Path, required=True, help="Contract package JSON file or directory.")
    parser.add_argument("--out", type=Path, required=True, help="Output directory for layout_proxy.scene.json and inspection report.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    generator = LayoutProxyGenerator(args.repo_root, args.package, args.out)
    result = generator.generate()
    if generator.issues:
        for issue in generator.issues:
            print(f"{issue.path}: {issue.message}", file=sys.stderr)
        return 1
    if result is None:
        print("layout proxy generation failed", file=sys.stderr)
        return 1
    print(f"Layout proxy scene: {result.scene_path}")
    print(f"Inspection report: {result.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
