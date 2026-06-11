"""Generated Zen CAD layout proxy source.

This file is generated from a kernel-neutral layout proxy scene.
It is a source adapter for downstream CAD generation, not final CAD evidence.
"""
from __future__ import annotations

import math

ZEN_CAD_SCENE_ID = 'flat_planetary_gear_assembly.layout_proxy_scene'
ZEN_CAD_SOURCE_SPEC_ID = 'flat_planetary_gear_assembly'
ZEN_CAD_PRIMITIVES = []
ZEN_CAD_SOURCED_PARTS = []
ZEN_CAD_FEATURE_PLAN = {'generator': 'zen_cad_feature_plan_v4_involute_premium_detail', 'intermesh_policy': {'boolean_overlap_required_max_volume_mm3': 0.0, 'center_distance_mm': 42.0, 'external_addendum_mm': 1.8, 'external_dedendum_mm': 2.2, 'internal_ring_negative_cutter': '60T involute SpurGear subtracted from ring blank to create internal tooth spaces', 'minimum_mesh_clearance_policy': 'backlash is created by 1.01x XY scaling of the internal ring tooth-space cutter; static Boolean overlap must be zero for all six mesh pairs', 'module_mm': 2.0, 'pitch_radii_mm': {'planet': 18.0, 'ring': 60.0, 'sun': 24.0}, 'planet_phase_rule': 'planet rotations are theta_deg - 10 deg; tested phases give zero Boolean common volume for sun/planet and planet/ring pairs', 'planet_ring_clearance_cases_mm': {'boolean_common_volume_mm3': 0.0}, 'planet_root_radius_mm': 15.8, 'planet_tip_radius_mm': 19.8, 'planet_tooth_count': 18, 'pressure_angle_deg': 14.5, 'ring_cutter_scale_xy': 1.01, 'ring_slot_phase_deg': -3.0, 'ring_slot_root_effective_radius_mm': 62.822, 'ring_tooth_count': 60, 'ring_tooth_tip_effective_radius_mm': 58.378, 'sun_phase_deg': 0.0, 'sun_planet_clearance_cases_mm': {'boolean_common_volume_mm3': 0.0}, 'sun_root_radius_mm': 21.8, 'sun_tip_radius_mm': 25.8, 'sun_tooth_count': 24, 'tooth_count_relation': 'ring = sun + 2*planet = 60; (sun + ring) / 3 = 28 integer for equal planet spacing', 'type': 'bd_warehouse_involute_internal_ring_proxy'}, 'parts': [{'base': 'gear', 'dimensions': {'addendum': 1.8, 'dedendum': 2.2, 'module': 2.0, 'outer_diameter': 51.6, 'pitch_diameter': 48.0, 'pressure_angle': 14.5, 'root_diameter': 43.6, 'thickness': 6, 'tooth_count': 24, 'root_fillet': 0.1}, 'features': [{'axis': 'z', 'diameter': 8, 'type': 'central_bore'}], 'metadata': {'tooth_profile': 'bd_warehouse_involute_spur'}, 'part_id': 'sun_gear', 'placement': {'position': [0, 0, 0], 'rotation': [0, 0, 0.0]}}, {'base': 'gear', 'dimensions': {'addendum': 1.8, 'dedendum': 2.2, 'module': 2.0, 'outer_diameter': 39.6, 'pitch_diameter': 36.0, 'pressure_angle': 14.5, 'root_diameter': 31.6, 'thickness': 6, 'tooth_count': 18, 'root_fillet': 0.1}, 'features': [{'axis': 'z', 'diameter': 5, 'type': 'central_bore'}], 'metadata': {'tooth_profile': 'bd_warehouse_involute_spur'}, 'part_id': 'planet_gear_1', 'placement': {'position': [42.0, 0.0, 0], 'rotation': [0, 0, -10.0]}}, {'base': 'gear', 'dimensions': {'addendum': 1.8, 'dedendum': 2.2, 'module': 2.0, 'outer_diameter': 39.6, 'pitch_diameter': 36.0, 'pressure_angle': 14.5, 'root_diameter': 31.6, 'thickness': 6, 'tooth_count': 18, 'root_fillet': 0.1}, 'features': [{'axis': 'z', 'diameter': 5, 'type': 'central_bore'}], 'metadata': {'tooth_profile': 'bd_warehouse_involute_spur'}, 'part_id': 'planet_gear_2', 'placement': {'position': [-21.0, 36.3731, 0], 'rotation': [0, 0, 110.0]}}, {'base': 'gear', 'dimensions': {'addendum': 1.8, 'dedendum': 2.2, 'module': 2.0, 'outer_diameter': 39.6, 'pitch_diameter': 36.0, 'pressure_angle': 14.5, 'root_diameter': 31.6, 'thickness': 6, 'tooth_count': 18, 'root_fillet': 0.1}, 'features': [{'axis': 'z', 'diameter': 5, 'type': 'central_bore'}], 'metadata': {'tooth_profile': 'bd_warehouse_involute_spur'}, 'part_id': 'planet_gear_3', 'placement': {'position': [-21.0, -36.3731, 0], 'rotation': [0, 0, 230.0]}}, {'base': 'internal_ring_gear', 'dimensions': {'addendum': 1.8, 'dedendum': 2.2, 'inner_diameter': 116.756, 'module': 2.0, 'outer_diameter': 144, 'pitch_diameter': 120.0, 'pressure_angle': 14.5, 'ring_cutter_addendum': 2.2, 'ring_cutter_dedendum': 2.2, 'ring_cutter_scale_xy': 1.01, 'slot_phase_deg': -3.0, 'slot_root_diameter': 125.644, 'thickness': 6, 'tooth_count': 60, 'tooth_depth': 4.444, 'ring_cutter_root_fillet': 0.1}, 'features': [{'type': 'bolt_circle_pattern', 'axis': 'z', 'count': 6, 'radius': 68.0, 'diameter': 3.4, 'purpose': 'ring_mount_holes'}], 'metadata': {'tooth_profile': 'negative_involute_internal_ring'}, 'part_id': 'ring_gear'}, {'base': 'cylinder', 'dimensions': {'addendum': 1.8, 'dedendum': 2.2, 'diameter': 104, 'height': 2, 'pressure_angle': 14.5}, 'features': [{'type': 'edge_fillet', 'edges': 'outside_circular_edges', 'radius': 0.25}, {'axis': 'z', 'diameter': 12, 'type': 'central_bore'}, {'axis': 'z', 'count': 3, 'diameter': 5, 'radius': 42.0, 'type': 'bolt_circle_pattern'}, {'type': 'bolt_circle_pattern', 'axis': 'z', 'count': 6, 'radius': 30.0, 'diameter': 8.0, 'purpose': 'carrier_lightening_holes', 'start_angle': 30.0}], 'metadata': {'tooth_profile': 'none'}, 'part_id': 'carrier', 'placement': {'position': [0, 0, -5]}}, {'base': 'cylinder', 'dimensions': {'addendum': 1.8, 'dedendum': 2.2, 'diameter': 5, 'height': 10, 'pressure_angle': 14.5}, 'features': [{'type': 'edge_fillet', 'edges': 'outside_circular_edges', 'radius': 0.25}], 'metadata': {'tooth_profile': 'none'}, 'part_id': 'pin_1', 'placement': {'position': [42, 0, 0]}}, {'base': 'cylinder', 'dimensions': {'addendum': 1.8, 'dedendum': 2.2, 'diameter': 5, 'height': 10, 'pressure_angle': 14.5}, 'features': [{'type': 'edge_fillet', 'edges': 'outside_circular_edges', 'radius': 0.25}], 'metadata': {'tooth_profile': 'none'}, 'part_id': 'pin_2', 'placement': {'position': [-21, 36.373, 0]}}, {'base': 'cylinder', 'dimensions': {'addendum': 1.8, 'dedendum': 2.2, 'diameter': 5, 'height': 10, 'pressure_angle': 14.5}, 'features': [{'type': 'edge_fillet', 'edges': 'outside_circular_edges', 'radius': 0.25}], 'metadata': {'tooth_profile': 'none'}, 'part_id': 'pin_3', 'placement': {'position': [-21, -36.373, 0]}}], 'tooth_profile': {'note': 'Sun and planets are bd_warehouse involute SpurGear solids. Ring is an internal gear made by subtracting a scaled 60T involute SpurGear cutter from an annular blank.', 'pressure_angle_deg': 14.5, 'ring_cutter_scale_xy': 1.01, 'type': 'bd_warehouse_involute_spur'}, 'aesthetic_detail_plan': {'intent': 'Reduce flat toy-like appearance while preserving locked involute mesh geometry.', 'mesh_boundary_policy': 'Do not alter pitch radii, tooth counts, planet centers, ring cutter phase, or ring cutter scale.', 'gear_root_fillet_mm': 0.1, 'hub_bosses': {'sun': {'diameter_mm': 18.0, 'height_mm': 1.2, 'fillet_mm': 0.35}, 'planet': {'diameter_mm': 11.5, 'height_mm': 1.0, 'fillet_mm': 0.25}}, 'ring_outer_lips': {'inner_diameter_mm': 134.0, 'outer_diameter_mm': 144.0, 'height_mm': 0.8, 'top_z_mm': 3.4, 'bottom_z_mm': -3.4}, 'ring_mount_holes': {'count': 6, 'radius_mm': 68.0, 'diameter_mm': 3.4}, 'carrier': {'edge_fillet_mm': 0.25, 'lightening_holes': {'count': 6, 'radius_mm': 30.0, 'diameter_mm': 8.0}}, 'pins': {'stem_edge_fillet_mm': 0.25, 'cap_diameter_mm': 8.0, 'cap_height_mm': 1.4, 'cap_center_z_mm': 4.3, 'cap_fillet_mm': 0.25}, 'validation': 'Supplemental Boolean mesh checks must remain zero for all six mesh pairs.'}}
ZEN_CAD_LOCKED_LAYOUT_FACTS = ['separate_bodies_locked', 'planet_radius_locked', 'gear_axes_parallel_locked', 'involute_teeth_locked', 'no_tooth_overlap_locked', 'module_locked_ring_mesh_locked', 'premium_detail_non_mesh_locked']
ZEN_CAD_INSPECTION_TARGETS = ['check_separate_bodies', 'check_planet_radius', 'check_ring_sun_coaxial', 'check_involute_teeth', 'check_viewer_link', 'check_no_tooth_overlap', 'check_module_locked_ring_mesh', 'check_involute_ring_mesh', 'check_premium_detailing']


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


