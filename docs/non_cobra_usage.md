# Non-CoBrA Usage

Zen CAD can be used in any agentic environment that can read Markdown, edit files, run scripts, and create CAD artifacts. In 0.6.x, treat Zen CAD as a harness-native, generate-first skill pack: the harness provides CAD generation and execution tools, while Zen CAD provides portable skills, artifact schemas, and optional final completion gates. Treat `skills/agentic-cad/SKILL.md` as the main operating manual, `docs/harness_adapters.md` plus `plugins/` as harness adapter notes, and the files in `prompts/` as task entrypoints.

## Claude Code, Codex, Cursor, or similar tools

Clone or download the Zen CAD repo, open it as the project root, and run:

```bash
./zen-cad doctor
```

Then tell the agent what you want to build in natural language, for example:

```text
기어 박스를 만들고 싶어
```

The expected agent behavior is prompt-first milestone startup: do not ask the user to run a milestone command or choose an id/title. The agent should internally run `python3 scripts/new_milestone.py --request "<goal>"`, create the next milestone such as `003_gearbox` titled `Gearbox` in this repository, then use `prompts/new_milestone.md` for the active milestone and keep validation evidence in the milestone folder.

For manual use, the same flow is available through the repo-local wrapper:

```bash
./zen-cad new "기어 박스를 만들고 싶어"
./zen-cad validate milestones/003_gearbox
```

Use `./zen-cad new` only when you intentionally want to create a milestone from the terminal. In agent-first use, the agent should create the milestone internally after receiving the natural-language prompt.

For automation or scripted startup, `./zen-cad init --milestone-request "<goal>"` and `scripts/setup_zen_cad.py --milestone-request "<goal>"` are both available. When an exact folder name must be pinned, explicit `--milestone-id` and `--milestone-title` still work.

CoBrA-only skill installation is not required in Claude Code or Codex because the skill files are already inside this repository. Use `skills/agentic-cad/SKILL.md` as the entrypoint, then load focused companion skills only when their scope is active: sourcing, CAD generation, kinematics, artifact review, manufacturing preflight, or producer/verifier iteration. If the harness supports a plugin/skill marketplace, package `skills/`, `docs/harness_adapters.md`, and the repo-local `./zen-cad` CLI as the installable payload. The default behavior should mirror text-to-cad: generate the first CAD artifact with the harness's available toolchain, then use `./zen-cad validate --level completion milestones/<id>` only for final/release claims.
