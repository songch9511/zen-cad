#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from validate_contract import ContractValidator, Issue


SCHEMA_VERSION = "0.8.0"


@dataclass
class CadArtifactResult:
    step_path: Path
    report_path: Path


class CadArtifactGenerator:
    def __init__(self, repo_root: Path, source: Path, manifest: Path, out: Path | None, report: Path | None) -> None:
        self.repo_root = repo_root
        self.source = source
        self.manifest = manifest
        self.out = out
        self.report = report
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

    def generate(self) -> CadArtifactResult | None:
        validator = ContractValidator(self.repo_root)
        validator.validate_repo()
        validator.validate_package(self.manifest)
        if validator.issues:
            self.issues.extend(validator.issues)
            return None

        manifest = self.load_json(self.manifest)
        if not isinstance(manifest, dict):
            return None
        if manifest.get("target_harness") != "build123d":
            self.error(self.manifest, "CAD artifact generation currently requires a build123d source manifest")
            return None

        source_path = self.source.resolve()
        if not source_path.exists():
            self.error(source_path, "source file does not exist")
            return None
        if str(source_path) != str(Path(str(manifest.get("source_path", ""))).resolve()):
            self.error(self.source, "source path does not match manifest.source_path")
            return None

        step_path = self.resolve_step_path(manifest)
        report_path = self.resolve_report_path(step_path)
        step_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)

        checks: list[dict[str, Any]] = []
        skipped_checks: list[dict[str, str]] = []
        limitations: list[str] = [
            "Generated STEP is a layout/detail candidate from generated build123d source, not engineering certification.",
        ]

        try:
            from build123d import export_step, import_step
        except Exception as exc:
            self.error("<python>", f"build123d import failed: {exc}")
            return None

        module = self.load_source_module(source_path)
        if module is None:
            return None

        gen_step = getattr(module, "gen_step", None)
        has_gen_step = callable(gen_step)
        checks.append(
            check_result(
                "source_has_gen_step",
                "source",
                has_gen_step,
                "source contains callable gen_step()" if has_gen_step else "source missing callable gen_step()",
            )
        )
        if not has_gen_step:
            self.write_report(report_path, manifest, step_path, checks, skipped_checks, limitations)
            return CadArtifactResult(step_path=step_path, report_path=report_path)

        manifest_feature_plan = {}
        if isinstance(manifest.get("extensions"), dict) and isinstance(manifest["extensions"].get("cad_feature_plan"), dict):
            manifest_feature_plan = manifest["extensions"]["cad_feature_plan"]
        source_feature_plan = getattr(module, "ZEN_CAD_FEATURE_PLAN", {})
        feature_checks, feature_limitations = feature_plan_checks(
            manifest_feature_plan,
            source_feature_plan if isinstance(source_feature_plan, dict) else {},
        )
        checks.extend(feature_checks)
        limitations.extend(feature_limitations)

        try:
            shape = gen_step()
        except Exception as exc:
            checks.append(check_result("gen_step_executes", "source", False, f"gen_step() raised {type(exc).__name__}: {exc}"))
            self.write_report(report_path, manifest, step_path, checks, skipped_checks, limitations)
            return CadArtifactResult(step_path=step_path, report_path=report_path)

        checks.append(check_result("gen_step_executes", "source", True, f"gen_step() returned {type(shape).__name__}"))
        checks.append(
            check_result(
                "gen_step_returns_shape",
                "source",
                hasattr(shape, "bounding_box"),
                f"returned object has bounding_box={hasattr(shape, 'bounding_box')}",
            )
        )

        export_ok = False
        if hasattr(shape, "bounding_box"):
            try:
                export_ok = bool(export_step(shape, str(step_path)))
            except Exception as exc:
                checks.append(check_result("step_export_succeeds", "step", False, f"export_step raised {type(exc).__name__}: {exc}"))
            else:
                checks.append(check_result("step_export_succeeds", "step", export_ok, f"export_step returned {export_ok}"))
        else:
            checks.append(check_result("step_export_succeeds", "step", False, "returned object cannot be exported as a build123d shape"))

        file_size = step_path.stat().st_size if step_path.exists() else 0
        checks.append(check_result("step_file_exists", "step", step_path.exists(), f"STEP path: {step_path}"))
        checks.append(check_result("step_file_nonempty", "step", file_size > 0, f"STEP file size: {file_size} bytes"))

        imported_shape = None
        if export_ok and file_size > 0:
            try:
                imported_shape = import_step(str(step_path))
            except Exception as exc:
                checks.append(check_result("step_import_succeeds", "step", False, f"import_step raised {type(exc).__name__}: {exc}"))
            else:
                checks.append(check_result("step_import_succeeds", "step", True, f"import_step returned {type(imported_shape).__name__}"))
        else:
            checks.append(check_result("step_import_succeeds", "step", False, "STEP export did not produce an importable file"))

        if imported_shape is not None:
            valid = call_bool(imported_shape, "is_valid")
            checks.append(check_result("step_shape_valid", "step", valid is True, f"is_valid={valid}"))
            bbox = safe_bbox(imported_shape)
            checks.append(
                check_result(
                    "step_bbox_nonzero",
                    "bbox",
                    bool(bbox and all(value > 0 for value in bbox["size"])),
                    f"bbox={bbox}" if bbox else "bounding box unavailable",
                )
            )
            volume = safe_volume(imported_shape)
            checks.append(
                check_result(
                    "step_volume_positive",
                    "volume",
                    volume is not None and volume > 0,
                    f"volume={volume}" if volume is not None else "volume unavailable",
                )
            )
            checks.extend(feature_geometry_checks(source_feature_plan if isinstance(source_feature_plan, dict) else {}, bbox, volume))
        else:
            checks.append(check_result("step_shape_valid", "step", False, "STEP was not imported"))
            checks.append(check_result("step_bbox_nonzero", "bbox", False, "STEP was not imported"))
            checks.append(check_result("step_volume_positive", "volume", False, "STEP was not imported"))

        sourced_parts = [part for part in manifest.get("sourced_parts", []) if isinstance(part, dict)]
        if sourced_parts:
            skipped_checks.append(
                {
                    "check_id": "sourced_step_alignment",
                    "reason": "Generated STEP includes source-locked imports, but this first-pass generator does not prove imported supplier geometry placement against mating datums.",
                }
            )
            limitations.append(
                "Source-locked imported STEP placement still needs downstream datum/mate inspection before final claims."
            )

        result = self.write_report(report_path, manifest, step_path, checks, skipped_checks, limitations)
        output_validator = ContractValidator(self.repo_root)
        output_validator.validate_package(report_path)
        if output_validator.issues:
            self.issues.extend(output_validator.issues)
            return None
        return result

    def resolve_step_path(self, manifest: dict[str, Any]) -> Path:
        if self.out is not None:
            return self.out
        expected = str(manifest.get("expected_primary_artifact", "")).strip()
        if expected:
            return Path(expected).expanduser()
        return self.source.with_suffix(".step")

    def resolve_report_path(self, step_path: Path) -> Path:
        if self.report is not None:
            return self.report
        return step_path.with_suffix(".generation.inspection_report.json")

    def load_source_module(self, source_path: Path) -> Any | None:
        module_name = f"_zen_cad_generated_{abs(hash(source_path))}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, source_path)
            if spec is None or spec.loader is None:
                self.error(source_path, "could not create import spec for source")
                return None
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            previous_dont_write_bytecode = sys.dont_write_bytecode
            sys.dont_write_bytecode = True
            try:
                spec.loader.exec_module(module)
            finally:
                sys.dont_write_bytecode = previous_dont_write_bytecode
            return module
        except Exception as exc:
            self.error(source_path, f"source import failed: {type(exc).__name__}: {exc}")
            return None

    def write_report(
        self,
        report_path: Path,
        manifest: dict[str, Any],
        step_path: Path,
        checks: list[dict[str, Any]],
        skipped_checks: list[dict[str, str]],
        limitations: list[str],
    ) -> CadArtifactResult:
        failed = [check for check in checks if check["status"] == "failed"]
        partial = [check for check in checks if check["status"] == "partial"]
        status = "failed" if failed else "partial" if partial or skipped_checks else "passed"
        report = {
            "schema_version": SCHEMA_VERSION,
            "kind": "inspection_report",
            "id": f"{manifest['id']}.cad_generation_report",
            "spec_id": str(manifest.get("source_scene_id", "unknown_scene")),
            "artifact": {
                "path": str(step_path),
                "kind": "step",
            },
            "status": status,
            "checks": checks,
            "skipped_checks": skipped_checks,
            "repair_attempts": [],
            "proceed_recommendation": "needs_repair" if failed else "ready_for_proceed_review",
            "limitations": limitations,
            "extensions": {
                "generator": "tools/generate_cad_artifact.py",
                "source": str(self.source),
                "manifest": str(self.manifest),
            },
        }
        write_json(report_path, report)
        return CadArtifactResult(step_path=step_path, report_path=report_path)