def _make_annulus(outer_radius, inner_radius, height):
    from build123d import Cylinder

    return Cylinder(outer_radius, height) - Cylinder(inner_radius, height + 0.4)


def _aesthetic_detail_plan():
    plan = ZEN_CAD_FEATURE_PLAN.get("aesthetic_detail_plan", {})
    return plan if isinstance(plan, dict) else {}


def _add_symmetric_hub_boss(shape, diameter, height, fillet_radius, base_thickness):
    from build123d import Location

    if diameter <= 0 or height <= 0:
        return shape
    boss = _make_filleted_cylinder(diameter / 2.0, height, fillet_radius)
    z = base_thickness / 2.0 + height / 2.0
    return shape + (Location((0.0, 0.0, z)) * boss) + (Location((0.0, 0.0, -z)) * boss)


def _apply_aesthetic_details(shape, part):
    from build123d import Location

    part_id = str(part.get("part_id", ""))
    dimensions = part.get("dimensions", {})
    details = _aesthetic_detail_plan()
    thickness = _feature_value(dimensions, "thickness", "height", default=6.0)

    if part_id == "sun_gear":
        hub = details.get("hub_bosses", {}).get("sun", {})
        return _add_symmetric_hub_boss(
            shape,
            _feature_value(hub, "diameter_mm", default=18.0),
            _feature_value(hub, "height_mm", default=1.2),
            _feature_value(hub, "fillet_mm", default=0.35),
            thickness,
        )

    if part_id.startswith("planet_gear_"):
        hub = details.get("hub_bosses", {}).get("planet", {})
        return _add_symmetric_hub_boss(
            shape,
            _feature_value(hub, "diameter_mm", default=11.5),
            _feature_value(hub, "height_mm", default=1.0),
            _feature_value(hub, "fillet_mm", default=0.25),
            thickness,
        )

    if part_id == "ring_gear":
        lips = details.get("ring_outer_lips", {})
        outer = _feature_value(lips, "outer_diameter_mm", default=0.0) / 2.0
        inner = _feature_value(lips, "inner_diameter_mm", default=0.0) / 2.0
        height = _feature_value(lips, "height_mm", default=0.0)
        if outer > inner > 0 and height > 0:
            lip = _make_annulus(outer, inner, height)
            top_z = _feature_value(lips, "top_z_mm", default=thickness / 2.0 + height / 2.0)
            bottom_z = _feature_value(lips, "bottom_z_mm", default=-top_z)
            shape = shape + (Location((0.0, 0.0, top_z)) * lip) + (Location((0.0, 0.0, bottom_z)) * lip)
        return shape

    if part_id.startswith("pin_"):
        pins = details.get("pins", {})
        cap_diameter = _feature_value(pins, "cap_diameter_mm", default=0.0)
        cap_height = _feature_value(pins, "cap_height_mm", default=0.0)
        if cap_diameter > 0 and cap_height > 0:
            cap = _make_filleted_cylinder(
                cap_diameter / 2.0,
                cap_height,
                _feature_value(pins, "cap_fillet_mm", default=0.25),
            )
            cap_z = _feature_value(pins, "cap_center_z_mm", default=thickness / 2.0 - cap_height / 2.0)
            shape = shape + (Location((0.0, 0.0, cap_z)) * cap)
        return shape

    return shape


