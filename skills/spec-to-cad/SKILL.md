---
name: spec-to-cad
description: Turn a measurable specification into a verified parametric CAD implementation using explicit CONTACT_MAP/CONNECTIONS, kernel-backed physical validation, full-CAD dynamic smoke tests, independent verifier harnesses, and failure-driven iteration.
---

# Spec-to-CAD

Use this skill when a user asks to create, improve, or validate a CAD model from a specification, reference product, drawing, benchmark, or loosely described mechanical concept. The workflow converts ambiguous requirements into a measurable spec, implements a parametric CAD/GFL/CadQuery model, and verifies it with independent test harnesses, CAD-kernel evidence, artifact checks, and, when needed, dynamic simulation.

The central rule: **do not accept visual inspection, metadata-only claims, or worker reports as completion**. Completion requires reproducible CLI/JSON evidence and independent verification.

## Prerequisites

- A target workspace directory is known and writable.
- The requested CAD scope is inside the user's stated goal.
- Irreversible, user-facing, or scope-expanding decisions use `ask_to_user` with a safe default.
- At least one CAD implementation stack is available or selectable, e.g. GFL, CadQuery, OpenCascade/OCP, FreeCAD, STEP/STL export, or another kernel-backed toolchain.
- For mechanical assemblies, acceptance must include kernel-backed checks, not only metadata or screenshots.
- For dynamic checks on macOS, prefer **MuJoCo** as the default rigid-body/contact smoke-test backend. Keep Drake/Isaac Sim optional unless the user explicitly chooses them and the target environment supports them.

---

## Standard Procedure

### 0. Define the goal

Start by making the project goal explicit:

- What device or mechanism is being modeled?
- What CAD artifacts are required?
- What physical behavior or assembly constraints must be verified?
- Which checks count as completion?

For a mechanical assembly, the goal should usually include:

- Part count and key dimensions
- STEP/STL generation
- Connection/contact coverage
- No floating parts
- Fastener or mechanical evidence for connections
- CAD-kernel shape validity
- Contact/clearance distance checks
- Unexpected interference checks
- Optional dynamic smoke test with explicit runtime evidence
- Machine-readable JSON acceptance output

---

### 1. Write a measurable spec before modeling

Create or update a spec document such as `spec.md` before CAD implementation.

The spec must contain measurable requirements, not vague descriptions.

Include:

1. **Device purpose and operating envelope**
   - Example: high-speed powder mill, rotor diameter, max RPM, motor power, throughput assumptions.

2. **Critical dimensions**
   - Rotor diameter
   - Shaft centerline and bearing positions
   - Housing dimensions
   - Clearances
   - Wall thicknesses
   - Seal/coupling/flange positions

3. **Part and subassembly targets**
   - Expected total part count
   - Rotating vs fixed components
   - Major subassemblies
   - Required named parts

4. **Connection requirements**
   - `CONTACT_MAP`
   - `CONNECTIONS`
   - Expected connection count
   - Connection type: `bolted`, `flanged`, `coaxial`, `seated`, `supported`, `clamped`, etc.
   - Evidence feature: bolt, screw, flange, bearing seat, clamp, bracket, boss, dowel, retaining ring, seal cartridge, etc.
   - Nominal clearance and tolerance
   - Intentional overlaps or whitelisted contacts
   - Forbidden floating components

5. **Validation criteria**
   - Shape validity
   - Contact distance
   - Clearance tolerance
   - Unexpected interference
   - No-floating graph coverage
   - Fastener evidence
   - Dynamic smoke test if required

6. **CLI/JSON contract**
   - `--json`
   - `--contact-smoke --json`
   - `--physical-check --json`
   - `--export-step`
   - `--export-stl`
   - `--dynamic-sim-suite`
   - `--dynamic-backend mujoco`

Unknowns should be recorded as assumptions, not hidden.

---

### 2. Choose execution mode and worker roles

Use direct mode only for small edits or quick checks.

For full spec-to-CAD work, prefer delegation:

- **Lead**
  - Owns user communication
  - Freezes spec and acceptance criteria
  - Assigns worker tasks
  - Runs or verifies final evidence
  - Performs completion audit

- **Coder / CAD implementer**
  - Implements production CAD/GFL/CadQuery source
  - Adds CLI options
  - Generates STEP/STL/JSON/MJCF/artifacts
  - Fixes geometry/runtime failures

