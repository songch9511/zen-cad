# Detail Shape Plan

A detail shape plan turns user shape intent into CAD that preserves locked layout facts. Use `schemas/detail_shape_plan.schema.json`.

## Zone Model

Split each custom part into three zones:

- `protected interface zone`: bores, shafts, bearing seats, mounting planes, bolt patterns, pitch references, clearance envelopes, and motion sweeps. These are not editable by style intent.
- `functional structure zone`: ribs, webs, bosses, bridges, wall thickness, support paths, and manufacturing allowances that connect protected zones.
- `freeform/style zone`: outer silhouette, corner treatment, pockets, cosmetic relief, and industrial design features that do not affect locked facts.

## Shape Intent

Record:

- style phrase, e.g. compact rounded triangular bracket;
- manufacturing method, e.g. CNC machined, 3D printed, sheet metal;
- minimum wall thickness;
- fillet/chamfer preference;
- features to avoid, such as sharp internal corners, hidden fasteners, unsupported overhangs, or unreachable pockets.

## Feature Ordering

Generate in this order:

1. base envelope around locked interfaces;
2. protected holes, bores, seats, planes, and clearance cutouts;
3. structural ribs, bosses, shells, and load paths;
4. weight relief and style features;
5. edge treatment.

The first two groups are constraint-preserving features. The last groups are allowed to change during repair.

## Inspection Gate

The detail candidate must measure:

- protected frame origin and axis residuals;
- bore/shaft diameters and centerlines;
- bolt circle or repeated pattern position;
- minimum wall around protected zones;
- clearance envelopes and motion sweeps;
- bbox/volume sanity only as secondary evidence.

If a style feature causes any protected measurement to fail, remove or resize the style feature first.
