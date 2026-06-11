# CAD Spec: Compact Belt-Drive Module

## Intent

Create a compact layout-proxy assembly for a GT2 belt-drive module mounted on a flat base plate. The module uses a NEMA 17 stepper motor driving a 20T GT2 pulley on the motor shaft, a parallel 8 mm output shaft supported by a 608 bearing, and a matching 20T GT2 pulley on the output shaft. The first pass prioritizes shaft axes, pulley pitch references, bearing bore alignment, belt centerline alignment, mounting patterns, and source-lock traceability over surface fidelity.

Classification: moving drivetrain assembly.

## Coordinate System

- Units: millimeters.
- Root frame: `base_plate_frame`.
- Base plane: XY.
- Up axis: +Z.
- Origin: center of the base plate lower face.
- +X: motor-to-output shaft direction.
- +Y: lateral direction across the belt spans in the base plane.
- +Z: shaft axis direction, motor shaft direction, and pulley/belt width direction.

Part-local frames:

| Part | Local Frame |
| --- | --- |
| `base_plate` | Origin at base plate lower-face center; XY footprint, +Z through plate thickness. |
| `nema17_motor` | Origin on motor shaft centerline at front mounting face; shaft axis +Z; body extends below plate in -Z. |
| `motor_pulley_20t_5mm` | Origin at pulley pitch-plane center on motor shaft axis; bore axis +Z; pitch plane XY. |
| `output_shaft_8mm` | Origin at output shaft center where it crosses the belt mid-plane; shaft axis +Z. |
| `output_pulley_20t_8mm` | Origin at pulley pitch-plane center on output shaft axis; bore axis +Z; pitch plane XY. |
| `bearing_608` | Origin at bearing bore center; bearing axis +Z; outer race seat concentric with support pocket. |
| `bearing_support_block` | Origin at output shaft axis projected to top face of base plate; pocket axis +Z. |
| `gt2_belt_loop` | Origin at midpoint between pulley axes on `belt_mid_plane_z`; belt mid-plane is XY. |
| `motor_fasteners_m3` | Four axes normal to motor mounting face, on the NEMA 17 31 mm square pattern. |
| `bearing_support_fasteners_m3` | Four axes normal to the base plate around the bearing support block. |

## Parameter Contract

| Name | Units | Value | Status | Source | Drives | Validation |
| --- | ---: | ---: | --- | --- | --- | --- |
| `base_plate_length` | mm | 125 | assumed | layout assumption | `base_plate` envelope | Bounding box X dimension is 125 mm. |
| `base_plate_width` | mm | 75 | assumed | layout assumption | `base_plate` envelope | Bounding box Y dimension is 75 mm. |
| `base_plate_thickness` | mm | 6 | assumed | layout assumption | `base_plate` envelope, motor shaft clearance | Plate thickness is 6 mm and does not consume the whole motor shaft length. |
| `motor_axis_x` | mm | -35 | locked | layout assumption | `nema17_motor.shaft_axis` | Motor shaft axis world X is -35 mm. |
| `output_axis_x` | mm | 35 | locked | derived constraint | `output_shaft_8mm.shaft_axis`, `bearing_608.bearing_axis` | Output shaft/bearing axis world X is 35 mm. |
| `axis_y` | mm | 0 | locked | derived constraint | all shaft axes | Both shaft axes share Y = 0. |
| `pulley_center_distance` | mm | 70 | locked | layout assumption | belt spans, base footprint | Distance between motor and output shaft axes is 70 mm. |
| `shaft_axis_direction` | dimensionless | +Z | locked | layout assumption | motor, output shaft, bearing, pulleys | All shaft/bore axes are parallel to +Z. |
| `belt_mid_plane_z` | mm | 13.5 | locked | layout assumption | pulley pitch planes, belt centerline | Both pulley pitch planes and belt centerline share Z = 13.5 mm. |
| `motor_mount_pattern_spacing` | mm | 31 | locked | project registry | NEMA 17 mounting holes | Four motor fastener axes form a 31 mm square pattern. |
| `motor_face_size` | mm | 42.3 | assumed | project registry | motor body proxy | Motor face envelope is 42.3 mm square nominal. |
| `motor_shaft_diameter` | mm | 5 | assumed | source/product candidate | motor pulley bore | Motor pulley bore candidate is 5 mm and must be confirmed for the final motor. |
| `gt2_pitch` | mm | 2 | locked | project registry | belt and pulley pitch references | Belt pitch is 2 mm. |
| `gt2_belt_width` | mm | 6 | locked | project registry | pulley width, belt envelope | Belt width envelope is 6 mm. |
| `pulley_tooth_count` | count | 20 | assumed | source/product candidate | both pulleys | Both pulleys are 20T for 1:1 ratio. |
| `pulley_pitch_diameter` | mm | 12.732 | derived | derived constraint | pitch circles | `tooth_count * gt2_pitch / pi`, tolerance +/-0.05 mm in detail CAD. |
| `belt_length_nominal` | mm | 180 | derived | derived constraint | closed-loop belt candidate | Equal 20T pulleys at 70 mm center distance imply about 180 mm pitch length. |
| `bearing_bore_diameter` | mm | 8 | locked | project registry | bearing bore, shaft fit | 608 bore and shaft nominal diameter are 8 mm. |
| `bearing_outer_diameter` | mm | 22 | locked | project registry | bearing support pocket | Bearing seat OD is 22 mm nominal. |
| `bearing_width` | mm | 7 | locked | project registry | bearing support pocket height | Bearing axial width is 7 mm. |
| `output_shaft_diameter` | mm | 8 | locked | project registry | shaft, output pulley bore, bearing bore | Shaft, bearing bore, and output pulley bore are coaxial at 8 mm nominal. |
| `output_shaft_length` | mm | 45 | assumed | layout assumption | output shaft proxy | Shaft extends through bearing and output pulley without changing locked axes. |
| `m3_clearance_diameter` | mm | 3.4 | locked | project registry | motor/support fastener holes | M3 clearance holes use 3.4 mm layout diameter. |
| `bearing_seat_radial_clearance` | mm | 0.05 | assumed | layout assumption | bearing pocket | Seat is represented as OD + 0.10 mm diameter in proxy; fit class must be selected before final. |

