"""
규정 fidelity 스위트 (자동 생성) — 전 룰을 근거 규정과 대조.

각 condition 룰의 requires/applicable_when 을 파싱해 (위반 레코드, 적합 레코드)를 합성하고,
엔진 판정이 위반→violated, 적합→compliant/not_applicable 인지 확인. 룰 변경 시 자동 추종.
staffing/document/prerequisite/appropriateness 는 evaluator 별 대표 케이스로 보강.

python fidelity_suite.py
"""
from __future__ import annotations
import paths
import glob, sys, yaml
from engine import conditions as C
from engine import prerequisites as P
from engine import documents as D
from engine import appropriateness as A
from engine import evaluate as E
sys.stdout.reconfigure(encoding="utf-8")

PASS = 0; FAIL = 0; SKIP = []


def setk(rec, dotted, val):
    parts = dotted.split("."); d = rec
    for p in parts[:-1]:
        d = d.setdefault(p, {})
    d[parts[-1]] = val


def apply_gate(rec, aw):
    """applicable_when presence 게이트 충족 (값은 requires 가 덮어씀)."""
    if not aw:
        return
    items = []
    if "any" in aw:
        s = aw["any"][0]
        items = list(s.items()) if isinstance(s, dict) else [(s, True)]
    elif "all" in aw:
        for s in aw["all"]:
            items += list(s.items()) if isinstance(s, dict) else [(s, True)]
    else:
        items = list(aw.items())
    for k, v in items:
        base = k.split("__")[0]
        if k.endswith("__eq"):
            setk(rec, base, v)
        elif k.endswith("__gte"):
            setk(rec, base, v)            # ≥v 충족
        elif k.endswith("__gt"):
            setk(rec, base, v + (abs(v) * 0.1 or 1))   # >v 충족
        elif k.endswith("__lte"):
            setk(rec, base, v)
        elif k.endswith("__lt"):
            setk(rec, base, v - (abs(v) * 0.1 or 1))
        else:
            setk(rec, base, v)


def synth_condition(rule):
    """(위반rec, 적합rec) 또는 None."""
    req = rule.get("requires", {})
    wk = rule.get("applies_to_work_kind")
    base = lambda: ({"work_kind": wk} if wk else {})
    vrec, crec = base(), base()
    aw = rule.get("applicable_when")
    apply_gate(vrec, aw); apply_gate(crec, aw)

    if rule.get("mode") == "prohibition":
        # 금지형: applicable_when 충족(vrec)=위반 / 미충족(crec, base)=not_applicable
        return vrec, base()

    if "measures_any" in req or "measures_all" in req:
        need = req.get("measures_any") or req.get("measures_all")
        vrec["applied_measures"] = []
        crec["applied_measures"] = list(need)
        return vrec, crec
    if "value_bounds" in req:
        def below(m): return m * 0.9 if m > 0 else m - 1   # min 미만이되 ≥0 게이트 유지
        def above(m): return m * 1.1 if m > 0 else m + 1
        for vb in req["value_bounds"]:
            if "min" in vb:
                setk(vrec, vb["key"], below(vb["min"])); setk(crec, vb["key"], vb["min"])
            elif "max" in vb:
                setk(vrec, vb["key"], above(vb["max"])); setk(crec, vb["key"], vb["max"])
        for vb in req["value_bounds"]:   # 적합 rec 전 bound 만족 보정
            cur = _resolve(crec, vb["key"])
            if "min" in vb and (cur is None or cur < vb["min"]):
                setk(crec, vb["key"], vb["min"])
            if "max" in vb and _resolve(crec, vb["key"]) > vb["max"]:
                setk(crec, vb["key"], (vb.get("min", 0) + vb["max"]) / 2)
        return vrec, crec
    if "lookup_bounds" in req:
        lb = req["lookup_bounds"]; cat = next(iter(lb["min_table"])); need = lb["min_table"][cat]
        setk(vrec, lb["by"], cat); setk(crec, lb["by"], cat)
        setk(vrec, lb["key"], need - (abs(need) * 0.1 or 1)); setk(crec, lb["key"], need)
        return vrec, crec
    if "lookup_max" in req:
        lm = req["lookup_max"]; cat = next(iter(lm["max_table"])); cap = lm["max_table"][cat]
        setk(vrec, lm["by"], cat); setk(crec, lm["by"], cat)
        setk(vrec, lm["key"], cap + (abs(cap) * 0.1 or 1)); setk(crec, lm["key"], cap)
        return vrec, crec
    if "ratio_bound" in req:
        rb = req["ratio_bound"]; ref = 100.0
        setk(vrec, rb["of"], ref); setk(crec, rb["of"], ref)
        setk(vrec, rb["key"], ref * rb["ratio"] - 1); setk(crec, rb["key"], ref * rb["ratio"])
        return vrec, crec
    if "deviation_bound" in req:
        db = req["deviation_bound"]; tgt = db["bands"][0].get("spec_lte", 50) or 50
        tol = db["bands"][0]["tol"]
        setk(vrec, db["target"], tgt); setk(crec, db["target"], tgt)
        setk(vrec, db["measured"], tgt + tol + 1); setk(crec, db["measured"], tgt)
        return vrec, crec
    if "frequency_bound" in req:
        fb = req["frequency_bound"]; iv = fb["interval_m3"]
        setk(vrec, fb["volume"], iv * 3); setk(crec, fb["volume"], iv * 3)
        setk(vrec, fb["count"], 1); setk(crec, fb["count"], 3)
        return vrec, crec
    return None


