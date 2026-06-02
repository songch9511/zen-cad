# Validation Checklist

- [ ] Required files exist
- [ ] JSON schemas pass
- [ ] `./zen-cad doctor --cad-required --python /path/to/.venv/bin/python` passes before final CAD generation when CoBrA needs a specific venv
- [ ] build123d/OCP, CadQuery, or OpenSCAD backend path is explicitly known
- [ ] `./zen-cad source-lock milestones/<id>` passes before standard parts are used as final evidence
- [ ] `concept`/`layout` source-lock warnings are not presented as final completion
- [ ] `./zen-cad validate --level structure milestones/<id>` passes separately from completion
- [ ] `./zen-cad validate --level completion milestones/<id>` passes before release/completion claims
- [ ] CAD/export paths recorded
- [ ] Proxy STL/GLB/viewer artifacts excluded from completion evidence
- [ ] CAD-kernel/export/contact/clearance checks are reproducible
- [ ] Screenshots not used as sole evidence
