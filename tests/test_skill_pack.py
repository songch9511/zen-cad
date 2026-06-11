from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_SKILLS = {
    "assembly-layout",
    "cad-replacement",
    "cad-handoff",
    "cad-spec",
    "constrained-detail-cad",
    "interface-signatures",
}


def tracked_files() -> list[Path]:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return [ROOT / line for line in completed.stdout.splitlines() if line]


class SkillPackTest(unittest.TestCase):
    def test_only_core_skills_are_shipped(self) -> None:
        actual = {
            path.parent.name
            for path in (ROOT / "skills").glob("*/SKILL.md")
        }
        self.assertEqual(EXPECTED_SKILLS, actual)

    def test_no_old_workflow_surface_in_tracked_text(self) -> None:
        old_terms = [
            "leg" + "acy",
            "depre" + "cated",
            "Co" + "bra",
            "co" + "bra",
            "agentic" + "-cad",
            "spec" + "-to-cad",
            "source" + "-step-parts",
            "mile" + "stone",
            "./" + "zen-cad",
            "validation" + "_report",
            "selected" + "_parts",
        ]
        text_suffixes = {".md", ".py", ".yaml", ".yml", ".json", ".csv", ".txt"}
        for path in tracked_files():
            if path.suffix not in text_suffixes and path.name not in {"README", "VERSION"}:
                continue
            text = path.read_text(encoding="utf-8")
            rel = str(path.relative_to(ROOT))
            for term in old_terms:
                self.assertNotIn(term, text, rel)

    def test_cad_spec_instructs_specialist_subagents(self) -> None:
        text = (ROOT / "skills/cad-spec/SKILL.md").read_text(encoding="utf-8")
        for phrase in [
            "orchestrate CAD work through specialist subagents",
            "Specialist Subagents",
            "layout-specialist",
            "interface-specialist",
            "parameter-specialist",
            "motion-specialist",
            "cad-generator",
            "cad-reviewer",
            "replacement-specialist",
            "detail-shape-specialist",
            "visual-reviewer",
            "engineering-reviewer",
            "Subagent Dispatch Plan",
            "If subagents are unavailable, perform the same roles as sequential local passes.",
            "references/specialist-subagents.md",
        ]:
            self.assertIn(phrase, text)

        reference = ROOT / "skills/cad-spec/references/specialist-subagents.md"
        self.assertTrue(reference.exists())
        reference_text = reference.read_text(encoding="utf-8")
        self.assertIn("Spawn subagents only when the harness supports them", reference_text)
        self.assertIn("Subagent status: unavailable; using sequential fallback roles", reference_text)
        self.assertIn("Lead Reconciliation", reference_text)

    def test_cad_spec_instructs_generation_quality_loop(self) -> None:
        text = (ROOT / "skills/cad-spec/SKILL.md").read_text(encoding="utf-8")
        for phrase in [
            "Parameter Contract",
            "Artifact Targets",
            "Inspection Plan",
            "Repair Loop",
            "Primary artifact intent: STEP/STP when the active CAD generator supports it.",
            "references/parameter-contract.md",
            "references/export-targets.md",
            "references/inspection-and-repair.md",
            "references/visual-inspection-and-repair.md",
        ]:
            self.assertIn(phrase, text)

        for rel in [
            "skills/cad-spec/references/parameter-contract.md",
            "skills/cad-spec/references/export-targets.md",
            "skills/cad-spec/references/inspection-and-repair.md",
            "skills/cad-spec/references/visual-inspection-and-repair.md",
        ]:
            self.assertTrue((ROOT / rel).exists(), rel)

        handoff = (ROOT / "skills/cad-handoff/SKILL.md").read_text(encoding="utf-8")
        for phrase in [
            "Subagent dispatch plan:",
            "Parameter contract:",
            "Artifact targets:",
            "Required checks:",
            "Visual/engineering review:",
            "Repair loop:",
        ]:
            self.assertIn(phrase, handoff)

    def test_subagent_dispatch_survives_generation_handoff(self) -> None:
        cad_spec = (ROOT / "skills/cad-spec/SKILL.md").read_text(encoding="utf-8")
        specialist = (ROOT / "skills/cad-spec/references/specialist-subagents.md").read_text(encoding="utf-8")
        handoff = (ROOT / "skills/cad-handoff/SKILL.md").read_text(encoding="utf-8")
        harness = (ROOT / "skills/cad-handoff/references/harness-briefs.md").read_text(encoding="utf-8")
        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        openai = (ROOT / "skills/cad-spec/agents/openai.yaml").read_text(encoding="utf-8")
        combined = "\n".join([cad_spec, specialist, handoff, harness, agents, openai])
        for phrase in [
            "Subagent Dispatch Plan",
            "Subagent status: unavailable; using sequential fallback roles",
            "layout, interface, parameter, motion, CAD generation, visual review, engineering review, CAD review, then repair",
            "Do not drop the Subagent Dispatch Plan",
            "visual inspection",
            "engineering review",
        ]:
            self.assertIn(phrase, combined)

    def test_machine_readable_schema_surface(self) -> None:
        expected = [
            "cad_spec.schema.json",
            "layout_contract.schema.json",
            "interface_signature.schema.json",
            "inspection_report.schema.json",
            "handoff_packet.schema.json",
            "layout_proxy_scene.schema.json",
            "cad_source_manifest.schema.json",
            "proceed_gate_package.schema.json",
            "proceed_approval.schema.json",
            "pipeline_run.schema.json",
            "source_lock_evidence.schema.json",
            "review_bundle.schema.json",
            "interface_frame.schema.json",
            "replacement_plan.schema.json",
            "detail_shape_plan.schema.json",
        ]
        for name in expected:
            path = ROOT / "schemas" / name
            self.assertTrue(path.exists(), name)
            schema = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
            self.assertEqual(False, schema["additionalProperties"])
            for required in ["schema_version", "kind", "extensions"]:
                self.assertIn(required, schema["required"], name)
            self.assertEqual("0.8.0", schema["properties"]["schema_version"]["const"])

    def test_interface_registry_records_are_layout_ready(self) -> None:
        index_path = ROOT / "registry/interfaces/index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        self.assertEqual("interface_registry_index", index["kind"])
        self.assertGreaterEqual(len(index["entries"]), 6)

        forbidden_keys = {
            "manufacturer",
            "supplier",
            "sku",
            "price",
            "availability",
            "bom_quantity",
            "step_file",
            "cad_file",
            "load_rating",
            "torque_rating",
            "material",
            "certification",
        }

        def walk_keys(value: object) -> set[str]:
            if isinstance(value, dict):
                keys = set(value)
                for child in value.values():
                    keys.update(walk_keys(child))
                return keys
            if isinstance(value, list):
                keys: set[str] = set()
                for child in value:
                    keys.update(walk_keys(child))
                return keys
            return set()

        for entry in index["entries"]:
            record_path = ROOT / "registry/interfaces" / entry
            self.assertTrue(record_path.exists(), entry)
            record = json.loads(record_path.read_text(encoding="utf-8"))
            for field in [
                "schema_version",
                "kind",
                "id",
                "title",
                "units",
                "family",
                "quality_label",
                "trusted_for_layout",
                "source",
                "primary_axes",
                "mounting_datums",
                "critical_dimensions",
                "envelope",
                "validation_targets",
                "proxy_may_simplify",
                "must_confirm_before_final",
                "extensions",
            ]:
                self.assertIn(field, record, entry)
            self.assertEqual("interface_signature", record["kind"])
            self.assertEqual("mm", record["units"])
            self.assertTrue(record["trusted_for_layout"], entry)
            for nonempty in [
                "primary_axes",
                "mounting_datums",
                "critical_dimensions",
                "validation_targets",
                "proxy_may_simplify",
                "must_confirm_before_final",
            ]:
                self.assertGreater(len(record[nonempty]), 0, f"{entry}: {nonempty}")
            self.assertFalse(forbidden_keys & walk_keys(record), entry)

    def test_handoff_requires_generation_evidence(self) -> None:
        text = (ROOT / "skills/cad-handoff/SKILL.md").read_text(encoding="utf-8")
        for phrase in [
            "Source-of-truth:",
            "Generated files:",
            "Validation actually run:",
            "Skipped checks and reasons:",
            "Snapshot/viewer evidence:",
            "Repair attempts:",
            "Claims not made:",
        ]:
            self.assertIn(phrase, text)

    def test_runtime_boundary_stays_lightweight(self) -> None:
        tracked = [str(path.relative_to(ROOT)) for path in tracked_files()]
        forbidden_paths = {
            "skills/cad/scripts/step",
            "skills/cad/scripts/inspect",
            "skills/cad/scripts/snapshot",
            "skills/cad/requirements.txt",
        }
        self.assertFalse(forbidden_paths & set(tracked))
        self.assertFalse(any("cadpy_" in path for path in tracked))

    def test_visual_review_and_explicit_target_rules(self) -> None:
        inspection = (ROOT / "skills/cad-spec/references/inspection-and-repair.md").read_text(encoding="utf-8")
        visual = (ROOT / "skills/cad-spec/references/visual-inspection-and-repair.md").read_text(encoding="utf-8")
        export_targets = (ROOT / "skills/cad-spec/references/export-targets.md").read_text(encoding="utf-8")
        principles = (ROOT / "docs/operating_principles.md").read_text(encoding="utf-8")
        for phrase in [
            "stronger evidence than screenshots or viewer links",
            "skipped with a reason",
            "Do not validate CAD by git diff, file size, screenshot, or viewer link alone.",
            "convert each concern into a measurable check",
        ]:
            self.assertIn(phrase, f"{inspection}\n{visual}\n{principles}")
        for phrase in [
            "floating_unconstrained_body",
            "unintended_interference",
            "insufficient_clearance",
            "missing_fastener_engagement",
            "coaxiality_or_plane_misalignment",
            "mesh_or_transmission_error",
            "unsupported_or_implausible_load_path",
            "Visual-To-Measurable Repair Loop",
        ]:
            self.assertIn(phrase, visual)
        for phrase in [
            "explicit file paths",
            "Do not request directory-wide generation",
            "source and spec remain authoritative; generated files are derived",
        ]:
            self.assertIn(phrase, export_targets)

    def test_component_registry_without_catalog_crawling(self) -> None:
        text = (ROOT / "skills/interface-signatures/SKILL.md").read_text(encoding="utf-8")
        for phrase in [
            "registry/interfaces/index.json",
            "record the miss and proceed with a documented envelope",
            "Do not start broad catalog crawling",
        ]:
            self.assertIn(phrase, text)

    def test_replacement_and_constrained_detail_skills(self) -> None:
        replacement = (ROOT / "skills/cad-replacement/SKILL.md").read_text(encoding="utf-8")
        detail = (ROOT / "skills/constrained-detail-cad/SKILL.md").read_text(encoding="utf-8")
        cad_spec = (ROOT / "skills/cad-spec/SKILL.md").read_text(encoding="utf-8")
        handoff = (ROOT / "skills/cad-handoff/SKILL.md").read_text(encoding="utf-8")
        combined = "\n".join([replacement, detail, cad_spec, handoff])
        for phrase in [
            "interface-frame mapping",
            "replacement_plan",
            "detail_shape_plan",
            "protected interface zones",
            "locked interface frames",
            "post-replacement locked-fact checks",
            "shape intent is soft",
            "locked facts are hard constraints",
        ]:
            self.assertIn(phrase, combined)
        for rel in [
            "skills/cad-replacement/references/interface-frame-contract.md",
            "skills/cad-replacement/references/replacement-plan.md",
            "skills/constrained-detail-cad/references/detail-shape-plan.md",
            "schemas/interface_frame.schema.json",
            "schemas/replacement_plan.schema.json",
            "schemas/detail_shape_plan.schema.json",
        ]:
            self.assertTrue((ROOT / rel).exists(), rel)

    def test_no_committed_example_specs(self) -> None:
        for path in tracked_files():
            lowered = str(path.relative_to(ROOT)).lower()
            self.assertNotIn("/examples/", f"/{lowered}")
            self.assertNotIn("example_spec", lowered)

    def test_codex_plugin_bundle_is_installable(self) -> None:
        marketplace_path = ROOT / ".codex-plugin" / "marketplace.json"
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
        self.assertEqual("zen-cad", marketplace["name"])
        self.assertEqual("Zen CAD", marketplace["interface"]["displayName"])
        self.assertEqual(1, len(marketplace["plugins"]))

        entry = marketplace["plugins"][0]
        self.assertEqual("zen-cad", entry["name"])
        self.assertEqual({"source": "local", "path": "./plugins/zen-cad"}, entry["source"])
        self.assertEqual("AVAILABLE", entry["policy"]["installation"])
        self.assertEqual("ON_INSTALL", entry["policy"]["authentication"])

        plugin_root = ROOT / "plugins" / "zen-cad"
        plugin = json.loads((plugin_root / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual("zen-cad", plugin["name"])
        self.assertEqual("1.1.0", plugin["version"])
        self.assertEqual("./skills/", plugin["skills"])
        self.assertEqual("Zen CAD", plugin["interface"]["displayName"])

        bundled_skills = {
            path.parent.name
            for path in (plugin_root / "skills").glob("*/SKILL.md")
        }
        self.assertEqual(EXPECTED_SKILLS, bundled_skills)
        for rel in [
            "tools/run_contract_pipeline.py",
            "tools/generate_cad_artifact.py",
            "tools/download_step_part.py",
            "tools/package_viewer_link.py",
            "tools/capture_viewer_snapshot.py",
            "schemas/cad_spec.schema.json",
            "schemas/interface_frame.schema.json",
            "schemas/replacement_plan.schema.json",
            "schemas/detail_shape_plan.schema.json",
            "registry/interfaces/index.json",
        ]:
            self.assertTrue((plugin_root / rel).exists(), rel)


if __name__ == "__main__":
    unittest.main()
