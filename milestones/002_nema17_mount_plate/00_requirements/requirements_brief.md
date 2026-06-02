# Requirements Brief

## Goal

Create a simple final-evidence demo CAD part: a NEMA17 motor mount plate.

## Functional requirements

- Units: millimeters.
- Plate size: 60 mm x 60 mm x 4 mm.
- Motor pilot bore: 22 mm through-bore centered on the plate.
- NEMA17 mounting holes: four 3.4 mm through-holes on a 31 mm square pattern.
- Plate mounting holes: four 4.5 mm through-holes at +/-24 mm in X and Y.
- Edge treatment: 1 mm chamfer on the top outside perimeter.
- Deliverables: build123d source, STEP export, STL export, validation JSON, BOM, final report.

## Constraints and assumptions

- This is a custom interface plate, not a sourced standard/catalog part.
- The model validates CAD geometry only; motor ratings, fastener strength, and manufacturing tolerances are outside this demo scope.
- The NEMA17 interface follows the common 31 mm square bolt pattern and 22 mm pilot opening assumption for a small generation-first demo.

## Completion evidence

- Required JSON artifacts pass schema validation.
- CAD source/export paths are recorded.
- BOM and final report distinguish verified facts from assumptions.
- Validation report records reproducible build123d/OCP export and load evidence.