def _tooth_profile_widths(base_width):
    profile = ZEN_CAD_FEATURE_PLAN.get("tooth_profile", {})
    root_factor = float(profile.get("root_width_factor", 0.82))
    top_factor = float(profile.get("top_width_factor", 0.46))
    return max(base_width * root_factor, 0.05), max(base_width * top_factor, 0.05)


def _make_trapezoid_prism(radial_depth, inner_width, outer_width, thickness):
    from build123d import BuildLine, BuildPart, BuildSketch, Plane, Polyline, extrude, make_face

    with BuildPart() as prism:
        with BuildSketch(Plane.XY):
            with BuildLine():
                Polyline(
                    (-radial_depth / 2.0, -inner_width / 2.0),
                    (radial_depth / 2.0, -outer_width / 2.0),
                    (radial_depth / 2.0, outer_width / 2.0),
                    (-radial_depth / 2.0, inner_width / 2.0),
                    close=True,
                )
            make_face()
        extrude(amount=thickness / 2.0, both=True)
    return prism.part


def _make_gear(part):
    from bd_warehouse.gear import SpurGear

    dimensions = part.get("dimensions", {})
    module = _feature_value(dimensions, "module", default=2.0)
    pressure_angle = _feature_value(dimensions, "pressure_angle", default=14.5)
    thickness = _feature_value(dimensions, "thickness", "height", default=6.0)
    tooth_count = int(_feature_value(dimensions, "tooth_count", default=16))
    addendum = _feature_value(dimensions, "addendum", default=0.9 * module)
    dedendum = _feature_value(dimensions, "dedendum", default=1.1 * module)
    root_fillet = _feature_value(dimensions, "root_fillet", default=0.0)
    return SpurGear(
        module=module,
        tooth_count=tooth_count,
        pressure_angle=pressure_angle,
        thickness=thickness,
        root_fillet=root_fillet if root_fillet > 0 else None,
        addendum=addendum,
        dedendum=dedendum,
    )