def check_result(check_id: str, check_type: str, passed: bool, evidence: str) -> dict[str, Any]:
    return check_result_status(check_id, check_type, "passed" if passed else "failed", evidence)


def check_result_status(check_id: str, check_type: str, status: str, evidence: str) -> dict[str, Any]:
    return {
        "check_id": check_id,
        "check_type": check_type,
        "status": status,
        "evidence": evidence,
        "locked_fact_refs": [],
    }


SUPPORTED_FEATURE_TYPES = {
    "bolt_circle_pattern",
    "central_bore",
    "edge_chamfer",
    "edge_fillet",
    "internal_tooth_pattern",
    "radial_tooth_pattern",
    "through_hole",
    "through_hole_pattern",
}


def feature_plan_checks(
    manifest_feature_plan: dict[str, Any],
    source_feature_plan: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    if not manifest_feature_plan and not source_feature_plan:
        return [], []

    manifest_parts = feature_part_ids(manifest_feature_plan)
    source_parts = feature_part_ids(source_feature_plan)
    feature_types = feature_types_from_plan(source_feature_plan)
    unsupported = sorted(feature_types - SUPPORTED_FEATURE_TYPES)
    checks = [
        check_result(
            "cad_feature_plan_carried",
            "source",
            manifest_feature_plan == source_feature_plan,
            f"manifest feature parts={len(manifest_parts)}; source feature parts={len(source_parts)}",
        ),
        check_result(
            "cad_feature_parts_declared",
            "source",
            bool(source_parts),
            f"feature parts={sorted(source_parts)}",
        ),
        check_result(
            "cad_feature_types_supported",
            "source",
            not unsupported,
            f"feature types={sorted(feature_types)}; unsupported={unsupported}",
        ),
    ]

    grouped = grouped_feature_counts(source_feature_plan)
    if grouped["holes"]:
        checks.append(
            check_result(
                "cad_feature_holes_declared",
                "source",
                True,
                f"hole/bore feature declarations={grouped['holes']}",
            )
        )
    if grouped["patterns"]:
        checks.append(
            check_result(
                "cad_feature_patterns_declared",
                "source",
                True,
                f"pattern feature declarations={grouped['patterns']}",
            )
        )
    if grouped["chamfers"]:
        checks.append(
            check_result(
                "cad_feature_chamfers_declared",
                "source",
                True,
                f"chamfer feature declarations={grouped['chamfers']}",
            )
        )
    if grouped["fillets"]:
        checks.append(
            check_result_status(
                "cad_feature_fillets_declared",
                "source",
                "partial",
                f"fillet feature declarations={grouped['fillets']}; generated source uses a torus-based edge-round approximation for supported cylinders",
            )
        )

    limitations: list[str] = []
    if grouped["fillets"]:
        limitations.append(
            "Fillet features are generated with a cylinder/torus approximation because this local build123d/OCP runtime cannot reliably enumerate edges for selector-based filleting."
        )
    if grouped["chamfers"]:
        limitations.append(
            "Chamfer features are feature-plan driven; rectangular top perimeter chamfers use lofted tapered geometry instead of selector-based edge operations."
        )
    return checks, limitations


def feature_part_ids(feature_plan: dict[str, Any]) -> set[str]:
    return {
        str(part.get("part_id"))
        for part in feature_plan.get("parts", [])
        if isinstance(part, dict) and part.get("part_id")
    }


def feature_types_from_plan(feature_plan: dict[str, Any]) -> set[str]:
    types: set[str] = set()
    for part in feature_plan.get("parts", []):
        if not isinstance(part, dict):
            continue
        base = part.get("base")
        if base == "gear":
            types.add("radial_tooth_pattern")
        if base == "internal_ring_gear":
            types.add("internal_tooth_pattern")
        for feature in part.get("features", []):
            if isinstance(feature, dict) and isinstance(feature.get("type"), str):
                types.add(feature["type"])
    return types


def grouped_feature_counts(feature_plan: dict[str, Any]) -> dict[str, int]:
    counts = {"holes": 0, "patterns": 0, "chamfers": 0, "fillets": 0}
    for feature_type in feature_types_from_plan(feature_plan):
        if feature_type in {"central_bore", "through_hole", "through_hole_pattern"}:
            counts["holes"] += 1
        if feature_type in {"bolt_circle_pattern", "through_hole_pattern", "radial_tooth_pattern", "internal_tooth_pattern"}:
            counts["patterns"] += 1
        if feature_type == "edge_chamfer":
            counts["chamfers"] += 1
        if feature_type == "edge_fillet":
            counts["fillets"] += 1
    return counts


def feature_geometry_checks(feature_plan: dict[str, Any], bbox: dict[str, list[float]] | None, volume: float | None) -> list[dict[str, Any]]:
    if not feature_plan:
        return []
    checks: list[dict[str, Any]] = []
    expected_bbox = expected_feature_plan_bbox(feature_plan)
    if expected_bbox and bbox:
        expected_size = expected_bbox["size"]
        actual_size = bbox["size"]
        deltas = [abs(actual - expected) for actual, expected in zip(actual_size, expected_size)]
        tolerances = [max(0.25, expected * 0.01) for expected in expected_size]
        checks.append(
            check_result(
                "cad_feature_bbox_matches_plan",
                "bbox",
                all(delta <= tolerance for delta, tolerance in zip(deltas, tolerances)),
                f"actual_size={actual_size}; expected_size={expected_size}; deltas={deltas}; tolerances={tolerances}",
            )
        )
    checks.append(
        check_result(
            "cad_feature_dimensions_positive",
            "source",
            feature_dimensions_positive(feature_plan),
            "all numeric dimensions, diameters, counts, radii, and placements are positive/finite where required",
        )
    )
    pattern_summary = feature_pattern_summary(feature_plan)
    if pattern_summary["patterns"]:
        checks.append(
            check_result(
                "cad_feature_pattern_counts_valid",
                "source",
                pattern_summary["valid"],
                f"patterns={pattern_summary['patterns']}",
            )
        )
    radius_summary = placement_radius_summary(feature_plan)
    if radius_summary["count"] >= 2:
        checks.append(
            check_result(
                "cad_feature_placement_radii_consistent",
                "distance",
                radius_summary["max_delta"] <= 0.05,
                f"radii={radius_summary['radii']}; max_delta={radius_summary['max_delta']}",
            )
        )
    if volume is not None:
        base_volume = approximate_base_volume(feature_plan)
        if base_volume > 0 and feature_types_from_plan(feature_plan) & {"central_bore", "through_hole", "through_hole_pattern", "bolt_circle_pattern"}:
            checks.append(
                check_result(
                    "cad_feature_cut_volume_below_uncut_estimate",
                    "volume",
                    volume < base_volume,
                    f"actual_volume={volume}; approximate_uncut_volume={base_volume}",
                )
            )
    return checks


def expected_feature_plan_bbox(feature_plan: dict[str, Any]) -> dict[str, list[float]] | None:
    bounds: list[tuple[list[float], list[float]]] = []
    for part in feature_plan.get("parts", []):
        if not isinstance(part, dict):
            continue
        size = feature_part_transformed_size(part)
        if size is None:
            continue
        position = placement_position(part.get("placement", {}))
        minimum = [position[index] - size[index] / 2.0 for index in range(3)]
        maximum = [position[index] + size[index] / 2.0 for index in range(3)]
        bounds.append((minimum, maximum))
    if not bounds:
        return None
    minimum = [min(item[0][index] for item in bounds) for index in range(3)]
    maximum = [max(item[1][index] for item in bounds) for index in range(3)]
    return {"min": minimum, "max": maximum, "size": [maximum[index] - minimum[index] for index in range(3)]}


def feature_part_size(part: dict[str, Any]) -> list[float] | None:
    dimensions = part.get("dimensions", {})
    base = str(part.get("base", part.get("type", "box")))
    if base == "box":
        return [
            feature_number(dimensions, "width", "length", "x", default=10.0),
            feature_number(dimensions, "depth", "y", default=feature_number(dimensions, "width", "length", "x", default=10.0)),
            feature_number(dimensions, "height", "thickness", "z", default=5.0),
        ]
    if base in {"cylinder", "gear", "internal_ring_gear"}:
        diameter = feature_number(dimensions, "diameter", "outer_diameter", default=10.0)
        height = feature_number(dimensions, "height", "thickness", default=5.0)
        return [diameter, diameter, height]
    return None


def feature_part_transformed_size(part: dict[str, Any]) -> list[float] | None:
    size = feature_part_size(part)
    if size is None:
        return None
    rotation = placement_rotation(part.get("placement", {}))
    if rotation == [0.0, 0.0, 0.0]:
        return size
    return rotated_axis_aligned_size(size, rotation)


def placement_position(placement: Any) -> list[float]:
    if isinstance(placement, dict):
        raw = placement.get("position", [0.0, 0.0, 0.0])
    else:
        raw = [0.0, 0.0, 0.0]
    if isinstance(raw, dict):
        return [float(raw.get(axis, 0.0)) for axis in ("x", "y", "z")]
    if isinstance(raw, (list, tuple)):
        values = [float(item) for item in raw[:3]]
        return values + [0.0] * (3 - len(values))
    return [0.0, 0.0, 0.0]


def placement_rotation(placement: Any) -> list[float]:
    if isinstance(placement, dict):
        raw = placement.get("rotation", [0.0, 0.0, 0.0])
    else:
        raw = [0.0, 0.0, 0.0]
    if isinstance(raw, dict):
        return [float(raw.get(axis, 0.0)) for axis in ("x", "y", "z")]
    if isinstance(raw, (list, tuple)):
        values = [float(item) for item in raw[:3]]
        return values + [0.0] * (3 - len(values))
    return [0.0, 0.0, 0.0]


def rotated_axis_aligned_size(size: list[float], rotation_deg: list[float]) -> list[float]:
    import math

    rx, ry, rz = [math.radians(value) for value in rotation_deg]
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)

    # Match the generated source's Euler-style placement closely enough for
    # feature-plan bbox inspection: R = Rz * Ry * Rx, then use abs(R) * size.
    matrix = [
        [cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx],
        [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx],
        [-sy, cy * sx, cy * cx],
    ]
    return [
        sum(abs(matrix[row][col]) * size[col] for col in range(3))
        for row in range(3)
    ]


