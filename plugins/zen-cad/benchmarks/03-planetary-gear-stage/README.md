# Simplified Planetary Gear Stage

CADSkills-style prompt:

> Create a flat planetary gear assembly with separate sun, planet, ring, carrier, and pin bodies. Use simplified trapezoidal teeth and place three planets around the sun on a 42 mm radius circle.

Zen CAD native package:

```bash
python3 tools/run_contract_pipeline.py \
  --package benchmarks/03-planetary-gear-stage/package \
  --out /tmp/zen-cad-planetary \
  --target-harness build123d
```

Feature coverage:

- separate sun, planet, ring, carrier, and pin bodies;
- radial tooth-block patterns for sun and planets;
- internal tooth-slot pattern for the ring gear;
- three planets and three pins on a locked 42 mm radius circle;
- STEP export, re-import, bbox, volume, and viewer-link packaging.
