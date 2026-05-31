"""(a) LLM 슬롯필러 — 룰이 정의한 슬롯만 자연어에서 추출하고, RANGE 로 검증해 채택.

**판정은 절대 안 한다(엔진 몫).** 역할은 정규식이 못 가르는 *동일 범위 2숫자*의 의미 분리다:
  "압축강도 19MPa, 설계기준강도 30MPa"  →  측정 strength=19 / 설계 fck=30
정규식 _pick 은 둘 다 같은 범위(3~150)라 마지막 숫자(30)를 측정값으로 오인 → 합부 뒤집힘.

보수 원칙(중요) — 라이브에서 드러난 결함 대응:
  · 룰 제목을 맥락으로 주고 "이 기준이 요구하는 그 측정을 텍스트가 명시할 때만 채워라"를 강제.
    일반어('압축강도')를 특수측정(긴장 시 강도 fci 등)으로 넘겨짚으면 엉뚱한 룰이 grounding 되어
    judge 가 오답을 채택한다 → 맥락 없으면 비운다.
  · LLM 반환 숫자는 전부 RANGE 재검증(범위 밖=폐기), 카테고리는 원문 표기만. → 환각/오인 주입 차단.
  · LLM 출력을 신뢰하고 정규식과 merge 하지 않는다(merge 하면 LLM 이 일부러 비운 특수필드에
    정규식이 숫자를 도로 채워 넣어 결함 재발). 파싱 실패(out={}) 시에만 정규식 전체 폴백.

키 없으면(llm.available()=False) retrieve.extract_slots(정규식)로 폴백 — '있으면 더 정확, 없어도 동작'.
"""
from __future__ import annotations
from rag import llm
from rag.retrieve import RANGE, threshold_field, extract_slots

SYS = (
    "너는 한국 토목/콘크리트 시험기록에서 '측정·지정값 슬롯만' 뽑는 추출기다. "
    "합격/부적합 같은 판정은 절대 하지 마라(판정은 별도 결정적 엔진이 한다). "
    "주어진 기준이 요구하는 필드만, 텍스트가 그 측정을 명시적으로 말할 때만 JSON 으로 반환하라. "
    "일반 용어(예: '압축강도')를 특수 측정(예: 긴장 시 강도·코어 강도비)으로 넘겨짚지 마라 — "
    "기준 맥락과 안 맞으면 그 필드는 생략하라. 없는 값·애매한 값은 키를 생략. "
    "추론·창작 금지. 숫자는 단위를 떼고 숫자만 적어라."
)


def _menu(rule):
    """룰이 요구하는 슬롯 메뉴 — 숫자 필드(필드명·의미·허용범위) + 카테고리 필드(택1)."""
    req = rule.get("requires") or {}
    title = rule.get("title") or ""
    rid = rule.get("rule_id") or ""
    nums, cats = {}, {}
    tf = threshold_field(rule)
    mkey = tf.split(".", 1)[1] if (tf and tf.startswith("test_values.")) else None
    if mkey and mkey in RANGE:
        lo, hi = RANGE[mkey]
        nums[mkey] = f"이 기준의 측정값 {mkey} (허용범위 {lo}~{hi})"
    if "deviation_bound" in req:
        tgt = req["deviation_bound"].get("target")        # 예: spec_slump_mm (지정/배합 목표)
        if tgt in RANGE:
            lo, hi = RANGE[tgt]
            nums[tgt] = f"지정/배합 목표값 {tgt} (허용범위 {lo}~{hi})"
    if mkey == "strength_mpa" or "fck" in title or "강도" in title:
        lo, hi = RANGE["design_fck_mpa"]
        nums["design_fck_mpa"] = f"설계기준강도 fck (허용범위 {lo}~{hi}; 측정강도와 반드시 구분)"
    if "shotcrete" in rid or "숏크리트" in title:
        cats["shotcrete_method"] = "건식|습식"
        cats["shotcrete_grade"] = "일반|고강도"
    if "exposure" in rid or "노출" in title or "lookup_max" in req:
        cats["exposure_class"] = "EC1~EC4 / ES1~ES4 / EA1~EA3 / EF1~EF4 중 하나(원문)"
    if "admixture_type" in str(req):
        cats["admixture_type"] = "혼화제 종류(원문 그대로)"
    return mkey, nums, cats


def llm_slots(query, rule):
    """LLM 슬롯필러 → extract_slots 와 동일 shape 의 rec. 범위 밖 숫자 폐기. 파싱 실패 시에만 정규식 폴백."""
    if not llm.available():
        return extract_slots(query, rule)
    mkey, nums, cats = _menu(rule)
    lines = [f"- {k}: {v} (숫자)" for k, v in nums.items()]
    lines += [f"- {k}: {v} (택1)" for k, v in cats.items()]
    user = (f"기준(맥락): {rule.get('title')}\n"
            f"이 기준이 요구하는 필드(텍스트가 그 측정을 명시할 때만 채움; 맥락 안 맞으면 생략):\n"
            + "\n".join(lines) + f"\n\n텍스트:\n{query}\n\nJSON만 출력.")
    out = llm.complete_json(SYS, user, task="slots")
    if not out:
        return extract_slots(query, rule)                 # 파싱 실패 → 정규식 전체 폴백

    rec = {"work_kind": rule.get("applies_to_work_kind"), "test_values": {}}
    for k, v in out.items():
        if k in RANGE:                                     # 숫자 슬롯 → 범위 재검증
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            lo, hi = RANGE[k]
            if not (lo <= fv <= hi):
                continue                                   # 범위 밖 = LLM 환각/오인 → 폐기
            (rec["test_values"].__setitem__ if k == mkey else rec.__setitem__)(k, fv)
        elif k in cats and isinstance(v, str) and v.strip():
            rec[k] = v.strip()
    return rec                                             # 정규식 merge 안 함(LLM 결정 신뢰, 환각은 RANGE 차단)
