# Review Checklist

Use this checklist before allowing detail CAD to proceed from a layout proxy.

## User Review

Ask the user to inspect:

- Does the fixed/root component make sense?
- Are moving axes oriented correctly?
- Are center distances and offsets plausible?
- Do shafts, bores, bearings, and pulleys share the intended axes?
- Are belt, gear, rail, screw, or linkage relationships positioned correctly?
- Are mounting faces and bolt patterns on the intended sides?
- Are clearance and keep-out envelopes visible and plausible?
- Are proxies acceptable for this stage?

## Generator Evidence

Ask the generator or reviewer to return:

- source-level placement method: joints, transforms, constraints, or explicit coordinates;
- generated artifact path;
- bounding box and top-level labels;
- checks for locked distances, axes, frames, or mating relationships;
- snapshot or viewer link when supported;
- failed or skipped checks with reasons.

## Detail May Change

Detail modeling may change:

- surface smoothness;
- fillets and chamfers;
- thread representation;
- tooth fidelity;
- supplier body contours;
- labels;
- export formats.

## Detail Must Not Change

Detail modeling must not change:

- root frame;
- assembly graph;
- fixed/moving hierarchy;
- axes;
- center distances;
- part transforms;
- pitch references;
- mounting faces;
- bolt patterns;
- clearances;
- travel ranges.

If any protected item must change, return to layout review.
