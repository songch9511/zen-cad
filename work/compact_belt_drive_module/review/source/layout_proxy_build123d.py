"""Generated Zen CAD layout proxy source.

This file is generated from a kernel-neutral layout proxy scene.
It is a source adapter for downstream CAD generation, not final CAD evidence.
"""
from __future__ import annotations

ZEN_CAD_SCENE_ID = 'compact_belt_drive_module.layout_proxy_scene'
ZEN_CAD_SOURCE_SPEC_ID = 'compact_belt_drive_module'
ZEN_CAD_PRIMITIVES = [
  {
    "derived_from": [
      "layout_contract"
    ],
    "dimensions": {
      "policy": "custom rectangular base plate envelope, 125 x 75 x 6 mm, with interface cut/axis markers only."
    },
    "fidelity": "layout_only",
    "frame": "base_plate_frame: origin at base plate lower-face center; XY footprint, +Z through 6 mm plate thickness.",
    "id": "base_plate.proxy_envelope",
    "notes": "No interface signature was attached; downstream CAD must use the spec envelope.",
    "part_id": "base_plate",
    "type": "envelope"
  },
  {
    "derived_from": [
      "motor.nema_17.layout"
    ],
    "dimensions": {
      "body_length": {
        "status": "assumed",
        "units": "mm",
        "value": 40.0
      },
      "body_width": {
        "status": "standard",
        "units": "mm",
        "value": 42.3
      },
      "face_size": {
        "status": "standard",
        "units": "mm",
        "value": 42.3
      }
    },
    "fidelity": "layout_only",
    "frame": "motor_frame: shaft axis +Z at X=-35 mm, Y=0 mm; front face flush to base_plate_bottom_plane; body extends -Z.",
    "id": "nema17_motor.motor_body",
    "notes": "Motor body is a box proxy; shaft and connector details remain confirm-before-final.",
    "part_id": "nema17_motor",
    "type": "box"
  },
  {
    "derived_from": [
      "motor.nema_17.layout"
    ],
    "dimensions": {},
    "fidelity": "layout_only",
    "frame": "motor_frame: shaft axis +Z at X=-35 mm, Y=0 mm; front face flush to base_plate_bottom_plane; body extends -Z.",
    "id": "nema17_motor.shaft_axis",
    "notes": "shaft_axis datum marker.",
    "part_id": "nema17_motor",
    "type": "axis"
  },
  {
    "derived_from": [
      "belt.gt2_6mm.layout"
    ],
    "dimensions": {
      "belt_width": {
        "status": "standard",
        "units": "mm",
        "value": 6.0
      },
      "pitch": {
        "status": "standard",
        "units": "mm",
        "value": 2.0
      }
    },
    "fidelity": "layout_only",
    "frame": "motor_pulley_frame: bore axis +Z coaxial with motor shaft, pitch plane XY at Z=13.5 mm, 20T pitch reference.",
    "id": "motor_pulley_20t_5mm.belt_mid_plane",
    "notes": "Belt proxy preserves pitch and belt mid-plane only.",
    "part_id": "motor_pulley_20t_5mm",
    "type": "plane"
  },
  {
    "derived_from": [
      "shaft_bore.8mm.layout"
    ],
    "dimensions": {
      "nominal_diameter": {
        "status": "assumed",
        "units": "mm",
        "value": 8.0
      }
    },
    "fidelity": "layout_only",
    "frame": "output_shaft_frame: shaft axis +Z at X=35 mm, Y=0 mm, crossing belt mid-plane at Z=13.5 mm.",
    "id": "output_shaft_8mm.shaft_or_bore",
    "notes": "Shaft/bore proxy preserves nominal coaxial interface.",
    "part_id": "output_shaft_8mm",
    "type": "cylinder"
  },
  {
    "derived_from": [
      "shaft_bore.8mm.layout"
    ],
    "dimensions": {},
    "fidelity": "layout_only",
    "frame": "output_shaft_frame: shaft axis +Z at X=35 mm, Y=0 mm, crossing belt mid-plane at Z=13.5 mm.",
    "id": "output_shaft_8mm.shaft_axis",
    "notes": "shaft_axis datum marker.",
    "part_id": "output_shaft_8mm",
    "type": "axis"
  },
  {
    "derived_from": [
      "belt.gt2_6mm.layout"
    ],
    "dimensions": {
      "belt_width": {
        "status": "standard",
        "units": "mm",
        "value": 6.0
      },
      "pitch": {
        "status": "standard",
        "units": "mm",
        "value": 2.0
      }
    },
    "fidelity": "layout_only",
    "frame": "output_pulley_frame: bore axis +Z coaxial with output shaft, pitch plane XY at Z=13.5 mm, 20T pitch reference.",
    "id": "output_pulley_20t_8mm.belt_mid_plane",
    "notes": "Belt proxy preserves pitch and belt mid-plane only.",
    "part_id": "output_pulley_20t_8mm",
    "type": "plane"
  },
  {
    "derived_from": [
      "shaft_bore.8mm.layout"
    ],
    "dimensions": {
      "nominal_diameter": {
        "status": "assumed",
        "units": "mm",
        "value": 8.0
      }
    },
    "fidelity": "layout_only",
    "frame": "output_pulley_frame: bore axis +Z coaxial with output shaft, pitch plane XY at Z=13.5 mm, 20T pitch reference.",
    "id": "output_pulley_20t_8mm.shaft_or_bore",
    "notes": "Shaft/bore proxy preserves nominal coaxial interface.",
    "part_id": "output_pulley_20t_8mm",
    "type": "cylinder"
  },
  {
    "derived_from": [
      "shaft_bore.8mm.layout"
    ],
    "dimensions": {},
    "fidelity": "layout_only",
    "frame": "output_pulley_frame: bore axis +Z coaxial with output shaft, pitch plane XY at Z=13.5 mm, 20T pitch reference.",
    "id": "output_pulley_20t_8mm.shaft_axis",
    "notes": "shaft_axis datum marker.",
    "part_id": "output_pulley_20t_8mm",
    "type": "axis"
  },
  {
    "derived_from": [
      "layout_contract"
    ],
    "dimensions": {
      "policy": "custom support block envelope with 608 bearing seat and M3 fastener axes; fillets and retainer details simplified."
    },
    "fidelity": "layout_only",
    "frame": "support_block_frame: origin at output shaft axis on top face of base plate; bearing pocket axis +Z.",
    "id": "bearing_support_block.proxy_envelope",
    "notes": "No interface signature was attached; downstream CAD must use the spec envelope.",
    "part_id": "bearing_support_block",
    "type": "envelope"
  },
  {
    "derived_from": [
      "belt.gt2_6mm.layout"
    ],
    "dimensions": {
      "belt_width": {
        "status": "standard",
        "units": "mm",
        "value": 6.0
      },
      "pitch": {
        "status": "standard",
        "units": "mm",
        "value": 2.0
      }
    },
    "fidelity": "layout_only",
    "frame": "belt_frame: belt centerline in XY plane at Z=13.5 mm, tangent to both pulley pitch circles.",
    "id": "gt2_belt_loop.belt_mid_plane",
    "notes": "Belt proxy preserves pitch and belt mid-plane only.",
    "part_id": "gt2_belt_loop",
    "type": "plane"
  }
]
ZEN_CAD_SOURCED_PARTS = [
  {
    "artifact_kind": "step",
    "import_strategy": "build123d.import_step",
    "label": "step.parts 608ZZ ball bearing STEP",
    "locator": "https://media.githubusercontent.com/media/earthtojake/step.parts/c8616cd125a52ec820cf548440c3842f17f82486/catalog/step/bearing_608zz.step",
    "part_id": "bearing_608",
    "placement_policy": "replace matching layout proxy primitives; imported at source STEP origin until downstream alignment applies locked facts",
    "source_lock_id": "compact_belt_drive_module.bearing_608.source_lock",
    "source_type": "other"
  },
  {
    "artifact_kind": "step",
    "import_strategy": "build123d.import_step",
    "label": "step.parts ISO 4762 socket head cap screw, M3 x 12 STEP",
    "locator": "https://media.githubusercontent.com/media/earthtojake/step.parts/c8616cd125a52ec820cf548440c3842f17f82486/catalog/step/iso4762_socket_head_cap_screw_m3x12.step",
    "part_id": "bearing_support_fasteners_m3",
    "placement_policy": "replace matching layout proxy primitives; imported at source STEP origin until downstream alignment applies locked facts",
    "source_lock_id": "compact_belt_drive_module.bearing_support_fasteners_m3.source_lock",
    "source_type": "other"
  },
  {
    "artifact_kind": "step",
    "import_strategy": "build123d.import_step",
    "label": "step.parts ISO 4762 socket head cap screw, M3 x 10 STEP",
    "locator": "https://media.githubusercontent.com/media/earthtojake/step.parts/c8616cd125a52ec820cf548440c3842f17f82486/catalog/step/iso4762_socket_head_cap_screw_m3x10.step",
    "part_id": "motor_fasteners_m3",
    "placement_policy": "replace matching layout proxy primitives; imported at source STEP origin until downstream alignment applies locked facts",
    "source_lock_id": "compact_belt_drive_module.motor_fasteners_m3.source_lock",
    "source_type": "other"
  }
]
ZEN_CAD_LOCKED_LAYOUT_FACTS = [
  "root_frame_locked",
  "shaft_axes_parallel_z_locked",
  "pulley_center_distance_locked",
  "motor_axis_position_locked",
  "output_axis_position_locked",
  "belt_midplane_locked",
  "motor_mount_pattern_locked",
  "bearing_interface_locked",
  "output_shaft_interface_locked",
  "gt2_interface_locked",
  "fastener_clearance_locked"
]
ZEN_CAD_INSPECTION_TARGETS = [
  "check_root_frame",
  "check_motor_axis",
  "check_output_bearing_axis",
  "check_center_distance",
  "check_belt_midplane",
  "check_motor_mount_pattern",
  "check_608_bearing_interface",
  "check_gt2_belt_interface",
  "check_source_locks"
]


def _dimension_value(dimensions, *names, default=1.0):
    for name in names:
        item = dimensions.get(name)
        if isinstance(item, dict) and isinstance(item.get("value"), (int, float)):
            return float(item["value"])
    return float(default)


def _make_primitive(primitive):
    from build123d import Axis, Box, Cylinder, Location, Plane, Pos, Sphere

    primitive_type = primitive.get("type")
    dimensions = primitive.get("dimensions", {})
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
    if parsed.scheme in {"http", "https"}:
        suffix = ".stp" if entry.get("artifact_kind") == "stp" else ".step"
        cache_dir = Path(__file__).resolve().parent / "sourced_parts_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in str(entry.get("part_id", "part")))
        target = cache_dir / f"{safe_name}{suffix}"
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