## Artifact Targets

- Target maturity: `layout_proxy`.
- CAD source intent: build123d adapter generated by Zen CAD runtime.
- Primary review artifact: kernel-neutral `layout_proxy.scene.json`.
- Secondary artifacts: generated build123d source adapter, CAD source manifest, inspection reports, proceed gate package, review bundle.
- Source-of-truth rule: this Markdown spec plus `cad_spec.json` and `layout_contract.json` define the contract. Generated files are derived review aids.

## Parts And Roles

| Part ID | Role | Interface Signatures | Source-Lock Intent |
| --- | --- | --- | --- |
| `base_plate` | structure | none | custom generated plate, not a catalog part. |
| `nema17_motor` | driver | `motor.nema_17.layout` | source-lock to a concrete NEMA 17 motor candidate before final. |
| `motor_pulley_20t_5mm` | driven | `belt.gt2_6mm.layout` | source-lock to a 20T GT2, 5 mm bore, 6 mm belt pulley. |
| `output_shaft_8mm` | driven | `shaft_bore.8mm.layout` | source-lock to an 8 mm shaft/rod candidate. |
| `output_pulley_20t_8mm` | driven | `belt.gt2_6mm.layout`, `shaft_bore.8mm.layout` | source-lock to a 20T GT2, 8 mm bore, 6 mm belt pulley. |
| `bearing_608` | guide | `bearing.608.layout` | source-lock to 608 or 608ZZ/2RS bearing candidate. |
| `bearing_support_block` | structure | none | generated custom block with bearing seat. |
| `gt2_belt_loop` | driven | `belt.gt2_6mm.layout` | optional source-lock to 180 mm closed-loop GT2 belt before final. |
| `motor_fasteners_m3` | fastener | `fastener.m3_clearance.layout` | source-lock to M3 socket head screws after stack height is confirmed. |
| `bearing_support_fasteners_m3` | fastener | `fastener.m3_clearance.layout` | source-lock to M3 socket head screws after stack height is confirmed. |

## Assembly Graph

- `base_plate` is fixed and defines the root frame.
- `nema17_motor` is fixed to `base_plate` by `motor_fasteners_m3`; its front mounting face is flush to the underside of the base plate.
- `motor_pulley_20t_5mm` is fixed coaxially to the NEMA 17 motor shaft.
- `bearing_support_block` is fixed to the top of `base_plate`.
- `bearing_608` is seated in `bearing_support_block`; the bearing bore axis is +Z.
- `output_shaft_8mm` rotates in `bearing_608` and is coaxial with the bearing bore.
- `output_pulley_20t_8mm` is fixed coaxially to `output_shaft_8mm`.
- `gt2_belt_loop` couples `motor_pulley_20t_5mm` to `output_pulley_20t_8mm` through pitch contact in the shared belt mid-plane.

## Interface Primitives

