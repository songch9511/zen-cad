# CAD Spec: Flat Planetary Gear Assembly

## Intent

Create a flat planetary gear assembly with separate sun, three planet, ring, carrier, and pin bodies. The current CAD artifact is a build123d STEP review model using module-locked involute gear geometry for the sun and planets, plus a negative involute cutter method for the internal ring gear. A premium-detail pass adds root fillets, raised hub bosses, ring lips, mount holes, carrier lightening holes, and filleted pin caps without changing locked mesh geometry. This is a stronger drivetrain-layout model than the earlier trapezoid proxy, but it is still not a load-rated or manufacturing-certified gearset.

## Coordinate System

- Units: millimeters.
- Root frame: `sun_axis`, origin at the sun gear axis.
- Base plane: XY gear plane.
- Up axis: +Z through all gear, carrier, and pin axes.
- Nominal pose: ring and sun are coaxial at world origin; planets and pins are arranged at 0, 120, and 240 degrees on a 42 mm radius circle.

## Parameter Contract

| Name | Value | Status | Source | Drives | Validation |
| --- | ---: | --- | --- | --- | --- |
| `planet_radius` | 42 mm | locked | user | planet and pin axis placement | `check_planet_radius` |
| `planet_count` | 3 | locked | user | repeated planet, pin, and carrier hole pattern | `check_separate_bodies`, `check_planet_radius` |
| `gear_module` | 2 mm | derived | `2 * planet_radius / (sun_teeth + planet_teeth)` | shared pitch system | `check_module_locked_ring_mesh` |
| `pressure_angle` | 14.5 deg | assumed | involute generator constraint for the 60T internal cutter | sun, planet, and ring cutter tooth profiles | `check_involute_teeth` |
| `sun_tooth_count` | 24 | assumed | layout assumption | sun involute tooth pattern | `check_involute_teeth` |
| `planet_tooth_count` | 18 | assumed | layout assumption | three planet involute tooth patterns | `check_involute_teeth` |
| `ring_tooth_count` | 60 | derived | `ring = sun + 2 * planet` | internal ring tooth spaces | `check_module_locked_ring_mesh` |
| `sun_pitch_radius` | 24 mm | derived | `module * sun_teeth / 2` | sun pitch reference | `check_planet_radius` |
| `planet_pitch_radius` | 18 mm | derived | `module * planet_teeth / 2` | planet pitch references | `check_planet_radius` |
| `ring_pitch_radius` | 60 mm | derived | `module * ring_teeth / 2` | internal ring pitch reference | `check_planet_radius` |
| `gear_thickness` | 6 mm | assumed | layout assumption | sun, planet, and ring body thickness | STEP bbox check |
| `sun_bore_diameter` | 8 mm | assumed | layout assumption | sun center bore | `check_ring_sun_coaxial` |
| `planet_pin_diameter` | 5 mm | assumed | layout assumption | planet bores, pin cylinders, carrier holes | `check_planet_radius` |
| `ring_outer_diameter` | 144 mm | assumed | layout envelope | ring body envelope | STEP bbox check |
| `ring_cutter_scale_xy` | 1.01 | derived | static backlash proxy | internal ring tooth-space clearance | `check_no_tooth_overlap` |
| `gear_root_fillet` | 0.1 mm | assumed | detail pass | sun, planet, and ring cutter tooth roots | `check_premium_detailing` |
| `sun_hub_boss_diameter` | 18 mm | assumed | detail pass | raised sun hub boss | `check_premium_detailing` |
| `planet_hub_boss_diameter` | 11.5 mm | assumed | detail pass | raised planet hub bosses | `check_premium_detailing` |
| `ring_mount_holes` | 6 holes on R68 mm | assumed | detail pass | ring mounting/detail holes | `check_premium_detailing` |
| `carrier_lightening_holes` | 6 holes on R30 mm | assumed | detail pass | carrier visual/weight relief | `check_premium_detailing` |

Derived pitch relationships:

- Sun/planet center distance: `24 + 18 = 42 mm`.
- Planet/ring center distance: `60 - 18 = 42 mm`.
- Ring tooth relation: `60 = 24 + 2 * 18`.
- Three-planet spacing condition: `(sun_teeth + ring_teeth) / 3 = 28`, an integer.

## Artifact Targets

- Maturity target: `detail_cad` review model from a layout-approved contract.
- CAD source intent: build123d with `bd_warehouse.gear.SpurGear`.
- Primary artifact: `layout_proxy_build123d.step`.
- Review artifacts: STEP generation inspection report, supplemental geometry report, viewer link, viewer snapshot PNG, layout snapshot PNG, proceed gate package.
- Source of truth: this Markdown spec and `package/cad_spec.json`; generated STEP and snapshots are derived evidence only.

## Parts And Roles

- `sun_gear`: 24T involute spur gear, centered at `sun_axis`.
- `planet_gear_1`, `planet_gear_2`, `planet_gear_3`: 18T involute planet gears centered on the locked 42 mm radius circle.
- `ring_gear`: fixed 60T internal ring gear made by subtracting a scaled 60T involute spur cutter from an annular blank; includes outer lips and six non-mesh mount holes.
- `carrier`: locator disk below the gear plane, with central bore, three pin holes, six lightening holes, and rounded outside edges.
- `pin_1`, `pin_2`, `pin_3`: separate locator pin cylinders coaxial with planet axes; each has a rounded stem and cap.

