# RAG (Ontology-Guided Extraction) — saegim

문서 → typed graph 추출 단계를 saegim 온톨로지로 **제약**하는 레이어. 일반 GraphRAG가 LLM에게
"엔티티·관계 자유 추출"을 시켜 노이즈·중복·임의 타입이 생기는 문제를, *추출 단계부터 스키마를 강제*해 막는다.

## saegim은 이미 그 "Ontology"다
ontology-driven GraphRAG의 전제(미리 정의된 Class/Relationship/Constraint로 추출을 가이드)를
saegim은 이미 갖고 있다 — 단 **자동추출한 온톨로지가 아니라 §-검증된 결정적 온톨로지**라는 게 차이.

| GraphRAG 온톨로지 구성요소 | saegim 자산 |
|---|---|
| **Class** (노드 타입) | `types/` + `opencrab_pack/types/` — 추출가능 17 + 기준층 3 |
| **Relationship** (엣지 타입) | `opencrab_pack/edges.yaml` — 22 (EXTRACT 18 · COMPUTED 2 · PACK 2) |
| **Property** | 각 type yaml의 `properties` |
| **Constraint** | grammar(`manifest.py` META_EDGES 허용 from→to) + `load_to_opencrab` 검증 = **SHACL 대응** |

## 결정적 차이 — 추출 vs 판정
일반 ontology-GraphRAG는 추출+검색에서 멈춘다. saegim은 **추출(facts)과 판정(verdict)을 분리**한다:

- **추출 대상 = factual만** (관측: 누가·언제·무엇·측정값). 18개 EXTRACT 관계.
- **`violates`·`responsible_for`는 추출 금지 = 엔진이 *계산*.** 측정값↔법정한도 대조, 시점유효성, 책임귀속은
  LLM 추출이 아니라 결정적 평가기 몫. → 추출 LLM이 판정을 지어낼 여지 자체가 없다(hallucination 차단).
- 기준층(LegalRequirement·Law·FacilityClass)은 추출 대상이 아니라 *링크/판정 대상*(고정 온톨로지).

## 파이프라인
```
문서(시공일지·검측·점검결과서)
  ↓ chunking
Ontology-Guided Extraction   ← extraction_prompt.md + extraction_schema.yaml (정의된 Class/Relation만)
  ↓ Validation                ← load_to_opencrab grammar 검증(허용 from→to) = SHACL 대응
typed graph (factual)
  ↓ saegim 엔진 ★일반 GraphRAG엔 없는 단계
violates·responsible_for 계산 (②판정 ③책임추적)
  ↓ 적재
OpenCRAB (Cloud Pack) → Hybrid Retrieval(Vector + Graph + Ontology)
```