def _resolve(rec, key):
    cur = rec
    for p in key.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    return cur


def chk(label, ok, src):
    global PASS, FAIL
    PASS += ok; FAIL += not ok
    if not ok:
        print(f"  ✗ FAIL {label}  (근거 {src})")


print("━━ 작업조건/검측 (condition) 룰 — 자동 생성 위반·적합 ━━")
for f in paths.rule_glob("condition_rules"):
    rule = yaml.safe_load(open(f, encoding="utf-8")); rid = rule["rule_id"].split("__")[0]
    src = (rule.get("authority", {}) or {}).get("standard") or (rule.get("authority", {}) or {}).get("law") or rule.get("regime")
    s = synth_condition(rule)
    if s is None:
        SKIP.append(rid); continue
    vrec, crec = s
    vv = C.evaluate_condition(vrec, rule)["verdict"]
    cv = C.evaluate_condition(crec, rule)["verdict"]
    chk(f"{rid} 위반탐지", vv == "violated", src)
    chk(f"{rid} 적합통과", cv in ("compliant", "not_applicable"), src)

print("━━ 인적배치 (staffing) — 대표 케이스 ━━")
def staff(rule_file, proj_ok, proj_bad, mgr_ok, mgr_bad):
    r = yaml.safe_load(open(rule_file, encoding="utf-8"))
    base = {"assessment_date": "2026-05-01", "construction_end_date": "2026-12-01"}
    vok = E.eval_qualification({"project": dict(base, **proj_ok), "appointed_managers": mgr_ok}, r)["verdict"]
    vbad = E.eval_qualification({"project": dict(base, **proj_bad), "appointed_managers": mgr_bad}, r)["verdict"]
    chk(f"{r['rule_id'].split('__')[0]} 적격", vok == "compliant", r.get("regime"))
    chk(f"{r['rule_id'].split('__')[0]} 미달", vbad in ("understaffed", "unqualified"), r.get("regime"))
staff("placement_rules/designer_structural_engineer.yaml", {"floor_count": 6}, {"floor_count": 6},
      [{"person": "a", "license": "건축구조기술사", "start_date": "2026-01-01"}], [{"person": "b", "license": "건축사", "start_date": "2026-01-01"}])
staff("placement_rules/facility_inspection_engineer.yaml", {"is_facility_grade_1_or_2": True}, {"is_facility_grade_1_or_2": True},
      [{"person": "a", "grade": "중급", "start_date": "2026-01-01"}], [{"person": "b", "grade": "초급", "start_date": "2026-01-01"}])

print("━━ 선행요건 (prerequisite) — 대표 케이스 ━━")
w = {"work_kind": "굴착", "event_date": "2026-05-01", "component_ref": "z1"}
chk("excavation_after_shoring 위반탐지", any(r["verdict"] == "violated" for r in P.check_all(w, [])), "KCS 11 10 15")
chk("excavation_after_shoring 적합", not any(r["rule_id"].startswith("excavation_after_shoring") and r["verdict"] == "violated"
    for r in P.check_all(w, [{"kind": "시공검측", "checkpoint": "흙막이설치검측", "result": "합격", "event_date": "2026-04-20", "target_component_ref": "z1"}])), "KCS 11 10 15")

print("━━ 의사결정 적절성 (appropriateness) — 대표 케이스 ━━")
site = {"region_rainy_season_work": True}
dd_bad = [{"name": "양생계획", "kind": "양생계획", "planned_mitigations": []}]
dd_ok = [{"name": "양생계획", "kind": "양생계획", "planned_mitigations": ["강우_보양"]}]
chk("design_curing_vs_rainfall 위반탐지", any(r["verdict"] == "violated" for r in A.check_all(site, dd_bad)), "별표7")
chk("design_curing_vs_rainfall 적합", not any(r["verdict"] == "violated" for r in A.check_all(site, dd_ok)), "별표7")

print("━━ 문서제출 (document) — 대표 케이스 ━━")
proj = {"total_contract_amount_krw": 60000000000, "contains_building": True}
docv = D.check_all(proj, [])
chk("품질관리계획서 미제출탐지", any(r["document"] == "품질관리계획서" and r["verdict"] == "violated" for r in docv), "건진법")
docok = D.check_all(proj, [{"document": "품질관리계획서"}])
chk("품질관리계획서 제출시 적합", any(r["document"] == "품질관리계획서" and r["verdict"] == "compliant" for r in docok), "건진법")

print("\n" + "=" * 64)
print(f"규정 fidelity 스위트: {PASS}/{PASS+FAIL} 일치" + (f"  | {FAIL} 불일치" if FAIL else " — 전부 일치"))
if SKIP:
    print(f"자동생성 불가(별도 케이스 필요) {len(SKIP)}: {', '.join(SKIP)}")
sys.exit(1 if FAIL else 0)
