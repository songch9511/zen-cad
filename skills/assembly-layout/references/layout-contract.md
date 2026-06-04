# Layout Contract

A layout contract describes how an assembly is organized before detail geometry is generated.

## Required Items

- root component;
- root frame;
- part list with roles;
- part-local frames;
- contact relationships;
- connection relationships;
- motion relationships;
- clearance and keep-out envelopes;
- locked facts;
- proxy parts and their trustworthy interfaces.

## Contact Relationship

Use contacts for geometry adjacency or clearance:

```text
contact: motor_face_to_plate
- part_a: motor_proxy
- part_b: mount_plate
- relationship: flush_plane
- expected_gap_mm: 0
- locked: true
```

## Connection Relationship

Use connections for attachment or power/motion transfer:

```text
connection: pulley_to_motor_shaft
- type: coaxial_clamp
- shaft_axis: motor_shaft_axis
- bore_diameter_mm: 5
- locked: true
```

## Locked Facts

Locked facts should be stable enough to drive detail modeling:

- axis directions;
- center distances;
- part transforms;
- mounting pattern coordinates;
- pitch references;
- clearances;
- travel limits;
- fixed/moving hierarchy.
