---
name: agentic-cad
description: Sourcing-aware mechanical CAD workflow that orchestrates requirements, research, Part RAG, custom CAD, validation, BOM, and engineering reporting.
version: 0.1.1
---

# Agentic CAD

## Purpose

`/agentic-cad` is a top-level harness-native mechanical CAD workflow skill. It turns ambiguous natural-language mechanical design goals into a first useful CAD artifact, then layers sourcing, validation, BOM, and engineering reporting as the required maturity increases.

It is not trying to replace text-to-CAD generators. It leverages the host harness and available CAD plugins/tools first, then uses Zen CAD conventions to keep assumptions, proxies, sourcing gaps, and final evidence honest.

Core principle: **Generate concept/layout CAD early; enforce source-lock and completion evidence only for final/release claims.**

## When to use

Use `/agentic-cad` when the task is a mechanical design project that needs more than a single CAD body, especially when it involves:

- ambiguous natural-language mechanical requirements;
- mechanisms, assemblies, frames, housings, brackets, adapters, fixtures, links, plates, shafts, or moving interfaces;
- motors, bearings, screws, rails, connectors, sensors, O-rings, springs, belts, pulleys, fasteners, or catalog components;
- engineering calculations, load/speed/torque/clearance sizing, or design assumptions;
- CAD files plus BOM, sourcing notes, validation evidence, and final reporting;
- a need to distinguish sourced standard parts from custom-designed geometry.

Do not use this skill as a shortcut for creating decorative or approximate CAD from text. If the job is only a narrow parametric CAD generation task with a complete measurable spec and no sourcing/architecture work, invoke `/spec-to-cad` directly instead.

## Zen CAD prompt-first milestone startup

When running inside a Zen CAD repository, a natural-language CAD goal at the start of a new CoBrA/agent session is a milestone-start request. For example, if the user says `기어 박스를 만들고 싶어`, do not ask the user to run a Python command and do not require the user to manually choose a milestone id/title.

When this skill is installed into CoBrA, first check whether a sibling `ZEN_CAD_WORKSPACE.md` exists next to this `SKILL.md`. If present, read it and use its `Repository root:` path as the Zen CAD workspace unless the user explicitly provides another root. This is the CoBrA adapter binding created by `./zen-cad init --with-cobra`.

Instead, from the Zen CAD repository root, internally run:

```bash
python3 scripts/new_milestone.py --request "<goal>"
```

Use the created milestone as the active CAD job. For `기어 박스를 만들고 싶어`, the expected derived milestone is the next available `*_gearbox`, such as `003_gearbox` in this repository, titled `Gearbox`. After creation, continue this `/agentic-cad` workflow inside that milestone, generate the first CAD artifact with the available harness toolchain, and reserve completion-script evidence for final/release claims.

## Execution mode

For non-trivial mechanical CAD projects, run `/agentic-cad` as an orchestration workflow rather than a single-shot CAD generation prompt. Split the work into roles or internal workstreams when the scope warrants it:

- **Requirements / Systems Engineer** — extracts goals, constraints, units, interfaces, loads, envelope, and acceptance criteria.
- **Research / Standards / Catalog Engineer** — finds reference designs, catalog parts, datasheets, standards, and credible manufacturer sources.
- **Mechanical Sizing Engineer** — performs first-order engineering calculations, sizing, margins, and assumptions.
- **Part Sourcing / STEP RAG Worker** — searches for off-the-shelf STEP/catalog parts and records source, metadata, dimensions, and limitations.
- **CAD Generator via `/spec-to-cad`** — generates only design-specific custom parts and assembly glue from a measurable handoff.
- **Assembly / Validation Worker** — verifies fit, interfaces, CONTACT_MAP, CONNECTIONS, collisions, units, and export integrity.
- **Independent Verifier** — reviews whether evidence supports completion claims and flags unverified engineering assumptions.
- **Report / BOM Worker** — produces the sourcing-aware BOM, validation summary, limitations, and final engineering report.

For small tasks, these roles may collapse into one executor, but the same gates still apply: requirements, sourcing decision, CAD/custom-part decision, validation evidence, and final reporting.

