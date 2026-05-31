# saegim-accountability

건축물 시공의 **책임추적(accountability tracing)** 을 위한 typed ontology + 법정 규칙 엔진.

사고·하자 발생 시 **"사고 당일, 이 현장이 인적·물적·행정 전 차원에서 법정 요건을 충족했나"** 를 계산으로 결정적 판정한다. 텍스트 검색(RAG)이 못 하는 **시점 기준 다차원 컴플라이언스 판정**이 목표.

## 5개 책임 차원

| 차원 | 질문 | 엔진 | rule |
|---|---|---|---|
| **인적 배치** | 법정 인원·자격이 사고 당일 유효 선임됐나 | `audit.py` | rules/ (9역할) |
| **의사결정 권한** | 검측·결정을 한 사람이 그 시점 유효 선임이었나 | `trail.py` | (시점 교차검증) |
| **작업 조건** | 온도·기상·재료·공법·근로가 그날 기준 충족했나 | `conditions.py` | condition_rules/ (14) |
| **선행요건** | 타설 전 정지점(검측)이 합격 선행됐나 | `prerequisites.py` | prerequisite_rules/ |
| **문서 제출** | 안전·품질 계획서가 제출 대상인데 이행됐나 | `documents.py` | document_rules/ (3) |

→ `report.py` 가 5차원을 **사고 1건 단일 보고서**로 통합 (책임 가중 지점 목록).

## 무엇이 다른가

| | 텍스트 검색(RAG) | 이 엔진 |
|---|---|---|
| "안전관리자 선임 기준?" | 법령 문장 반환 | 동일 |
| "사고 당일 적정했나?" | 불가 | 규모→요구 산출 + 사고시점 유효선임 대조 → 판정 |
| "그날 영하인데 한중조치 했나?" | 불가 | 작업조건 rule → violated |
| "타설 전 철근검측 했나?" | 불가 | 선행요건 → 정지점 미통과 포착 |
| "사고 현장 전체 책임 가중 지점은?" | 불가 | **5차원 일괄 → N건 단일 보고서** |

판정은 LLM 추론이 아니라 **계산**. 재현·추적 가능, 근거 법령·별표 인용.

> 검색·LLM 단독과 무엇이 다른지 8개 콘크리트·안전 질문으로 실측 비교 →
> [`docs/why_ontology.md`](docs/why_ontology.md) — 재현 스크립트를 문서 안에 포함한 단일 문서(키 불필요·결정적).

## 빠른 시작

```bash
python report.py examples/report_full.yaml      # 5차원 통합 (사고1건 → 10건 위반)
python audit.py  examples/audit_full_project.yaml   # 배치 9역할 일괄
python conditions.py examples/work_cold_pour.yaml   # 작업조건
python prerequisites.py examples/prereq_pour.yaml   # 선행요건
python documents.py examples/doc_project.yaml       # 문서제출
python test_rules.py && python test_conditions.py   # 회귀
```

## 커버하는 규제·규격 (검증 직렬화)

- **자격·배치**: 안전/보건관리자, 안전보건(총괄)관리책임자, 안전보건조정자, 현장대리인, 품질관리자, 책임CM, 공사감리자 — 산안법 별표2/3/5, 건산법 별표5, 건진법 시행규칙 별표5/§35, 건축법 §19
- **온도·기상**: 한중(4℃)·서중(25℃)·강우타설(3mm/h)·강풍(타워15·철골10 m/s)·폭염(체감33/35℃) — KCS 14 20 40/44, 산안규칙 §37/§383
- **재료**: 염화물(≤0.30)·AE공기량(3~6%) — KS F 4009
- **공법**: 거푸집존치강도(부재별)·굴착기울기(지반별)·비계기둥간격 — KCS 14 20 12, 산안규칙 별표11/§60
- **작업환경**: 밀폐공간 산소(18~23.5%) — 산안규칙 §619
- **근로시간**: 주52시간 — 근로기준법 §50/§53
- **선행요건**: 타설 전 철근·거푸집 검측 정지점(H) — KCS 14 20 11/12
- **문서**: 안전관리계획서(건진법 §62)·유해위험방지계획서(산안법 §42)·품질관리계획서(건진법 §55)

