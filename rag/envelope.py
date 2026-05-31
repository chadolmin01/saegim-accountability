"""제약 envelope — 현장 조건 → 콘크리트 배합이 *지켜야 할 모든 법정 한도* + 적용 의무 종류 집계.

추천(설계)이 아니라 **결정적 제약 집계**다. "이 배합 써라"가 아니라 "이 한도를 다 지켜야 하고,
이 조건이면 이 종류 기준이 의무"를 회수한다. 시험배합/배합설계는 이 envelope 안에서 하고,
나온 배합 결과는 engine.conditions.check_all로 합부판정한다.

  python -m rag.envelope exposure_class=EC4 design_fck_mpa=30
  python -m rag.envelope exposure_class=ES3 design_fck_mpa=35 daily_avg_temp_c=2 marine=1 mass=1
"""
from __future__ import annotations
import sys
import yaml
import paths

CONCRETE_WK = ("콘크리트타설", None, "전체")

# (rule_id 키워드, 트리거(conditions)→bool, 종류명). 순서 중요: lightweight가 mass_concrete보다 먼저.
SPECIAL = [
    ("cold_weather", lambda c: _num(c, "daily_avg_temp_c") is not None and _num(c, "daily_avg_temp_c") <= 4, "한중콘크리트(일평균≤4℃)"),
    ("hot_weather", lambda c: _num(c, "daily_avg_temp_c") is not None and _num(c, "daily_avg_temp_c") > 25, "서중콘크리트(>25℃)"),
    ("marine", lambda c: c.get("marine"), "해양콘크리트"),
    ("underwater", lambda c: c.get("underwater"), "수중콘크리트"),
    ("lightweight", lambda c: c.get("lightweight"), "경량콘크리트"),
    ("mass_concrete", lambda c: c.get("mass"), "매스콘크리트"),
    ("high_strength", lambda c: (_num(c, "design_fck_mpa") or 0) >= 40 or c.get("high_strength"), "고강도콘크리트(fck≥40)"),
    ("scc", lambda c: c.get("scc"), "고유동(SCC)"),
    ("recycled_aggregate", lambda c: c.get("recycled_aggregate"), "순환골재콘크리트"),
    ("fly_ash", lambda c: c.get("uses_fly_ash"), "플라이애시 사용"),
    ("slag", lambda c: c.get("uses_slag"), "슬래그 사용"),
    ("expansive", lambda c: c.get("expansive"), "팽창콘크리트"),
]


def _num(c, k):
    try:
        return float(c.get(k))
    except (TypeError, ValueError):
        return None


def load():
    return [yaml.safe_load(open(f, encoding="utf-8"))
            for f in paths.rule_glob("condition_rules") + paths.rule_glob("material_specs")]


def fmt_limit(rule, cond):
    """조건에 맞춰 한도값 해석(노출등급별 등은 그 값으로 resolve). 못 풀면 authority.rule 원문."""
    req = rule.get("requires") or {}
    a = rule.get("authority") or {}
    if "lookup_max" in req:
        lm = req["lookup_max"]; bv = cond.get(lm.get("by")); tbl = lm.get("max_table", {})
        if bv in tbl:
            return f"≤ {tbl[bv]}  ({lm['by']}={bv})"
        return a.get("rule") or f"≤ {tbl}"
    if "lookup_bounds" in req:
        lb = req["lookup_bounds"]; bv = cond.get(lb.get("by")); tbl = lb.get("min_table", {})
        if bv in tbl:
            return f"≥ {tbl[bv]}  ({lb['by']}={bv})"
        return a.get("rule") or f"≥ {tbl}"
    if "value_bounds" in req:
        ps = []
        for vb in req["value_bounds"]:
            k = (vb.get("key", "")).split(".")[-1]
            if vb.get("min") is not None and vb.get("max") is not None:
                ps.append(f"{k} {vb['min']}~{vb['max']}")
            elif vb.get("max") is not None:
                ps.append(f"{k} ≤ {vb['max']}")
            elif vb.get("min") is not None:
                ps.append(f"{k} ≥ {vb['min']}")
        return "; ".join(ps) or a.get("rule") or ""
    return a.get("rule") or "(requires 참조)"


def envelope(cond):
    cons, types, skipped = [], set(), set()
    for r in load():
        rid = r.get("rule_id", "")
        if r.get("applies_to_work_kind") not in CONCRETE_WK:
            continue
        if any(x in rid for x in ("steel", "rebar")) or any(x in (r.get("title") or "") for x in ("철근", "강재")):
            continue                                            # 철근·강재는 콘크리트 배합 envelope 대상 아님
        if "durability_exposure" in rid and not cond.get("exposure_class"):
            continue
        sp = next(((trig, name) for kw, trig, name in SPECIAL if kw in rid), None)
        if sp:
            trig, name = sp
            if trig(cond):
                types.add(name)
            else:
                skipped.add(name)
                continue
        cons.append({"항목": r.get("title"), "한도": fmt_limit(r, cond),
                     "차원": r.get("dimension") or "", "§": r.get("regime") or (r.get("authority") or {}).get("standard") or ""})
    return {"conditions": cond, "mandatory_types": sorted(types),
            "not_triggered": sorted(skipped - types), "constraints": cons}


def main():
    cond = {}
    for arg in sys.argv[1:]:
        if "=" in arg:
            k, v = arg.split("=", 1)
            cond[k] = float(v) if v.replace(".", "", 1).isdigit() else (True if v.lower() in ("1", "true") else v)
    e = envelope(cond)
    print(f"현장 조건: {cond}\n")
    print(f"■ 적용 의무 종류: {', '.join(e['mandatory_types']) or '(일반 콘크리트)'}")
    if e["not_triggered"]:
        print(f"  (조건 미충족으로 미적용: {', '.join(e['not_triggered'])})")
    print(f"\n■ 지켜야 할 한도 {len(e['constraints'])}건 (배합이 만족해야 할 가드레일):")
    for c in sorted(e["constraints"], key=lambda x: x["차원"]):
        print(f"  [{c['차원']:6}] {c['항목'][:30]:32} {str(c['한도'])[:52]}  ({c['§']})")
    print("\n→ 추천이 아님: 이 한도 안에서 시험배합/배합설계, 결과는 engine으로 합부판정.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
