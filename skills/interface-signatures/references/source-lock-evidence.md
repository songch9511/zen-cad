# Source-Lock Evidence

Use source-lock evidence when a standard, catalog, or supplier part is moving from layout proxy/detail candidate toward final-stage sourcing.

Interface signatures and source locks are different artifacts:

- `interface_signature` records axes, datums, envelopes, and mating dimensions that are trusted for layout.
- `source_lock_evidence` records explicit source locators for a final part candidate.
- A layout interface signature never proves supplier geometry, ratings, certification, price, inventory, or availability.
- A source lock does not crawl catalogs. It only records evidence provided by the user, project, step.parts, manufacturer pages, datasheets, or files.

## Evidence Shape

Use `schemas/source_lock_evidence.schema.json` and `tools/generate_source_lock_evidence.py` to create one evidence document per sourced part.

Required distinctions:

- `interface_signature_refs` may point back to layout signatures.
- `interface_signature_role` must be `layout_reference_only`.
- `evidence_sources` must contain explicit locators such as a step.parts page, a STEP/STP source URL, a manufacturer product page, a datasheet URL, or a user-provided file.
- `claims_made` is limited to source identity, geometry reference URL, critical-dimensions reference, or review reference.
- `claims_not_made` must mention that rating and certification are not claimed.

## Common Commands

Record a step.parts page plus a direct STEP source URL:

```bash
python3 tools/generate_source_lock_evidence.py \
  --package <contract-package> \
  --part-id bearing_proxy \
  --part-role catalog_part \
  --name "608ZZ ball bearing" \
  --model 608ZZ \
  --step-parts-url https://www.step.parts/parts/bearing_608zz \
  --step-source-url <provided-step-or-stp-url> \
  --out <run-dir>/source_locks/bearing_proxy.source_lock.json
```

Record manufacturer identity evidence:

```bash
python3 tools/generate_source_lock_evidence.py \
  --package <contract-package> \
  --part-id motor_proxy \
  --part-role supplier_part \
  --name "<manufacturer model>" \
  --manufacturer-name "<manufacturer>" \
  --model "<model>" \
  --manufacturer-url <manufacturer-product-url> \
  --out <run-dir>/source_locks/motor_proxy.source_lock.json
```

The tool validates the resulting JSON but does not fetch URLs, download STEP files, check ratings, or certify the geometry. Downstream CAD must import the locked source and run geometry checks before final readiness claims.
