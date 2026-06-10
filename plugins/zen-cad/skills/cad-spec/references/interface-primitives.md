# Interface Primitives

Read this when a spec needs mating surfaces, shafts, bores, bolt patterns, belt/gear references, rails, slots, or fastening features.

## Principle

Assemblies are mostly governed by simple interface primitives. Name those primitives explicitly so low-detail CAD can still be mechanically meaningful.

## Common Primitives

Use these names where applicable:

- `datum_plane`: mounting face, seating face, lid underside, bracket face.
- `axis`: shaft centerline, hinge axis, pulley axis, bearing axis, screw axis.
- `cylinder`: bore, shaft, boss, bearing seat, spacer, wheel, roller.
- `bolt_pattern`: count, diameter, circle/rectangle pattern, hole size, orientation.
- `slot`: width, length, end radii, travel axis, centerline.
- `rail`: guide axis, carriage envelope, datum face, travel range.
- `pitch_circle`: gear, pulley, sprocket, or timing pulley reference.
- `belt_plane`: belt mid-plane, width envelope, span direction, pulley alignment.
- `keep_out`: volume or envelope that detail geometry must not invade.
- `clearance`: minimum gap, nominal gap, or intentional interference.

## Interface Signature Shape

When a standard interface is known, write a compact signature instead of a full catalog part:

```text
Interface signature: NEMA17 face
- frame size: 42.3 mm nominal
- pilot diameter: 22 mm
- shaft diameter: 5 mm
- mount pattern: 4 holes on 31 mm square
- shaft axis: normal to motor face
```

Signatures are layout facts, not procurement proof. They can drive layout proxies before supplier STEP files exist.

## Quality Rules

- A proxy may simplify visual geometry but must preserve interface primitive dimensions.
- A standard part may be represented by an envelope in layout when the interface signature is sufficient.
- A downstream CAD generator must not infer a mating axis from appearance when the spec can name it.
- If an interface controls motion or fit, give it an id so validation and proceed review can reference it.
