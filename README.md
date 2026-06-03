# Zen CAD

Zen CAD는 에이전트/harness가 실제 CAD를 먼저 만들도록 돕는 **portable CAD skill pack + lightweight workflow notes + optional validation CLI**입니다.

0.6.x부터 Zen CAD의 기본값은 text-to-cad 스타일의 harness-native 실행입니다. CoBrA, Codex, Claude Code, Cursor 같은 harness가 CAD 생성 도구, 파일 편집, 터미널 실행, 웹/카탈로그 검색, 메모리, worker orchestration을 담당합니다. Zen CAD는 그 위에 source-lock, milestone, BOM/report, completion evidence 같은 장점을 **final/release 단계에서 켜는 optional gate**로 제공합니다.

즉 기본 목표는 “env를 완전히 고치기 전에도 CAD를 생성하고 확인한다”입니다. `doctor --cad-required`와 `validate-completion`은 첫 CAD pass를 막는 preflight가 아니라 final claim을 걸 때 쓰는 stricter gate입니다.

## 3분 quickstart

처음 실행할 때는 레포가 정상인지 확인합니다.

```bash
git clone https://github.com/songch9511/zen-cad.git
cd zen-cad
./zen-cad doctor
```

`doctor`는 현재 폴더가 Zen CAD 레포인지, 필수 파일과 JSON/CSV 스키마가 맞는지, CoBrA skill discovery/workspace binding 상태가 어떤지 확인합니다. CAD toolchain preflight도 보여주지만, 0.6.x 기본 flow에서는 여기서 멈추지 않습니다. `numpy`, `trimesh`, `build123d` 등이 `ENV_BLOCKED`로 떠도 repo/skills가 정상이면 에이전트에게 CAD 생성을 맡깁니다.

Strict CAD preflight는 final/release claim을 걸 때만 사용합니다.

```bash
./zen-cad doctor --cad-required --python /path/to/.venv/bin/python
```

그다음에는 CoBrA, Codex, Claude Code, Cursor 같은 에이전트에서 자연어로 요청합니다.

```text
NEMA17 mount plate를 만들어줘
```

에이전트는 이 요청을 Zen CAD milestone 시작으로 해석하고, 레포 안에서 내부적으로 `scripts/new_milestone.py --request "<goal>"`를 실행해야 합니다. 새 milestone은 기본적으로 `maturity: concept`에서 시작하므로 CAD 생성이 source-lock보다 먼저 진행될 수 있습니다. 사용자가 milestone id나 title을 직접 고르거나 `zen-cad new`를 외울 필요는 없습니다.

직접 터미널에서 milestone을 만들고 싶을 때만 수동 래퍼를 사용합니다.

```bash
./zen-cad new --maturity concept "NEMA17 mount plate를 만들어줘"
```

milestone이 생성된 뒤 첫 CAD pass에서는 구조만 확인하고 바로 생성으로 들어갑니다.

```bash
./zen-cad validate --level structure milestones/<id>
```

final/release-grade 완료를 주장할 때만 completion evidence gate를 실행합니다.

```bash
./zen-cad validate --level completion milestones/<id>
```

검증 출력은 두 층으로 나뉩니다.

- `Zen CAD validation result: PASS`: 필수 파일, schema, BOM header, milestone 구조가 유효합니다.
- `Zen CAD completion validation result: BLOCKED`: source-lock, proxy 격리, STEP cache/export, CAD kernel checks, BOM/report evidence 중 아직 막힌 final gate가 있습니다. concept/layout 산출물에서는 정상적인 중간 상태일 수 있습니다.

기존 호환 명령도 남아 있습니다. `./zen-cad validate milestones/<id>`는 구조 PASS를 exit code 0으로 유지하면서 completion blockers를 같이 출력합니다. CI나 release gate에서는 `validate-completion` 또는 `--level completion`을 사용해야 합니다.

```bash
./zen-cad validate-structure milestones/<id>
./zen-cad validate-completion milestones/<id>
./zen-cad source-lock milestones/<id>
./zen-cad blocked-report --write milestones/<id>
```

Preview는 사람이 보는 리뷰 자료입니다. 완료 선언에는 재현 가능한 evidence가 필요합니다.

- CAD source
- STEP/STL exports
- validation JSON
- CONTACT_MAP / CONNECTIONS
- BOM
- final engineering report

## 핵심 원칙