def _make_internal_ring_gear(part):
    from bd_warehouse.gear import SpurGear
    from build123d import Cylinder, Location, scale

    dimensions = part.get("dimensions", {})
    module = _feature_value(dimensions, "module", default=2.0)
    pressure_angle = _feature_value(dimensions, "pressure_angle", default=14.5)
    outer_radius = _feature_value(dimensions, "outer_diameter", default=105.0) / 2.0
    thickness = _feature_value(dimensions, "thickness", "height", default=6.0)
    tooth_count = int(_feature_value(dimensions, "tooth_count", default=48))
    cutter_addendum = _feature_value(dimensions, "ring_cutter_addendum", "addendum", default=1.1 * module)
    cutter_dedendum = _feature_value(dimensions, "ring_cutter_dedendum", "dedendum", default=1.1 * module)
    cutter_root_fillet = _feature_value(dimensions, "ring_cutter_root_fillet", "root_fillet", default=0.0)
    cutter_scale = _feature_value(dimensions, "ring_cutter_scale_xy", default=1.01)
    slot_phase = _feature_value(dimensions, "slot_phase_deg", default=0.0)
    cutter = SpurGear(
        module=module,
        tooth_count=tooth_count,
        pressure_angle=pressure_angle,
        thickness=thickness + 2.0,
        root_fillet=cutter_root_fillet if cutter_root_fillet > 0 else None,
        addendum=cutter_addendum,
        dedendum=cutter_dedendum,
    )
    cutter = Location((0.0, 0.0, 0.0), (0.0, 0.0, slot_phase)) * scale(cutter, by=(cutter_scale, cutter_scale, 1.0))
    return Cylinder(outer_radius, thickness) - cutter


