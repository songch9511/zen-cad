# Motion And Drivetrain

Read this when the design moves or transmits force through belts, pulleys, gears, screws, sliders, rails, shafts, bearings, or linkages.

## Required Motion Facts

For every moving relationship, state:

- joint type: fixed, revolute, prismatic, cylindrical, hinge, slider, belt, gear mesh, screw, linkage;
- moving frame and fixed frame;
- axis direction in the root frame;
- nominal pose for the first CAD artifact;
- travel or rotation limits;
- center distance or offset;
- clearance envelope;
- driven and passive components;
- ratio, pitch, lead, or tooth count when known;
- assumptions that must be confirmed before detail or final.

## Belt And Pulley Specs

For belt-driven layouts, define:

- belt pitch;
- belt width;
- belt mid-plane;
- pulley axes;
- pulley pitch diameter or tooth count if known;
- center distance;
- straight-span direction;
- tensioning/idler strategy;
- clearance around moving belt spans.

The layout proxy may use smooth cylinders or coarse teeth, but pitch plane, axes, center distance, and belt span envelopes must be correct.

## Gear Specs

For gear layouts, define:

- gear type;
- module or pitch;
- tooth count;
- pitch diameter;
- shaft axes;
- center distance;
- mesh plane;
- intended ratio;
- backlash or clearance assumption.

The layout proxy may use simplified teeth, but pitch circles and shaft axes must be correct.

## Rail, Screw, And Slider Specs

For linear motion, define:

- travel axis;
- carriage frame;
- rail/guide datum faces;
- screw or belt drive axis;
- end stops or travel limits;
- moving envelope and keep-outs;
- coupling to motor or driven element.

## Reporting

Separate motion facts from engineering claims. A CAD spec can define geometry and kinematics; it does not prove torque, speed, life, stiffness, backlash, thermal behavior, or safety without downstream analysis.
