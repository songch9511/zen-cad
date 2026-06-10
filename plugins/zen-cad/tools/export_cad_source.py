#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from validate_contract import ContractValidator, Issue


SCHEMA_VERSION = "0.8.0"


@dataclass
class ExportResult:
    source_path: Path
    manifest_path: Path


class CadSourceExporter:
    def __init__(self, repo_root: Path, package: Path, scene_path: Path, out: Path, target: str) -> None:
        self.repo_root = repo_root
        self.package = package
        self.scene_path = scene_path
        self.out = out
        self.target = target
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

    def export(self) -> ExportResult | None:
        if self.target != "build123d":
            self.error("<args>", "only build123d source export is currently supported")
            return None

        validator = ContractValidator(self.repo_root)
        validator.validate_repo()
        validator.validate_package(self.package)
        validator.validate_package(self.scene_path)
        if validator.issues:
            self.issues.extend(validator.issues)
            return None

        scene = self.load_json(self.scene_path)
        if not isinstance(scene, dict):
            return None
        sourced_parts = self.load_sourced_parts()

        self.out.mkdir(parents=True, exist_ok=True)
        source_path = self.out / "layout_proxy_build123d.py"
        manifest_path = self.out / "cad_source_manifest.json"
        source_path.write_text(render_build123d_source(scene, sourced_parts), encoding="utf-8")
        manifest = self.build_manifest(scene, source_path, manifest_path, sourced_parts)
        write_json(manifest_path, manifest)

        output_validator = ContractValidator(self.repo_root)
        output_validator.validate_package(manifest_path)
        if output_validator.issues:
            self.issues.extend(output_validator.issues)
            return None

        return ExportResult(source_path=source_path, manifest_path=manifest_path)

    def load_sourced_parts(self) -> list[dict[str, str]]:
        paths = [self.package] if self.package.is_file() else sorted(self.package.rglob("*.json"))
        sourced_parts: list[dict[str, str]] = []
        for path in paths:
            document = self.load_json(path)
            if not isinstance(document, dict) or document.get("kind") != "source_lock_evidence":
                continue
            if document.get("lock_status") != "source_locked":
                continue
            geometry_sources = [
                source
                for source in document.get("evidence_sources", [])
                if isinstance(source, dict)
                and source.get("artifact_kind") in {"step", "stp"}
                and "geometry_reference" in source.get("trusted_for", [])
            ]
            if not geometry_sources:
                continue
            source = geometry_sources[0]
            locator = str(source.get("locator", ""))
            resolved_locator = resolve_import_locator(locator, self.package)
            part_id = str(document.get("part_id", "sourced_part"))
            sourced_parts.append(
                {
                    "part_id": part_id,
                    "source_lock_id": str(document.get("id", "")),
                    "locator": resolved_locator,
                    "artifact_kind": str(source.get("artifact_kind")),
                    "import_strategy": "build123d.import_step",
                    "label": str(document.get("source_identity", {}).get("display_name") or part_id),
                    "source_type": str(source.get("source_type", "")),
                    "placement_policy": "replace matching layout proxy primitives; imported at source STEP origin until downstream alignment applies locked facts",
                }
            )
        return sourced_parts

    def build_manifest(self, scene: dict[str, Any], source_path: Path, manifest_path: Path, sourced_parts: list[dict[str, str]]) -> dict[str, Any]:
        primitive_ids = [
            str(primitive["id"])
            for primitive in scene.get("primitives", [])
            if isinstance(primitive, dict) and isinstance(primitive.get("id"), str)
        ]
        return {
            "schema_version": SCHEMA_VERSION,
            "kind": "cad_source_manifest",
            "id": f"{scene['id']}.build123d_manifest",
            "source_scene_id": scene["id"],
            "target_harness": self.target,
            "source_path": str(source_path),
            "expected_primary_artifact": str(source_path.with_suffix(".step")),
            "generated_files": [str(source_path), str(manifest_path)],
            "primitives": primitive_ids,
            "locked_layout_facts": [str(item) for item in scene.get("locked_layout_facts", [])],
            "inspection_targets": [str(item) for item in scene.get("inspection_targets", [])],
            "sourced_parts": sourced_parts,
            "source_of_truth": {
                "scene": str(self.scene_path),
                "package": str(self.package),
            },
            "extensions": {
                "exporter": "tools/export_cad_source.py",
                "note": "Source-level export imports source-locked STEP/STP parts when geometry references are present; final STEP generation still requires a downstream build123d runtime.",
            },
        }


