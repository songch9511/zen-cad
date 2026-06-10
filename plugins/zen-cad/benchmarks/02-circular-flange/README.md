# Circular Flange

CADSkills-style prompt:

> Create an 80 mm diameter, 10 mm thick circular flange with a 30 mm central through-bore. Add six 6 mm through-holes on a 60 mm bolt circle and fillet the outside circular edges.

Zen CAD native package:

```bash
python3 tools/run_contract_pipeline.py \
  --package benchmarks/02-circular-flange/package \
  --out /tmp/zen-cad-flange \
  --target-harness build123d
```

Feature coverage:

- cylindrical flange base;
- central through-bore;
- six-hole bolt circle pattern;
- outside circular edge fillet approximation using torus geometry;
- STEP export, re-import, bbox, volume, and viewer-link packaging.
