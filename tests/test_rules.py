"""
회귀 테스트 — 모든 rule × 모든 shape 의 판정이 기대대로 나오는지.
  python test_rules.py
파일 시나리오 + 인라인 케이스를 함께 검증. 실패 시 비0 종료.
"""
from __future__ import annotations

import sys
import yaml

from engine import evaluate as E

sys.stdout.reconfigure(encoding="utf-8")

CASES = [
    # (label, scenario_dict_or_path, rule_path, expected_verdict)
    ("안전 understaffed(해임공백)", "examples/scenario_understaffed.yaml", "placement_rules/safety_manager_staffing.yaml", "understaffed"),
    ("안전 compliant(해임없음)", "examples/scenario_compliant.yaml", "placement_rules/safety_manager_staffing.yaml", "compliant"),
    ("품질 understaffed(특급해임)", "examples/scenario_quality_understaffed.yaml", "placement_rules/quality_manager_staffing.yaml", "understaffed"),
    ("품질 unqualified(전원초급)", "examples/scenario_quality_unqualified.yaml", "placement_rules/quality_manager_staffing.yaml", "unqualified"),
    ("현장대리인 unqualified", "examples/scenario_site_agent_unqualified.yaml", "placement_rules/site_agent_placement.yaml", "unqualified"),
]

INLINE = [
    ("안전보건관리책임자 25억 미선임",
     {"project": {"name": "t", "contract_amount_krw": 2_500_000_000, "construction_end_date": "2027-01-01"},
      "appointed_managers": [], "incident": {"event_date": "2026-06-01"}},
     "placement_rules/safety_health_manager_in_charge.yaml", "understaffed"),
    ("안전보건관리책임자 15억 의무없음",
     {"project": {"name": "t", "contract_amount_krw": 1_500_000_000, "construction_end_date": "2027-01-01"},
      "appointed_managers": [], "incident": {"event_date": "2026-06-01"}},
     "placement_rules/safety_health_manager_in_charge.yaml", "not_required"),
    ("안전보건관리책임자 25억 선임됨",
     {"project": {"name": "t", "contract_amount_krw": 2_500_000_000, "construction_end_date": "2027-01-01"},
      "appointed_managers": [{"person": "소장", "start_date": "2025-01-01", "end_date": None}],
      "incident": {"event_date": "2026-06-01"}},
     "placement_rules/safety_health_manager_in_charge.yaml", "compliant"),
    ("조정자 분리3건 60억 미선임",
     {"project": {"name": "t", "split_order_count": 3, "combined_amount_krw": 6_000_000_000, "construction_end_date": "2027-01-01"},
      "appointed_managers": [], "incident": {"event_date": "2026-06-01"}},
     "placement_rules/safety_health_coordinator.yaml", "understaffed"),
    ("조정자 단일발주 의무없음",
     {"project": {"name": "t", "split_order_count": 1, "combined_amount_krw": 6_000_000_000, "construction_end_date": "2027-01-01"},
      "appointed_managers": [], "incident": {"event_date": "2026-06-01"}},
     "placement_rules/safety_health_coordinator.yaml", "not_required"),
    ("총괄책임자 25억 미선임",
     {"project": {"name": "t", "total_contract_amount_krw": 2_500_000_000, "construction_end_date": "2027-01-01"},
      "appointed_managers": [], "incident": {"event_date": "2026-06-01"}},
     "placement_rules/safety_health_supervisor_overall.yaml", "understaffed"),
    ("보건 2200억(요구2) 1명",
     {"project": {"name": "t", "contract_amount_krw": 220_000_000_000, "work_category": "일반",
                  "construction_start_date": "2025-01-01", "construction_end_date": "2028-01-01"},
      "appointed_managers": [{"person": "보건1", "start_date": "2025-01-01", "end_date": None}],
      "incident": {"event_date": "2026-06-01"}},
     "placement_rules/health_manager_staffing.yaml", "understaffed"),
    ("보건 500억 의무없음",
     {"project": {"name": "t", "contract_amount_krw": 50_000_000_000, "work_category": "일반",
                  "construction_start_date": "2025-01-01", "construction_end_date": "2028-01-01"},
      "appointed_managers": [], "incident": {"event_date": "2026-06-01"}},
     "placement_rules/health_manager_staffing.yaml", "not_required"),
    ("책임CM 민간 비해당",
     {"project": {"name": "t", "total_contract_amount_krw": 30_000_000_000, "is_public_client": False, "construction_end_date": "2027-01-01"},
      "appointed_managers": [], "incident": {"event_date": "2026-06-01"}},
     "placement_rules/cm_engineer_in_charge.yaml", "not_required"),
    ("책임CM 공공350억 특급배치",
     {"project": {"name": "t", "total_contract_amount_krw": 35_000_000_000, "is_public_client": True, "construction_end_date": "2027-01-01"},
      "appointed_managers": [{"person": "CM", "grade": "특급", "cm_experience_years": 2, "start_date": "2025-01-01", "end_date": None}],
      "incident": {"event_date": "2026-06-01"}},
     "placement_rules/cm_engineer_in_charge.yaml", "compliant"),
    ("공사감리 상주(8000㎡) 분야부족",
     {"project": {"name": "t", "gross_floor_area_m2": 8000, "construction_end_date": "2027-01-01"},
      "appointed_managers": [{"person": "감리", "field": "총괄", "start_date": "2025-01-01", "end_date": None},
                             {"person": "보1", "field": "건축", "start_date": "2025-01-01", "end_date": None}],
      "incident": {"event_date": "2026-06-01"}},
     "placement_rules/building_supervisor_placement.yaml", "understaffed"),
    ("공사감리 비상주(2000㎡) 감리자만 적정",
     {"project": {"name": "t", "gross_floor_area_m2": 2000, "construction_end_date": "2027-01-01"},
      "appointed_managers": [{"person": "감리", "field": "총괄", "start_date": "2025-01-01", "end_date": None}],
      "incident": {"event_date": "2026-06-01"}},
     "placement_rules/building_supervisor_placement.yaml", "compliant"),
    ("공사감리 상주 전분야 충족",
     {"project": {"name": "t", "gross_floor_area_m2": 8000, "construction_end_date": "2027-01-01"},
      "appointed_managers": [{"person": "감리", "field": "총괄", "start_date": "2025-01-01", "end_date": None},
                             {"person": "보1", "field": "건축", "start_date": "2025-01-01", "end_date": None},
                             {"person": "보2", "field": "토목", "start_date": "2025-01-01", "end_date": None},
                             {"person": "보3", "field": "전기", "start_date": "2025-01-01", "end_date": None},
                             {"person": "보4", "field": "기계", "start_date": "2025-01-01", "end_date": None}],
      "incident": {"event_date": "2026-06-01"}},
     "placement_rules/building_supervisor_placement.yaml", "compliant"),
]


