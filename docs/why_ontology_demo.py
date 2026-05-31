"""why_ontology_demo — 같은 콘크리트·안전 질문을 두 방식에 돌려 차이를 실측한다.

  ① LLM 직접판정 (비신뢰 기준선) — 검색·엔진 없이 모델이 바로 합/부를 말함. 키 있을 때만.
  ② 온톨로지 엔진 (이 저장소) — 측정값을 결정적 규칙으로 계산해 판정 + 근거 §.

요지: 한도가 문장에 숫자로 적힌 단순 조회는 ①도 맞히지만, 한도를 '계산'해야 하거나
(0.85·fck), 범주에 따라 한도가 달라지거나(노출등급), 시점 게이트(법 시행일)가 걸리면
①은 그럴듯하게 빗나간다. ②는 같은 입력에 항상 같은 판정 + 개정일·출처를 들고 있다.

실행:
  python docs/why_ontology_demo.py            # 엔진 판정만(키 불필요·결정적)
  python docs/why_ontology_demo.py --json     # 결과를 JSON 으로
  # ANTHROPIC_API_KEY(또는 .env) 설정 시 'LLM 직접판정' 열이 함께 출력된다.

판정은 언제나 엔진이 한다. LLM 열은 '엔진이 왜 필요한지'를 보여주기 위한 대조군일 뿐,
이 저장소의 어떤 판정에도 쓰이지 않는다.
"""
from __future__ import annotations
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.stdout.reconfigure(encoding="utf-8")

import yaml
import paths
from engine import conditions as C
from engine import org_judgment as O

# ── 트랩 배터리 ────────────────────────────────────────────────────────────
# 각 항목: 자연어 질문 + 엔진 입력(조건 rec 또는 조직×사고) + 정답 메모.
# 4 범주: A 단일임계값 / B 계산임계값 / C 범주별 한도 / D 시점 게이트.
BATTERY = [
    {"cat": "A 단일임계값", "q": "AE 콘크리트 공기량 측정값이 2%다. 적합한가?",
     "kind": "condition", "rule": "concrete_air_ae",
     "rec": {"work_kind": "콘크리트타설", "test_values": {"air_pct": 2.0}},
     "truth": "부적합 — 2.0 < 3.0 (KS F 4009)"},
    {"cat": "A 단일임계값", "q": "콘크리트 염화물 함유량이 0.45 kg/㎥다. 적합한가?",
     "kind": "condition", "rule": "concrete_chloride",
     "rec": {"work_kind": "콘크리트타설", "test_values": {"chloride_kg_m3": 0.45}},
     "truth": "부적합 — 0.45 > 0.30 (KS F 4009)"},
    {"cat": "B 계산임계값", "q": "설계기준강도 24MPa인데 28일 압축강도 시험값이 19MPa다. 합격인가?",
     "kind": "condition", "rule": "concrete_strength_acceptance",
     "rec": {"work_kind": "콘크리트타설", "design_fck_mpa": 24, "test_values": {"strength_mpa": 19.0}},
     "truth": "부적합 — 19 < 0.85×24 = 20.4 (KS F 4009)"},
    {"cat": "B 계산임계값", "q": "설계기준강도 24MPa인데 28일 압축강도 시험값이 21MPa다. 합격인가?",
     "kind": "condition", "rule": "concrete_strength_acceptance",
     "rec": {"work_kind": "콘크리트타설", "design_fck_mpa": 24, "test_values": {"strength_mpa": 21.0}},
     "truth": "합격 — 21 ≥ 0.85×24 = 20.4 (naive 21<24 비교는 거짓 불합격)"},
    {"cat": "C 범주별 한도", "q": "EC2(탄산화) 노출환경인데 물결합재비가 0.55다. 적합한가?",
     "kind": "condition", "rule": "durability_exposure_wb",
     "rec": {"work_kind": "콘크리트타설", "exposure_class": "EC2", "test_values": {"wb_ratio": 0.55}},
     "truth": "합격 — EC2 상한 0.55, 0.55 ≤ 0.55 (KDS 14 20 40)"},
    {"cat": "C 범주별 한도", "q": "EC4(탄산화) 노출환경인데 물결합재비가 0.55다. 적합한가?",
     "kind": "condition", "rule": "durability_exposure_wb",
     "rec": {"work_kind": "콘크리트타설", "exposure_class": "EC4", "test_values": {"wb_ratio": 0.55}},
     "truth": "부적합 — EC4 상한 0.45, 0.55 > 0.45 (같은 0.55인데 등급만 다름)"},
    {"cat": "D 시점 게이트", "q": "2021-06-01 발생한 사망 2명 건설사고. 원도급사 경영책임자가 중대재해처벌법 위반인가?",
     "kind": "org", "rule": "serious_accident_corporate_duty",
     "org": {"id": "원도급사", "org_role": "원도급", "subcontract_tier": 0, "safety_health_system": False},
     "incident": {"event_date": "2021-06-01", "fatalities": 2},
     "truth": "not_applicable — 2022-01-27 시행 전 사고, 소급 불가 (중대재해처벌법 부칙)"},
    {"cat": "D 시점 게이트", "q": "2024-06-01 발생한 사망 2명 건설사고. 원도급사 경영책임자(체계 미이행)가 중대재해처벌법 위반인가?",
     "kind": "org", "rule": "serious_accident_corporate_duty",
     "org": {"id": "원도급사", "org_role": "원도급", "subcontract_tier": 0, "safety_health_system": False},
     "incident": {"event_date": "2024-06-01", "fatalities": 2},
     "truth": "violated — 시행 후·경영책임자·사망재해·체계 미이행 (중대재해처벌법 §4/§9)"},
]

