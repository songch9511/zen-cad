# Replacement Plan

A replacement plan is the contract between the approved layout proxy and the sourced/detail geometry that replaces it.

Use `schemas/replacement_plan.schema.json`.

## Status

- `blocked_missing_proxy_frame`: the layout proxy lacks required machine-readable frames.
- `blocked_missing_source_frame`: sourced/detail CAD lacks matching interface frames.
- `alignment_ready`: transforms are computable, but geometry has not been inspected after placement.
- `inspection_required`: CAD source has been prepared and post-replacement checks must run.
- `failed`: inspection found locked fact drift, clearance loss, or unresolved source mismatch.
- `passed`: all required post-replacement checks passed.

## Replacement Entry

Each entry should include:

- `part_id`;
- `mode`: `source_step`, `generated_detail`, or `manual_detail`;
- `source_lock_id` or `detail_shape_plan_id` when applicable;
- `proxy_frame_id`;
- `source_frame_id`;
- `transform`;
- `locked_fact_refs`;
- `required_checks`;
- `status`.

## Pass Criteria

The replacement may enter proceed review only when:

- all required proxy and source frames exist;
- every transform is explicit;
- source geometry has been imported or generated;
- post-transform inspection measured the locked facts;
- skipped checks have explicit reasons and do not affect proceed-critical facts.

If a skipped check affects a locked fact, the plan remains blocked.