def _make_feature_base(part):
    from build123d import Box, Cylinder

    base = part.get("base", part.get("type", "box"))
    dimensions = part.get("dimensions", {})
    if base == "box":
        width = _feature_value(dimensions, "width", "length", "x", default=10.0)
        depth = _feature_value(dimensions, "depth", "y", default=width)
        height = _feature_value(dimensions, "height", "thickness", "z", default=5.0)
        chamfer = _first_feature(part, "edge_chamfer", "top_outer_perimeter")
        chamfer_size = _feature_value(chamfer or {}, "size", "length", default=0.0)
        return _make_chamfered_box(width, depth, height, chamfer_size)
    if base == "cylinder":
        radius = _feature_value(dimensions, "radius", default=0.0)
        if radius <= 0:
            radius = _feature_value(dimensions, "diameter", "outer_diameter", default=10.0) / 2.0
        height = _feature_value(dimensions, "height", "thickness", default=5.0)
        fillet = _first_feature(part, "edge_fillet", "outside_circular_edges")
        fillet_radius = _feature_value(fillet or {}, "radius", default=0.0)
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
    base_dimensions = part.get("dimensions", {})
    for feature in _feature_list(part):
        feature_type = feature.get("type")
        if feature_type in {"edge_chamfer", "edge_fillet", "radial_tooth_pattern", "internal_tooth_pattern"}:
            continue
        if feature_type in {"through_hole", "central_bore"}:
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
    shape = _apply_aesthetic_details(shape, part)
    shape = _apply_features(shape, part)
    return _apply_placement(shape, part.get("placement"), part.get("part_id", "feature_part"))


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
    feature_children = [
        _make_feature_part(part)
        for part in ZEN_CAD_FEATURE_PLAN.get("parts", [])
        if isinstance(part, dict)
    ]
    proxy_children = [_make_primitive(primitive) for primitive in ZEN_CAD_PRIMITIVES]
    children = sourced_children + feature_children + proxy_children
    assembly = Compound(label=ZEN_CAD_SCENE_ID, children=children)
    return assembly
