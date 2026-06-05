# Zen CAD

Agentic mechanical design을 위한 harness-native CAD specification skill pack.

[![Version](https://img.shields.io/badge/version-0.8.0-4A5568?style=for-the-badge)](VERSION)
[![Spec First](https://img.shields.io/badge/CAD--native-spec--first-00A676?style=for-the-badge)](skills/cad-spec/SKILL.md)
[![Assembly First](https://img.shields.io/badge/assembly--first-layout-2F80ED?style=for-the-badge)](skills/assembly-layout/SKILL.md)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

Zen CAD는 Codex, Claude Code 같은 General Purpose 에이전트와 CAD 생성 harness가 더 나은 CAD 결과를 만들도록 돕는 스킬 팩입니다.

이 레포의 목표는 자연어 요청을 바로 형상으로 밀어 넣는 것이 아니라, 먼저 CAD-native spec을 작성해 어셈블리의 위치 관계, 결합부, 구동계, 파라미터, 검사 계획을 잠그는 것입니다.

핵심 철학은 단순합니다. 처음 생성되는 모델은 표면 품질보다 어셈블리 계약을 맞추는 데 집중합니다. 즉, 복잡한 곡면이나 미려한 외형보다 좌표계, datum, 축, bore, shaft, bolt pattern, pitch reference, clearance, motion relationship이 먼저 맞아야 합니다.
이후 사용자가 layout proxy를 보고 proceed하면, 그 locked facts를 유지한 채 detail CAD로 넘어가 최종적으로 패키징하게 됩니다.

## Workflow

1. 사용자의 자연어 요청을 CAD-native spec으로 변환합니다.
2. CAD 생성 전에 named parameters, artifact targets, inspection checks, repair rules를 정의합니다.
3. coordinate frames, datums, interface primitives, motion relationships, proxy fidelity를 잠급니다.
4. harness가 지원하면 specialist subagents를 사용합니다: layout, parameters, interfaces, motion, CAD generation, inspection, review.
5. 표면 품질보다 어셈블리 positioning이 맞는 low-detail layout proxy를 먼저 생성합니다.
6. locked facts 기준으로 inspect, repair, rerun을 수행합니다.
7. 사용자가 assembly contract를 승인한 뒤 detail CAD로 진행합니다.

Generated CAD는 downstream harness가 explicit artifact paths, 실제 실행한 deterministic checks, skipped checks와 이유, repair attempts, 지원되는 snapshot/viewer evidence를 반환하기 전까지 reviewed로 취급하지 않습니다. Visual evidence는 리뷰에 유용하지만, geometry facts, measurements, frames, mating checks가 더 강한 검증 근거입니다.

## Skills

| Skill | 역할 |
| --- | --- |
| [`cad-spec`](skills/cad-spec/SKILL.md) | 기본 entrypoint. CAD-native spec을 작성하고 layout, parameter, interface, motion, handoff, generation, inspection, review subtask를 조율합니다. |
| [`assembly-layout`](skills/assembly-layout/SKILL.md) | root frame, assembly graph, contact, connection, motion relationship, locked facts, proceed readiness를 정의하고 리뷰합니다. |
| [`interface-signatures`](skills/interface-signatures/SKILL.md) | supplier STEP 없이도 layout에 필요한 표준 부품의 interface facts를 캡처합니다. |
| [`cad-handoff`](skills/cad-handoff/SKILL.md) | 승인된 spec을 active CAD generator가 실행할 수 있는 간결한 downstream brief로 변환합니다. |

## Spec에 포함되어야 하는 것

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

## Machine-Readable Foundation

Zen CAD 0.8.0은 Markdown spec을 기본 사용자 경험으로 유지하지만, agent/runtime이 같은 계약을 검증할 수 있도록 machine-readable foundation을 포함합니다.

- [`schemas/`](schemas): CAD spec, layout contract, interface signature, inspection report, handoff packet JSON Schemas.
- [`registry/interfaces/`](registry/interfaces): first-pass layout proxy에 필요한 built-in interface signatures.
- [`tools/validate_contract.py`](tools/validate_contract.py): schema surface, interface registry, optional contract package를 검사하는 dependency-free validator.
- [`tools/generate_layout_proxy.py`](tools/generate_layout_proxy.py): validated contract package에서 kernel-neutral layout proxy scene과 inspection report skeleton을 생성하는 dependency-free generator.
- [`tools/inspect_layout_proxy.py`](tools/inspect_layout_proxy.py): layout proxy scene이 spec/layout contract의 locked facts, parts, relationships, interface datums를 보존하는지 검사하는 dependency-free inspector.
- [`tools/export_cad_source.py`](tools/export_cad_source.py): layout proxy scene을 build123d-style CAD source와 source manifest로 변환하는 adapter.
- [`tools/inspect_cad_source.py`](tools/inspect_cad_source.py): exported CAD source가 scene/manifest의 primitives, locked facts, inspection targets를 보존하는지 검사하는 source-level adapter.
- [`tools/package_proceed_gate.py`](tools/package_proceed_gate.py): artifacts와 inspection reports를 사용자 proceed review용 package로 묶습니다.
- [`tools/generate_detail_handoff.py`](tools/generate_detail_handoff.py): ready proceed gate에서 locked facts를 보존하는 detail CAD handoff packet을 생성합니다.

이 registry는 부품 카탈로그가 아닙니다. supplier identity, SKU, 가격, 재고, rating, certification, 최종 STEP geometry를 보장하지 않습니다. 목적은 웹서치 없이도 layout 단계에서 축, datum, bore, shaft, pitch reference, clearance, envelope를 빠르게 잡는 것입니다.

이 도구들의 출력은 STEP이나 최종 CAD certification이 아닙니다. Zen CAD는 spec, scene, source, report, proceed gate, handoff를 연결해 downstream CAD harness가 덜 임의적으로 동작하게 만드는 runtime입니다. 실제 CAD generation과 geometry inspection은 여전히 downstream harness에서 수행해야 합니다.

## Recommended Prompt

```text
$cad-spec를 사용해서 아래 기계 설계 요청을 CAD-native layout spec으로 변환해줘:
<요청>

CAD 생성까지 필요하다면 harness가 지원하는 범위에서 layout, parameters, interfaces,
motion/drivetrain, CAD generation, inspection, review specialist subagents를 사용해줘.
```

## Development Checks

```bash
python3 -m unittest discover -s tests
python3 tools/validate_contract.py
python3 tools/generate_layout_proxy.py --package <contract-package> --out <out-dir>
python3 tools/inspect_layout_proxy.py --package <contract-package> --scene <out-dir>/layout_proxy.scene.json --out <report.json>
python3 tools/export_cad_source.py --package <contract-package> --scene <out-dir>/layout_proxy.scene.json --out <source-dir>
python3 tools/inspect_cad_source.py --scene <out-dir>/layout_proxy.scene.json --manifest <source-dir>/cad_source_manifest.json --source <source-dir>/layout_proxy_build123d.py --out <source-report.json>
python3 tools/package_proceed_gate.py --package <contract-package> --artifact <out-dir>/layout_proxy.scene.json --artifact <source-dir>/layout_proxy_build123d.py --report <report.json> --report <source-report.json> --out <proceed-gate.json>
python3 tools/generate_detail_handoff.py --package <contract-package> --proceed-gate <proceed-gate.json> --out <detail-handoff.json>
```

예시 CAD spec은 메인에 커밋하지 않습니다. 예시는 테스트용 임시 fixture나 별도 curated artifact로 관리합니다.
