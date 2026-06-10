# Zen CAD Native Benchmarks

These benchmarks adapt three CADSkills-style prompts into Zen CAD native contract packages. Each package is meant to run through the local contract pipeline and produce a build123d STEP artifact plus proceed-gate review evidence.

Run one benchmark:

```bash
python3 tools/run_contract_pipeline.py \
  --package benchmarks/01-rectangular-calibration-block/package \
  --out /tmp/zen-cad-rectangular-block \
  --target-harness build123d
```

For a CAD-Visualizer auto-load link, pass the viewer public directory:

```bash
python3 tools/run_contract_pipeline.py \
  --package benchmarks/02-circular-flange/package \
  --out /tmp/zen-cad-flange \
  --target-harness build123d \
  --viewer-base-url http://localhost:5173 \
  --viewer-public-dir /Users/daniel/CAD-Visualizer/public
```

## Targets

| # | Benchmark | Prompt |
|---|-----------|--------|
| 1 | [Rectangular calibration block](01-rectangular-calibration-block/README.md) | Create a centered 100 x 60 x 20 mm block with four 8 mm vertical through-holes. Add only a 2 mm chamfer on the top outer perimeter. |
| 2 | [Circular flange](02-circular-flange/README.md) | Create an 80 mm diameter, 10 mm thick circular flange with a 30 mm central through-bore. Add six 6 mm through-holes on a 60 mm bolt circle and fillet the outside circular edges. |
| 3 | [Simplified planetary gear stage](03-planetary-gear-stage/README.md) | Create a flat planetary gear assembly with separate sun, planet, ring, carrier, and pin bodies. Use simplified trapezoidal teeth and place three planets around the sun on a 42 mm radius circle. |
