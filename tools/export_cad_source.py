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
        feature_plan = self.load_feature_plan()

        self.out.mkdir(parents=True, exist_ok=True)
        source_path = self.out / "layout_proxy_build123d.py"
        manifest_path = self.out / "cad_source_manifest.json"
        source_path.write_text(render_build123d_source(scene, sourced_parts, feature_plan), encoding="utf-8")
        manifest = self.build_manifest(scene, source_path, manifest_path, sourced_parts, feature_plan)
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
            geometry_sources = sorted(
                [
                    source
                    for source in document.get("evidence_sources", [])
                    if isinstance(source, dict)
                    and source.get("artifact_kind") in {"step", "stp"}
                    and "geometry_reference" in source.get("trusted_for", [])
                ],
                key=geometry_source_priority,
            )
            if not geometry_sources:
                continue
            source = geometry_sources[0]
            locator = str(source.get("locator", ""))
            resolved_locator = self.resolve_import_locator(locator)
            part_id = str(document.get("part_id", "sourced_part"))
            entry = {
                "part_id": part_id,
                "source_lock_id": str(document.get("id", "")),
                "locator": resolved_locator,
                "artifact_kind": str(source.get("artifact_kind")),
                "import_strategy": "build123d.import_step",
                "label": str(document.get("source_identity", {}).get("display_name") or part_id),
                "source_type": str(source.get("source_type", "")),
                "retrieval_status": str(source.get("retrieval_status", "")),
                "placement_policy": "replace matching layout proxy primitives; imported at source STEP origin until downstream alignment applies locked facts",
            }
            if source.get("sha256"):
                entry["sha256"] = str(source.get("sha256"))
            sourced_parts.append(entry)
        return sourced_parts

    def resolve_import_locator(self, locator: str) -> str:
        parsed = urlparse(locator)
        if parsed.scheme in {"http", "https"}:
            return locator
        path = Path(locator).expanduser()
        if path.is_absolute():
            return str(path)
        base = self.package.parent if self.package.is_file() else self.package
        package_relative = (base / path).resolve()
        if package_relative.exists():
            return str(package_relative)
        repo_relative = (self.repo_root / path).resolve()
        if repo_relative.exists():
            return str(repo_relative)
        return str(package_relative)

    def load_feature_plan(self) -> dict[str, Any] | None:
        paths = [self.package] if self.package.is_file() else sorted(self.package.rglob("*.json"))
        plans: list[dict[str, Any]] = []
        for path in paths:
            document = self.load_json(path)
            if not isinstance(document, dict) or document.get("kind") != "cad_spec":
                continue
            extensions = document.get("extensions", {})
            if isinstance(extensions, dict) and isinstance(extensions.get("cad_feature_plan"), dict):
                plans.append(extensions["cad_feature_plan"])
        if len(plans) > 1:
            self.error(self.package, "source export supports exactly one cad_spec.extensions.cad_feature_plan")
            return None
        return plans[0] if plans else None

    def build_manifest(
        self,
        scene: dict[str, Any],
        source_path: Path,
        manifest_path: Path,
        sourced_parts: list[dict[str, str]],
        feature_plan: dict[str, Any] | None,
    ) -> dict[str, Any]:
        primitive_ids = [
            str(primitive["id"])
            for primitive in scene.get("primitives", [])
            if isinstance(primitive, dict) and isinstance(primitive.get("id"), str)
        ]
        extensions: dict[str, Any] = {
            "exporter": "tools/export_cad_source.py",
            "note": "Source-level export imports source-locked STEP/STP parts when geometry references are present; final STEP generation still requires a downstream build123d runtime.",
            "sourced_parts_count": len(sourced_parts),
        }
        if feature_plan is not None:
            extensions["cad_feature_plan"] = feature_plan
            extensions["feature_plan_status"] = "carried_to_build123d_source"
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
            "extensions": extensions,
        }