1. `/agentic-cad`가 최상위 워크플로우이자 source of truth입니다.
2. 첫 concept/layout pass에서는 harness가 가능한 CAD를 먼저 생성하고, 표준/카탈로그 부품은 proxy 또는 unresolved sourcing으로 명확히 표시합니다.
3. final/release 단계에서는 나사, 베어링, 모터, 커넥터 같은 표준/카탈로그 부품을 생성 CAD로 대체하지 말고 source-lock합니다.
4. 소싱과 검증이 끝나지 않은 생성 표준품은 최종 부품이 아니라 proxy입니다.
5. STEP 형상은 엔지니어링 인증, 정격, 재질, 수명, 안전성을 증명하지 않습니다.
6. 뷰어 스크린샷과 GLB preview는 사람이 보기 위한 리뷰 자료일 뿐 completion evidence가 아닙니다.
7. 완료 선언에는 CAD source, STEP exports, validation JSON, kernel/export checks, CONTACT_MAP, CONNECTIONS, BOM, final engineering report 같은 재현 가능한 증거가 필요합니다.
8. 새 CAD 작업은 기본적으로 milestone으로 진행합니다.
9. 워크플로우 개선점은 다시 `/agentic-cad`에 피드백합니다.

작은 final demo가 포함되어 있습니다.

```bash
./zen-cad validate-completion milestones/002_nema17_mount_plate
```

## 0.6.x harness-native contract

Zen CAD 0.6.x의 제품 경계는 다음과 같습니다.

- **Harness**: CoBrA/Codex/Claude Code/Cursor가 CAD generation, file edit, terminal, web/catalog lookup, memory, worker delegation을 수행합니다.
- **Zen CAD skills**: `/agentic-cad`, `/spec-to-cad`, `/self-evolving-producer-verifier`가 lightweight CAD workflow policy와 role handoff를 제공합니다.
- **Zen CAD validation core**: `./zen-cad`, `scripts/`, `schemas/`, `templates/`, `checklists/`가 milestone structure와 optional final completion evidence를 기계적으로 검사합니다.
- **Harness adapters**: `plugins/`와 `docs/harness_adapters.md`가 각 agent harness에서 skills와 validation CLI를 연결하는 얇은 설치/운영 계약을 설명합니다. CoBrA에서는 `init --with-cobra`가 설치된 skill 옆에 `ZEN_CAD_WORKSPACE.md`를 생성해서 repo root binding을 보존합니다.

즉 Zen CAD는 CAD kernel, STEP search engine, browser automation을 자체 구현하지 않습니다. 그 기능은 harness와 외부 CAD/Part RAG 도구에 맡기고, Zen CAD는 첫 CAD artifact가 나온 뒤 final/release 품질을 높이는 보조 gate로 작동합니다.

## Maturity and gate contract

Zen CAD는 이제 one-shot CAD generator와 경쟁하지 않고 harness-native generator를 활용합니다. `concept`와 `layout`에서는 proxy/envelope CAD 생성을 우선 허용하고, `final` completion claim은 아래 gate가 PASS일 때만 가능합니다.

1. Gate 0: doctor / environment preflight
2. Gate 1: requirement normalization
3. Gate 2: standard part source-lock
4. Gate 3: custom CAD generation
5. Gate 4: assembly contract
6. Gate 5: export/cache verification
7. Gate 6: CAD-kernel validation
8. Gate 7: final report / BOM / evidence bundle

표준품은 final maturity에서 `status: "source_locked"`, supplier/SKU/source URL/datasheet/cached STEP/STP/critical dimensions evidence가 있어야 completion-eligible입니다. `concept`와 `layout`에서는 source-lock blocker를 truthful warning으로 남기고 CAD 생성을 진행할 수 있습니다. `placeholder_proxy`, proxy STL, screenshot, GLB/viewer snapshot은 preview/debug artifact일 뿐 final completion evidence가 아닙니다.

막힌 milestone은 실패를 감추지 말고 blocked report로 남깁니다.

```bash
./zen-cad blocked-report --write milestones/<id>
```

이 명령은 `07_report/blocked_report.md`에 완료된 gate, 막힌 gate, smallest unblock step을 기록합니다.

## 포함된 스킬

- `/agentic-cad`: 상위 오케스트레이터입니다. 요구사항, 리서치, 파트 분류, 표준품 소싱, CAD handoff, 검증, BOM, 최종 리포트를 관리합니다.
- `/spec-to-cad`: measurable spec과 CONTACT_MAP/CONNECTIONS를 받아 실제 CAD 구현, STEP/STL export, kernel-backed validation, JSON evidence를 만드는 downstream 실행 스킬입니다.
- `/self-evolving-producer-verifier`: producer와 verifier를 분리해 반복 개선하는 루프입니다. verifier가 원래 기준으로 산출물을 반려/승인하고, producer는 접근 문서를 갱신하며 같은 결함을 줄입니다.

