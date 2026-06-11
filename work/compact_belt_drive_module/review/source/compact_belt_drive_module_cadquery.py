from __future__ import annotations

from pathlib import Path

import cadquery as cq


BASE_LENGTH = 125.0
BASE_WIDTH = 75.0
BASE_THICKNESS = 6.0

MOTOR_X = -35.0
OUTPUT_X = 35.0
AXIS_Y = 0.0
CENTER_DISTANCE = OUTPUT_X - MOTOR_X
BELT_MID_PLANE_Z = 13.5

NEMA17_FACE = 42.3
NEMA17_BODY_LENGTH = 40.0
NEMA17_PATTERN = 31.0
MOTOR_SHAFT_DIAMETER = 5.0

GT2_PITCH = 2.0
GT2_TOOTH_COUNT = 20
GT2_BELT_WIDTH = 6.0
PULLEY_PITCH_DIAMETER = GT2_PITCH * GT2_TOOTH_COUNT / 3.141592653589793
PULLEY_VISUAL_DIAMETER = 16.0
PULLEY_HEIGHT = 8.0

SHAFT_DIAMETER = 8.0
SHAFT_LENGTH = 45.0

BEARING_BORE = 8.0
BEARING_OD = 22.0
BEARING_WIDTH = 7.0
BEARING_SEAT_CLEARANCE_DIAMETER = 22.1

M3_CLEARANCE = 3.4
SUPPORT_LENGTH = 34.0
SUPPORT_WIDTH = 30.0
SUPPORT_HEIGHT = 10.0

BELT_THICKNESS = 1.4

OUT_DIR = Path(__file__).resolve().parents[1] / "step"
STEP_PATH = OUT_DIR / "compact_belt_drive_module_layout.step"
SOURCE_PARTS_DIR = Path(__file__).resolve().parents[2] / "sourced_parts" / "step_parts"
SOURCE_BEARING_608ZZ = SOURCE_PARTS_DIR / "bearing_608zz.step"
SOURCE_M3X10 = SOURCE_PARTS_DIR / "iso4762_socket_head_cap_screw_m3x10.step"
SOURCE_M3X12 = SOURCE_PARTS_DIR / "iso4762_socket_head_cap_screw_m3x12.step"


def cylinder_z(radius: float, height: float, x: float, y: float, z_min: float) -> cq.Workplane:
    return cq.Workplane("XY").circle(radius).extrude(height).translate((x, y, z_min))


def annular_cylinder_z(
    outer_radius: float,
    inner_radius: float,
    height: float,
    x: float,
    y: float,
    z_min: float,
) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .circle(outer_radius)
        .circle(inner_radius)
        .extrude(height)
        .translate((x, y, z_min))
    )


def box_centered(length: float, width: float, height: float, x: float, y: float, z: float) -> cq.Workplane:
    return cq.Workplane("XY").box(length, width, height).translate((x, y, z))


def import_sourced_step(path: Path, x: float, y: float, z: float) -> cq.Workplane:
    if not path.exists():
        raise FileNotFoundError(f"Missing sourced STEP file: {path}")
    return cq.importers.importStep(str(path)).translate((x, y, z))


def make_base_plate() -> cq.Workplane:
    base = cq.Workplane("XY").box(BASE_LENGTH, BASE_WIDTH, BASE_THICKNESS, centered=(True, True, False))

    half_pattern = NEMA17_PATTERN / 2.0
    motor_holes = [
        (MOTOR_X - half_pattern, -half_pattern),
        (MOTOR_X + half_pattern, -half_pattern),
        (MOTOR_X - half_pattern, half_pattern),
        (MOTOR_X + half_pattern, half_pattern),
    ]
    support_holes = [
        (OUTPUT_X - 12.0, -10.0),
        (OUTPUT_X + 12.0, -10.0),
        (OUTPUT_X - 12.0, 10.0),
        (OUTPUT_X + 12.0, 10.0),
    ]

    return (
        base.faces(">Z")
        .workplane()
        .pushPoints(motor_holes + support_holes)
        .hole(M3_CLEARANCE)
        .faces(">Z")
        .workplane()
        .pushPoints([(MOTOR_X, AXIS_Y), (OUTPUT_X, AXIS_Y)])
        .hole(9.0)
    )


def make_support_block() -> cq.Workplane:
    block = (
        cq.Workplane("XY")
        .box(SUPPORT_LENGTH, SUPPORT_WIDTH, SUPPORT_HEIGHT, centered=(True, True, False))
        .translate((OUTPUT_X, AXIS_Y, BASE_THICKNESS))
    )
    return (
        block.faces(">Z")
        .workplane()
        .hole(BEARING_SEAT_CLEARANCE_DIAMETER)
        .faces(">Z")
        .workplane()
        .pushPoints([(-12.0, -10.0), (12.0, -10.0), (-12.0, 10.0), (12.0, 10.0)])
        .hole(M3_CLEARANCE)
    )


def make_pulley(x: float, bore_diameter: float, name: str) -> list[tuple[str, cq.Workplane]]:
    z_min = BELT_MID_PLANE_Z - PULLEY_HEIGHT / 2.0
    pulley = annular_cylinder_z(
        PULLEY_VISUAL_DIAMETER / 2.0,
        bore_diameter / 2.0,
        PULLEY_HEIGHT,
        x,
        AXIS_Y,
        z_min,
    )
    pitch_marker = cylinder_z(
        PULLEY_PITCH_DIAMETER / 2.0,
        0.35,
        x,
        AXIS_Y,
        BELT_MID_PLANE_Z - 0.175,
    )
    return [(f"{name}_body", pulley), (f"{name}_pitch_plane_marker", pitch_marker)]