## Relationship to `/spec-to-cad`

`/agentic-cad` is the upstream orchestrator. `/spec-to-cad` is a downstream execution and validation skill.

`/agentic-cad` prepares the engineering context that `/spec-to-cad` needs:

- measurable requirements and assumptions;
- researched constraints, standards, and datasheet references;
- engineering sizing calculations;
- mechanical architecture and coordinate frames;
- selected off-the-shelf parts manifest;
- custom parts list with dimensions, interfaces, tolerances, and functional intent;
- `CONTACT_MAP` and `CONNECTIONS` describing intended mating/contact/attachment relationships;
- validation criteria and expected machine-readable evidence.

`/spec-to-cad` then generates the custom CAD, integrates sourced STEP parts, builds the assembly glue, and produces reproducible CAD-kernel/CLI/JSON/test evidence where applicable.

`/spec-to-cad` must not silently replace selected catalog parts with generated lookalikes. If `/agentic-cad` says a part is sourced, `/spec-to-cad` should use the sourced STEP file or return a blocker explaining why it cannot.

## Relationship to `step-parts` / Part RAG

`step-parts`, `skills/step-parts`, `step.parts`, or another STEP Part RAG module is the retrieval layer for off-the-shelf parts. `/agentic-cad` uses it before generating any standard/catalog geometry.

Typical Part RAG targets include:

- screws, bolts, nuts, washers, threaded inserts, pins, clips, and standard fasteners;
- bearings, bushings, shafts where catalog shafts are appropriate, linear rails, guide rods, couplers, belts, pulleys, gears, sprockets, springs, O-rings, seals, and spacers;
- motors, servos, gearmotors, encoders, sensors, switches, connectors, cable glands, fans, power supplies, and other catalog electromechanical components;
- standard extrusions, plates, brackets, hinges, latches, handles, feet, and panels when credible catalog geometry exists.

The Part RAG layer finds candidate parts, ranks them, downloads/caches STEP geometry, extracts metadata, links datasheets/source URLs, and records evidence. `/agentic-cad` decides whether a retrieved part is acceptable for the design, whether the engineering rating is verified, and whether a custom part is still needed.

## Core rules

1. **Source before generating standard parts.** Do not generate standard parts when credible off-the-shelf STEP/catalog parts can be retrieved.
2. **Generate only design-specific geometry.** CoBrA-generated CAD is for housings, brackets, adapters, links, frames, fixtures, custom plates/shafts, mechanism-specific structures, and assembly glue that cannot be credibly sourced.
3. **Separate geometry from rating.** STEP geometry alone does not prove engineering rating, load capacity, electrical rating, safety rating, material, certification, or manufacturer authenticity.
4. **Track two validations for sourced parts.** `geometry_match` means the CAD shape/dimensions/interfaces appear suitable. `engineering_rating_verified` means the datasheet/source evidence supports the required load, speed, torque, voltage, current, temperature, life, environment, or certification claim.
5. **Screenshots are not completion evidence.** Viewer snapshots are human review artifacts only. They may help communicate design state but do not prove completion.
6. **Completion requires reproducible evidence.** Final claims require CLI/JSON/CAD-kernel/test evidence via `/spec-to-cad` where applicable.
7. **Do not conflate analysis domains.** Always distinguish CAD validation from FEA, thermal, vibration, fatigue, bearing life, manufacturability, compliance, and certification. CAD checks can prove geometry/connectivity/interference properties; they do not certify real-world performance by themselves.
8. **Make uncertainty visible.** Any proxy, placeholder, unverified rating, missing datasheet, untested load case, or non-manufacturing-ready feature must be explicitly flagged.

## Workflow

### 1. Frame the task and success criteria

- Restate the design goal in mechanical terms.
- Identify functional requirements, operating environment, load cases, envelope constraints, interfaces, target manufacturing methods, expected deliverables, and unknowns.
- Open an assumptions log for unresolved requirements.
- Define what counts as completion: files, manifests, validation reports, BOM, sourcing report, and final engineering report.

### 2. Extract measurable requirements