## Assembly Graph

- `sun_gear` and `ring_gear`: coaxial on the root +Z axis.
- `planet_gear_*` axes: parallel to +Z and positioned on the 42 mm radius circle.
- `pin_*` axes: coaxial with corresponding planet axes.
- `carrier`: centered on the root frame and patterned to the same three pin axes.

## Interface Primitives

- `sun_axis`: root +Z axis.
- `ring_axis`: coaxial +Z axis at origin.
- `planet_axis_1`: +Z axis at `(42, 0, 0)`.
- `planet_axis_2`: +Z axis at `(-21, 36.373, 0)`.
- `planet_axis_3`: +Z axis at `(-21, -36.373, 0)`.
- `carrier_pin_pattern`: three-hole pattern at radius 42 mm.
- `gear_pitch_references`: sun 24 mm, planet 18 mm, ring 60 mm pitch radii.
- `ring_internal_mesh`: 60T involute cutter scaled 1.01x in XY and subtracted from the ring blank; this creates static backlash in the review proxy.
- `premium_non_mesh_detail`: raised hub bosses, ring outer lips, mount holes, lightening holes, and pin caps stay outside the locked tooth contact envelopes.

## Motion And Drivetrain

The assembly represents a flat planetary stage layout. All rotating components use revolute +Z axes. Gear ratio references can be derived from sun 24T and ring 60T; with a fixed ring, the nominal carrier speed relation is `omega_carrier = omega_sun * sun / (sun + ring) = omega_sun * 24 / 84`. This review artifact does not certify torque, load, bearing strategy, lubrication, noise, or efficiency.

## Proxy Fidelity Policy

Preserve axes, pitch radii, center distance, separate body structure, carrier pin pattern, bores, and involute tooth-pattern presence. Ring backlash is represented by the scaled negative cutter. The premium-detail pass may add non-mesh shape detail, but must not alter gear centers, pitch radii, tooth counts, or Boolean no-overlap checks. Simplify material, tolerance stack, and detailed bearing/shaft interfaces.

## Locked Layout Facts

- `separate_bodies_locked`: sun, three planets, ring, carrier, and three pins remain separate logical CAD bodies.
- `planet_radius_locked`: planet and pin axes remain on a 42 mm radius circle.
- `gear_axes_parallel_locked`: all gear, carrier, and pin axes remain parallel to +Z.
- `involute_teeth_locked`: sun and planet gears use `bd_warehouse` involute SpurGear geometry; ring gear uses a matching negative involute cutter.
- `module_locked_ring_mesh_locked`: module 2 pitch system remains sun 24T, planet 18T, ring 60T with `Nr = Ns + 2Np`.
- `no_tooth_overlap_locked`: static Boolean common volume between all six meshing sun/planet and planet/ring pairs remains zero.
- `premium_detail_non_mesh_locked`: cosmetic/detail features remain outside the locked mesh envelopes.

## Inspection Plan

- Validate contract package schema.
- Generate and inspect layout proxy scene.
- Inspect build123d source carry-through.
- Generate STEP from build123d and re-import it for validity, bbox, volume, and feature-plan checks.
- Run supplemental build123d Boolean checks for all sun/planet and planet/ring mesh pairs.
- Inspect premium detailing carry-through: tooth root fillets, hub bosses, ring lips/mount holes, carrier lightening holes, pin caps, and unchanged bbox.
- Package viewer link and snapshot evidence.
- Package proceed gate with generated artifacts and inspection reports.

## Repair Loop

If a check fails, change the smallest responsible source, feature-plan parameter, datum, or artifact packaging step; regenerate affected outputs; rerun failed checks and dependent checks. If a repair requires changing the locked 42 mm planet radius, the 24/18/60 tooth-count relationship, separate-body structure, or +Z axes, return to the proceed gate instead of silently changing layout.

## Assumptions And Open Questions

- Pressure angle is 14.5 degrees because the current `bd_warehouse` involute generator rejects the 60T internal cutter configuration at 20 degrees under the chosen root/addendum settings.
- Ring tooth-space backlash is represented by scaling the negative ring cutter 1.01x in XY.
- The STEP is a static review model; it does not simulate rolling contact, load, dynamic backlash, or manufacturability.
- Some cylindrical edge rounds are torus-based build123d approximations rather than selector-derived topology fillets.
- Material, tolerances, carrier bearing strategy, ring mounting holes, and shaft interfaces are not yet locked.

## Proceed Gate

Review the STEP/viewer/snapshot for positioning, interfaces, drivetrain structure, and the new premium-detail treatment. If the separate bodies, +Z axes, 42 mm planet circle, 24/18/60 tooth-count relationship, internal ring mesh, premium non-mesh details, and zero-overlap Boolean report are acceptable, say `proceed` before production-oriented refinement.

## Downstream CAD Handoff

Target harness: build123d. Preserve all locked layout facts and stop if detail modeling would move planet axes off the 42 mm radius circle, change the module/tooth-count relationship, merge bodies, remove internal ring mesh evidence, or change the root frame.