def render_build123d_source(scene: dict[str, Any], sourced_parts: list[dict[str, str]] | None = None) -> str:
    sourced_parts = sourced_parts or []
    sourced_part_ids = {str(part.get("part_id")) for part in sourced_parts}
    primitives = [
        primitive
        for primitive in scene.get("primitives", [])
        if isinstance(primitive, dict)
        and isinstance(primitive.get("id"), str)
        and str(primitive.get("part_id", "")) not in sourced_part_ids
    ]
    primitive_literal = json.dumps(primitives, indent=2, sort_keys=True)
    sourced_literal = json.dumps(sourced_parts, indent=2, sort_keys=True)
    locked_literal = json.dumps(scene.get("locked_layout_facts", []), indent=2, sort_keys=True)
    inspection_literal = json.dumps(scene.get("inspection_targets", []), indent=2, sort_keys=True)
    scene_id = scene.get("id", "unknown_scene")
    spec_id = scene.get("source_spec_id", "unknown_spec")
    return f'''"""Generated Zen CAD layout proxy source.

This file is generated from a kernel-neutral layout proxy scene.
It is a source adapter for downstream CAD generation, not final CAD evidence.
"""
from __future__ import annotations

ZEN_CAD_SCENE_ID = {scene_id!r}
ZEN_CAD_SOURCE_SPEC_ID = {spec_id!r}
ZEN_CAD_PRIMITIVES = {primitive_literal}
ZEN_CAD_SOURCED_PARTS = {sourced_literal}
ZEN_CAD_LOCKED_LAYOUT_FACTS = {locked_literal}
ZEN_CAD_INSPECTION_TARGETS = {inspection_literal}


def _dimension_value(dimensions, *names, default=1.0):
    for name in names:
        item = dimensions.get(name)
        if isinstance(item, dict) and isinstance(item.get("value"), (int, float)):
            return float(item["value"])
    return float(default)


def _make_primitive(primitive):
    from build123d import Axis, Box, Cylinder, Location, Plane, Pos, Sphere

    primitive_type = primitive.get("type")
    dimensions = primitive.get("dimensions", {{}})
    primitive_id = primitive.get("id", "primitive")

    if primitive_type == "box":
        width = _dimension_value(dimensions, "face_size", "body_width", "rail_width", "rail_width_envelope", default=10.0)
        depth = width
        height = _dimension_value(dimensions, "body_length", "width", default=5.0)
        shape = Box(width, depth, height)
    elif primitive_type == "cylinder":
        diameter = _dimension_value(dimensions, "outer_diameter", "nominal_diameter", "bore_diameter", default=5.0)
        height = _dimension_value(dimensions, "width", default=10.0)
        shape = Cylinder(radius=diameter / 2.0, height=height)
    elif primitive_type == "axis":
        shape = Cylinder(radius=0.35, height=12.0)
    elif primitive_type == "plane":
        width = _dimension_value(dimensions, "belt_width", default=6.0)
        shape = Box(20.0, width, 0.2)
    elif primitive_type == "pattern":
        diameter = _dimension_value(dimensions, "normal_clearance_diameter", default=3.0)
        shape = Cylinder(radius=diameter / 2.0, height=2.0)
    else:
        shape = Box(8.0, 8.0, 8.0)

    shape.label = primitive_id
    return shape


def _resolve_step_locator(entry):
    from pathlib import Path
    from urllib.parse import urlparse
    from urllib.request import urlretrieve

    locator = str(entry.get("locator", ""))
    parsed = urlparse(locator)
    if parsed.scheme in {{"http", "https"}}:
        suffix = ".stp" if entry.get("artifact_kind") == "stp" else ".step"
        cache_dir = Path(__file__).resolve().parent / "sourced_parts_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(entry.get("part_id", "part")))
        target = cache_dir / f"{{safe_name}}{{suffix}}"
        if not target.exists():
            urlretrieve(locator, target)
        return target
    return Path(locator).expanduser()


def _import_sourced_part(entry):
    from build123d import import_step

    shape = import_step(str(_resolve_step_locator(entry)))
    try:
        shape.label = str(entry.get("label") or entry.get("part_id") or "sourced_step")
    except Exception:
        pass
    return shape


def gen_step():
    from build123d import Compound

    sourced_children = [_import_sourced_part(entry) for entry in ZEN_CAD_SOURCED_PARTS]
    proxy_children = [_make_primitive(primitive) for primitive in ZEN_CAD_PRIMITIVES]
    children = sourced_children + proxy_children
    assembly = Compound(label=ZEN_CAD_SCENE_ID, children=children)
    return assembly
'''


def resolve_import_locator(locator: str, package: Path) -> str:
    parsed = urlparse(locator)
    if parsed.scheme in {"http", "https"}:
        return locator
    path = Path(locator).expanduser()
    if path.is_absolute():
        return str(path)
    base = package.parent if package.is_file() else package
    return str((base / path).resolve())


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a Zen CAD layout proxy scene to CAD source.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1], help="Zen CAD repository root.")
    parser.add_argument("--package", type=Path, required=True, help="Contract package JSON file or directory.")
    parser.add_argument("--scene", type=Path, required=True, help="layout_proxy.scene.json to export.")
    parser.add_argument("--out", type=Path, required=True, help="Output directory for CAD source and manifest.")
    parser.add_argument("--target", choices=["build123d"], default="build123d", help="CAD source target.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    exporter = CadSourceExporter(args.repo_root, args.package, args.scene, args.out, args.target)
    result = exporter.export()
    if exporter.issues:
        for issue in exporter.issues:
            print(f"{issue.path}: {issue.message}", file=sys.stderr)
        return 1
    if result is None:
        print("CAD source export failed", file=sys.stderr)
        return 1
    print(f"CAD source: {result.source_path}")
    print(f"Source manifest: {result.manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
