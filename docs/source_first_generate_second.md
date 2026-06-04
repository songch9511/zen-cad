# Source First, Generate Second

For final/release CAD, standard components should be sourced through credible catalogs, datasheets, manufacturer STEP downloads, or a project registry before they are treated as real parts. For 0.8 layout work, do not block the first assembly spec or layout proxy on catalog crawling when an interface signature is enough.

Custom generation is reserved for design-specific parts and assembly glue. If a standard component must be represented temporarily, mark it as `placeholder_proxy` or interface-signature-derived and non-final.

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

Run `./zen-cad source-lock milestones/<id>` before final CAD evidence, not before the first layout spec. If source-lock is blocked, downstream CAD, assembly, and validation may continue only as a truthful blocked/proxy iteration, not as completion evidence.