def render_build123d_source(
    scene: dict[str, Any],
    sourced_parts: list[dict[str, str]] | None = None,
    feature_plan: dict[str, Any] | None = None,
) -> str:
    sourced_parts = sourced_parts or []
    sourced_part_ids = {str(part.get("part_id")) for part in sourced_parts}
    feature_part_ids = {
        str(part.get("part_id"))
        for part in (feature_plan or {}).get("parts", [])
        if isinstance(part, dict) and part.get("part_id")
    }
    primitives = [
        primitive
        for primitive in scene.get("primitives", [])
        if isinstance(primitive, dict)
        and isinstance(primitive.get("id"), str)
        and str(primitive.get("part_id", "")) not in sourced_part_ids
        and str(primitive.get("part_id", "")) not in feature_part_ids
    ]
    primitive_literal = repr(primitives)
    sourced_literal = repr(sourced_parts)
    feature_literal = repr(feature_plan or {})
    locked_literal = repr(scene.get("locked_layout_facts", []))
    inspection_literal = repr(scene.get("inspection_targets", []))
    scene_id = scene.get("id", "unknown_scene")
    spec_id = scene.get("source_spec_id", "unknown_spec")
    return f'''"""Generated Zen CAD layout proxy source.

This file is generated from a kernel-neutral layout proxy scene.
It is a source adapter for downstream CAD generation, not final CAD evidence.
"""
from __future__ import annotations

import math

ZEN_CAD_SCENE_ID = {scene_id!r}
ZEN_CAD_SOURCE_SPEC_ID = {spec_id!r}
ZEN_CAD_PRIMITIVES = {primitive_literal}
ZEN_CAD_SOURCED_PARTS = {sourced_literal}
ZEN_CAD_FEATURE_PLAN = {feature_literal}
ZEN_CAD_LOCKED_LAYOUT_FACTS = {locked_literal}
ZEN_CAD_INSPECTION_TARGETS = {inspection_literal}


def _dimension_value(dimensions, *names, default=1.0):
    for name in names:
        item = dimensions.get(name)
        if isinstance(item, dict) and isinstance(item.get("value"), (int, float)):
            return float(item["value"])
    return float(default)


def _feature_value(mapping, *names, default=0.0):
    if not isinstance(mapping, dict):
        return float(default)
    for name in names:
        item = mapping.get(name)
        if isinstance(item, dict) and isinstance(item.get("value"), (int, float)):
            return float(item["value"])
        if isinstance(item, (int, float)):
            return float(item)
    return float(default)


def _feature_list(part):
    features = part.get("features", [])
    return [feature for feature in features if isinstance(feature, dict)]


def _first_feature(part, feature_type, edge_selector=None):
    for feature in _feature_list(part):
        if feature.get("type") != feature_type:
            continue
        if edge_selector is not None and feature.get("edges") != edge_selector:
            continue
        return feature
    return None


def _placement_tuple(raw, fallback=(0.0, 0.0, 0.0)):
    if isinstance(raw, dict):
        return (
            float(raw.get("x", fallback[0])),
            float(raw.get("y", fallback[1])),
            float(raw.get("z", fallback[2])),
        )
    if isinstance(raw, (list, tuple)) and len(raw) >= 3:
        return (float(raw[0]), float(raw[1]), float(raw[2]))
    if isinstance(raw, (list, tuple)) and len(raw) >= 2:
        return (float(raw[0]), float(raw[1]), fallback[2])
    return fallback


def _apply_placement(shape, placement, label):
    if isinstance(placement, dict):
        position = _placement_tuple(placement.get("position"), (0.0, 0.0, 0.0))
        rotation = _placement_tuple(placement.get("rotation"), (0.0, 0.0, 0.0))
        if position != (0.0, 0.0, 0.0) or rotation != (0.0, 0.0, 0.0):
            from build123d import Location

            shape = Location(position, rotation) * shape
    try:
        shape.label = str(label)
    except Exception:
        pass
    return shape


def _make_chamfered_box(width, depth, height, chamfer):
    from build123d import Box, Plane, Pos, Solid, Wire

    if chamfer <= 0 or chamfer >= min(width, depth, height) / 2.0:
        return Box(width, depth, height)
    core_height = max(height - chamfer, 0.1)
    core = Pos(0, 0, -chamfer / 2.0) * Box(width, depth, core_height)
    lower_z = height / 2.0 - chamfer
    upper_z = height / 2.0
    lower = Wire.make_rect(width, depth, plane=Plane(origin=(0, 0, lower_z)))
    upper = Wire.make_rect(width - 2.0 * chamfer, depth - 2.0 * chamfer, plane=Plane(origin=(0, 0, upper_z)))
    cap = Solid.make_loft([lower, upper], ruled=True)
    return core + cap


def _make_filleted_cylinder(radius, height, fillet_radius):
    from build123d import Cylinder, Pos, Solid

    if fillet_radius <= 0 or fillet_radius >= min(radius, height / 2.0):
        return Cylinder(radius, height)
    core = Cylinder(radius - fillet_radius, height)
    side = Cylinder(radius, max(height - 2.0 * fillet_radius, 0.1))
    top = Pos(0, 0, height / 2.0 - fillet_radius) * Solid.make_torus(radius - fillet_radius, fillet_radius)
    bottom = Pos(0, 0, -height / 2.0 + fillet_radius) * Solid.make_torus(radius - fillet_radius, fillet_radius)
    return core + side + top + bottom


def _make_gear(part):
    from build123d import Box, Cylinder, Location

    dimensions = part.get("dimensions", {{}})
    root_radius = _feature_value(dimensions, "root_diameter", default=24.0) / 2.0
    outer_radius = _feature_value(dimensions, "outer_diameter", default=root_radius * 2.25) / 2.0
    thickness = _feature_value(dimensions, "thickness", "height", default=6.0)
    tooth_count = int(_feature_value(dimensions, "tooth_count", default=16))
    tooth_depth = max(outer_radius - root_radius, 0.1)
    tooth_width = _feature_value(dimensions, "tooth_width", default=max(1.0, 2.0 * math.pi * root_radius / max(tooth_count, 1) * 0.55))
    shape = Cylinder(root_radius, thickness)
    for index in range(max(tooth_count, 0)):
        angle = 360.0 * index / tooth_count
        radians = math.radians(angle)
        center = (root_radius + tooth_depth / 2.0) * math.cos(radians), (root_radius + tooth_depth / 2.0) * math.sin(radians), 0.0
        tooth = Location(center, (0.0, 0.0, angle)) * Box(tooth_depth, tooth_width, thickness)
        shape = shape + tooth
    return shape


def _make_internal_ring_gear(part):
    from build123d import Box, Cylinder, Location

    dimensions = part.get("dimensions", {{}})
    outer_radius = _feature_value(dimensions, "outer_diameter", default=105.0) / 2.0
    inner_radius = _feature_value(dimensions, "inner_diameter", default=72.0) / 2.0
    thickness = _feature_value(dimensions, "thickness", "height", default=6.0)
    tooth_count = int(_feature_value(dimensions, "tooth_count", default=48))
    notch_depth = _feature_value(dimensions, "tooth_depth", default=2.0)
    notch_width = _feature_value(dimensions, "tooth_width", default=max(1.0, 2.0 * math.pi * inner_radius / max(tooth_count, 1) * 0.45))
    shape = Cylinder(outer_radius, thickness) - Cylinder(inner_radius, thickness + 2.0)
    for index in range(max(tooth_count, 0)):
        angle = 360.0 * index / tooth_count
        radians = math.radians(angle)
        center = (inner_radius + notch_depth / 2.0) * math.cos(radians), (inner_radius + notch_depth / 2.0) * math.sin(radians), 0.0
        notch = Location(center, (0.0, 0.0, angle)) * Box(notch_depth, notch_width, thickness + 2.0)
        shape = shape - notch
    return shape


def _make_feature_base(part):
    from build123d import Box, Cylinder

    base = part.get("base", part.get("type", "box"))
    dimensions = part.get("dimensions", {{}})
    if base == "box":
        width = _feature_value(dimensions, "width", "length", "x", default=10.0)
        depth = _feature_value(dimensions, "depth", "y", default=width)
        height = _feature_value(dimensions, "height", "thickness", "z", default=5.0)
        chamfer = _first_feature(part, "edge_chamfer", "top_outer_perimeter")
        chamfer_size = _feature_value(chamfer or {{}}, "size", "length", default=0.0)
        return _make_chamfered_box(width, depth, height, chamfer_size)
    if base == "cylinder":
        radius = _feature_value(dimensions, "radius", default=0.0)
        if radius <= 0:
            radius = _feature_value(dimensions, "diameter", "outer_diameter", default=10.0) / 2.0
        height = _feature_value(dimensions, "height", "thickness", default=5.0)
        fillet = _first_feature(part, "edge_fillet", "outside_circular_edges")
        fillet_radius = _feature_value(fillet or {{}}, "radius", default=0.0)
        return _make_filleted_cylinder(radius, height, fillet_radius)
    if base == "gear":
        return _make_gear(part)
    if base == "internal_ring_gear":
        return _make_internal_ring_gear(part)
    return Box(8.0, 8.0, 8.0)


def _hole_cut(axis, diameter, depth):
    from build123d import Cylinder, Location

    cut = Cylinder(diameter / 2.0, depth)
    if axis == "x":
        return Location((0.0, 0.0, 0.0), (0.0, 90.0, 0.0)) * cut
    if axis == "y":
        return Location((0.0, 0.0, 0.0), (90.0, 0.0, 0.0)) * cut
    return cut


def _cut_hole(shape, feature, base_dimensions, default_position=(0.0, 0.0, 0.0)):
    from build123d import Location

    diameter = _feature_value(feature, "diameter", "hole_diameter", "bore_diameter", default=3.0)
    axis = str(feature.get("axis", "z")).lower()
    default_depth = _feature_value(base_dimensions, "height", "thickness", "depth", default=10.0) + 4.0
    depth = _feature_value(feature, "depth", default=default_depth)
    position = _placement_tuple(feature.get("position"), default_position)
    return shape - (Location(position) * _hole_cut(axis, diameter, depth))


def _bolt_circle_positions(feature):
    count = int(_feature_value(feature, "count", default=0))
    radius = _feature_value(feature, "radius", default=0.0)
    if radius <= 0:
        radius = _feature_value(feature, "bolt_circle_diameter", "circle_diameter", default=0.0) / 2.0
    start_angle = _feature_value(feature, "start_angle", default=0.0)
    return [
        (
            radius * math.cos(math.radians(start_angle + 360.0 * index / max(count, 1))),
            radius * math.sin(math.radians(start_angle + 360.0 * index / max(count, 1))),
            0.0,
        )
        for index in range(max(count, 0))
    ]


def _apply_features(shape, part):
    base_dimensions = part.get("dimensions", {{}})
    for feature in _feature_list(part):
        feature_type = feature.get("type")
        if feature_type in {{"edge_chamfer", "edge_fillet", "radial_tooth_pattern", "internal_tooth_pattern"}}:
            continue
        if feature_type in {{"through_hole", "central_bore"}}:
            shape = _cut_hole(shape, feature, base_dimensions)
        elif feature_type == "through_hole_pattern":
            positions = feature.get("positions", [])
            if positions:
                for position in positions:
                    shape = _cut_hole(shape, feature, base_dimensions, _placement_tuple(position))
            else:
                for position in _bolt_circle_positions(feature):
                    shape = _cut_hole(shape, feature, base_dimensions, position)
        elif feature_type == "bolt_circle_pattern":
            for position in _bolt_circle_positions(feature):
                shape = _cut_hole(shape, feature, base_dimensions, position)
    return shape


def _make_feature_part(part):
    shape = _make_feature_base(part)
    shape = _apply_features(shape, part)
    return _apply_placement(shape, part.get("placement"), part.get("part_id", "feature_part"))


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
    feature_children = [
        _make_feature_part(part)
        for part in ZEN_CAD_FEATURE_PLAN.get("parts", [])
        if isinstance(part, dict)
    ]
    proxy_children = [_make_primitive(primitive) for primitive in ZEN_CAD_PRIMITIVES]
    children = sourced_children + feature_children + proxy_children
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


def geometry_source_priority(source: dict[str, Any]) -> tuple[int, int, str]:
    locator = str(source.get("locator", ""))
    parsed = urlparse(locator)
    is_remote = parsed.scheme in {"http", "https"}
    retrieval_status = str(source.get("retrieval_status", ""))
    source_type = str(source.get("source_type", ""))
    has_sha = bool(source.get("sha256"))
    local_score = 0 if not is_remote and source_type in {"user_provided", "project_file"} else 1
    checksum_score = 0 if retrieval_status == "checksum_recorded" and has_sha else 1
    return (local_score, checksum_score, locator)


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
