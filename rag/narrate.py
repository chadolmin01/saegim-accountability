"""(b) 자연어 생성층 — 엔진이 *이미 계산한* 결과만 한국어 문장으로 전달.

override-proof 설계(라이브에서 LLM 이 한도+질문 숫자로 verdict 를 재계산해 뒤집은 결함 대응):
  · 판정(verdict)이 있으면 LLM 에는 **판정 + 판정근거(reason) + 근거조항(§)만** 준다.
    한도·질문 원문 숫자를 주지 않으므로 LLM 이 스스로 계산해 결론을 뒤집을 수단 자체가 없다.
  · reason 이 비어 있으면 LLM 을 부르지 않고 결정적 템플릿(LLM 이 빈칸을 추론으로 메우는 것 차단).
  · 한도 조회(판정 없음)일 때만 기준·한도·근거를 서술.
  · 키 없거나 API 오류면 항상 결정적 템플릿. **판정은 항상 엔진, 생성은 표현일 뿐.**
"""
from __future__ import annotations
import json
from rag import llm

SYS = (
    "너는 결정적 엔진이 이미 내린 결과를 한국어 한두 문장으로 전달하는 서술기다. "
    "절대 규칙: 입력 JSON 의 사실만 말한다. 판정(합격/부적합)은 입력값을 그대로 옮긴다 — "
    "직접 계산하거나 결론을 바꾸지 마라. 새 숫자·새 한도를 만들지 마라. "
    "근거조항(§)을 반드시 포함하고, 군더더기·면책문구 없이 결론부터 말하라."
)

_MARK = {"violated": "부적합", "compliant": "합격"}


def _verdict_facts(jr, g):
    ga = g.get("authority") or {}
    return {
        "판정": _MARK.get(g["verdict"], g["verdict"]),
        "판정근거": g.get("reason"),
        "근거조항": " / ".join(x for x in [(jr or {}).get("regime"), ga.get("standard")] if x),
    }


def _lookup_facts(hits):
    top = hits[0][2] if hits else None
    if not top:
        return {}
    a = top.get("authority") or {}
    return {
        "기준": top.get("title"),
        "한도": a.get("rule"),
        "근거": " / ".join(x for x in [top.get("regime"), a.get("standard") or top.get("legal_basis")] if x),
    }


def template(facts):
    """결정적 폴백 — facts 만으로 문장 조립(추측 0)."""
    if "판정" in facts:
        mark = {"부적합": "✗ 부적합", "합격": "✓ 합격"}.get(facts["판정"], facts["판정"])
        src = facts.get("근거조항") or ""
        body = (facts.get("판정근거") or "").strip()
        return f"{mark}." + (f" {body}" if body else "") + (f" (근거: {src})" if src else "")
    if "기준" in facts:
        src = facts.get("근거") or ""
        return f"{facts['기준']}: {facts.get('한도') or '(requires 참조)'}" + (f" (근거: {src})" if src else "")
    return "온톨로지 범위 밖 — 확신 매칭 없음."


def answer(query, hits, jr, g):
    """검색·판정 결과 → 한국어 답. 판정 있으면 verdict 만 서술(override 불가), 없으면 한도 서술."""
    if g:
        facts = _verdict_facts(jr, g)
        if not (g.get("reason") or "").strip():     # reason 비면 LLM 안 부름(추론으로 메우기 차단)
            return template(facts)
    else:
        facts = _lookup_facts(hits)
    if not llm.available():
        return template(facts)
    user = "결과 JSON:\n" + json.dumps(facts, ensure_ascii=False, indent=2) + "\n\n위 사실만으로 한두 문장 서술."
    try:
        return llm.complete(SYS, user, task="narrate") or template(facts)
    except Exception:
        return template(facts)                       # 라이브 API 오류여도 결정적 답 보장