- **Verifier**
  - Builds independent pytest harnesses
  - Defines acceptance checklist
  - Rejects fake PASS
  - Does not loosen production acceptance by editing tests to match bad output
  - Should avoid modifying production CAD source unless explicitly asked

Worker briefs must include:

- Concrete goal
- Absolute target directory
- Files in scope and out of scope
- Spec path
- Expected CLI commands
- Expected JSON fields
- Verification command
- Non-goals
- Skill reference: `spec-to-cad`

---

### 3. Implement the parametric CAD model

Use a production script such as:

```text
GFL/test_materials/<model_name>.py
```

Implementation requirements:

- Generate real CAD solids, not only placeholder metadata.
- Avoid accepting primitive/proxy-only geometry as final full-CAD output.
- Name every important part.
- Record part role, location, material/assumption, and connection metadata.
- Keep geometry parametric enough to adjust dimensions and clearances.
- Export required artifacts.

Typical JSON metadata:

```json
{
  "part_count": 313,
  "rotor_diameter_mm": 160,
  "max_rpm": 18000,
  "expected_connections": 29,
  "connections": [],
  "contact_map": [],
  "generated_artifacts": {}
}
```

---

### 4. Implement basic artifact generation

The CAD script should support basic JSON and export modes:

```bash
python3 GFL/test_materials/high_speed_powder_mill.py --json
```

```bash
python3 GFL/test_materials/high_speed_powder_mill.py \
  --export-step \
  --export-stl \
  --json
```

Required artifacts:

- STEP file
- STL file
- JSON summary
- Part metadata
- Connection metadata
- Artifact manifest

Acceptance checks:

- Files exist.
- Files are non-empty.
- STEP terminates with `END-ISO-10303-21` when applicable.
- STL has plausible binary size and triangle count when applicable.
- JSON reports artifact paths.
- Part and connection counts match the spec.

---

### 5. Do metadata validation, but never stop there

Metadata validation is useful as a first screen, but it is not sufficient for completion.

Check:

- `part_count == expected part count`
- `expected_connections == required connection count`
- Each connection has `shape_a`, `shape_b`, and `connection_type`.
- Each connection has `nominal_clearance_mm` and `tolerance_mm`.
- Each connection has evidence features.
- No-floating summary exists.
- Limitations are explicit.

Important: metadata-only PASS is a fake PASS. Use it only as input to kernel validation.

---

### 6. Implement `--physical-check --json`

Mechanical assemblies need a physical validation CLI:

```bash
python3 GFL/test_materials/high_speed_powder_mill.py \
  --physical-check \
  --json
```

Required JSON fields:

```json
{
  "physical_check_supported": true,
  "physical_check_passed": true,
  "kernel_backend": "OCP/CadQuery",
  "cadquery_version": "...",
  "ocp_version": "...",
  "part_count": 313,
  "expected_connections": 29,
  "connections_checked": 29,
  "invalid_shapes": [],
  "contact_failures": [],
  "clearance_failures": [],
  "unexpected_interferences": [],
  "limitations": []
}
```

The JSON must distinguish:

- Unsupported check
- Check not run
- Check run and passed
- Check run and failed

Do not set pass booleans to `true` unless the check actually executed.

---

### 7. Validate shape validity with `BRepCheck_Analyzer`

For OCP/CadQuery workflows, validate all major shapes with `BRepCheck_Analyzer` or an equivalent CAD-kernel validity check.

Expected JSON pattern:

```json
{
  "methods": {
    "shape_validity": "BRepCheck_Analyzer"
  },
  "shape_validity_checked": 313,
  "shape_validity_count": 313,
  "invalid_shapes": []
}
```

Procedure:

1. Collect every part's `TopoDS_Shape`.
2. Run `BRepCheck_Analyzer(shape).IsValid()` or equivalent.
3. Record checked count.
4. Record invalid shape names and diagnostic information.
5. Fail if invalid shapes exist.

Acceptance guidelines:

- `shape_validity_checked` should cover the full assembly or a justified subset.
- For full PM160-style assemblies, require at least 300 checked shapes when the expected part count is 313.
- `shape_validity_count == shape_validity_checked`.
- `invalid_shapes == []`.

---

### 8. Validate connection/contact distance with `BRepExtrema_DistShapeShape`

Every expected connection must have kernel-backed distance or contact evidence.

Expected JSON pattern:

