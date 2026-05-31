"""rag LLM 레이어 결정적 검증 — API 키 없이 백엔드를 모킹해 (a)슬롯필러 (b)생성층의 *새 로직*을 증명.

핵심으로 검증하는 것:
  1. (a) 동일범위 2숫자 분리: '강도 19 / 설계 30' → 측정=19·설계=30 → 엔진 부적합 (정규식만으론 못 가르던 갭)
  2. (a) 범위검증: LLM 이 범위 밖(999) 주면 폐기 (환각 차단)
  3. (a) 폴백 동일성: 키 없으면 llm_slots == extract_slots (검증된 정규식 무변경)
  4. (b) 생성층: 엔진 verdict·근거만 서술, 판정 안 만듦. 키 없으면 결정적 템플릿
실행: python -m tests.test_rag_llm
"""
import paths
import yaml
from rag import llm, narrate
from rag.slots_llm import llm_slots
from rag.retrieve import extract_slots, search, load_rules, judge

STRENGTH = "concrete_strength_acceptance__ksf4009"


def _rule(rid):
    for f in paths.rule_glob("condition_rules"):
        r = yaml.safe_load(open(f, encoding="utf-8"))
        if r.get("rule_id") == rid:
            return r
    raise AssertionError(f"rule {rid} 없음")


def _patch(monkey_available, monkey_json=None, monkey_complete=None):
    """llm 백엔드 모킹 헬퍼 — 원복 함수 반환."""
    orig = (llm.available, llm.complete_json, llm.complete)
    llm.available = lambda: monkey_available
    if monkey_json is not None:
        llm.complete_json = lambda s, u, max_tokens=600, task=None: monkey_json
    if monkey_complete is not None:
        llm.complete = lambda s, u, max_tokens=600, task=None: monkey_complete
    def restore():
        llm.available, llm.complete_json, llm.complete = orig
    return restore


def test_a_disambiguation():
    """측정강도 vs 설계강도 — LLM 이 의미로 분리, rec 에 정확히 들어가고 엔진이 부적합 판정."""
    r = _rule(STRENGTH)
    q = "압축강도 19MPa, 설계기준강도 30MPa"
    restore = _patch(True, monkey_json={"strength_mpa": 19, "design_fck_mpa": 30})
    try:
        rec = llm_slots(q, r)
        assert rec["test_values"].get("strength_mpa") == 19.0, rec
        assert rec.get("design_fck_mpa") == 30.0, rec
        from engine import conditions as C
        hit = [x for x in C.check_all(rec) if x["rule_id"] == STRENGTH]
        assert hit and hit[0]["verdict"] == "violated", hit   # 19 < 0.85*30=25.5
    finally:
        restore()
    print("  [1] (a) 동일범위 2숫자 분리 + 엔진 부적합 OK")


def test_a_range_rejection():
    """LLM 이 범위 밖 숫자(999)를 주면 폐기 — 환각/오인 주입 차단."""
    r = _rule(STRENGTH)
    restore = _patch(True, monkey_json={"strength_mpa": 999, "design_fck_mpa": 30})
    try:
        rec = llm_slots("강도 측정", r)
        assert rec["test_values"].get("strength_mpa") != 999, rec   # 999는 RANGE(3~150) 밖 → 폐기
        assert rec.get("design_fck_mpa") == 30.0, rec               # 30은 범위 내 → 채택
    finally:
        restore()
    print("  [2] (a) 범위검증으로 환각값 폐기 OK")


def test_a_fallback_identity():
    """키 없으면 llm_slots 는 검증된 정규식과 완전히 동일(무회귀)."""
    r = _rule(STRENGTH)
    assert llm.available() is False, "테스트 환경에 키가 설정됨 — 폴백 동일성 검증 불가"
    for q in ["습식 숏크리트 리바운드율 25%", "압축강도 19MPa 설계기준강도 30MPa", "슬럼프 지정 120 측정 150"]:
        assert llm_slots(q, r) == extract_slots(q, r), q
    print("  [3] (a) 키 없을 때 정규식과 동일(무회귀) OK")


def test_b_template_grounded():
    """생성층 템플릿 — 엔진 facts 만으로 문장 조립, 판정·근거 포함, 없는 결론 안 만듦."""
    rules = load_rules()
    q = "습식 숏크리트 리바운드율 25%"
    hits = search(q, rules)
    jr, g = judge(q, hits)
    ans = narrate.answer(q, hits, jr, g)            # 키 없음 → template 경로
    if g:
        assert ("부적합" in ans or "합격" in ans), ans
        assert g.get("reason", "")[:10] in ans or "근거" in ans, ans
    # 매칭 없는 질문 → 범위 밖 문구(결론 날조 금지)
    none_q = "오늘 점심 메뉴 추천"
    assert "범위 밖" in narrate.answer(none_q, search(none_q, rules), None, None)
    print("  [4] (b) 템플릿 생성: verdict·근거 서술 + 무매칭시 범위밖 OK")


def test_b_llm_path():
    """LLM 생성 경로 — 모킹된 문장을 그대로 반환(생성은 표현일 뿐, 판정 무변경)."""
    rules = load_rules()
    q = "습식 숏크리트 리바운드율 25%"
    hits = search(q, rules)
    jr, g = judge(q, hits)
    restore = _patch(True, monkey_complete="리바운드율 25%는 습식 기준 한도를 초과해 부적합입니다 (KS 기준).")
    try:
        ans = narrate.answer(q, hits, jr, g)
        assert "부적합" in ans
    finally:
        restore()
    print("  [5] (b) LLM 생성 경로(모킹) OK")


if __name__ == "__main__":
    test_a_disambiguation()
    test_a_range_rejection()
    test_a_fallback_identity()
    test_b_template_grounded()
    test_b_llm_path()
    print("\n[OK] rag LLM 레이어 5/5 통과")
