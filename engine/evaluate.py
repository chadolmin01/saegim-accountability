"""
Reference evaluator — placement_rules/*.yaml 를 현장 시나리오에 대조하여 ComplianceFinding 산출.

RAG 와 다른 점: "비슷한 법령 문장" 검색이 아니라
required = f(규모, 시점) 를 계산하고 effective(유효 선임)와 비교 → 결정적 판정.

두 산출 형태(requirement_shape)를 dispatch:
  - simple_count  : 공사금액 → 요구 인원수 (예 안전관리자)
  - graded_slots  : 규모 → 등급별 인원 슬롯 (예 품질관리자)

Usage:
  python -m engine.evaluate examples/scenario_understaffed.yaml
  python -m engine.evaluate examples/scenario_quality_understaffed.yaml placement_rules/quality_manager_staffing.yaml
"""
from __future__ import annotations

import sys
from datetime import date

import yaml

DEFAULT_RULE = "placement_rules/safety_manager_staffing.yaml"


def d(s) -> date | None:
    if not s:
        return None
    if isinstance(s, date):
        return s
    y, m, dd = map(int, str(s).split("-"))
    return date(y, m, dd)


def effective(managers: list, at: date) -> list:
    """assessment_date 시점에 유효(선임~해임)한 사람만."""
    out = []
    for m in managers:
        s = d(m["start_date"])
        e = d(m.get("end_date"))
        if s <= at and (e is None or at <= e):
            out.append(m)
    return out


def in_relief_window(start: date, end: date, at: date) -> bool:
    total = (end - start).days
    if total <= 0:
        return False
    margin = total * 0.15
    return at.toordinal() <= start.toordinal() + margin or at.toordinal() >= end.toordinal() - margin


# --- select_when 조건 평가 (graded_slots 용) -------------------------------
_OPS = {"__gte": lambda a, b: a >= b, "__gt": lambda a, b: a > b,
        "__lte": lambda a, b: a <= b, "__lt": lambda a, b: a < b, "__eq": lambda a, b: a == b}


def eval_clause(clause, params: dict) -> bool:
    if isinstance(clause, str):
        return bool(params.get(clause))
    if isinstance(clause, dict):
        if "any" in clause:
            return any(eval_clause(c, params) for c in clause["any"])
        if "all" in clause:
            return all(eval_clause(c, params) for c in clause["all"])
        # comparison {key__op: value}
        for k, v in clause.items():
            for suf, fn in _OPS.items():
                if k.endswith(suf):
                    key = k[: -len(suf)]
                    pv = params.get(key)
                    if pv is None:
                        return False
                    return fn(pv, v)
            # bare {key: truthy-expected} fallback
            return bool(params.get(k)) == bool(v)
    return False


