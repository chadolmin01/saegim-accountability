"""
규정 fidelity 검증 — 업무지시/규정 조항이 "이래야 한다"고 말한 것을 시나리오로 만들고,
엔진 판정이 그 조항의 결론과 일치하는지 확인. (실사고 ground-truth 아님; 엔진↔규정 충실도)

각 케이스: 근거조항 → 시나리오(조항이 규정한 상황) → 엔진판정 vs 조항이 말한 기대값.
python regulation_check.py
"""
from __future__ import annotations
import sys
from engine import conditions as C
from engine import prerequisites as P
sys.stdout.reconfigure(encoding="utf-8")

PASS = 0
FAIL = 0


def show(clause, src, scenario_desc, engine_verdict, expected, ok):
    global PASS, FAIL
    PASS += ok; FAIL += not ok
    mark = "✓ 일치" if ok else "✗ 불일치"
    print(f"[{mark}] {clause}")
    print(f"    근거: {src}")
    print(f"    시나리오: {scenario_desc}")
    print(f"    엔진 판정: {engine_verdict}  |  조항 기대: {expected}\n")


def cond_v(rec, rid):
    return any(r["rule_id"].split("__")[0] == rid and r["verdict"] == "violated" for r in C.check_all(rec))

# ── 1. CM 업무수행지침: 검측 합격 없이 다음공정 불가 (입회점) ──
w = {"name": "타설", "work_kind": "콘크리트타설", "event_date": "2026-09-15", "component_ref": "c1"}
miss = P.check_all(w, [])  # 선행 검측 전무
v1 = any(r["verdict"] == "violated" for r in miss)
show("검측 합격 없이 타설하면 위반", "CM 업무수행지침(검측 입회점)·KCS 14 20 11",
     "철근배근·거푸집 검측 없이 콘크리트 타설", "선행요건 violated" if v1 else "compliant", "violated", v1)

# ── 2. CM 업무수행지침: 동일공정 시정지시 3회 미이행 → 중지 의무 ──
v2 = cond_v({"uncorrected_directive_count": 3, "applied_measures": []}, "corrective_order_escalation")
show("시정지시 3회 미이행+미중지는 위반", "CM 업무수행지침(시정지시 3회→부분중지)",
     "동일공정 시정지시 3회 미이행, 공사 계속 진행(미중지)", "violated" if v2 else "compliant", "violated", v2)

# ── 3. CM 업무수행지침 §99: 착공 전 안전관리계획 감리검토 선행 ──
doc3 = {"decisions": [{"name": "착공신고", "kind": "착공신고", "event_date": "2026-04-01"}]}
miss3 = P.check_all({}, doc3["decisions"])
v3 = any(r["rule_id"].startswith("safety_plan_review") and r["verdict"] == "violated" for r in miss3)
show("안전관리계획 감리검토 없는 착공은 위반", "CM 업무수행지침 §99",
     "안전관리계획 감리검토 없이 착공신고", "violated" if v3 else "compliant", "violated", v3)

# ── 4. 별표2/KCS 11 20 20: 노상 다짐도 ≥95% ──
v4 = cond_v({"work_kind": "다짐", "fill_layer": "노상", "test_values": {"compaction_degree_pct": 92}}, "compaction_degree")
show("노상 다짐도 92%는 위반(기준 95%)", "별표2 / KCS 11 20 20",
     "노상 다짐 현장밀도 92% 측정", "violated" if v4 else "compliant", "violated", v4)

# ── 5. KDS 14 20 52: 정착길이 확보 ≥ 요구 ──
v5 = cond_v({"work_kind": "철근배근", "test_values": {"devel_length_provided_mm": 450, "devel_length_required_mm": 500}}, "rebar_development_splice")
show("정착길이 확보<요구는 위반", "KDS 14 20 52",
     "확보 정착길이 450mm < 요구 500mm", "violated" if v5 else "compliant", "violated", v5)

# ── 6. (반대 케이스) 규정 충족 시 compliant 여야 ──
ok6 = not cond_v({"work_kind": "다짐", "fill_layer": "노상", "test_values": {"compaction_degree_pct": 96}}, "compaction_degree")
show("노상 다짐도 96%는 적합(위반 아님)", "별표2 / KCS 11 20 20",
     "노상 다짐 현장밀도 96% 측정", "compliant" if ok6 else "violated", "compliant", ok6)

print("=" * 60)
print(f"규정 fidelity: {PASS}/{PASS+FAIL} 일치 — 엔진 판정이 규정 조항 기대와 {'전부 일치' if not FAIL else str(FAIL)+'건 불일치'}")
sys.exit(1 if FAIL else 0)