```json
{
  "expected_connections": 29,
  "connections_checked": 29,
  "contact_distance_check_count": 29,
  "contact_distance_checks": [],
  "contact_failures": [],
  "clearance_failures": []
}
```

Each connection record should include:

```json
{
  "connection_id": "rotor_to_shaft",
  "shape_a": "rotor",
  "shape_b": "drive_shaft",
  "connection_type": "coaxial_press_fit",
  "nominal_clearance_mm": 0.0,
  "tolerance_mm": 0.2,
  "best_pair": {
    "distance_mm": 0.03
  },
  "passed": true
}
```

Procedure:

1. Iterate over `CONNECTIONS`.
2. Resolve `shape_a` and `shape_b` to real kernel shapes.
3. Run `BRepExtrema_DistShapeShape` or equivalent.
4. Compute minimum distance.
5. Compare against connection-type tolerance.
6. Record finite distance evidence.
7. Add failures to `contact_failures` or `clearance_failures`.

Acceptance guidelines:

- `connections_checked == expected_connections`.
- `contact_distance_check_count == expected_connections`.
- Every passing connection has finite `best_pair.distance_mm`.
- Every check exposes `shape_a`, `shape_b`, `nominal_clearance_mm`, and `tolerance_mm`.
- `contact_failures == []`.
- `clearance_failures == []`.

---

### 9. Validate unexpected interference with AABB + `BRepAlgoAPI_Common`

Unexpected interference checks should run in two stages.

#### 9.1 Broad phase

Use AABB or equivalent bounding boxes to reduce candidate pairs.

Expected JSON:

```json
{
  "broad_phase": {
    "target_count": 313,
    "candidate_count": 120,
    "checked_count": 45
  }
}
```

#### 9.2 Kernel phase

For candidate pairs, use `BRepAlgoAPI_Common` or an equivalent boolean common operation to estimate overlap volume.

Expected JSON:

```json
{
  "interference_check": {
    "method": "AABB + BRepAlgoAPI_Common volume",
    "pairs_checked": 45
  },
  "unexpected_interferences": [],
  "max_unexpected_overlap_mm3": 0.0
}
```

Acceptance guidelines:

- `methods.unexpected_interference` names `BRepAlgoAPI_Common`, `AABB`, and volume evidence.
- `broad_phase.target_count > 0`.
- `broad_phase.candidate_count > 0`.
- `broad_phase.checked_count > 0`.
- `candidate_count >= checked_count`.
- `interference_check.pairs_checked == broad_phase.checked_count`.
- Whitelist or intended-contact basis is explicit.
- `unexpected_interferences == []`.
- `max_unexpected_overlap_mm3` is finite.

Implementation guardrails:

- Handle null/empty common shapes.
- Avoid `StopIteration` or empty-volume crashes.
- Separate intended overlaps/contacts from unexpected interferences.

---

### 10. Validate no-floating graph coverage

Build a connection graph.

Procedure:

1. Register each part as a graph node.
2. Register each valid connection as a graph edge.
3. Choose root assembly components.
4. Traverse from root.
5. Mark unreachable parts as floating.
6. Report floating parts in JSON.

Expected JSON:

```json
{
  "no_floating_check_passed": true,
  "floating_parts": [],
  "connected_part_count": 313
}
```

Acceptance guidelines:

- No-floating summary is tied to graph/connection coverage, not just metadata presence.
- `floating_parts == []`.
- Connected part count is consistent with the part count or explicitly justified.

---

### 11. Validate fastener/mechanical evidence

Each mechanical connection must have concrete evidence, not only a claim that two parts are connected.

Evidence examples:

- Bolt
- Screw
- Clamp
- Flange
- Dowel
- Bearing seat
- Retaining ring
- Seal cartridge
- Bracket
- Boss
- Coupling

Expected JSON:

```json
{
  "fastener_evidence_passed": true,
  "missing_fastener_evidence": []
}
```

Acceptance guidelines:

- Each major connection maps to physical evidence.
- Small components such as sensor bosses, seal cartridges, bearing housings, guards, brackets, and covers must not be ignored.
- If simplified geometry represents a real fastener, record the simplification in `limitations`.

---

### 12. Implement MuJoCo full-CAD dynamic smoke test when required

For dynamic rigid-body/contact smoke tests, prefer MuJoCo as the default macOS-compatible backend.

Example CLI:

```bash
python3 GFL/test_materials/high_speed_powder_mill.py \
  --dynamic-sim-suite \
  --dynamic-backend mujoco \
  --dynamic-output-dir GFL/test_materials/pm160_mujoco_full_model \
  --json
```

Required behavior:

- Use full-CAD STL/mesh-based MJCF where the acceptance requires full-CAD evidence.
- Do not accept primitive/proxy-only runtime as full-CAD acceptance.
- Generate runtime artifacts.
- Record whether MuJoCo actually ran.
- Record unexpected collision pairs.
- Record visual/collision limitations honestly.

Expected JSON:

```json
{
  "source_stl": "GFL/test_materials/high_speed_powder_mill.stl",
  "ran_in_mujoco": true,
  "runtime_status": "executed",
  "mujoco_version": "3.8.1",
  "simulated_steps": 240,
  "joint_failures": [],
  "unexpected_collision_pairs": [],
  "full_cad_mesh_runtime": true,
  "not_a_primitive_proxy_video": true,
  "part_mesh_count": 313,
  "dynamic_rotor_mesh_count": 82,
  "fixed_mesh_count": 231,
  "mesh_export_failures": [],
  "mp4": "...runtime.mp4",
  "gif": "...runtime.gif"
}
```

Acceptance guidelines:

- `ran_in_mujoco == true` for runtime acceptance.
- `runtime_status == "executed"`.
- `simulated_steps >= 240` unless the spec sets another threshold.
- `joint_failures == []`.
- `unexpected_collision_pairs == []`.
- `part_mesh_count` meets the expected full-CAD part/mesh threshold.
- `source_stl` points to the canonical STL.
- MP4/GIF artifacts exist and are non-empty when required.
- The result explicitly says whether it is full-CAD or proxy/primitive.

---

### 13. Create independent verifier harnesses

Production code should not be trusted to declare itself complete. Create independent tests under `tests/`.

Example harness files:

```text
tests/test_pm160_kernel_physical_validation_harness.py
tests/test_pm160_physical_acceptance_harness.py
tests/test_pm160_fastener_evidence_harness.py
tests/test_pm160_full_cad_mujoco_harness.py
```

Verifier harnesses should enforce:

- CLI flags exist and return JSON.
- JSON schema is stable.
- `physical_check_supported is True` when acceptance depends on physical checks.
- `physical_check_passed is True` only when kernel checks ran.
- Kernel backend names OCP/CadQuery or the selected equivalent.
- Version fields are present.
- `BRepCheck_Analyzer` shape validity evidence is present.
- `BRepExtrema_DistShapeShape` connection distance evidence is present.
- `BRepAlgoAPI_Common` + AABB interference evidence is present.
- All expected connections are checked.
- No floating parts remain.
- Fastener evidence is complete.
- Full-CAD dynamic smoke test is not primitive/proxy-only.
- Generated artifacts exist.
- Limitations are non-empty and honest.

Canonical combined verification command pattern:

```bash
cd /Users/vanta/.cobra/workspace/GFL

python3 -m pytest \
  tests/test_pm160_kernel_physical_validation_harness.py \
  tests/test_pm160_physical_acceptance_harness.py \
  tests/test_pm160_fastener_evidence_harness.py \
  tests/test_pm160_full_cad_mujoco_harness.py \
  -q
```

Adapt file names to the project.

---

### 14. Run regression/package acceptance from the lead context

Before declaring completion, verify with tools in the lead context. Worker reports are not enough.

Example PM160-style acceptance sequence:

```bash
cd /Users/vanta/.cobra/workspace/GFL

python3 -m py_compile GFL/test_materials/high_speed_powder_mill.py

python3 GFL/test_materials/high_speed_powder_mill.py --json

python3 GFL/test_materials/high_speed_powder_mill.py \
  --contact-smoke \
  --json

python3 GFL/test_materials/high_speed_powder_mill.py \
  --physical-check \
  --json

python3 GFL/test_materials/high_speed_powder_mill.py \
  --export-step \
  --export-stl \
  --json

python3 GFL/test_materials/high_speed_powder_mill.py \
  --dynamic-sim-suite \
  --dynamic-backend mujoco \
  --dynamic-output-dir GFL/test_materials/pm160_mujoco_full_model \
  --json

python3 -m pytest \
  tests/test_pm160_kernel_physical_validation_harness.py \
  tests/test_pm160_physical_acceptance_harness.py \
  tests/test_pm160_fastener_evidence_harness.py \
  tests/test_pm160_full_cad_mujoco_harness.py \
  -q
```

