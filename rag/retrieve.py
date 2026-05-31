"""saegim RAG 검색+grounding 코어 — 벡터 임베딩 없이 typed 온톨로지 위에서 정확 검색.

OpenCRAB 벡터 Q&A가 한글 기술용어에 부정확한 문제를, 룰 메타(title·dimension·regime·authority)에
대한 키워드 스코어링으로 우회한다(임베딩 약점 회피). 매칭 룰의 한도·§를 회수하고, 질문에 측정값이
있으면 엔진(conditions)으로 결정적 합부판정까지 — 즉 RAG의 'retrieval'은 온톨로지가, 'grounding'은
결정적 엔진이 한다(LLM 추측 없음). 생성(자연어 답)은 선택적으로 뒤에 붙인다.

  python -m rag.retrieve "숏크리트 리바운드율 한도"
  python -m rag.retrieve "습식 숏크리트 리바운드율 25%"     # 측정값 → 엔진 판정
"""
from __future__ import annotations
import re
import sys
import yaml
import paths
from engine import conditions as C

RULE_DIRS = ["condition_rules", "document_rules", "prerequisite_rules", "placement_rules",
             "appropriateness_rules", "org_rules", "maintenance_rules", "material_specs"]
# 흔한 조사·질문어 — 토큰 끝에서 떼어 핵심어만 매칭
PARTICLES = ("인데", "으로", "에서", "은", "는", "이", "가", "을", "를", "의", "도", "만", "와", "과", "에", "로")


def load_rules():
    rules = []
    for d in RULE_DIRS:
        for f in paths.rule_glob(d):
            r = yaml.safe_load(open(f, encoding="utf-8"))
            r["_dir"] = d
            rules.append(r)
    return rules


def _strip(tok):
    for p in sorted(PARTICLES, key=len, reverse=True):
        if tok.endswith(p) and len(tok) > len(p) + 1:
            return tok[:-len(p)]
    return tok


def tokens(q):
    return [_strip(t) for t in re.findall(r"[가-힣A-Za-z0-9]+", q) if len(t) >= 2]


def _blob(r):
    a = r.get("authority") or {}
    ev = r.get("evaluation") or {}
    return " ".join(str(x) for x in [
        r.get("title"), r.get("dimension"), r.get("topic"), r.get("regime"),
        r.get("legal_basis"), r.get("document"), a.get("standard"), a.get("rule"),
        a.get("table"), ev.get("audit_significance")] if x)


def _norm(s):
    return re.sub(r"[-\s()·/]", "", s or "")   # 하이픈·공백·괄호 무시 (물결합재비 ↔ 물-결합재비)


def search(query, rules, k=5):
    toks = {_norm(t) for t in tokens(query)}
    scored = []
    for r in rules:
        title = _norm(r.get("title", ""))
        blob = _norm(_blob(r))
        matched = [t for t in toks if t and t in blob]
        if not matched:
            continue
        s = sum(3 if t in title else 1 for t in matched)
        scored.append((s, len(matched), r))   # (score, 매칭토큰수, rule)
    scored.sort(key=lambda x: (-x[0], -x[1]))
    return scored[:k]


def threshold_field(r):
    for v in (r.get("requires") or {}).values():
        if isinstance(v, dict):
            return v.get("key") or v.get("measured")
        if isinstance(v, list) and v and isinstance(v[0], dict):
            return v[0].get("key")
    return None


# 측정값 타당 범위 — naive 추출이 노출코드(EC4의 4)·재령(28일)·표준번호를 측정값으로 오인하던 걸
# '룰이 요구하는 필드의 값 범위'로 검증해 차단. = ontology-guided extraction을 측정값에 적용.
RANGE = {"wb_ratio": (0.2, 0.85), "rebound_rate_pct": (0, 100), "strength_mpa": (3, 150),
         "slump_mm": (0, 300), "spec_slump_mm": (0, 300), "air_content_pct": (0.5, 15),
         "gmax_mm": (5, 80), "design_fck_mpa": (8, 120), "chloride_kg": (0, 1.5)}


def _pick(text, key, near=None):
    """RANGE[key] 범위 내 숫자만 후보. near 키워드 있으면 그 뒤 가장 가까운 것(지정/측정/설계 구분)."""
    lo, hi = RANGE.get(key, (float("-inf"), float("inf")))
    cands = [(m.start(), float(m.group())) for m in re.finditer(r"\d+\.?\d*", text) if lo <= float(m.group()) <= hi]
    if not cands:
        return None
    if near and (idx := text.find(near)) >= 0:
        after = [(p, v) for p, v in cands if p >= idx]
        if after:
            return min(after, key=lambda x: x[0])[1]
    return cands[-1][1]