Produce a measurable spec with units. Include dimensions, forces, torques, speeds, travel, duty cycle, alignment constraints, safety factors, mass/volume limits, environmental constraints, and interface requirements when available.

If a requirement is missing, choose a conservative assumption only when safe and reversible. Record the assumption, rationale, and what would change if the user later provides the real value.

### 3. Research catalogs, standards, and datasheets

Research relevant standards, common component families, datasheets, manufacturer catalogs, and prior art. Record URLs, part numbers, rating data, dimensional data, access/license constraints, and confidence.

Do not invent manufacturer part numbers, ratings, or datasheet values. If source evidence is unavailable, mark the claim as unverified.

### 4. Perform engineering sizing

Calculate or estimate key sizing values before selecting or generating CAD. Examples:

- bearing bore/OD/load/life requirements;
- screw size, thread engagement, preload assumptions, and clearance;
- motor torque/speed/power and mounting pattern;
- shaft diameter, keyway/coupler interface, bending/torsion assumptions;
- bracket thickness, bolt pattern, clearance, and stiffness assumptions;
- gear ratio, pulley ratio, belt length, travel, and alignment;
- enclosure wall thickness, bosses, ribs, heat/ventilation allowances.

Record equations, input values, assumptions, safety factors, outputs, and limitations. Mark calculations as preliminary unless independently verified or backed by accepted standards.

### 5. Define mechanical architecture

Decompose the system into assemblies, subassemblies, functional interfaces, coordinate frames, degrees of freedom, mounting strategy, service/maintenance access, and manufacturing approach.

Identify which components carry loads, which locate geometry, which transfer motion/power, which are protective/enclosure parts, and which are purchased/catalog items.

### 6. Classify every part

Classify each part before CAD generation:

- `off_the_shelf`: standard/catalog part to retrieve via STEP Part RAG;
- `semi_standard_configurable`: catalog/configurable family should be searched first, custom generation allowed only with rationale;
- `custom_design_specific`: part to generate because it is specific to this mechanism or product;
- `placeholder_proxy`: temporary stand-in when no credible part or final geometry exists yet.

Every part in the architecture must appear in the part classification manifest. Unclassified parts are blockers.

### 7. Retrieve off-the-shelf STEP/catalog parts

For each `off_the_shelf` or source-first `semi_standard_configurable` part:

- build Part RAG queries from the measurable requirements;
- retrieve multiple candidates when possible;
- compare dimensions, interfaces, ratings, source quality, STEP availability, and assembly compatibility;
- download/cache STEP files when allowed;
- store datasheets/source URLs and evidence;
- mark `geometry_match` and `engineering_rating_verified` separately.

If no credible candidate is found, record failed queries and decide whether to revise requirements, use a clearly marked proxy, or generate a custom alternative only when it is truly design-specific.

### 8. Normalize STEP geometry and extract metadata

For every retrieved STEP file:

- confirm file path, source URL, manufacturer/part number when available;
- detect units and coordinate orientation;
- extract bounding box, mass/material if available, named bodies, principal axes, mounting holes, mating surfaces, connection points, and simplified envelope geometry;
- normalize origin/frames for assembly;
- record file quality issues, missing metadata, or geometry uncertainty.

Normalization is an evidence-producing step, not a cosmetic conversion.

### 9. Specify custom CAD parts

Generate only custom design-specific parts and required assembly glue. Typical generated parts include housings, brackets, adapters, frames, links, fixtures, custom plates, custom shafts, mechanism-specific structures, guards, covers, and mounting plates.

For each custom part, provide:

- purpose and load/function;
- required dimensions and tolerances;
- mating interfaces to sourced parts;
- material/manufacturing assumptions;
- mounting holes, axes, datum frames, clearances, and fastener strategy;
- validation criteria.

### 10. Prepare `CONTACT_MAP` and `CONNECTIONS`

Create a source-aware assembly contract:

- `CONTACT_MAP`: intended contacts, mating surfaces, clearances, keep-out zones, alignment features, and interference expectations;
- `CONNECTIONS`: fastened joints, press fits, bearings, shafts, hinges, pins, welds, adhesives, electrical/mechanical connector relationships, and degrees of freedom;
- explicit references to sourced STEP parts and generated custom parts;
- coordinate frames and named mating features.