- `base_plate_top_plane`: datum plane at Z = 6 mm.
- `base_plate_bottom_plane`: datum plane at Z = 0 mm.
- `motor_mount_face`: NEMA 17 front face flush to `base_plate_bottom_plane`; shaft axis normal to face.
- `motor_shaft_axis`: axis through X = -35 mm, Y = 0 mm, direction +Z.
- `output_shaft_axis`: axis through X = 35 mm, Y = 0 mm, direction +Z.
- `bearing_axis`: coincident with `output_shaft_axis`.
- `bearing_outer_race_seat`: cylinder OD 22.10 mm assumed proxy seat, axis `bearing_axis`, width 7 mm minimum.
- `motor_mount_pattern`: four M3 clearance axes on 31 mm square, centered on `motor_shaft_axis`.
- `support_mount_pattern`: four M3 clearance axes around the output support block, centered on `output_shaft_axis`; exact spacing assumed 32 mm x 26 mm.
- `motor_pulley_pitch_circle`: 20T GT2 pitch circle, diameter 12.732 mm, centered on `motor_shaft_axis` at `belt_mid_plane_z`.
- `output_pulley_pitch_circle`: 20T GT2 pitch circle, diameter 12.732 mm, centered on `output_shaft_axis` at `belt_mid_plane_z`.
- `belt_mid_plane`: XY plane at Z = 13.5 mm.
- `belt_centerline`: GT2 closed loop tangent to both pulley pitch circles in `belt_mid_plane`.
- `belt_keep_out`: 6 mm belt width plus 2 mm lateral clearance; no support block or fastener head may enter this envelope.

## Motion And Drivetrain

- Joint `motor_rotor_joint`: revolute about `motor_shaft_axis`.
- Joint `motor_pulley_joint`: fixed to motor shaft; pulley rotation follows motor 1:1.
- Joint `output_shaft_bearing_joint`: revolute about `bearing_axis`/`output_shaft_axis`.
- Belt relationship: GT2 belt pitch contact between equal 20T pulleys, pitch 2 mm, belt width 6 mm.
- Ratio: 1:1 because both pulleys are 20T.
- Nominal belt length: approximately 180 mm pitch length for equal 20T pulleys at 70 mm center distance. Final belt selection must confirm tooth count, belt length, and tensioning method.
- Tensioning strategy: no separate tensioner in the layout proxy. Detail CAD may add motor mounting slots or a sliding support only if the approved axes and belt mid-plane remain preserved, or the design returns to the proceed gate.

## Proxy Fidelity Policy

The layout proxy may simplify:

- NEMA 17 body shape, rear cap, connector, cable exit, and exact length.
- Pulley tooth profiles, flanges, set screws, and hub details.
- Bearing balls, cage, seals/shields, chamfers, and fit tolerances.
- Shaft end details, flats, retaining rings, threads, and surface finish.
- Fastener head recesses and thread geometry.
- Base plate edge treatment, pocket fillets, labels, and cosmetic chamfers.

The layout proxy must preserve:

- Root frame and base plate datum planes.
- Motor shaft axis, output shaft axis, bearing axis, and their +Z orientation.
- 70 mm pulley center distance.
- NEMA 17 31 mm square mounting pattern.
- 608 bearing 8 mm bore, 22 mm OD, and 7 mm width.
- 8 mm output shaft nominal diameter.
- GT2 pitch 2 mm, 6 mm belt width, 20T pitch references, and shared belt mid-plane.
- M3 clearance hole layout diameter.
- Belt keep-out envelope around both pitch spans.

## Locked Layout Facts

1. `root_frame_locked`: `base_plate_frame` uses XY base plane, +Z up, origin at base lower-face center.
2. `shaft_axes_parallel_z_locked`: motor shaft axis, output shaft axis, and bearing axis are parallel to +Z.
3. `pulley_center_distance_locked`: motor and output shaft axes are 70 mm apart along +X.
4. `motor_axis_position_locked`: motor shaft axis is X = -35 mm, Y = 0 mm.
5. `output_axis_position_locked`: output shaft/bearing axis is X = 35 mm, Y = 0 mm.
6. `belt_midplane_locked`: both pulley pitch planes and the belt centerline are in the XY plane at Z = 13.5 mm.
7. `motor_mount_pattern_locked`: NEMA 17 motor pattern is four M3 clearance axes on a 31 mm square centered on the motor shaft axis.
8. `bearing_interface_locked`: 608 bearing interface is 8 mm bore, 22 mm OD, 7 mm width, coaxial with output shaft.
9. `output_shaft_interface_locked`: output shaft nominal diameter is 8 mm and coaxial with the bearing bore and output pulley.
10. `gt2_interface_locked`: GT2 pitch is 2 mm, belt width is 6 mm, pulley tooth count is 20T at both shafts, and ratio is 1:1.
11. `fastener_clearance_locked`: M3 layout clearance diameter is 3.4 mm for motor and support fastener axes.