각 rule 은 `authority`(근거 법령·별표·개정일)를 갖고, 미검증·법령상 부재(인·월 공식 등)는 `pending` 정직 표기.

## 설계 원칙

1. **시간은 1급 축.** 모든 시점 노드 event_date / 유효구간(start·end). 사고 당일 기준 판정. 선임했으나 해임으로 인한 공백, 검측 후 타설 순서 위반 등을 포착.
2. **책임은 결정별 법정 주체에서 끊긴다.** 도급 무한트리 X. 위반→책임주체(시공사/도급인/발주자/발주청/건축주) 귀속.
3. **규칙이 심장.** raw 법령 텍스트가 아니라 `actual≥required`·`조건→의무/금지` 계산 구조. RAG 불가 영역.

## 구조

```
docs/                문서 — 아키텍처·설계·타입·규칙 카탈로그·비교 (docs/README.md 인덱스)
types/               타입 정의 (Project·Person·Organization·Appointment·Incident·Decision·WorkRecord·Location·BuildingComponent …)
engine/              판정 엔진 (evaluate·audit·trail·conditions·prerequisites·documents·report·maintenance·org_judgment·appropriateness·lifecycle)
placement_rules/     인적 배치 9역할 (requirement_shape)
condition_rules/     작업조건 (온도·기상·재료·공법·작업환경·근로) + material_specs/
prerequisite_rules/  선행요건 (Hold Point)
document_rules/      문서 제출 의무
maintenance_rules/ org_rules/ appropriateness_rules/   유지·조직·적정성 기준층
rag/                 검색·grounding·제약 envelope·슬롯필러·생성층 (rag/README.md)
opencrab_pack/       OpenCRAB Cloud Pack 산출물 (export_opencrab_pack.py)
tests/               회귀 (python -m tests.X)
examples/            합성 시나리오
```

## 설치·실행

```bash
python -m tests.test_conditions          # 회귀(키 불필요)
python -m engine.conditions examples/work_cold_pour.yaml      # 단일 차원
python report.py examples/scenario_understaffed.yaml          # 5차원 통합 보고서
python -m rag.retrieve "습식 숏크리트 리바운드율 25%"          # 검색+판정
python -m rag.envelope exposure_class=EC4 design_fck_mpa=30   # 제약 envelope
```

의존성: `pyyaml` (코어). RAG 자연어 레이어(선택)는 `anthropic`.

## RAG / LLM 레이어 (선택)

`rag/`는 온톨로지 위 검색·결정적 grounding·제약 envelope를 제공한다. 자연어 슬롯추출·서술에
LLM을 붙일 수 있으나 **판정은 항상 결정적 엔진**이 한다(LLM은 슬롯 채우기·결과 서술만). 활성화:

```bash
pip install anthropic
cp .env.example .env        # .env 는 .gitignore — 추적 안 됨. 본인 ANTHROPIC_API_KEY 입력
python -c "from rag import llm; print(llm.selfcheck())"
```

키는 환경변수 또는 `.env`에서만 읽으며 **코드·커밋에 하드코딩하지 않는다.** 자세한 내용은 `rag/README.md`.

## 도메인 근거

규칙의 `audit_significance`/`source`는 공개 법령(KCS·KS·산안법·시특법·중대재해처벌법 등)과 공개
사고조사 결론을 규제 유래(provenance)로 인용한다 — 공개 사실이며, 현장 데이터가 아니다.

## 라이선스

Apache-2.0. 규칙이 인용하는 법령·표준 원문의 저작권은 각 발행기관에 있으며, 본 저장소는
그 사실을 구조화한 모델·코드를 라이선스한다.
