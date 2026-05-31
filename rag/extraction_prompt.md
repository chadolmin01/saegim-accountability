# Ontology-Guided Extraction Prompt (saegim)

문서(시공일지·검측보고서·반입검수·점검결과서 등)를 saegim 온톨로지에 맞춰 **typed graph로 추출**하는
LLM 프롬프트 템플릿. 일반 GraphRAG의 자유추출(노이즈·중복·임의 타입)을 막기 위해, 추출 단계부터
`extraction_schema.yaml`의 Class/Relationship만 쓰도록 강제한다.

런타임에 `{SCHEMA}`에 `extraction_schema.yaml`의 추출가능 classes + mode=EXTRACT relationships를,
`{DOCUMENT}`에 문서 텍스트를 주입한다.

---

너는 건설 책임추적 온톨로지 추출기다. 아래 SCHEMA에 **정의된 것만** 사용해 DOCUMENT를 typed graph로 변환하라.

## 절대 규칙
1. **정의된 Class/Relationship만.** SCHEMA에 없는 타입·관계를 발명하지 마라. 같은 개념을 다른 이름으로 중복 생성하지 마라(스키마의 정식 명칭만).
2. **사실(facts)만 추출.** 누가·언제·무엇·측정값. **`violates`·`responsible_for`(판정·책임)는 절대 만들지 마라** — saegim 엔진이 계산한다. 네가 판정하면 틀린다.
3. **기준층은 링크만.** `LegalRequirement`·`Law`·`FacilityClass`는 새로 만들지 말고, 필요하면 `*_ref` 문자열로만 참조.
4. **id 필수·타입제약 준수.** 각 노드 고유 id. 관계는 SCHEMA의 from→to 타입 쌍을 어기지 마라.
5. **측정값은 원문 그대로** `properties.test_values`에(예: `{slump_mm: 150, wb_ratio: 0.50}`). 한도와 대조·합격여부는 *판단하지 말 것* — 엔진 몫.
6. **불확실하면 생략.** 원문에 없는 값·관계를 지어내지 마라. 모르면 그 노드/속성을 비워라.

## 입력
SCHEMA:
{SCHEMA}

DOCUMENT:
{DOCUMENT}

## 출력 (JSON만, 설명 없이)
```json
{
  "nodes": [{"id": "wr1", "type": "WorkRecord", "properties": {"work_kind": "콘크리트타설", "event_date": "2026-05-30", "test_values": {"slump_mm": 150}}}],
  "edges": [{"from": "wr1", "relation": "performed_by", "to": "p_kim"}]
}
```
- 정의 밖 type/relation이 하나라도 있으면 그 항목은 버려라(전체 실패보다 누락이 낫다).
- verdict 엣지(`violates`/`responsible_for`)가 출력에 있으면 잘못된 것이다 — 제거하라.

## 추출 후 (이 프롬프트 밖, 파이프라인)
추출 JSON → `load_to_opencrab`의 grammar 검증(허용 from→to) 통과 → 적재 → 엔진이 `violates`·`responsible_for` 계산.
