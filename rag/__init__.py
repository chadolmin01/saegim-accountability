"""rag — Ontology-Guided Extraction + 검색·grounding·서술 코어. 실행: python -m rag.retrieve "<질문>".

레이어: retrieve(검색·grounding) · envelope(제약 집계) · slots_llm(a:슬롯필러) · narrate(b:생성) · llm(백엔드).
LLM은 슬롯 채우기·결과 서술만 — 판정은 항상 결정적 엔진(추측 0). 키 없으면 정규식·템플릿 폴백."""
