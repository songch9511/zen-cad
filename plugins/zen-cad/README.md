# Zen CAD

Assembly-first CAD contract runtime for mechanical design agents.

[![Version](https://img.shields.io/badge/version-1.0.1-4A5568?style=for-the-badge)](VERSION)
[![1.0 Line](https://img.shields.io/badge/1.0--line-source--lock-00A676?style=for-the-badge)](CHANGELOG.md)
[![Assembly First](https://img.shields.io/badge/assembly--first-layout-2F80ED?style=for-the-badge)](skills/assembly-layout/SKILL.md)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

Zen CAD는 Codex, Claude Code 같은 범용 에이전트와 CAD 생성 harness가 자연어 요청을 더 안정적인 어셈블리 모델로 바꾸도록 돕는 runtime입니다.

핵심 목표는 자연어를 바로 고품질 형상으로 밀어 넣는 것이 아닙니다. 먼저 CAD-native spec을 만들고, 어셈블리의 위치 관계, 결합부, 구동계, 파라미터, 검사 계획을 잠근 뒤, 낮은 표면 품질의 layout proxy로 assembly contract를 검증합니다. 사용자가 proceed하면 그 locked facts를 보존한 채 detail CAD handoff로 넘어갑니다.

처음 모델에서 중요한 것은 미려한 곡면보다 좌표계, datum, 축, bore, shaft, bolt pattern, pitch reference, clearance, motion relationship입니다. Zen CAD는 이 사실들을 명시하고 검사 가능한 산출물로 연결해 downstream CAD generator의 임의성을 줄입니다.

## 현재 범위

Zen CAD 1.0.1은 Markdown skills와 machine-readable contracts를 함께 제공합니다. 현재 구현은 contract validation부터 layout proxy, inspections, CAD source adapter, feature-aware build123d STEP generation, local viewer link/snapshot packaging, proceed package까지 이어지는 one-command contract pipeline runner를 포함합니다. Detail handoff는 별도 proceed approval artifact가 있을 때만 생성됩니다. Final-stage standard/catalog parts can record explicit source-lock evidence from step.parts, manufacturer URLs, datasheets, project files, or user-provided files without catalog crawling. `tools/download_step_part.py` can search `api.step.parts`, download the selected STEP, verify `sha256`, and write checksum-backed source-lock evidence. When a source-lock artifact includes a STEP/STP geometry reference, the build123d source adapter imports that geometry with `import_step()` and replaces the matching layout proxy primitives. Contract documents keep `schema_version: 0.8.0` for contract compatibility.

Zen CAD가 하는 일:

- CAD-native spec 작성 규칙 제공;
- specialist subagent orchestration 지시 제공;
- assembly layout, interface signature, handoff skill 제공;
- JSON Schema 기반 contract surface 제공;
- built-in interface registry 제공;
- runner, validator, layout proxy generator, source adapter, build123d STEP generator, inspector 제공;
- feature plan 기반 holes, bores, bolt-circle/repeated patterns, rectangular chamfers, simplified gear teeth, and supported cylinder edge-round approximations 제공;
- generated STEP에 대한 local CAD Viewer link artifact 및 optional PNG snapshot 제공;
- proceed 전 layout facts 보존 여부를 machine-readable하게 점검.
- final-stage standard/catalog parts의 source-lock evidence를 machine-readable하게 기록.

Zen CAD가 하지 않는 일:

- 모든 CAD kernel/runtime을 자체 구현하기;
- supplier 카탈로그를 광범위하게 뒤지기;
- SKU, 가격, 재고, rating, certification 보장하기;
- 최종 상세 STEP geometry, true involute gear teeth, manufacturing readiness 자체를 보장하기;
- selector-based topology fillet/chamfer 검사를 모든 build123d/OCP 환경에서 보장하기;
- geometry inspection이나 engineering certification을 대체하기.

Zen CAD는 build123d가 있는 환경에서 layout/detail candidate STEP을 직접 생성할 수 있습니다. 다만 고급 topology inspection, source-locked supplier geometry alignment, manufacturing checks는 여전히 active CAD harness나 후속 검사 도구가 맡아야 합니다. Local viewer links and snapshots are review aids only.

## Pipeline

1. 사용자의 자연어 요청을 CAD-native spec으로 변환합니다.
2. named parameters, artifact targets, inspection checks, repair rules를 먼저 정의합니다.
3. coordinate frames, datums, interface primitives, motion relationships, proxy fidelity를 잠급니다.
4. harness가 지원하면 layout, parameters, interfaces, motion, CAD generation, inspection, review subagents를 사용합니다.
5. interface registry에서 layout에 필요한 표준 결합 facts를 조회합니다.
6. one-command runner가 schema와 registry 기준으로 contract package를 검증합니다.
7. runner가 표면 품질보다 positioning을 우선하는 kernel-neutral layout proxy scene을 생성합니다.
8. runner가 layout proxy의 locked facts, parts, relationships, interface datums 보존 여부를 검사합니다.
9. runner가 CAD source adapter로 source intent와 manifest를 생성합니다.
10. runner가 source-level carry-through를 검사합니다.
11. `build123d` target이면 generated source를 실행해 primary STEP artifact와 CAD generation inspection report를 만듭니다.
12. generated STEP이 있으면 local CAD Viewer link artifact를 만듭니다.
13. runner가 사용자 proceed review용 package를 만듭니다.
14. 사용자가 proceed하면 `proceed_approval` artifact를 기록합니다.
15. approval artifact가 있을 때만 runner가 locked facts를 유지하는 detail CAD handoff packet을 생성합니다.
16. standard/catalog/proxy part를 final-stage source로 고정해야 하면 explicit URL/file 기반 `source_lock_evidence`를 별도 artifact로 기록합니다.

Visual evidence는 리뷰에 유용하지만 충분하지 않습니다. geometry facts, measurements, frames, mating checks, skipped checks와 이유, repair attempts가 더 강한 근거입니다.

## Skills

| Skill | 역할 |
| --- | --- |
| [`cad-spec`](skills/cad-spec/SKILL.md) | 기본 entrypoint. CAD-native spec을 작성하고 layout, parameter, interface, motion, handoff, generation, inspection, review subtask를 조율합니다. |
| [`assembly-layout`](skills/assembly-layout/SKILL.md) | root frame, assembly graph, contact, connection, motion relationship, locked facts, proceed readiness를 정의하고 리뷰합니다. |
| [`interface-signatures`](skills/interface-signatures/SKILL.md) | supplier STEP 없이도 layout에 필요한 표준 부품의 interface facts를 캡처합니다. |
| [`cad-handoff`](skills/cad-handoff/SKILL.md) | 승인된 spec을 active CAD generator가 실행할 수 있는 간결한 downstream brief로 변환합니다. |

## Spec에 포함할 것

좋은 CAD-native spec은 최소한 다음을 명시해야 합니다.

- coordinate system, root frame, part-local frames;
- parameter contract: units, defaults, locked/assumed/derived status, driven features, validation targets;
- artifact targets: source intent, primary STEP/STP or equivalent artifact, secondary outputs, review artifacts;
- assembly graph, fixed/moving hierarchy, repeated component families;
- interface primitives: planes, cylinders, bores, shafts, bolt circles, pitch circles, rails, slots, belt planes, gear mesh references;
- motion and drivetrain relationships;
- proxy fidelity policy;
- locked layout facts;
- inspection plan and repair loop;
- proceed gate and downstream CAD handoff.

## Machine-Readable Runtime

| Surface | 역할 |
| --- | --- |
| [`schemas/`](schemas) | CAD spec, layout contract, interface signature, inspection report, handoff packet, layout proxy scene, source manifest, proceed package, proceed approval, pipeline run, review bundle, source-lock evidence JSON Schemas. |
| [`registry/interfaces/`](registry/interfaces) | first-pass layout proxy에 필요한 built-in interface signatures. |
| [`tools/run_contract_pipeline.py`](tools/run_contract_pipeline.py) | validated contract package에서 layout proxy, inspections, CAD source intent, build123d STEP generation, proceed package까지 실행하고, approval이 있으면 detail handoff까지 이어가는 one-command pipeline runner. |
| [`tools/validate_contract.py`](tools/validate_contract.py) | schema surface, interface registry, optional contract package를 검사하는 dependency-free validator. |
| [`tools/generate_layout_proxy.py`](tools/generate_layout_proxy.py) | validated contract package에서 kernel-neutral layout proxy scene과 inspection report skeleton을 생성합니다. |
| [`tools/inspect_layout_proxy.py`](tools/inspect_layout_proxy.py) | layout proxy scene이 spec/layout contract의 locked facts, parts, relationships, interface datums를 보존하는지 검사합니다. |
| [`tools/export_cad_source.py`](tools/export_cad_source.py) | layout proxy scene을 build123d-style CAD source와 source manifest로 변환하고, importable source-lock STEP/STP가 있으면 proxy를 실제 sourced CAD로 대체합니다. |
| [`tools/inspect_cad_source.py`](tools/inspect_cad_source.py) | exported CAD source가 scene/manifest의 primitives, locked facts, inspection targets를 보존하는지 검사합니다. |
| [`tools/generate_cad_artifact.py`](tools/generate_cad_artifact.py) | generated build123d source의 `gen_step()`을 실행해 primary STEP artifact를 만들고 export/import/bbox/volume 및 feature-plan carry-through 검사를 기록합니다. |
| [`tools/package_viewer_link.py`](tools/package_viewer_link.py) | generated STEP을 local CAD Viewer로 열 수 있는 `viewer_link.html` artifact로 패키징합니다. |
| [`tools/capture_viewer_snapshot.py`](tools/capture_viewer_snapshot.py) | local CAD Viewer URL을 Playwright로 열어 모델 load/canvas/PNG snapshot inspection report를 기록합니다. |
| [`tools/package_proceed_gate.py`](tools/package_proceed_gate.py) | artifacts와 inspection reports를 사용자 proceed review용 package로 묶습니다. |
| [`tools/package_review_bundle.py`](tools/package_review_bundle.py) | proceed gate artifacts를 machine-readable review bundle로 묶고, visual evidence가 completion evidence가 아님을 명시합니다. |
| [`tools/package_viewer_review.py`](tools/package_viewer_review.py) | proceed gate와 선택적 viewer artifacts를 사람이 읽는 CAD Viewer review brief로 변환합니다. |
| [`tools/approve_proceed_gate.py`](tools/approve_proceed_gate.py) | 사용자의 proceed 결정을 machine-readable approval artifact로 기록합니다. |
| [`tools/generate_detail_handoff.py`](tools/generate_detail_handoff.py) | proceed gate와 approval이 일치할 때 locked facts를 보존하는 detail CAD handoff packet을 생성합니다. |
| [`tools/package_text_to_cad_bundle.py`](tools/package_text_to_cad_bundle.py) | approved `text-to-cad` handoff packet을 CAD Skills/text-to-cad prompt bundle로 패키징하며, CAD 자체는 생성하지 않습니다. |
| [`tools/generate_source_lock_evidence.py`](tools/generate_source_lock_evidence.py) | explicit step.parts, manufacturer, datasheet, project-file, user-provided locators를 final-stage source-lock evidence로 기록합니다. |
| [`tools/download_step_part.py`](tools/download_step_part.py) | `api.step.parts`에서 part를 찾고 STEP을 다운로드한 뒤 sha256을 검증해 local STEP과 source-lock evidence를 기록합니다. |

이 registry는 부품 카탈로그가 아닙니다. 목적은 웹서치 없이도 layout 단계에서 축, datum, bore, shaft, pitch reference, clearance, envelope를 빠르게 잡는 것입니다.

## Codex Plugin Install

Zen CAD ships a Codex plugin bundle under [`plugins/zen-cad`](plugins/zen-cad). The root
[`.codex-plugin/marketplace.json`](.codex-plugin/marketplace.json) points Codex at that bundle.

Connecting this repository as a project is not enough to register slash skills. Install the
`zen-cad` plugin from the local marketplace, then start a new Codex chat. After installation,
the slash skills are available as:

- `/cad-spec`
- `/assembly-layout`
- `/interface-signatures`
- `/cad-handoff`

For plain prompts, [`AGENTS.md`](AGENTS.md) tells project agents to route mechanical CAD and
assembly requests through `skills/cad-spec/SKILL.md` first.

## Command Flow

```bash
python3 tools/run_contract_pipeline.py --package <contract-package> --out <run-dir> --target-harness build123d
python3 tools/run_contract_pipeline.py --package <contract-package> --out <run-dir> --target-harness build123d --viewer-base-url http://localhost:5173 --viewer-public-dir /Users/daniel/CAD-Visualizer/public
python3 tools/run_contract_pipeline.py --package <contract-package> --out <run-dir> --target-harness build123d --viewer-base-url http://localhost:5173 --viewer-public-dir /Users/daniel/CAD-Visualizer/public --capture-viewer-snapshot --viewer-root /Users/daniel/CAD-Visualizer
python3 tools/package_review_bundle.py --proceed-gate <run-dir>/proceed_gate.json --out <run-dir>/review_bundle.json
python3 tools/approve_proceed_gate.py --proceed-gate <run-dir>/proceed_gate.json --out <approval.json>
python3 tools/run_contract_pipeline.py --package <contract-package> --out <detail-run-dir> --target-harness text-to-cad --approval <approval.json>
python3 tools/package_text_to_cad_bundle.py --handoff <detail-run-dir>/detail_handoff.json --out <text-to-cad-bundle-dir>
python3 tools/generate_source_lock_evidence.py --package <contract-package> --part-id <part-id> --name <source-name> --step-parts-url <url> --step-source-url <step-url> --out <source-lock.json>
python3 tools/download_step_part.py --id <step-parts-id> --download --out-dir <contract-package>/sourced_parts/step_parts --package <contract-package> --part-id <part-id> --source-lock-out <contract-package>/<part-id>_source_lock.json
```

The runner validates the package, generates the kernel-neutral layout proxy scene, inspects scene carry-through, exports CAD source intent, inspects source carry-through, generates a build123d STEP artifact when `--target-harness build123d`, packages a local viewer link, optionally captures a local viewer PNG snapshot with `--capture-viewer-snapshot`, and packages proceed review. During CAD source export, `source_locked` parts with STEP/STP geometry references are carried into the generated build123d source as sourced CAD imports and matching proxy primitives are removed. Contract packages can also include `cad_spec.extensions.cad_feature_plan` for feature-aware generated source: holes, bores, bolt-circle/repeated patterns, rectangular top chamfers, simplified gears, and supported cylinder edge-round approximations. `package_review_bundle.py` can turn the proceed package into a viewer-oriented review bundle, while making clear that screenshots and viewer links are review aids, not completion evidence. After the user approves the layout, `approve_proceed_gate.py` records that decision, and the runner can create the detail handoff packet with `--approval`. For CAD Skills/text-to-cad, `package_text_to_cad_bundle.py` packages that approved handoff into a downstream prompt bundle. Use `generate_source_lock_evidence.py` for explicit source locators and `download_step_part.py` when a standard/catalog/proxy part should be hydrated from step.parts with a verified local STEP checksum. Use individual phase tools when diagnosing a failed stage or integrating a custom harness.

The curated native benchmark packages live under [`benchmarks/`](benchmarks): rectangular calibration block, circular flange, and simplified planetary gear stage.

## Recommended Prompt

```text
$cad-spec를 사용해서 아래 기계 설계 요청을 CAD-native layout spec으로 변환해줘:
<요청>

CAD 생성까지 필요하다면 harness가 지원하는 범위에서 layout, parameters, interfaces,
motion/drivetrain, CAD generation, inspection, review specialist subagents를 사용해줘.
```

## Development Checks

```bash
python3 tools/validate_contract.py
python3 -m unittest discover -s tests
python3 -m py_compile tools/*.py tests/*.py
```

Ad hoc CAD specs are not committed to main. Curated benchmark contracts live under [`benchmarks/`](benchmarks); temporary user/project runs stay under `work/` or another ignored run directory.