# --- simple_count (안전관리자류) -------------------------------------------
def eval_simple_count(scenario: dict, rule: dict) -> dict:
    p = scenario["project"]
    amount = p["contract_amount_krw"]
    ctype = p.get("contractor_type", "원도급")
    wcat = p.get("work_category", "일반")
    start, end = d(p["construction_start_date"]), d(p["construction_end_date"])
    assessment = d((scenario.get("incident") or {}).get("event_date")) or end

    thr = rule["applicability_threshold"]
    floor = thr["관계수급인_min_krw"] if ctype == "관계수급인" else thr["원도급_min_krw"]
    if amount < floor:
        return {"verdict": "not_required", "rationale": f"공사금액 {amount:,} < 하한 {floor:,}"}

    bracket = None
    for b in rule["brackets"]:
        lo, hi = b["min_krw"], b["max_krw"]
        ov = b.get("boundary_override") or {}
        if wcat == "토목공사업":
            lo = ov.get("토목공사업_min_krw", lo)
            hi = ov.get("토목공사업_max_krw", hi)
        if amount >= lo and (hi is None or amount < hi):
            bracket = b
            break
    if not bracket:
        return {"verdict": "not_required", "rationale": "구간 없음"}

    required = bracket["required_count"]
    inc = bracket.get("increment")
    if inc and amount >= inc["base_krw"]:
        steps = (amount - inc["base_krw"]) // inc["step_krw"]
        required = inc["base_count"] + int(steps) * inc["step_count"]
    relieved = False
    if bracket.get("relief_15pct_count") is not None and in_relief_window(start, end, assessment):
        required, relieved = bracket["relief_15pct_count"], True

    eff = effective(scenario.get("appointed_managers", []), assessment)
    n = len(eff)
    # 자격 검증 (별표4/별표6): rule 에 acceptable_qualifications 있으면 유효선임자 자격 확인
    acceptable = rule.get("acceptable_qualifications")
    unqualified_people = []
    if acceptable:
        for m in eff:
            q = m.get("qualification")
            if q is not None and q not in acceptable:
                unqualified_people.append(m["person"])
    if n < required:
        verdict = "understaffed"
    elif unqualified_people:
        verdict = "unqualified"
    else:
        verdict = "compliant"
    return {
        "verdict": verdict, "required_count": required, "effective_count": n,
        "effective_people": [m["person"] for m in eff], "shortfall": max(0, required - n),
        "unqualified_people": unqualified_people,
        "relieved_15pct": relieved,
        "rationale": f"공사금액 {amount:,} → 요구 {required}명"
                     + (" (전·후15% 완화)" if relieved else "")
                     + f", 사고시점 {assessment} 유효 {n}명. 근거 {rule['authority']['table'][:18]}…",
    }


# --- graded_slots (품질관리자류) -------------------------------------------
def eval_graded_slots(scenario: dict, rule: dict) -> dict:
    p = scenario["project"]
    start, end = d(p["construction_start_date"]), d(p["construction_end_date"])
    assessment = d((scenario.get("incident") or {}).get("event_date")) or end

    params = dict(p)  # contract_amount_krw, gross_floor_area_m2, is_multiuse_building …

    tier = None
    for b in rule["brackets"]:
        if eval_clause(b["select_when"], params):
            tier = b
            break
    if not tier:
        return {"verdict": "not_required", "rationale": "어느 등급 구간에도 미해당"}

    order = {g: i for i, g in enumerate(rule["grade_order"])}  # 초급0 … 특급3
    slots = sorted(tier["required_slots"], key=lambda s: order[s["min_grade"]], reverse=True)
    total_required = sum(s["count"] for s in slots)

    eff = effective(scenario.get("appointed_managers", []), assessment)
    pool = sorted(eff, key=lambda m: order.get(m.get("grade", "초급"), 0), reverse=True)

    used = [False] * len(pool)
    unfilled = []
    for s in slots:
        for _ in range(s["count"]):
            assigned = False
            for i, m in enumerate(pool):
                if not used[i] and order.get(m.get("grade", "초급"), 0) >= order[s["min_grade"]]:
                    used[i] = True
                    assigned = True
                    break
            if not assigned:
                unfilled.append(f"{s['min_grade']}↑ 1명")

    if not unfilled:
        verdict = "compliant"
    elif len(eff) < total_required:
        verdict = "understaffed"
    else:
        verdict = "unqualified"

    return {
        "verdict": verdict, "tier": tier["tier"],
        "required_slots": [f"{s['min_grade']}↑×{s['count']}" for s in slots],
        "total_required": total_required, "effective_count": len(eff),
        "effective_people": [f"{m['person']}({m.get('grade')})" for m in eff],
        "unfilled_slots": unfilled,
        "rationale": f"현장 품질등급 {tier['tier']} → 요구 {[f'{s['min_grade']}↑×{s['count']}' for s in slots]}, "
                     f"사고시점 {assessment} 유효 {len(eff)}명{[f'{m['person']}({m.get('grade')})' for m in eff]}. "
                     f"근거 {rule['authority']['table'][:18]}…",
    }