## 파일
- `extraction_schema.yaml` — **자동생성** SchemaConfig(`python build_extraction_schema.py`). 추출 허용 Class/Relation + 제약. types/·edges.yaml에서 파생(드리프트 없음).
- `extraction_prompt.md` — LLM 추출 프롬프트 템플릿(스키마 주입, factual-only, verdict 금지).
- `envelope.py` — **제약 envelope.** `python -m rag.envelope exposure_class=EC4 design_fck_mpa=30 ...`. 현장조건 → 콘크리트 배합이 *지켜야 할 모든 법정 한도*(노출등급별 W/B·fck resolve, Gmax·염화물·단위수량·슬럼프·강도·혼화제품질·양생) + *적용 의무 종류*(한중/서중/해양/매스/고강도…). **추천(설계) 아님 — 결정적 제약 집계.** "이 배합 써라"가 아니라 "이 한도 다 지켜라". 시험배합은 이 안에서, 결과는 conditions.check_all로 판정.
- `retrieve.py` — **검색+grounding 코어.** `python -m rag.retrieve "<질문>"`. 벡터 임베딩 없이 룰 메타(title·regime·authority)에 키워드 스코어링으로 정확 검색(OpenCRAB 벡터의 한글 부정확 회피) + 질문에 측정값 있으면 엔진(conditions)으로 결정적 합부판정 + 끝에 자연어 답(narrate). retrieval=온톨로지 / grounding=엔진 / generation=선택적 LLM(후행).
- `llm.py` — **LLM 백엔드 추상화.** 슬롯필러·생성층이 LLM에 닿는 유일한 통로. `ANTHROPIC_API_KEY`+anthropic SDK 있으면 `available()=True`, 없으면 False(→ 각 레이어 결정적 폴백). 모델 기본 haiku(`SAEGIM_LLM_MODEL`로 오버라이드). **LLM은 슬롯 채우기·결과 서술만 — 판정은 절대 안 함.**
- `slots_llm.py` — **(a) LLM 슬롯필러.** 룰이 정의한 슬롯만 NL에서 추출하고 **RANGE로 재검증**(범위 밖=폐기). 정규식이 못 가르는 *동일범위 2숫자*("강도 19 / 설계 30")를 의미로 분리. 판정 안 함(엔진 몫). 키 없으면 `retrieve.extract_slots`(정규식)로 폴백 — '있으면 더 정확, 없어도 동작'.
- `narrate.py` — **(b) 자연어 생성층.** 엔진이 *이미 계산한* 결과(verdict·근거·§·한도)만 한국어 문장으로 서술. LLM은 입력 facts만 다시 말함(새 숫자·결론 금지, verdict 그대로). 키 없으면 결정적 템플릿(추측 0). **판정은 항상 엔진, 생성은 표현일 뿐.**

### LLM 레이어 활성화 (선택 — 없어도 전부 동작)
```
pip install anthropic
copy .env.example .env            # .env 는 .gitignore — 추적 안 됨
#  .env 에 ANTHROPIC_API_KEY=sk-ant-... 채우기 (또는 환경변수로)
python -c "from rag import llm; print(llm.selfcheck())"   # 라이브 1콜 점검
```
키는 `ANTHROPIC_API_KEY` 환경변수 또는 `ROOT/.env`(gitignore)에서만 읽음 — **코드·커밋에 절대 하드코딩 안 함.** 모델 기본 haiku(`SAEGIM_LLM_MODEL`/`_SLOTS`/`_NARRATE`로 작업별 오버라이드), `SAEGIM_LLM_TIMEOUT`/`_RETRIES`로 호출 안정성.

키 없이도 검증됨: `python -m tests.test_rag_llm` (5/5 — 백엔드 모킹으로 새 로직 결정적 검증: 2숫자 분리·범위검증 폐기·폴백 동일성·서술 grounding).

라이브에서 잡은 결함(수정 완료):
- **슬롯필러 보수화** — LLM 이 룰의 특수필드(긴장 시 강도 fci 등)에 일반 숫자를 날조 → 엉뚱한 룰 grounding → judge 오답. 룰 제목을 맥락으로 주고 '맥락 안 맞으면 비워라' 강제 + 정규식 merge 제거(LLM 결정 신뢰, 환각은 RANGE 차단).
- **생성층 override-proof** — verdict 있으면 LLM 에 판정+근거(reason)+§ 만 줌(한도·질문숫자 제외). LLM 이 재계산해 판정을 뒤집을 수단 제거. reason 비면 결정적 템플릿.

## 스택 메모 (일반 추천과의 차이)
- Graph DB: 일반은 Neo4j. saegim은 **OpenCRAB + local typed graph**(이미 grammar 검증 내장).
- 검증: 일반은 SHACL. saegim은 **grammar(manifest.py) + load 검증** — 역할 동일(허용 구조 강제).
- LLM: 추출기는 LLM-agnostic(프롬프트 템플릿). 판정은 LLM이 아니라 결정적 엔진.

## 제약 그물 (이게 RAG를 제자리에 가둔다)
추출은 **④ RAG/접지 레이어** — ① 결정적 온톨로지가 *허용범위를 정의*하고, 추출된 facts를 ② 엔진이 *판정*한다.
demand-pull 유지: 다 추출하지 말고, 사고·질문이 끄는 문서·범위만. 검증 안 된 수치는 pending(추측금지).
