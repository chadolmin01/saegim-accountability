# 문서 (Documentation)

saegim-accountability 의 설계·타입·규칙·비교 문서 모음. 저장소 개요는 [`../README.md`](../README.md).

## 목차

| 문서 | 내용 |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | 시스템 구조 — 기준층/사건층, 5 책임 차원, 판정 흐름 |
| [DESIGN.md](DESIGN.md) | 설계 원칙 — 시간 1급 축 · 결정별 법정 책임 · 규칙이 심장 |
| [TYPES.md](TYPES.md) | 타입 카탈로그 — 책임추적에 필요한 노드·관계만 정의 |
| [RULES.md](RULES.md) | 규칙 카탈로그 (154개, 자동생성) — 배치·작업조건·선행요건·문서 |
| [INGESTION_MAPPING.md](INGESTION_MAPPING.md) | 현장 문서 → 입력 스키마 매핑 |
| [why_ontology.md](why_ontology.md) | 검색·LLM 단독과의 실측 비교 — 왜 결정적 엔진인가 |

## 처음 본다면

1. [ARCHITECTURE.md](ARCHITECTURE.md) 로 전체 그림을 잡고,
2. [why_ontology.md](why_ontology.md) 로 "검색·LLM과 무엇이 다른가"를 실측으로 확인한 뒤,
3. [DESIGN.md](DESIGN.md) · [TYPES.md](TYPES.md) · [RULES.md](RULES.md) 로 내부를 본다.

---

`RULES.md` 는 [`../generate_rules_index.py`](../generate_rules_index.py) 가 규칙 디렉토리를 스캔해
자동생성한다 — 저장소 루트에서 `python generate_rules_index.py`. 직접 편집하지 말 것.