Minimum final evidence:

- Source compiles.
- JSON summary runs.
- Contact/assembly smoke check runs.
- Physical/kernel check runs and passes.
- STEP/STL artifacts exist.
- Independent verifier harness passes.
- Dynamic smoke test passes if in scope.
- Generated artifacts exist at expected paths.

---

### 15. Use failure-driven self-evolution

When a test fails, do not retry the same thing blindly.

Failure loop:

1. Read the exact failure message.
2. Classify the failure:
   - CLI missing
   - JSON schema missing
   - Metadata mismatch
   - Geometry/kernel failure
   - Contact/clearance failure
   - Unexpected interference
   - Floating part
   - Fastener evidence gap
   - Dynamic runtime issue
   - Artifact missing
3. Modify the production script, spec, or harness as appropriate.
4. Regenerate artifacts.
5. Run the narrow failing harness first.
6. Run the full regression suite after the narrow fix passes.
7. Update `limitations` and the spec so the failure cannot recur silently.

Examples:

- Add empty-common guards after boolean common/volume failures.
- Add explicit tolerances when simplified geometry represents seated components.
- Add harness assertions to prevent fake PASS.
- Add connection evidence fields when floating parts are discovered.
- Add `visual_collision_limitations` when MuJoCo visual mesh and collision semantics differ.

Forbidden fixes:

- Metadata-only fake PASS.
- Loosening tests to accept incomplete output.
- Claiming primitive/proxy runtime as full-CAD validation.
- Setting `ran_in_mujoco=true` without actual runtime execution.
- Matching connection count while omitting kernel evidence.
- Reporting completion from worker text without lead-side verification.

---

### 16. Completion criteria

Declare completion only when every in-scope deliverable has tool-backed evidence.

Checklist:

```text
[CAD artifacts]
- STEP generated
- STL generated
- JSON summary generated
- Artifact paths recorded

[Model completeness]
- part_count == expected part count
- expected_connections == required connection count
- all expected connections represented
- no floating parts

[Kernel physical validation]
- BRepCheck_Analyzer or equivalent shape validity passes
- BRepExtrema_DistShapeShape or equivalent contact/clearance passes
- AABB + BRepAlgoAPI_Common or equivalent unexpected interference check passes
- unexpected_interferences == []

[Fastener evidence]
- all major connections have physical evidence
- missing_fastener_evidence == []

[Dynamic simulation, if in scope]
- MuJoCo or selected backend actually ran
- full-CAD mesh path is explicit when required
- joint_failures == []
- unexpected_collision_pairs == []
- runtime artifacts exist

[Regression]
- py_compile passes
- CLI commands pass
- independent pytest harnesses pass
```

If any item lacks direct evidence, the project is not complete.

---

### 17. Completion report

The final user report should include:

- What was built
- Exact source paths
- Exact artifact paths
- Commands run
- Pass/fail results
- Key counts and dimensions
- Kernel/backend versions
- Dynamic runtime status if applicable
- Known limitations
- What was deliberately not certified

Always distinguish:

- CAD assembly/contact/interference validation
- FEA
- thermal analysis
- vibration/rotordynamics
- bearing life
- manufacturability
- regulatory certification

Do not imply that unperformed analyses were completed.

---

## Short Form

Use this condensed sequence when briefing workers or auditing progress:

```text
1. Write measurable spec.md with dimensions, CONTACT_MAP, CONNECTIONS, tolerances, artifact and CLI/JSON requirements.
2. Implement parametric GFL/CadQuery production model.
3. Add STEP/STL/JSON export CLI.
4. Add CONTACT_MAP / CONNECTIONS / fastener evidence.
5. Add --physical-check --json.
6. Use BRepCheck_Analyzer for shape validity.
7. Use BRepExtrema_DistShapeShape for all expected contact/clearance checks.
8. Use AABB + BRepAlgoAPI_Common volume for unexpected interference checks.
9. Use graph coverage for no-floating validation.
10. Add MuJoCo full-CAD dynamic smoke test when in scope.
11. Generate runtime artifacts such as MJCF, JSON, MP4, GIF when required.
12. Build independent pytest verifier harnesses.
13. Run lead-side regression commands.
14. On failure: fix production/spec/harness, regenerate artifacts, rerun narrow test, then full regression.
15. Declare completion only when all CLI, artifact, kernel, dynamic, and independent harness checks pass.
```
