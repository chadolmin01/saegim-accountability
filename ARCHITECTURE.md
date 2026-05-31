# 구조 (ARCHITECTURE)

건축·토목 시공 **책임추적 엔진**. 사고·하자 발생 시 "그 시점에 법정 기준이 충족됐나"를
계산으로 결정적 판정하고, 책임 주체까지 그래프로 추적한다.

## 처리 단계 (5)

판정은 한 덩어리가 아니라 단계로 나뉘고, 각 단계가 어느 *층*에 속하는지가 설계의 핵심이다.

| 단계 | 하는 일 | 층 |
|---|---|---|
| ① 불일치 탐지 | 같은 측정에 걸리는 기준 N개 수집·대조 → 불일치 표시 | 온톨로지 (기준노드 + `source_type`) |
| ② 판정 | 측정값 ↔ 법정/표준 기준 합부 | 온톨로지 (결정적 룰) |
| ③ 기록 | 사건·결정·책임 trail (누가·언제 뭘 택했나) | 온톨로지 (사건층 그래프) |
| ④ 중재 | 진짜 충돌 *해소* (어느 기준 우선) — 판단보조 | RAG·서비스 |
| ⑤ 자동 업로드 | ingest·publish | 인프라 |

**온톨로지(이 repo)는 ①~③의 결정적 영역**까지. ④·⑤는 결정적 룰로 못 푸는 롱테일·판단·인프라라 별도 층이다.
충돌의 *해소*는 인간 판단으로 남기고, 엔진은 불일치를 *감사가능한 사건으로 기록*한다.

## 두 계층

- **기준층 (type graph)** — 고정 스키마. 법정요건(LegalRequirement) + 소관법(Law) + 시설클래스. 룰 = 결정적 체.
- **사건층 (instance graph)** — 사건별 데이터. 배합·운송·반입검수·타설·공시체 측정 이벤트(시간·사람·자격·트럭·부재).
  학술 정렬: PROV-O(Activity/Agent/hadRole) · SOSA(채취 T1 / 28일 결과 T2) · BCOM/EPCIS(배치→부재) · OCQA(합부).

## 디렉토리

```
engine/        판정 라이브러리 12 — 룰 패밀리와 1:1 대응하는 평가기
tests/         회귀·충실도·커버리지 (python -m tests.<name>)
paths.py       경로 앵커 — 모든 룰/데이터를 repo ROOT 기준(CWD 무관)
build_instance_graph.py  사건 시나리오 → 타입드 노드/엣지 (어댑터)
load_to_opencrab.py      그래프를 OpenCRAB local store에 적재
export_opencrab_pack.py  룰 → OpenCRAB pack(modules/composed)
report.py / generate_rules_index.py   리포트·인덱스
run_all_tests.py         전체 회귀 러너
verify_refactor.py       디버그 보험 (리팩터 회귀 가드)
```

룰 데이터(패밀리 폴더 ↔ 평가기):

| 룰 폴더 | 개수 | 평가기 | 차원 |
|---|---|---|---|
| `condition_rules/` | 113 | `engine/conditions.py` | 작업조건 (측정값↔기준 합부) |
| `document_rules/` | 22 | `engine/documents.py` | 문서제출 |
| `prerequisite_rules/` | 8 | `engine/prerequisites.py` | 선행요건 (Hold Point) |
| `placement_rules/` | 11 | `engine/evaluate.py` | 인적배치·선임 |
| `appropriateness_rules/` | 2 | `engine/appropriateness.py` | 설계 적절성 |
| `org_rules/` | 2 | `engine/org_judgment.py` | 도급책임 |
| `maintenance_rules/` | 1 | `engine/maintenance.py` | 유지관리 |
| `material_specs/` | 2 | (재료 임계값, conditions가 참조) | 재료 |

기타: `types/`(스키마) · `examples/`(사건 시나리오) · `corpus/`(법령 원문) · `references/`(설계 노트) · `opencrab_pack/`(export 타깃).
모든 룰에 `regime`+`authority`(근거 §·검증출처) + `source_type`(법령>고시>KDS/KCS·KS>권고, binding 강도) 라벨.

## 실행

```
python build_instance_graph.py examples/incident_graph_demo.yaml   # 사건 그래프 조립
python -m engine.evaluate examples/scenario_understaffed.yaml      # 단일 평가기 CLI
python run_all_tests.py                                            # 전체 회귀
python verify_refactor.py [--cross-cwd]                            # 디버그 보험
```

`paths.py` 앵커 덕분에 실행 위치(CWD)와 무관하게 룰이 로드된다.
리팩터 시 `verify_refactor.py`로 회귀(룰 개수·카논 출력·CWD 독립성)를 먼저 확인할 것.
