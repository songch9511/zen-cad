from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXPECTED_SKILLS = {
    "assembly-layout",
    "cad-handoff",
    "cad-spec",
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
            "If subagents are unavailable, perform the same roles as sequential local passes.",
            "references/specialist-subagents.md",
        ]:
            self.assertIn(phrase, text)

        reference = ROOT / "skills/cad-spec/references/specialist-subagents.md"
        self.assertTrue(reference.exists())
        reference_text = reference.read_text(encoding="utf-8")
        self.assertIn("Spawn subagents only when the harness supports them", reference_text)
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
        ]:
            self.assertIn(phrase, text)

        for rel in [
            "skills/cad-spec/references/parameter-contract.md",
            "skills/cad-spec/references/export-targets.md",
            "skills/cad-spec/references/inspection-and-repair.md",
        ]:
            self.assertTrue((ROOT / rel).exists(), rel)

        handoff = (ROOT / "skills/cad-handoff/SKILL.md").read_text(encoding="utf-8")
        for phrase in [
            "Parameter contract:",
            "Artifact targets:",
            "Required checks:",
            "Repair loop:",
        ]:
            self.assertIn(phrase, handoff)

    def test_no_committed_example_specs(self) -> None:
        for path in tracked_files():
            lowered = str(path.relative_to(ROOT)).lower()
            self.assertNotIn("/examples/", f"/{lowered}")
            self.assertNotIn("example_spec", lowered)


if __name__ == "__main__":
    unittest.main()