def feature_number(mapping: Any, *names: str, default: float = 0.0) -> float:
    if not isinstance(mapping, dict):
        return float(default)
    for name in names:
        value = mapping.get(name)
        if isinstance(value, dict) and isinstance(value.get("value"), (int, float)):
            return float(value["value"])
        if isinstance(value, (int, float)):
            return float(value)
    return float(default)


def feature_dimensions_positive(feature_plan: dict[str, Any]) -> bool:
    for part in feature_plan.get("parts", []):
        if not isinstance(part, dict):
            return False
        size = feature_part_size(part)
        if size is None or any(value <= 0 for value in size):
            return False
        for feature in part.get("features", []):
            if not isinstance(feature, dict):
                return False
            feature_type = feature.get("type")
            for key in ["diameter", "hole_diameter", "bore_diameter", "radius", "bolt_circle_diameter", "circle_diameter", "size", "length", "depth"]:
                if key in feature and feature_number(feature, key, default=1.0) <= 0:
                    return False
            if feature_type in {"through_hole_pattern", "bolt_circle_pattern"} and int(feature_number(feature, "count", default=len(feature.get("positions", [])))) <= 0 and not feature.get("positions"):
                return False
    return True


def feature_pattern_summary(feature_plan: dict[str, Any]) -> dict[str, Any]:
    patterns: list[dict[str, Any]] = []
    valid = True
    for part in feature_plan.get("parts", []):
        if not isinstance(part, dict):
            continue
        for feature in part.get("features", []):
            if not isinstance(feature, dict) or feature.get("type") not in {"through_hole_pattern", "bolt_circle_pattern"}:
                continue
            count = int(feature_number(feature, "count", default=0))
            positions = feature.get("positions", [])
            position_count = len(positions) if isinstance(positions, list) else 0
            expected = count or position_count
            actual = position_count or count
            valid = valid and expected > 0 and actual == expected
            patterns.append({"part_id": part.get("part_id", ""), "type": feature.get("type"), "expected": expected, "actual": actual})
    return {"valid": valid, "patterns": patterns}