# --- threshold_binary (선임의무 yes/no, 보통 1명) ---------------------------
def eval_threshold_binary(scenario: dict, rule: dict) -> dict:
    p = scenario["project"]
    end = d(p.get("construction_end_date"))
    assessment = d((scenario.get("incident") or {}).get("event_date")) or end or d(p.get("assessment_date"))
    params = dict(p)
    th = rule["threshold"]
    if not eval_clause(th["trigger_when"], params):
        return {"verdict": "not_required", "rationale": "임계값 미달 → 선임 의무 없음"}
    required = th.get("required_count", 1)
    eff = effective(scenario.get("appointed_managers", []), assessment)
    n = len(eff)
    verdict = "compliant" if n >= required else "understaffed"
    return {"verdict": verdict, "required_count": required, "effective_count": n,
            "effective_people": [m["person"] for m in eff], "shortfall": max(0, required - n),
            "rationale": f"임계값 충족 → 요구 {required}명, 사고시점 {assessment} 유효 {n}명. 근거 {rule['authority'].get('article','')}"}


# --- qualification (자격 프로파일 충족, count=1) -----------------------------
def _grade_rank(rule, g):
    order = {x: i for i, x in enumerate(rule.get("grade_order", []))}
    return order.get(g, -1)


def _matches_profile(person: dict, prof: dict, rule: dict) -> bool:
    if "license" in prof and person.get("license") != prof["license"]:
        return False
    if "min_grade" in prof and _grade_rank(rule, person.get("grade")) < _grade_rank(rule, prof["min_grade"]):
        return False
    if "min_experience_years" in prof and (person.get("experience_years") or 0) < prof["min_experience_years"]:
        return False
    if "min_cm_experience_years" in prof and (person.get("cm_experience_years") or 0) < prof["min_cm_experience_years"]:
        return False
    return True


def eval_qualification(scenario: dict, rule: dict) -> dict:
    p = scenario["project"]
    end = d(p.get("construction_end_date"))
    assessment = d((scenario.get("incident") or {}).get("event_date")) or end or d(p.get("assessment_date"))
    params = dict(p)

    if "applicability" in rule and not eval_clause(rule["applicability"]["trigger_when"], params):
        return {"verdict": "not_required", "rationale": "적용 대상 아님 (applicability 미충족)"}

    amount = next((params[k] for k in ("estimated_amount_krw", "total_contract_amount_krw", "contract_amount_krw")
                   if params.get(k) is not None), None)
    amt = amount if amount is not None else 0   # 규모 게이트 룰(금액 무관, min_krw:0)은 0으로 bracket 선택
    bracket = None
    for b in rule["brackets"]:
        if amt >= b["min_krw"] and (b["max_krw"] is None or amt < b["max_krw"]):
            bracket = b
            break
    if not bracket:
        return {"verdict": "not_required", "rationale": "구간 없음"}

    count = bracket.get("count", 1)
    all_appts = scenario.get("appointed_managers", [])
    eff = effective(all_appts, assessment)
    qualified = [m for m in eff if any(_matches_profile(m, prof, rule) for prof in bracket["accepts"])]
    if len(qualified) >= count:
        verdict = "compliant"
    elif len(eff) < count:
        verdict = "understaffed"
    else:
        verdict = "unqualified"
    # 시점공백: 선임이 있었으나 사고시점에 전원 만료·해임 → 유효선임 0 (단순 '미선임'과 구분)
    gap = ""
    if all_appts and not eff:
        spans = ", ".join(f"{m.get('person') or m.get('id','?')}({m.get('start_date')}~{m.get('end_date') or '현재'})" for m in all_appts)
        gap = f" ★시점공백: 선임 {len(all_appts)}명[{spans}] 사고시점 {assessment} 전원 만료·해임 → 유효선임 0"
    return {"verdict": verdict, "required_count": count, "effective_count": len(eff),
            "qualified_count": len(qualified),
            "effective_people": [f"{m['person']}({m.get('grade') or m.get('license')})" for m in eff],
            "accepts": bracket["accepts"],
            "rationale": (f"공사금액 {amount:,} → 구간[{bracket['min_krw']:,}~]" if amount is not None else "규모 게이트(금액무관)")
                         + f", 자격충족 {len(qualified)}/{count}. 근거 {rule['authority'].get('table','')[:18]}…" + gap}


