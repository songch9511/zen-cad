# Rectangular Calibration Block

CADSkills-style prompt:

> Create a centered 100 x 60 x 20 mm block with four 8 mm vertical through-holes. Add only a 2 mm chamfer on the top outer perimeter.

Zen CAD native package:

```bash
python3 tools/run_contract_pipeline.py \
  --package benchmarks/01-rectangular-calibration-block/package \
  --out /tmp/zen-cad-rectangular-block \
  --target-harness build123d
```

Feature coverage:

- box base body;
- four vertical through-holes from explicit XY positions;
- top outer perimeter chamfer using lofted tapered geometry;
- STEP export, re-import, bbox, volume, and viewer-link packaging.