def placement_radius_summary(feature_plan: dict[str, Any]) -> dict[str, Any]:
    radii: list[float] = []
    for part in feature_plan.get("parts", []):
        if not isinstance(part, dict):
            continue
        part_id = str(part.get("part_id", ""))
        if not (part_id.startswith("planet_") or part_id.startswith("pin_")):
            continue
        position = placement_position(part.get("placement", {}))
        radius = (position[0] ** 2 + position[1] ** 2) ** 0.5
        if radius > 0:
            radii.append(round(radius, 4))
    if not radii:
        return {"count": 0, "radii": [], "max_delta": 0.0}
    return {"count": len(radii), "radii": radii, "max_delta": max(radii) - min(radii)}


def approximate_base_volume(feature_plan: dict[str, Any]) -> float:
    import math

    total = 0.0
    for part in feature_plan.get("parts", []):
        if not isinstance(part, dict):
            continue
        dimensions = part.get("dimensions", {})
        base = str(part.get("base", part.get("type", "box")))
        size = feature_part_size(part)
        if size is None:
            continue
        if base == "box":
            total += size[0] * size[1] * size[2]
        elif base in {"cylinder", "gear"}:
            total += math.pi * (size[0] / 2.0) ** 2 * size[2]
        elif base == "internal_ring_gear":
            outer = feature_number(dimensions, "outer_diameter", default=size[0])
            inner = feature_number(dimensions, "inner_diameter", default=0.0)
            total += math.pi * ((outer / 2.0) ** 2 - (inner / 2.0) ** 2) * size[2]
    return total