## 설치

레포를 받은 뒤 루트에서 doctor를 먼저 실행합니다.

```bash
git clone https://github.com/songch9511/zen-cad.git
cd zen-cad
./zen-cad doctor
```

초기 검증과 선택적 milestone 생성을 한 번에 하려면 `init`을 사용할 수 있습니다.

```bash
./zen-cad init
```

기존 스크립트도 그대로 사용할 수 있습니다.

```bash
python3 scripts/setup_zen_cad.py
```

두 명령 모두 필수 파일, JSON/CSV 스키마, 모든 milestone skeleton을 검증합니다.

CoBrA에서 사용할 경우 bundled skills를 CoBrA skills 디렉터리로 동기화합니다.

```bash
./zen-cad init --with-cobra
```

이때 `/agentic-cad`, `/spec-to-cad`, `/self-evolving-producer-verifier`가 함께 설치됩니다.

중요: CoBrA skill sync는 워크플로우 스킬과 repo root binding을 설치합니다. CoBrA 프로세스의 현재 작업 디렉터리를 자동으로 바꾸지는 않습니다. CoBrA daemon이나 세션은 가능하면 `zen-cad` 레포에서 시작하고, repo 밖에서 skill이 호출되면 설치된 `ZEN_CAD_WORKSPACE.md`를 읽어 이 레포 경로를 복구해야 합니다.

0.6.1부터 CoBrA sync는 각 설치 skill 디렉터리에 `ZEN_CAD_WORKSPACE.md`도 씁니다. CoBrA가 `/agentic-cad`를 repo 밖에서 호출해도 이 파일을 읽어 Zen CAD repo root를 복구할 수 있습니다.

## 실제 사용 흐름

### 1. 사용자가 자연어로 CAD 목표를 말합니다

CoBrA나 다른 에이전트 세션에서 사용자는 별도 명령을 외울 필요 없이 CAD 목표를 말하면 됩니다.

```text
기어 박스를 만들고 싶어
```

에이전트는 이것을 새 Zen CAD 작업 요청으로 해석합니다. 사용자가 milestone id나 title을 직접 정하게 하지 않고, 내부적으로 다음 명령을 실행합니다.

```bash
python3 scripts/new_milestone.py --request "<goal>"
```

`./zen-cad new "<goal>"`는 같은 작업을 터미널에서 직접 실행하기 위한 수동 래퍼입니다.

예를 들어 `기어 박스를 만들고 싶어`는 다음 사용 가능한 `*_gearbox` milestone을 만들고, title은 `Gearbox`로 설정합니다.

### 2. milestone 폴더가 작업 공간이 됩니다

새 작업은 `milestones/<id>/` 아래에 생성됩니다.

```text
milestones/003_gearbox/
├─ 00_requirements/requirements_brief.md
├─ 01_research/research_log.md
├─ 02_parts/part_classification_table.md
├─ 02_parts/selected_parts_manifest.json
├─ 03_cad/custom_cad_handoff.yaml
├─ 04_assembly/contact_map.json
├─ 04_assembly/connections.json
├─ 05_validation/validation_report.json
├─ 06_bom/bom.csv
└─ 07_report/final_engineering_report.md
```

이 폴더가 요구사항, 리서치, 부품 소싱, CAD handoff, assembly relationship, 검증 증거, BOM, 최종 리포트의 기준 위치가 됩니다.

### 3. 표준 부품은 먼저 소싱합니다

Zen CAD의 기본 흐름은 source-first/generate-second입니다.

예를 들어 기어박스라면:

- 베어링, 볼트, 모터, 샤프트 키, 표준 기어는 먼저 제조사/카탈로그/데이터시트/STEP 소스를 찾습니다.
- 하우징, 브래킷, 커버, 어댑터, 내부 배치용 플레이트처럼 설계에 특화된 부품만 생성 대상으로 둡니다.
- 임시 형상이 필요하면 `placeholder_proxy`로 표시하고, 최종 소싱/검증이 필요하다는 제한을 남깁니다.

### 4. `/spec-to-cad`로 custom CAD를 생성합니다

`/agentic-cad`는 downstream CAD 실행을 위해 handoff bundle을 준비합니다.

이 handoff에는 다음이 포함됩니다.

- measurable spec과 assumptions
- selected sourced parts manifest
- generated 금지 대상인 표준/카탈로그 부품 목록
- custom parts list
- CONTACT_MAP
- CONNECTIONS
- expected exports
- validation criteria

