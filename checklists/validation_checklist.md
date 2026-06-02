# Validation Checklist

- [ ] Required files exist
- [ ] JSON schemas pass
- [ ] `./zen-cad doctor --cad-required` passes before final CAD generation
- [ ] `./zen-cad source-lock milestones/<id>` passes before standard parts are used as final evidence
- [ ] `./zen-cad validate --level structure milestones/<id>` passes separately from completion
- [ ] `./zen-cad validate --level completion milestones/<id>` passes before release/completion claims
- [ ] CAD/export paths recorded
- [ ] Proxy STL/GLB/viewer artifacts excluded from completion evidence
- [ ] CAD-kernel/export/contact/clearance checks are reproducible
- [ ] Screenshots not used as sole evidence