def extract_slots(query, rule):
    """매칭 룰의 슬롯 스키마에 맞춰 NL에서 값 추출 — 룰이 '무엇을 뽑을지' 지정 + 범위 검증(robust)."""
    qx = re.sub(r"\d+\s*일", " ", query)          # 재령(28일) 제거
    rec = {"work_kind": rule.get("applies_to_work_kind"), "test_values": {}}
    if "건식" in query: rec["shotcrete_method"] = "건식"
    if "습식" in query: rec["shotcrete_method"] = "습식"
    if "고강도" in query: rec["shotcrete_grade"] = "고강도"
    elif "일반" in query: rec["shotcrete_grade"] = "일반"
    if m := re.search(r"E[CSAF]\d", query): rec["exposure_class"] = m.group()
    tf = threshold_field(rule)
    key = tf.split(".", 1)[1] if (tf and tf.startswith("test_values.")) else None
    req = rule.get("requires") or {}
    if "deviation_bound" in req:                  # 슬럼프류: 지정/측정 쌍
        tgt = req["deviation_bound"].get("target")
        if (sv := _pick(qx, tgt, near="지정")) is not None: rec[tgt] = sv
        if key and (mv := _pick(qx, key, near="측정")) is not None: rec["test_values"][key] = mv
    elif key:                                     # 단일 측정값
        if (v := _pick(qx, key)) is not None: rec["test_values"][key] = v
    if "설계" in query and (fv := _pick(qx, "design_fck_mpa", near="설계")) is not None:
        rec["design_fck_mpa"] = fv
    return rec


def _slots(query, rule):
    """슬롯 추출 — LLM 슬롯필러(있으면, 동일범위 2숫자 분리) → 없으면 정규식. 둘 다 RANGE 검증.
    lazy import 로 slots_llm↔retrieve 순환 회피. 키 없으면 llm_slots 가 곧장 extract_slots 로 폴백."""
    try:
        from rag.slots_llm import llm_slots
        return llm_slots(query, rule)
    except Exception:
        return extract_slots(query, rule)


def ground(query, rule):
    """NL → 스키마-가이드 슬롯 추출(robust) → 엔진 결정적 판정. 판정은 엔진만(추측 0)."""
    rec = _slots(query, rule)
    if not rec.get("test_values"):
        return None
    for r in C.check_all(rec):
        if r["rule_id"] == rule["rule_id"] and r["verdict"] != "not_applicable":
            return r
    return None


def judge(query, hits, k=3):
    """검색 상위 후보가 형제 룰로 흔들릴 수 있어 top-k에 grounding 시도 — 슬롯 채워지고
    판정 나는 첫 룰을 채택(엉뚱한 룰은 슬롯 미충족→NA로 자연 탈락)."""
    for s, m, r in hits[:k]:
        if m < 2:
            continue
        g = ground(query, r)
        if g:
            return r, g
    return None, None


def main():
    q = " ".join(sys.argv[1:]).strip() or "숏크리트 리바운드율 한도"
    rules = load_rules()
    hits = search(q, rules)
    print(f"질문: {q}\n")
    if not hits or hits[0][1] < 2:   # 매칭 토큰 2개 미만 = 우연한 단어겹침 → 범위 밖
        print("확신 매칭 없음 — 온톨로지 범위 밖(pending/RAG 롱테일). 단어 1개만 우연히 겹침.")
        return 0
    for i, (s, m, r) in enumerate(hits, 1):
        if m < 2:
            continue
        a = r.get("authority") or {}
        print(f"[{i}] {r['title']}  (score {s}, 매칭 {m})")
        print(f"    한도: {a.get('rule') or '(requires 참조)'}")
        print(f"    근거: {r.get('regime')} / {a.get('standard') or r.get('legal_basis') or ''}  [{r.get('source_type','')}]")
    jr, g = judge(q, hits)
    if g:
        mark = {"violated": "✗ 부적합", "compliant": "✓ 합격"}.get(g["verdict"], g["verdict"])
        print(f"\n★ 측정값 판정 (엔진, 추측 아닌 계산): {mark} — {g.get('reason', '')}")
    else:
        print("\n(측정값 주면 엔진이 합부 판정 — 예: \"습식 숏크리트 리바운드율 25%\")")
    from rag import narrate                       # (b) 생성층 — 엔진 결과만 서술(키 없으면 템플릿)
    print(f"\n■ 답변: {narrate.answer(q, hits, jr, g)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
