---
name: self-evolving-producer-verifier
description: "/self-evolving-producer-verifier: Producer-verifier loop where the producer maintains and evolves a persistent approach document each iteration, so verifier critiques compound across iterations instead of being treated independently. General-purpose; layer domain specifics on top."
version: 0.8.0
---

# Self-Evolving Producer-Verifier (/self-evolving-producer-verifier)

**Invocation**: `/self-evolving-producer-verifier <task>`

Examples: `/self-evolving-producer-verifier implement this feature until tests pass`, `/self-evolving-producer-verifier draft this plan until the rubric checker approves`.

> **Iron rule — use the harness loop when it exists.** If the harness provides `emit_loop`, the lead sets up producer + verifier once and lets the loop handle produce → verify → critique. If it does not, use the portable file-based fallback in this skill.

> **Iron rule — the approach document is the locus of evolution.** The producer must persist a named approach document so iteration N+1 sees iteration N's lessons. Artifact revision without approach revision is only L0.

> **Iron rule — verifier judges artifacts, not the producer's self-story.** The verifier may inspect the approach document for context, but scores only the original task brief / acceptance criteria. The verifier never edits the approach document.

This skill is the middle layer between `/producer-verifier-loop` and `/gepa`: one producer, one verifier, one loop, plus one evolving producer-owned state object. It is deliberately general-purpose; domain-specific skills should layer their own artifact, tooling, and scoring rules on top.

---

## Taxonomy: L0 / L1 / L2

| Level | What evolves | Skill / pattern | Boundary |
|---|---|---|---|
| **L0 — artifact revision only** | Artifact changes; producer approach is fixed | `/producer-verifier-loop` | Critique is treated as a local checklist |
| **L1 — explicit approach evolution** | Artifact **and** producer approach document change | **this skill** | Critiques compound into forward-looking rules |
| **L2 — candidate-frontier evolution** | Multiple candidate approaches compete on measured axes | `/gepa` | Pareto frontier, batch rollout, mutation pool |

L1 is not a small GEPA: no candidate pool, no Pareto frontier, no multi-axis tournament. If the method needs multi-candidate search, escalate to `/gepa` instead of raising the loop cap.

---

## Harness Primitive: `emit_loop`

`emit_loop`, `complete_sequence`, `assign_task`, CoMeT memory, `/producer-verifier-loop`, and `/gepa` are optional harness primitives. They are not shipped by Zen CAD itself. Some harness environments may provide them; Codex, Claude Code, and simple terminal/file harnesses may not.

When these primitives are unavailable, do not pretend the autonomous loop ran. Use the fallback procedure below and record the producer/verifier artifacts as files.

```python
emit_loop(
    sessions=[producer_sid, verifier_sid],
    task='<initial producer brief including approach_doc location + acceptance criteria>',
    count=5,                  # default safety cap
    enable_complete=True,     # verifier can terminate on approval
    sink='',                  # default = lead
)
```

Semantics:
- **Iteration 1**: producer reads the task brief + initial approach document, produces artifact A, and records any initial strategy refinements.
- **Verifier turn**: verifier judges A against the original acceptance criteria.
- **Approve**: verifier calls `complete_sequence(final_output=approved_artifact)`; sink receives the approved deliverable.
- **Critique**: verifier returns failed checks + evidence + required changes; the loop routes that critique back to the producer.
- **Iteration 2+**: producer reads the approach document, abstracts the critique into approach updates, then regenerates the artifact under the evolved approach.
- **Cap**: if `count` is reached without approval, treat it as diagnostic evidence, not permission to blindly increase `count`.

Default `count=5` fits most bounded tasks. Use `count=3` for cheap/simple outputs, `count=7-10` for complex single-trajectory work, and `/gepa` when broader policy search is the real need.

### Verifier approval contract

```text
If the artifact satisfies the original acceptance criteria, call:
complete_sequence(final_output=<approved artifact or approved artifact path/report>)

Otherwise return a structured critique:
- failed_check: <criterion name>
- evidence: <file:line, command output, field, screenshot region, rubric clause, etc.>
- required_change: <concrete fix target>
- recurrence_hint: <if this resembles a prior defect class, name it>
```

The critique is the producer's next input. Concrete failed checks become approach-document rules; vague taste notes burn iterations.

## Portable Fallback

Use this when `emit_loop` or `complete_sequence` is not available:

1. Create `<workdir>/producer_approach.md` from the approach template.
2. Create `<workdir>/producer_output.md` or the requested artifact path.
3. Create `<workdir>/verifier_report.md`.
4. Run producer pass 1 against the original task and approach document.
5. Run verifier pass 1 against the original acceptance criteria, citing files, commands, schema fields, or screenshots as evidence.
6. If verifier passes, stop and return the approved artifact plus verifier report.
7. If verifier fails, update `producer_approach.md` with generalized forward-looking rules before changing the artifact.
8. Repeat for a fixed cap, normally 3-5 iterations.
9. If the same blocker recurs three times, stop with a blocked report instead of repeating the same artifact.

Fallback file contract:

```text
<workdir>/producer_approach.md
<workdir>/producer_output.md or requested artifact path
<workdir>/verifier_report.md
```

For Zen CAD work, the verifier report should reference `./zen-cad validate --level structure` or `./zen-cad validate --level completion` output when those commands are part of acceptance.

---

## Approach document contract

The approach document is the only new primitive over `/producer-verifier-loop`.

**What it is**: a persistent producer-owned document containing current strategy, mental model, learned rules, anti-patterns, and uncertainty notes.

| Storage | Pick when | Handle |
|---|---|---|
| **File** | Short-lived run; concrete working directory; artifact files already exist | `<workdir>/producer_approach.md` |
| **Harness memory node** | Run spans turns and the harness provides memory primitives such as CoMeT | tag `self_evolving_pv:approach:{run_id}` |

File is simpler and diffable. Memory is better for project continuity and cross-worker reuse. Pass the exact path, node id, or tag recipe in every brief.

**Who writes it**: producer only.

**Who reads it**: producer reads it at the start of every iteration. Verifier may read it for context, but must not score against it; original task brief and acceptance criteria remain the rubric.

**When it updates**: after receiving verifier critique, before regenerating the artifact.

**What it contains**:

```markdown
# Producer approach — self-evolving PV run {run_id}

## Task brief anchor
- Original task:
- Acceptance criteria:
- Non-negotiable constraints:

## Current strategy / mental model
- ...

## Learned failure patterns → adopted rules
| observed failure | generalized rule now applied | evidence iteration |
|---|---|---|
| specific defect from critique | forward-looking rule that would catch related defects | loop_02 |

## Anti-patterns to avoid
- ...

## Confidence notes
- Solid:
- Uncertain / needs verifier attention:
```

**How it grows**: append-mostly during the loop, but every addition must be forward-looking. Do not write only "iteration 3 changed X"; write the general rule that would also catch related failures. When the document exceeds roughly **2-3k tokens**, refactor it down: consolidate duplicates, remove superseded notes, preserve the strongest rules and uncertainty notes.

---

## Producer brief template

```text
Role: producer in a self-evolving producer-verifier loop.

Task: {task}
Acceptance criteria: {criteria}
Approach document: {path_or_memory_node_or_tag_recipe}

Loop procedure:
0. At the start of EVERY iteration, read the approach document.
1. Read the current input. Iteration 1 = task brief; later iterations = verifier critique.
2. If critique is present, update the approach document BEFORE regenerating the artifact:
   - name the failure pattern revealed;
   - abstract it into a general rule that would also catch related failures;
   - add or revise anti-patterns and confidence notes;
   - do not merely paraphrase the critique.
3. Produce the next artifact under the evolved approach.
4. In the handoff, cite the approach-doc rule(s) that motivated major design choices or fixes.
5. If you cannot make progress on a critique, block with the specific obstacle rather than repeating the same artifact.

Guard: the approach doc is not a changelog. "Iteration 3: changed X" is insufficient; write "When criterion Y is present, always check Z before choosing X".
```

The producer response is the next verifier input. Return the artifact or a clear block, not process narration.

---

## Verifier brief template

```text
Role: verifier in a self-evolving producer-verifier loop.

Original task: {task}
Acceptance criteria: {checkable criteria}
Approach document: {path_or_memory_node_or_tag_recipe}  # context only

Procedure:
1. Inspect the producer artifact.
2. Run or apply the original checks, citing tool output / file:line / fields / rubric clauses / visual regions as evidence.
3. If all criteria pass, call complete_sequence(final_output=<approved artifact/report>).
4. If anything fails, return failed_check, evidence, required_change, and recurrence_hint.
5. You may read the approach document to understand intent, but MUST NOT approve because it sounds thoughtful and MUST NOT fail because it violates its own self-imposed rule. Score only original criteria.
6. Never edit the approach document. If the approach seems self-serving or dangerous, critique it; producer owns the update.
```

