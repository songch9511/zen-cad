# Zen CAD

기계 설계 에이전트를 위한 assembly-first CAD contract runtime입니다.

[![Version](https://img.shields.io/badge/version-1.1.0-4A5568?style=for-the-badge)](VERSION)
[![1.1 Line](https://img.shields.io/badge/1.1--line-replacement-00A676?style=for-the-badge)](CHANGELOG.md)
[![Assembly First](https://img.shields.io/badge/assembly--first-layout-2F80ED?style=for-the-badge)](skills/assembly-layout/SKILL.md)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

Zen CAD는 Codex 같은 범용 에이전트가 자연어 기계 설계 요청을 더 검사 가능한 CAD 작업으로 바꾸도록 돕습니다. 핵심 규칙은 단순합니다. **형상을 예쁘게 만들기 전에 기계적 의도를 먼저 잠급니다.**

워크플로는 CAD-native spec에서 시작합니다. 그 다음 frame, datum, axis, bore, shaft, bolt pattern, pitch reference, clearance, motion relationship, source evidence를 layout, generation, review, handoff artifact 전체에 걸쳐 보존합니다.

## 현재 버전

- 제품/plugin 버전: `1.1.0`
- contract schema 버전: `0.8.0`
- 기본 local generation target: `build123d`
- review target: generated STEP + 선택적 repo-local viewer link/snapshot
- evidence 우선순위: 측정 가능한 geometry check 먼저, visual review는 그 다음, prose caveat는 마지막

## 하는 일

- 자연어 기계 설계 요청을 CAD-native spec으로 변환합니다.
- layout, interface, inspection, proceed review, handoff용 machine-readable contract package를 만듭니다.
- local dependency가 있으면 first-pass build123d STEP artifact를 생성합니다.
- hole, bore, repeated hole pattern, chamfer, 지원되는 fillet approximation, simplified gear teeth 같은 feature intent를 보존합니다.
- 명시적 evidence가 있으면 source-locked STEP/STP 부품을 generated build123d source에 import합니다.
- `interface_frame`과 `replacement_plan` contract로 source/detail CAD가 proxy를 치환해도 locked facts가 움직이지 않게 합니다.
- `detail_shape_plan`으로 custom part가 사용자 shape intent를 따르면서 protected interface zone을 보존하게 합니다.
- repo-local viewer review link와 선택적 PNG snapshot을 package합니다.
- floating body, interference, clearance, fastening, alignment, mesh/contact, implausible support path를 visual/engineering review에서 점검하도록 안내합니다.

## 하지 않는 일

- CAD kernel, CAE solver, manufacturing review, certification process를 대체하지 않습니다.
- supplier SKU 정확성, 재고, rating, certification, compliance claim을 보장하지 않습니다.
- 광범위한 catalog crawling을 기본 동작으로 하지 않습니다.
- screenshot이나 viewer link만으로 완료를 증명하지 않습니다.
- 특정 subagent runtime을 강제하지 않습니다. subagent가 있으면 dispatch plan을 쓰고, 없으면 lead agent가 같은 review role을 순차 실행합니다.

## Workflow

1. locked parameter, frame, interface, inspection target을 포함한 CAD-native spec을 작성합니다.
2. kernel-neutral layout proxy를 생성하고 locked facts가 보존됐는지 검사합니다.
3. build123d source를 export하고 source-level carry-through를 검사합니다.
4. `build123d`가 가능하면 STEP artifact를 생성합니다.
5. standard/catalog proxy는 interface frame mapping과 inspection이 가능할 때 source-locked STEP/STP로 치환합니다.
6. source component가 아닌 custom part는 locked facts와 user shape intent를 기반으로 constrained detail CAD를 생성합니다.
7. inspection report, generated artifact, 선택적 viewer evidence를 proceed gate로 package합니다.
8. visual/mechanical review를 수행하고 가장 작은 source-level 원인을 수정한 뒤 재생성합니다.
9. 사용자 approval 이후 downstream detail handoff를 생성합니다.

## Codex 사용법

local plugin bundle은 [`plugins/zen-cad`](plugins/zen-cad)에 있습니다. 폴더를 project로 연결하는 것만으로는 slash skill이 등록되지 않습니다. `.codex-plugin/marketplace.json`에서 local `zen-cad` plugin을 설치한 뒤 새 chat을 시작하세요.

주요 entrypoint:

- `/cad-spec`
- `/assembly-layout`
- `/interface-signatures`
- `/cad-handoff`
- `/cad-replacement`
- `/constrained-detail-cad`

plain prompt로도 사용할 수 있습니다.

```text
Use skills/cad-spec/SKILL.md to create a CAD-native spec for:
Create a flat planetary gear assembly with separate sun, planet, ring, carrier, and pin bodies. Use simplified trapezoidal teeth and place three planets around the sun on a 42 mm radius circle.
```

generation과 review까지 이어갈 때는 다음 지시가 유용합니다.

```text
Create the CAD-native spec, generate the first-pass STEP if the local harness supports it, inspect the result visually and mechanically, repair source-level issues, and package the proceed gate. Use specialist subagents if available; otherwise run the same review roles sequentially.
```

## CoBrA 사용법

CoBrA workspace skill로 설치하려면 installer를 실행합니다.

```bash
python3 tools/install_cobra.py --with-cad-deps
```

설치 후 새 CoBrA chat을 시작하거나 skill picker를 새로고침한 뒤 `/zen-cad` 또는 `/cad-spec`로 시작합니다.

```text
/zen-cad create a NEMA17 mount plate
/cad-spec create a GT2 belt driven linear slide
```

CAD 의존성 없이 spec/handoff만 사용하려면 `--with-cad-deps`를 빼고 실행합니다. 자세한 옵션은 [`docs/cobra_usage.md`](docs/cobra_usage.md)를 보세요.

## Command Flow

전체 local build123d pipeline:

```bash
python3 tools/run_contract_pipeline.py --package <contract-package> --out <run-dir> --target-harness build123d
```

`http://localhost:5173`용 repo-local viewer link 생성:

```bash
(cd viewer && npm run dev:local)
python3 tools/run_contract_pipeline.py --package <contract-package> --out <run-dir> --target-harness build123d --viewer-base-url http://localhost:5173
```

review evidence용 viewer snapshot capture:

```bash
python3 tools/run_contract_pipeline.py --package <contract-package> --out <run-dir> --target-harness build123d --viewer-base-url http://localhost:5173 --capture-viewer-snapshot
```

proceed gate 승인 후 detail handoff 생성:

```bash
python3 tools/approve_proceed_gate.py --proceed-gate <run-dir>/proceed_gate.json --out <approval.json>
python3 tools/run_contract_pipeline.py --package <contract-package> --out <detail-run-dir> --target-harness text-to-cad --approval <approval.json>
```

step.parts source download 및 source-lock 생성:

```bash
python3 tools/download_step_part.py --id <step-parts-id> --download --out-dir <contract-package>/sourced_parts/step_parts --package <contract-package> --part-id <part-id> --source-lock-out <contract-package>/<part-id>_source_lock.json
```

## 1.1 핵심: Proxy 이후

1.1.0에서 layout proxy는 단순한 rough visual placeholder가 아닙니다. proxy는 source/detail CAD를 끼워 넣기 위한 **정밀 interface scaffold**입니다.

### Source/Detail Replacement

`/cad-replacement`는 proxy part를 source-locked STEP/STP, user-provided detail CAD, generated detail candidate로 치환할 때 사용합니다.

핵심 contract:

- proxy `interface_frame`
- source/detail `interface_frame`
- `replacement_plan`
- frame transform: `world_source = world_proxy_frame * inverse(source_frame)`
- post-replacement locked-fact inspection

source geometry가 import됐다는 사실만으로는 충분하지 않습니다. 치환 후 axis, plane, bolt pattern, clearance, relationship이 tolerance 안에 들어왔는지 측정해야 합니다.

### Constrained Detail CAD

`/constrained-detail-cad`는 bracket, plate, cover, housing, adapter 같은 custom part를 만들 때 사용합니다.

custom detail generation은 세 영역을 분리합니다.

- protected interface zone: bore, shaft, bearing seat, mounting plane, bolt pattern, clearance envelope, motion sweep
- functional structure zone: rib, boss, wall, support path, shell
- freeform/style zone: outer silhouette, pocket, cosmetic relief, edge treatment

사용자 shape intent는 중요하지만 soft constraint입니다. locked facts, protected zone, clearance rule은 hard constraint입니다.

## Native Benchmarks

curated benchmark package는 [`benchmarks/`](benchmarks)에 있습니다.

- rectangular calibration block
- circular flange
- simplified planetary gear stage

각 benchmark는 through-hole, bore, bolt circle, chamfer, edge-round approximation, separate bodies, repeated gear-like teeth처럼 Zen CAD가 보존해야 하는 feature를 작게 검증합니다.

## Visual Review And Repair

Zen CAD의 visual review는 simulation이 아닙니다. 목표는 generated CAD를 보고 기계적 문제를 이름 붙인 뒤, 이를 측정 가능한 contract check로 바꾸고, source를 고친 뒤, 다시 생성하는 것입니다.

review에서 확인할 항목:

- floating 또는 unsupported body
- unintended intersection
- insufficient clearance
- missing fastener engagement
- shaft, bore, bearing, pulley misalignment
- belt, gear, contact-plane mismatch
- weak 또는 implausible load path

viewer screenshot은 review artifact로 유용하지만 완료 evidence는 아닙니다. 완료 판단은 geometry report, locked facts, inspection check, user approval에 의존합니다.

## Repository Map

- [`skills/`](skills): agent-facing workflow
- [`schemas/`](schemas): machine-readable contract surface
- [`registry/interfaces/`](registry/interfaces): layout-ready interface facts
- [`tools/run_contract_pipeline.py`](tools/run_contract_pipeline.py): one-command pipeline runner
- [`tools/generate_cad_artifact.py`](tools/generate_cad_artifact.py): build123d STEP generation 및 inspection
- [`tools/download_step_part.py`](tools/download_step_part.py): step.parts download 및 checksum-backed source-lock evidence
- [`tools/package_viewer_link.py`](tools/package_viewer_link.py): repo-local viewer link packaging
- [`tools/capture_viewer_snapshot.py`](tools/capture_viewer_snapshot.py): 선택적 viewer PNG capture
- [`schemas/interface_frame.schema.json`](schemas/interface_frame.schema.json): proxy/source/detail frame anchor
- [`schemas/replacement_plan.schema.json`](schemas/replacement_plan.schema.json): source/detail replacement transform 및 inspection contract
- [`schemas/detail_shape_plan.schema.json`](schemas/detail_shape_plan.schema.json): locked facts와 shape intent 기반 custom detail CAD plan

## Development Checks

```bash
python3 tools/validate_contract.py
python3 -m unittest discover -s tests
python3 -m py_compile tools/*.py tests/*.py
```

temporary project run은 `work/` 같은 ignored run directory에 둡니다. curated benchmark contract는 [`benchmarks/`](benchmarks)에 둡니다.