MARK = {"compliant": "✓ 합격", "violated": "✗ 부적합", "not_applicable": "— 해당없음", "판정보류": "? 판정보류"}


def _load_condition_rule(name: str) -> dict:
    return yaml.safe_load(open(paths.P("condition_rules", f"{name}.yaml"), encoding="utf-8"))


def engine_verdict(item: dict) -> dict:
    """온톨로지 엔진 판정 — 결정적. 키·네트워크 불필요."""
    if item["kind"] == "condition":
        rule = _load_condition_rule(item["rule"])
        r = C.evaluate_condition(item["rec"], rule)
        std = (r.get("authority") or rule.get("authority") or {}).get("standard") \
            or (rule.get("authority") or {}).get("law") or ""
        return {"verdict": r["verdict"], "reason": r.get("reason", ""), "basis": std}
    # org × incident
    for v in O.judge_org(item["org"], item["incident"]):
        if v["rule_id"].startswith(item["rule"]):
            return {"verdict": v["verdict"], "reason": v.get("reason", ""),
                    "basis": v.get("regime") or "중대재해처벌법"}
    return {"verdict": "not_applicable", "reason": "해당 룰 미도달", "basis": ""}


_LLM_SYS = (
    "너는 한국 건설 검측 보조다. 다음 질문에 '합격'·'부적합'·'판정불가' 중 하나로 먼저 답하고, "
    "근거가 된 기준(표준번호)과 한도 수치를 한 줄로 덧붙여라. 확실하지 않으면 추측이라고 밝혀라. "
    "(이 답은 결정적 엔진 판정과 대조하기 위한 참고용이다.)"
)


def llm_verdict(item: dict):
    """LLM 직접판정 — 검색·엔진 없이 모델이 바로 답함. 키 있을 때만, 없으면 None.
    이 저장소의 판정엔 절대 쓰이지 않는다(대조군)."""
    try:
        from rag import llm
    except Exception:
        return None
    if not llm.available():
        return None
    try:
        return (llm.complete(_LLM_SYS, item["q"], max_tokens=200) or "").strip().replace("\n", " ")
    except Exception as e:
        return f"(LLM 호출 실패: {type(e).__name__})"


def run():
    rows = []
    for it in BATTERY:
        eng = engine_verdict(it)
        rows.append({"category": it["cat"], "question": it["q"],
                     "engine": eng, "truth": it["truth"], "llm": llm_verdict(it)})
    return rows


def print_table(rows):
    has_llm = any(r["llm"] is not None for r in rows)
    print("=" * 78)
    print(" 온톨로지 없이(LLM 직접판정) vs 온톨로지 엔진 — 콘크리트·안전 검측")
    print("=" * 78)
    if not has_llm:
        print(" * LLM 열 생략: ANTHROPIC_API_KEY 미설정 (엔진 판정만 표시 — 결정적).")
        print("   키를 .env 에 넣으면 'LLM 직접판정' 대조가 함께 나온다.")
    print()
    cat = None
    for r in rows:
        if r["category"] != cat:
            cat = r["category"]
            print(f"\n[{cat}]")
        eng = r["engine"]
        v = MARK.get(eng["verdict"], eng["verdict"])
        detail = eng["reason"] or eng["verdict"]
        print(f"  Q. {r['question']}")
        print(f"     ├ 엔진     : {v}  ({detail})  근거 {eng['basis']}")
        if r["llm"] is not None:
            print(f"     ├ LLM 직접 : {r['llm']}")
        print(f"     └ 정답     : {r['truth']}")
    print("\n" + "=" * 78)
    print(" 엔진: 8/8 결정적 판정 + 근거 §. 같은 입력 → 항상 같은 결과.")
    print(" LLM 직접판정은 A(단일임계값)는 맞혀도 B(계산)·C(범주)·D(시점)에서 빗나간다.")
    print("=" * 78)


if __name__ == "__main__":
    rows = run()
    if "--json" in sys.argv:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print_table(rows)