These maps must be machine-checkable where possible and human-readable enough for review.

### 11. Hand off to `/spec-to-cad`

Pass `/spec-to-cad` a complete handoff bundle containing measurable spec, selected parts manifest, normalized STEP file paths, custom parts list, CONTACT_MAP, CONNECTIONS, and validation criteria.

The handoff must say which parts are prohibited from generation because they are sourced standard/catalog parts.

### 12. Run CAD generation, assembly, and kernel validation

Use `/spec-to-cad` to generate custom CAD, assemble sourced STEP parts and custom parts, and run kernel-backed checks. Required checks depend on the project, but usually include file loadability, units, solids validity, non-empty geometry, bounding boxes, placement transforms, connection references, interference checks, clearance checks, and export reproducibility.

### 13. Obtain independent verifier evidence

Have an independent verifier check the outputs against the original requirements, artifacts, manifests, and validation evidence. The verifier must inspect reproducible evidence, not just narrative claims or screenshots.

### 14. Produce BOM, sourcing report, and final engineering report

Create a BOM and sourcing report that distinguish sourced parts, generated custom parts, semi-standard/customized parts, and proxies. Include part numbers, manufacturers, source URLs, datasheets, STEP file paths, rating verification status, quantities, and unresolved sourcing risks.

The final engineering report must state what is verified, what is only CAD-validated, what requires further engineering analysis, and what remains blocked or assumed.

## Required artifacts

A complete `/agentic-cad` project should produce or update these artifacts, unless explicitly out of scope:

- `requirements.md` or `requirements.json`: measurable requirements, assumptions, open questions, and success criteria;
- `research_log.md` or `research_sources.json`: catalogs, datasheets, standards, URLs, source evidence, and confidence;
- `calculations.md` or `calculations.json`: engineering sizing calculations, assumptions, safety factors, and limitations;
- `mechanical_architecture.md` or `architecture.json`: assemblies, interfaces, frames, functions, and design rationale;
- `part_classification.json`: every part classified as `off_the_shelf`, `semi_standard_configurable`, `custom_design_specific`, or `placeholder_proxy`;
- `selected_parts_manifest.json`: selected off-the-shelf/catalog parts with source, datasheet, STEP path, dimensions, interfaces, `geometry_match`, and `engineering_rating_verified`;
- `part_rag_candidates.json`: candidate list and ranking rationale for sourced parts;
- `parts_cache/`: downloaded/retrieved STEP files where allowed;
- `normalized_step_metadata.json`: units, bounding boxes, axes, mating features, connection points, and metadata extracted from retrieved STEP files;
- `custom_parts_list.json`: custom parts to generate, including dimensions, functions, interfaces, and validation criteria;
- `CONTACT_MAP.json`: contacts, mating surfaces, clearances, keep-outs, and interference expectations;
- `CONNECTIONS.json`: joints, fasteners, bearings, shafts, connectors, degrees of freedom, and assembly relationships;
- `spec_to_cad_handoff.json`: complete downstream bundle for `/spec-to-cad`;
- generated CAD/assembly files from `/spec-to-cad`;
- `validation_report.json`: reproducible CAD-kernel/CLI/test evidence;
- `verifier_report.md` or `verifier_report.json`: independent verifier findings and pass/fail status;
- `BOM.csv` or `BOM.json`: quantities, part numbers, source/manufacturing method, and status;
- `sourcing_report.md`: supplier/source evidence, datasheet/rating status, alternatives, risks, and unresolved items;
- `final_engineering_report.md`: verified claims, limitations, next engineering steps, and delivery summary.

## Part classification

### `off_the_shelf`

Use for standard/catalog parts that should be retrieved, not generated. Examples: screws, nuts, washers, bearings, bushings, motors, servos, connectors, sensors, seals, springs, belts, linear rails, guide rods, fans, hinges, latches, and catalog brackets.

Rules:

- Always search Part RAG/catalog sources first.
- Prefer real manufacturer/catalog STEP files with datasheets.
- Do not model a lookalike unless it is explicitly a temporary proxy.
- Track both `geometry_match` and `engineering_rating_verified`.

### `semi_standard_configurable`

Use for parts that may come from configurable catalog families or may be custom depending on constraints. Examples: extrusions, shafts, spacers, standoffs, pulleys, gears, plates, panels, couplers, and springs with special constraints.

Rules:

- Search catalog/configurable sources first.
- If generated, record why sourcing was insufficient.
- Treat generated semi-standard parts as custom-manufactured unless an actual source is selected.

### `custom_design_specific`

Use for geometry unique to the design. Examples: housings, brackets, adapters, frames, links, fixtures, custom plates, custom shafts, guards, covers, mechanism-specific structures, jigs, and assembly glue.

Rules:

- Generate with `/spec-to-cad` or equivalent CAD tooling.
- Define interfaces to sourced parts before generation.
- Validate geometry and assembly relationships with kernel-backed checks.

### `placeholder_proxy`

Use only when the final part is unknown or unavailable but a temporary envelope is needed for architecture or clearance work.

Rules:

- Include `proxy_part: true`.
- Include `reason`.
- Include `replacement_required_before_final: true` unless the final deliverable explicitly allows proxies.
- Never present a proxy as a verified sourced or engineered part.

## Source vs generate decision tree

For every part, before creating CAD:

1. If the part is a standard/catalog/off-the-shelf component, search STEP Part RAG, manufacturer catalogs, or internal part libraries first. Do not generate final CAD for it unless the design intentionally requires a custom substitute.
2. If it is not a standard/catalog component, check whether the geometry is design-specific to this project.
3. If geometry is design-specific, generate custom CAD through `/spec-to-cad` or the selected CAD workflow.
4. If geometry is not clearly design-specific, treat it as semi-standard/configurable and search catalog families, configurable STEP sources, or prior internal libraries before generating.

Default classifications:

- **Standard/catalog part** → source first.
- **Semi-standard/configurable part** → search/configure first, then generate only if justified.
- **Design-specific part** → generate custom CAD.
- **Unknown part** → research/classify before CAD creation.
- **Placeholder/proxy** → allowed only when explicitly marked as non-final.

## STEP Part RAG contract

For each requested part, the Part RAG step should receive structured requirements such as:

- part category and function;
- target dimensions and tolerances;
- load, speed, torque, voltage/current, life, environmental, or certification requirements;
- mounting pattern, bore/shaft/thread/connector/interface constraints;
- material or compatibility constraints;
- preferred standards, manufacturers, region, availability, and license/access constraints.

For each candidate, return structured metadata where available:

```json
{
  "part_id": "bearing_6204_2rs_candidate_1",
  "category": "bearing",
  "manufacturer": "example manufacturer",
  "manufacturer_part_number": "example part number",
  "source_url": "https://example.com/product",
  "datasheet_url": "https://example.com/datasheet.pdf",
  "step_url": "https://example.com/model.step",
  "cached_step_path": "parts_cache/bearings/example.step",
  "license_or_access_notes": "download allowed for project use",
  "key_dimensions": {
    "bore_mm": 20,
    "outer_diameter_mm": 47,
    "width_mm": 14
  },
  "interface_metadata": {
    "axis": "Z",
    "mating_features": ["inner race bore", "outer race OD"]
  },
  "ratings": {
    "dynamic_load_N": null,
    "static_load_N": null,
    "max_speed_rpm": null
  },
  "geometry_match": "pass|fail|partial|unknown",
  "engineering_rating_verified": "pass|fail|partial|unknown",
  "evidence_refs": ["datasheet_url", "catalog page", "retrieval log"],
  "ranking_rationale": "why this candidate was selected or rejected"
}
```

Ranking should consider requirement fit, dimensional/interface match, datasheet/rating evidence, manufacturer/source reliability, STEP availability, license/access, assembly compatibility, file quality, and traceability.