def run_trail() -> int:
    """의사결정 트레일 — 권한 유효성 교차검증 회귀."""
    from engine import trail as T
    doc = yaml.safe_load(open("examples/trail_incident.yaml", encoding="utf-8"))
    r = T.build_trail(doc)
    invalid = [t for t in r["trail"] if not t["appointment_valid"]]
    fails = 0
    # 기대: 3건 결정, 그중 1건(9/15 시공검측 by 김감리) 권한 무효
    ok1 = len(r["trail"]) == 3
    ok2 = len(invalid) == 1 and invalid[0]["date"] == "2026-09-15"
    for label, ok in [("트레일 결정 3건 회수", ok1), ("권한무효 1건(9/15) 포착", ok2)]:
        fails += not ok
        print(f"{'✓' if ok else '✗ FAIL'} {label}")
    return fails


def run() -> int:
    fails = 0
    for label, scn, rule_path, expect in CASES:
        scenario = yaml.safe_load(open(scn, encoding="utf-8")) if isinstance(scn, str) else scn
        rule = yaml.safe_load(open(rule_path, encoding="utf-8"))
        got = E.evaluate(scenario, rule)["verdict"]
        ok = got == expect
        fails += not ok
        print(f"{'✓' if ok else '✗ FAIL'} {label:34s} expect={expect:13s} got={got}")
    for label, scn, rule_path, expect in INLINE:
        rule = yaml.safe_load(open(rule_path, encoding="utf-8"))
        got = E.evaluate(scn, rule)["verdict"]
        ok = got == expect
        fails += not ok
        print(f"{'✓' if ok else '✗ FAIL'} {label:34s} expect={expect:13s} got={got}")
    fails += run_trail()
    print(f"\n{'ALL PASS' if not fails else str(fails)+' FAILED'} — {len(CASES)+len(INLINE)} staffing + 2 trail cases")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(run())