# --- field_slots (분야별 인원, 예 공사감리자) -------------------------------
def eval_field_slots(scenario: dict, rule: dict) -> dict:
    p = scenario["project"]
    end = d(p.get("construction_end_date"))
    assessment = d((scenario.get("incident") or {}).get("event_date")) or end or d(p.get("assessment_date"))
    params = dict(p)
    eff = effective(scenario.get("appointed_managers", []), assessment)

    # 요구 슬롯 = base + (상주 조건 충족 시) residency_slots
    required_slots = [dict(rule["base_requirement"])]
    if eval_clause(rule.get("residency_trigger", {}), params):
        required_slots += [dict(s) for s in rule.get("residency_slots", [])]

    by_field: dict[str, int] = {}
    for m in eff:
        by_field[m.get("field")] = by_field.get(m.get("field"), 0) + 1

    unfilled = []
    for slot in required_slots:
        have = by_field.get(slot["field"], 0)
        if have < slot["count"]:
            unfilled.append(f"{slot['field']} {slot['count'] - have}명")

    verdict = "compliant" if not unfilled else "understaffed"
    return {"verdict": verdict,
            "required_count": sum(s["count"] for s in required_slots),
            "effective_count": len(eff),
            "required_fields": [f"{s['field']}×{s['count']}" for s in required_slots],
            "unfilled_slots": unfilled,
            "rationale": f"요구 분야 {[s['field'] for s in required_slots]}, 사고시점 {assessment} 유효 {len(eff)}명. "
                         f"부족: {unfilled or '없음'}. 근거 {rule['authority'].get('article','')}"}


def evaluate(scenario: dict, rule: dict) -> dict:
    shape = rule.get("requirement_shape", "simple_count")
    return {
        "graded_slots": eval_graded_slots,
        "threshold_binary": eval_threshold_binary,
        "qualification": eval_qualification,
        "field_slots": eval_field_slots,
        "simple_count": eval_simple_count,
    }.get(shape, eval_simple_count)(scenario, rule)


def main() -> int:
    scenario_path = sys.argv[1] if len(sys.argv) > 1 else "examples/scenario_understaffed.yaml"
    scenario = yaml.safe_load(open(scenario_path, encoding="utf-8"))
    rule_path = sys.argv[2] if len(sys.argv) > 2 else scenario.get("rule", DEFAULT_RULE)
    rule = yaml.safe_load(open(rule_path, encoding="utf-8"))

    print(f"=== 시나리오: {scenario['project']['name']}  (rule: {rule['rule_id']}) ===")
    inc = scenario.get("incident", {})
    if inc:
        print(f"사고: {inc.get('name')} ({inc.get('event_date')})")
    print("선임 이력:")
    for m in scenario.get("appointed_managers", []):
        g = f" [{m.get('grade')}]" if m.get("grade") else ""
        print(f"  - {m['person']}{g} {m['start_date']} ~ {m.get('end_date') or '현직'}")
    print()

    r = evaluate(scenario, rule)
    print("=== ComplianceFinding ===")
    for k, v in r.items():
        print(f"  {k}: {v}")
    badge = {"compliant": "[적정]", "understaffed": "[인원 미달]",
             "unqualified": "[등급/자격 미달]", "not_required": "[의무 없음]"}.get(r["verdict"], "?")
    print(f"\n>>> 판정: {badge}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