`/spec-to-cad`는 이 정보를 바탕으로 custom CAD를 생성하고, 소싱된 STEP 부품과 통합하며, 가능한 경우 kernel-backed checks와 JSON evidence를 남깁니다.

### 5. verifier가 산출물을 독립적으로 확인합니다

복잡한 작업에서는 `/self-evolving-producer-verifier` 루프를 사용할 수 있습니다.

Producer는 CAD 산출물을 만들고, verifier는 원래 요구사항과 검증 기준에 맞춰 승인 또는 반려합니다. 반려가 나오면 producer는 단순 수정만 하는 것이 아니라 접근 문서에 실패 패턴과 새 규칙을 반영해 다음 반복에서 같은 결함을 줄입니다.

### 6. 검증 후 완료를 선언합니다

수동으로 검증하려면 다음 명령을 실행합니다.

```bash
./zen-cad validate milestones/<id>
```

내부적으로는 `check_required_files.py`, `check_json_schemas.py`, `validate_milestone.py`를 호출합니다. `check_required_files.py`와 `check_json_schemas.py`는 `milestones/` 아래 모든 milestone을 검사합니다.

## 자동화용 milestone 생성

```bash
./zen-cad init \
  --milestone-request "foldable drone landing gear를 만들고 싶어"
```

정확한 id/title을 고정해야 할 때는 다음처럼 명시할 수 있습니다.

```bash
./zen-cad init \
  --milestone-id 002_desktop_cnc_fixture \
  --milestone-title "Desktop CNC workholding fixture"
```

## 레포 구조

```text
zen-cad/
├─ docs/                  휴대 가능한 운영 문서와 harness adapter contract
├─ skills/                `/agentic-cad`, `/spec-to-cad`, verifier 스킬
├─ plugins/               CoBrA, Codex-style, Claude Code-style adapter notes
├─ packages/zen_cad_core/ validation-core package boundary documentation
├─ prompts/               kickoff, milestone, validation, release 프롬프트
├─ templates/             재사용 가능한 artifact 템플릿
├─ schemas/               machine-checkable JSON/CSV 스키마
├─ checklists/            intake, sourcing, CAD, assembly, validation, release 체크리스트
├─ zen-cad                첫 실행용 repo-local CLI wrapper
├─ scripts/               setup, milestone 생성, 검증, release export helper
├─ milestones/_template/  표준 milestone skeleton
├─ milestones/001_nema17_belt_linear_actuator/  source-lock BLOCKED reference milestone
└─ milestones/002_nema17_mount_plate/  final completion PASS demo milestone
```

## CoBrA 사용

전체 CoBrA 흐름은 `docs/cobra_usage.md`를 참고하세요. 짧게는 다음 순서입니다.

1. `./zen-cad init --with-cobra`
2. CoBrA daemon이나 세션을 이 `zen-cad` 레포에서 시작합니다. 다른 폴더에서 시작한다면 프롬프트에 이 레포 경로를 명시합니다.
3. 새 CoBrA 세션에서 `기어 박스를 만들고 싶어`처럼 CAD 목표를 말합니다.
4. 에이전트가 내부적으로 `scripts/new_milestone.py --request "<goal>"`를 실행합니다.
5. 생성된 milestone 안에서 `/agentic-cad` 워크플로우를 진행합니다.
6. `/spec-to-cad`와 verifier evidence를 통해 CAD 결과를 검증합니다.
7. 검증 스크립트와 최종 리포트 근거 없이 완료를 선언하지 않습니다.

`--sync-cobra-skill` 또는 `./zen-cad init --with-cobra`는 CoBrA skill 설치만 수행합니다. 레포 workspace 선택은 CoBrA 실행 위치나 세션 설정에서 별도로 결정됩니다.

## CoBrA가 아닌 환경

`docs/non_cobra_usage.md`, `docs/harness_adapters.md`, `plugins/`, `skills/`, `prompts/`를 일반 Markdown 운영 지침으로 사용할 수 있습니다. 파일 읽기/쓰기, CAD artifact 생성 또는 수정, 검증 스크립트 실행, evidence 보존이 가능한 에이전트 환경이라면 Zen CAD를 사용할 수 있습니다.

## 현재 한계

Zen CAD 자체는 CAD kernel이나 STEP part search engine이 아닙니다. 실제 형상 생성, STEP/STL export, catalog part retrieval, simulation은 연결된 CAD 도구, Part RAG, 또는 에이전트 환경의 실행 능력에 의존합니다. Zen CAD의 역할은 그 작업이 구조화되고, 검증 가능하며, 재현 가능한 evidence를 남기도록 강제하는 것입니다.
