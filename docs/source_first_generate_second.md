# Source First, Generate Second

Standard components should be sourced through credible catalogs, datasheets, manufacturer STEP downloads, or STEP Part RAG before any attempt to generate them. Custom generation is reserved for design-specific parts and assembly glue. If a standard component must be generated temporarily, mark it as `placeholder_proxy` and non-final.

For completion, a standard part is source-locked only when the manifest records:

```json
{
  "part_id": "P-003",
  "kind": "standard",
  "status": "source_locked",
  "completion_eligible": true,
  "supplier": "manufacturer or distributor",
  "sku": "exact part number",
  "source_url": "https://...",
  "datasheet_url": "https://...",
  "step_file": "02_parts/step/P-003.step",
  "critical_dimensions_verified": true
}
```

Proxy records must stay completion-ineligible:

```json
{
  "status": "proxy_only",
  "completion_eligible": false
}
```

Run `./zen-cad source-lock milestones/<id>` before CAD generation. If source-lock is blocked, downstream CAD, assembly, and validation may continue only as a truthful blocked/proxy iteration, not as completion evidence.