## Inspection Plan

- Check the generated scene has all required top-level parts and labels.
- Check `base_plate_frame` root axes match XY base plane and +Z up.
- Check motor shaft, output shaft, and bearing axes are present and direction +Z.
- Check motor-output axis distance is 70 mm.
- Check both pulley pitch references share `belt_mid_plane_z`.
- Check `bearing_608` bore, output shaft, and output pulley are coaxial.
- Check NEMA 17 mounting pattern is centered on the motor shaft axis and uses 31 mm square spacing.
- Check 608 bearing dimensions are 8 x 22 x 7 mm.
- Check GT2 belt pitch, width, pitch circles, and belt keep-out are represented.
- Check source-lock evidence exists for the standard motor, pulleys, bearing, shaft, and fasteners before final packaging.

## Repair Loop

If a generated artifact fails inspection:

1. Classify the failure as missing part, wrong frame, wrong axis, wrong distance, missing interface primitive, source-lock gap, or unsupported downstream export.
2. Change the smallest responsible source contract, parameter, datum, relationship, or handoff instruction.
3. Regenerate the affected layout proxy, source adapter, inspection report, and proceed package.
4. Rerun the failed check and dependent alignment checks.
5. Stop and return to the proceed gate if a repair would change a locked axis, center distance, belt mid-plane, mounting pattern, bearing interface, or drivetrain ratio.

## Assumptions And Open Questions

- The module uses vertical, parallel shaft axes with the motor mounted below the base plate and pulleys above the plate. This is a compact plate-mounted architecture; approve or revise at the proceed gate.
- The selected 70 mm center distance is a compact layout assumption, not user-provided.
- A 20T/20T GT2 pair gives a 1:1 ratio. Change tooth counts before approval if a different ratio is required.
- A nominal 180 mm GT2 belt is derived for the initial layout. Final belt source, tension, and tooth count must be confirmed.
- The selected `belt_mid_plane_z` assumes the motor shaft length and pulley hub allow a 6 mm belt above a 6 mm plate. Confirm the exact motor shaft length and pulley hub dimensions before final CAD.
- A single 608 bearing is represented because the prompt requested a 608 bearing support. If the belt load or shaft overhang is significant, detail design should use paired bearings or an additional support, returning to layout review if the assembly graph changes.
- Bearing fit class, shaft retention, pulley set-screw flats, motor cable keep-out, and fastener stack lengths are not certified by the layout proxy.

## Proceed Gate

Layout verdict target: `ready_for_review`.

Review the rough layout for positioning, interfaces, and drivetrain structure. If the vertical shaft architecture, 70 mm center distance, 13.5 mm belt mid-plane, NEMA 17 mounting pattern, 608 bearing support location, GT2 pulley pair, and belt path are correct, say "proceed" and detail modeling can preserve these locked facts.

Allowed detail-stage changes after approval:

- Replace proxy bodies with sourced STEP/STP or detailed generated geometry.
- Add cosmetic fillets, chamfers, labels, and fastener head detail.
- Add motor wire keep-out and non-interfering cable routing.
- Add set-screw flats, retaining rings, and bearing retainers if they do not move locked axes or belt plane.
- Add motor slots for tension only if the approved nominal axis locations remain represented or the change returns to the proceed gate.

Changes requiring return to layout:

- Changing shaft orientation, center distance, belt plane height, pulley tooth count, drivetrain ratio, mounting face location, bearing support count, or assembly graph.
- Moving motor or output shaft axes.
- Replacing the single-bearing support with a different support topology.

## Downstream CAD Handoff

Target harness: build123d-compatible layout proxy adapter generated by Zen CAD runtime; downstream detail CAD can target build123d, CAD Skills/text-to-cad, CadQuery, FreeCAD, or another harness after proceed approval.

Instructions for downstream generation:

- Use low visual fidelity but high interface fidelity during layout.
- Preserve the locked layout facts exactly.
- Model base plate, motor envelope, two GT2 pulley pitch references, GT2 belt envelope, 608 bearing support, output shaft, and M3 fastener axes.
- Do not treat viewer screenshots as completion evidence; use source-level parameters, datums, labels, and measured axes/distances.
- Stop if source geometry or final part selection changes any approved locked layout fact.