STEP geometry is acceptable as geometry evidence only. It is not evidence for material, load rating, electrical rating, certification, bearing life, fatigue life, thermal performance, or manufacturability unless those claims are backed by datasheets, standards, calculations, or tests.

## STEP Part RAG fallback rules

A failed sourcing attempt must not silently turn into generated final CAD. Use this fallback sequence when no credible STEP/catalog candidate is found:

1. Record attempted queries, sources, standards, manufacturer families, and why candidates failed.
2. Try alternate names, standards, regional naming, equivalent part families, and manufacturer catalogs.
3. Check whether an internal library, previous project, or configurable CAD source can provide the geometry.
4. If geometry is still unavailable, create a proxy only if the current phase allows placeholders.
5. Mark the proxy clearly as non-final.
6. Do not treat a generated proxy as a validated off-the-shelf part.
7. Do not replace a standard/catalog part with generated final CAD unless the engineering decision is to design a custom-manufactured substitute.

Example proxy record:

```json
{
  "part_id": "example_standard_part",
  "source_strategy": "proxy_pending_source",
  "is_final_geometry": false,
  "replacement_required_before_final": true,
  "reason": "No credible STEP/catalog candidate found after documented search.",
  "limitations": [
    "Proxy geometry is for layout/interface checking only.",
    "Engineering rating, certification, and exact manufacturer geometry are unverified."
  ]
}
```

## `/spec-to-cad` handoff contract

The handoff to `/spec-to-cad` must be explicit and machine-readable. Include:

- project title, goal, units, coordinate conventions, and target output formats;
- measurable spec and assumptions;
- selected sourced parts manifest with cached STEP paths and normalized metadata;
- list of parts that must not be generated because they are sourced catalog/standard parts;
- custom parts list with functional requirements, dimensions, materials/manufacturing assumptions, datums, interfaces, and tolerances;
- CONTACT_MAP and CONNECTIONS;
- expected assembly tree and part naming conventions;
- validation criteria and required evidence files;
- known risks, proxies, missing ratings, and open questions.

Expected `/spec-to-cad` outputs:

- generated custom CAD files;
- assembly files integrating sourced and custom geometry;
- normalized exports as required by the project;
- `validation_report.json` with reproducible CLI/kernel/test evidence;
- failure report with exact blockers if generation or validation cannot complete.

## Validation gates

Zen CAD uses a generation-first, maturity-aware order. Structure validation and completion validation are different. `./zen-cad validate --level structure milestones/<id>` may pass while `./zen-cad validate --level completion milestones/<id>` is blocked. That is acceptable for concept/layout work. Never present final completion while an upstream final gate remains blocked.

### Gate 0: Doctor / environment preflight

For `concept` and `layout`, `./zen-cad doctor` is diagnostic only. If strict local CAD/mesh packages are missing, use the harness's available CAD path and record the limitation instead of returning without CAD.

For `final`, pass only when `./zen-cad doctor --cad-required` can run for the CAD/mesh/kernel stack needed by the job, or when the final report truthfully states `ENV_BLOCKED` and stops before final completion claims.

Prefer the harness's working CAD stack over repairing one preferred local stack. If a known venv exists, run doctor with `--python /path/to/.venv/bin/python` or set `ZEN_CAD_PYTHON`.

### Gate 1: Requirement normalization

Pass only when requirements are measurable enough to size, source, generate, assemble, and validate the design, or when assumptions are explicit and safe for the current phase.

### Gate 2: Standard part source-lock

Pass only when every standard/catalog/semi-standard part required for completion is source-locked before custom CAD proceeds as final evidence. Source-lock means exact supplier/manufacturer, SKU/part number, source URL, datasheet/rating evidence where relevant, cached STEP/STP file, and critical dimensions verified.

Required source-lock shape:

```json
{
  "part_id": "P-003",
  "kind": "standard",
  "status": "source_locked",
  "completion_eligible": true,
  "supplier": "...",
  "sku": "...",
  "source_url": "...",
  "datasheet_url": "...",
  "step_file": "02_parts/step/P-003.step",
  "critical_dimensions_verified": true
}
```

Proxy shape:

```json
{
  "status": "proxy_only",
  "completion_eligible": false
}
```

Run `./zen-cad source-lock milestones/<id>` before treating standard parts as final evidence.

### Gate 3: Custom CAD generation

Pass only when generated geometry is design-specific custom CAD, not generated lookalikes for standard parts. Proxy STL/debug geometry may be useful for layout but is completion-ineligible.

### Gate 4: Assembly contract

Pass only when CONTACT_MAP and CONNECTIONS reference known sourced and custom parts, include expected contacts/connections, and state clearances, fasteners, joints, or unresolved assumptions.

### Gate 5: Export/cache verification

Pass only when source-backed STEP/STP files are cached and normalized for standard parts, final custom exports exist, and normalized metadata records units, bounding boxes, interfaces, source paths, and unresolved limits.

### Gate 6: CAD-kernel validation

Pass only when reproducible tooling confirms required CAD files load, solids are valid where required, units and bounding boxes are plausible, references resolve, placements are defined, contacts/clearances are checked where in scope, and required exports can be regenerated.

### Gate 7: Final report / BOM / evidence bundle

Pass only when the BOM, sourcing report, validation report, and final engineering report agree on one verdict. If source-lock, exports, or kernel validation are blocked, the final report must say `Verdict: BLOCKED` and list completed evidence, blockers, and the smallest unblock step.

## Completion criteria

A project using `/agentic-cad` is complete only when all in-scope deliverables are supported by evidence:

- requirements, assumptions, calculations, architecture, and part classification artifacts exist;
- standard/catalog parts were retrieved or their absence was documented;
- no credible off-the-shelf standard part was replaced by generated geometry without a documented exception;
- sourced STEP geometry has source metadata and normalized geometry metadata;
- any engineering rating claim has datasheet/calculation/test evidence, not just STEP geometry;
- custom parts were generated from measurable specs and integrated with sourced parts;
- CONTACT_MAP and CONNECTIONS exist and are reflected in assembly validation;
- `/spec-to-cad` or equivalent tooling produced reproducible CLI/JSON/CAD-kernel/test evidence;
- independent verifier evidence exists;
- BOM and sourcing report distinguish sourced, generated, semi-standard, and proxy parts;
- final engineering report states verified claims, unverified claims, blockers, assumptions, and required downstream analyses.

Viewer snapshots, screenshots, and rendered images may be included for human review, but they are never sufficient completion evidence.

## Forbidden shortcuts

- Generating screws, bearings, motors, connectors, fasteners, or other standard parts when credible STEP/catalog parts can be retrieved.
- Treating STEP geometry as proof of engineering rating, certification, material, load capacity, bearing life, or electrical safety.
- Treating viewer snapshots, screenshots, or visual inspection as completion evidence.
- Skipping requirements extraction and building from vague natural language.
- Selecting catalog parts without datasheet/source URLs when ratings matter.
- Inventing part numbers, ratings, dimensions, or manufacturer claims.
- Failing to mark proxies and placeholders.
- Allowing `/spec-to-cad` to generate sourced standard parts silently.
- Omitting CONTACT_MAP or CONNECTIONS for assemblies.
- Reporting CAD validation as if it were FEA, thermal, vibration, fatigue, bearing life, manufacturability, tolerance, compliance, certification, procurement, or physical-test validation.
- Declaring done without reproducible CLI/JSON/kernel/test evidence where applicable.

## Short form

`/agentic-cad` = requirements → research/datasheets → calculations → architecture → classify every part → retrieve standard/catalog STEP parts with Part RAG → generate only custom design-specific CAD → normalize sourced STEP metadata → define CONTACT_MAP/CONNECTIONS → hand off to `/spec-to-cad` → run kernel/CLI/JSON/test validation → independent verifier → BOM/sourcing report → final engineering report.

Remember: **Do not generate standard parts when credible off-the-shelf STEP/catalog parts can be retrieved.** STEP files prove geometry only; ratings need datasheets/calculations/tests. Viewer snapshots are for humans, not completion. CAD validation is not FEA, thermal, vibration, fatigue, bearing life, manufacturability, or certification.