def make_belt_loop() -> list[tuple[str, cq.Workplane]]:
    pitch_radius = PULLEY_PITCH_DIAMETER / 2.0
    z_center = BELT_MID_PLANE_Z
    z_min = z_center - GT2_BELT_WIDTH / 2.0
    outer_radius = pitch_radius + BELT_THICKNESS / 2.0
    inner_radius = max(0.1, pitch_radius - BELT_THICKNESS / 2.0)

    top_span = box_centered(
        CENTER_DISTANCE,
        BELT_THICKNESS,
        GT2_BELT_WIDTH,
        (MOTOR_X + OUTPUT_X) / 2.0,
        pitch_radius,
        z_center,
    )
    bottom_span = box_centered(
        CENTER_DISTANCE,
        BELT_THICKNESS,
        GT2_BELT_WIDTH,
        (MOTOR_X + OUTPUT_X) / 2.0,
        -pitch_radius,
        z_center,
    )
    motor_wrap = annular_cylinder_z(outer_radius, inner_radius, GT2_BELT_WIDTH, MOTOR_X, AXIS_Y, z_min)
    output_wrap = annular_cylinder_z(outer_radius, inner_radius, GT2_BELT_WIDTH, OUTPUT_X, AXIS_Y, z_min)
    return [
        ("gt2_belt_top_span", top_span),
        ("gt2_belt_bottom_span", bottom_span),
        ("gt2_belt_motor_wrap", motor_wrap),
        ("gt2_belt_output_wrap", output_wrap),
    ]


def build_assembly() -> cq.Assembly:
    asm = cq.Assembly(name="compact_belt_drive_module_layout")

    asm.add(make_base_plate(), name="base_plate", color=cq.Color(0.72, 0.72, 0.70))
    asm.add(
        box_centered(NEMA17_FACE, NEMA17_FACE, NEMA17_BODY_LENGTH, MOTOR_X, AXIS_Y, -NEMA17_BODY_LENGTH / 2.0),
        name="nema17_motor_body",
        color=cq.Color(0.18, 0.20, 0.23),
    )
    asm.add(cylinder_z(11.0, 2.0, MOTOR_X, AXIS_Y, 0.0), name="nema17_front_boss", color=cq.Color(0.35, 0.35, 0.35))
    asm.add(
        cylinder_z(MOTOR_SHAFT_DIAMETER / 2.0, 24.0, MOTOR_X, AXIS_Y, 0.0),
        name="motor_shaft_axis_5mm",
        color=cq.Color(0.85, 0.85, 0.82),
    )

    asm.add(make_support_block(), name="bearing_support_block", color=cq.Color(0.38, 0.46, 0.55))
    asm.add(
        import_sourced_step(SOURCE_BEARING_608ZZ, OUTPUT_X, AXIS_Y, BASE_THICKNESS + 0.25 + BEARING_WIDTH / 2.0),
        name="source_locked_bearing_608zz",
        color=cq.Color(0.82, 0.82, 0.78),
    )
    asm.add(
        cylinder_z(SHAFT_DIAMETER / 2.0, SHAFT_LENGTH, OUTPUT_X, AXIS_Y, 0.0),
        name="output_shaft_axis_8mm",
        color=cq.Color(0.78, 0.78, 0.76),
    )

    for name, part in make_pulley(MOTOR_X, MOTOR_SHAFT_DIAMETER, "motor_gt2_20t_5mm_pulley"):
        asm.add(part, name=name, color=cq.Color(0.96, 0.63, 0.18))
    for name, part in make_pulley(OUTPUT_X, SHAFT_DIAMETER, "output_gt2_20t_8mm_pulley"):
        asm.add(part, name=name, color=cq.Color(0.96, 0.63, 0.18))

    for name, part in make_belt_loop():
        asm.add(part, name=name, color=cq.Color(0.06, 0.06, 0.06))

    half_pattern = NEMA17_PATTERN / 2.0
    for index, (x, y) in enumerate(
        [
            (MOTOR_X - half_pattern, -half_pattern),
            (MOTOR_X + half_pattern, -half_pattern),
            (MOTOR_X - half_pattern, half_pattern),
            (MOTOR_X + half_pattern, half_pattern),
        ],
        start=1,
    ):
        asm.add(
            import_sourced_step(SOURCE_M3X10, x, y, BASE_THICKNESS),
            name=f"source_locked_motor_m3x10_fastener_{index}",
            color=cq.Color(0.2, 0.2, 0.2),
        )

    for index, (x, y) in enumerate(
        [
            (OUTPUT_X - 12.0, -10.0),
            (OUTPUT_X + 12.0, -10.0),
            (OUTPUT_X - 12.0, 10.0),
            (OUTPUT_X + 12.0, 10.0),
        ],
        start=1,
    ):
        asm.add(
            import_sourced_step(SOURCE_M3X12, x, y, BASE_THICKNESS + SUPPORT_HEIGHT),
            name=f"source_locked_support_m3x12_fastener_{index}",
            color=cq.Color(0.2, 0.2, 0.2),
        )

    return asm


def export_step(path: Path = STEP_PATH) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    asm = build_assembly()
    try:
        asm.save(str(path), exportType="STEP")
    except TypeError:
        asm.save(str(path))
    return path


if __name__ == "__main__":
    result = export_step()
    print(result)