def call_bool(obj: object, method_name: str) -> bool | None:
    method = getattr(obj, method_name, None)
    if isinstance(method, bool):
        return method
    if not callable(method):
        return None
    try:
        return bool(method())
    except Exception:
        return None


def safe_bbox(shape: object) -> dict[str, list[float]] | None:
    try:
        bbox = shape.bounding_box()  # type: ignore[attr-defined]
        return {
            "min": vector_to_list(bbox.min),
            "max": vector_to_list(bbox.max),
            "size": vector_to_list(bbox.size),
        }
    except Exception:
        return None


def safe_volume(shape: object) -> float | None:
    try:
        value = getattr(shape, "volume")
        return float(value)
    except Exception:
        return None


def vector_to_list(vector: object) -> list[float]:
    return [float(getattr(vector, axis)) for axis in ("X", "Y", "Z")]


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a STEP artifact from Zen CAD build123d source.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1], help="Zen CAD repository root.")
    parser.add_argument("--source", type=Path, required=True, help="Generated build123d source containing gen_step().")
    parser.add_argument("--manifest", type=Path, required=True, help="cad_source_manifest.json for the generated source.")
    parser.add_argument("--out", type=Path, help="Output STEP path. Defaults to manifest.expected_primary_artifact.")
    parser.add_argument("--report", type=Path, help="Output inspection report path. Defaults beside the STEP.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    generator = CadArtifactGenerator(args.repo_root, args.source, args.manifest, args.out, args.report)
    result = generator.generate()
    if generator.issues:
        for issue in generator.issues:
            print(f"{issue.path}: {issue.message}", file=sys.stderr)
        return 1
    if result is None:
        print("CAD artifact generation failed", file=sys.stderr)
        return 1
    print(f"STEP artifact: {result.step_path}")
    print(f"Inspection report: {result.report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