The verifier remains the only judge of artifact acceptability. The approach document improves the producer; it does not replace independent verification.

---

## Lead playbook

1. **Choose complementary roles.** Examples: coder + test runner, drafter + rubric checker, planner + adversarial reviewer. Avoid same model + same prompt.
2. **Define checkable criteria.** The verifier needs an approval condition it can apply without lead intervention.
3. **Initialize `run_id`.** Use a project id, task slug, timestamp, or sequence id; thread it through approach-doc names and briefs.
4. **Create the approach document.** Seed `<workdir>/producer_approach.md` or a node tagged `self_evolving_pv:approach:{run_id}` with the task brief, acceptance criteria, and empty sections from the template.
5. **Brief producer and verifier separately.** Producer owns approach evolution; verifier owns approval and critique.
6. **Call the loop when the harness provides it**:
   ```python
   emit_loop(
       sessions=[producer_sid, verifier_sid],
       task='Produce {artifact}. Approach document: {location}. Acceptance criteria: {criteria}.',
       count=5,
       enable_complete=True,
       sink='',
   )
   ```
7. **Use the portable fallback otherwise.** Store producer output, verifier report, and approach document as files and iterate manually up to the cap.
8. **On terminal output, read both deliverables.** The approved artifact is the immediate output; the approach document is the distilled experience of the run and may seed future similar tasks.
9. **If terminated by cap, diagnose before retrying.** Compare final critique with the approach document. If the same critique recurs unchanged, change setup or escalate to a broader candidate-search method when available.

---

## Anti-patterns

| Anti-pattern | Why it fails | Guard |
|---|---|---|
| Producer ignores its approach document | Plain `/producer-verifier-loop` behavior with extra overhead | Producer cites approach-doc rule(s) behind major choices |
| Approach doc as changelog | History does not improve future behavior | Write forward-looking rules, not diffs |
| Critique paraphrased without abstraction | Related failures recur | Use `observed failure → generalized rule` |
| Verifier scores against the approach doc | Producer can game the loop by relaxing its own rubric | Original acceptance criteria only |
| Approach doc bloats unboundedly | Context noise degrades later iterations | Cap ~2-3k tokens; refactor periodically |
| Same critique appears 3+ times unchanged | Fixed point; producer cannot use the feedback | Terminate as cap/block and surface recurrence evidence |
| Producer self-verifies via approach doc | Reintroduces producer bias | Verifier remains the only acceptability judge |
| Lead manually relays critiques despite loop support | Lead returns to critical path | Use `emit_loop` when available; otherwise use the file-based fallback deliberately |

---

## When NOT to use this skill

- **Genuinely single-pass work** → use a direct task assignment or one normal agent pass.
- **No checkable approval criterion** → tighten criteria first, or do one pass + user review.
- **Need Pareto-frontier multi-candidate search** → use `/gepa` or another candidate-search method if the harness provides one.
- **Producer and verifier are the same model with the same prompt** → no perspective shift; this skill cannot save the setup.
- **Approach learning is irrelevant** → use L0 `/producer-verifier-loop`.
- **The user must approve every iteration** → do not hide user-gated judgement inside an autonomous loop.

---

## Diagnostic: did the loop self-evolve?

Inspect the approach document alongside the terminal artifact.

Healthy L1 signs:
- Specific critique details become general rules.
- Later artifacts cite and obey earlier learned rules.
- Repeated defect classes disappear or narrow.
- The document contains strategy, failure patterns, anti-patterns, and confidence notes — not just a chronological log.

Failed L1 signs:
- Each delta is only "verifier said X, so I changed X".
- No artifact decision cites the approach document.
- The same critique appears 3+ times with no behavior change.
- The approach document relaxes criteria or rationalizes defects instead of improving production.

If the artifact passes but self-evolution failed, accept the artifact and mark the approach document low-value. If neither passes nor self-evolves, change producer/verifier setup, tighten verifier evidence, or escalate to `/gepa`.

---

## References / related skills

- **`/producer-verifier-loop`** — optional L0 base machinery when the harness provides verifier-approved termination via `complete_sequence`.
- **`/gepa`** — optional L2 escalation when the harness provides candidate pools, Pareto frontiers, rollout batches, evaluators, and harness-tuner roles.
- **`/spec-to-cad`** — CAD E2E pipeline consumer; CAD-specific rules belong there, not in this general skill.

Use this skill as a composable middle layer: autonomous producer-verifier iteration with one evolving producer approach, no domain assumptions, and no frontier machinery.
