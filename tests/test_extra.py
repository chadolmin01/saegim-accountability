"""문서제출·선행요건 차원 회귀. python test_extra.py"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
from engine import documents as D
from engine import prerequisites as P

fails = 0

# --- documents ---
def doc_viol(project, submitted):
    return sorted(r["document"] for r in D.check_all(project, submitted) if r["verdict"] == "violated")

cases_doc = [
    ("지하12m·25층 안전계획만제출",
     {"excavation_depth_m": 12, "floor_count": 25, "building_height_m": 95, "gross_floor_area_m2": 38000,
      "total_contract_amount_krw": 85000000000, "is_multiuse_building": True, "is_special_use_building": True,
      "is_building_permit_target": True, "contains_building": True},
     [{"document": "안전관리계획서"}],
     # 정기안전점검결과서(시특법 유지단계) 제외 — 시공 중 건물엔 비적용(lifecycle_stage 게이트가 false positive 제거)
     ["건설폐기물처리계획서", "구조안전확인서", "비산먼지발생사업신고서", "산업안전보건관리비_사용내역서", "소방시설_준공", "안전보건관리체계", "유해위험방지계획서", "임시소방시설", "착공신고서", "품질관리계획서", "휴게시설"]),
    ("소규모 5억 건축(660㎡미만)",
     {"floor_count": 2, "gross_floor_area_m2": 500, "total_contract_amount_krw": 500000000, "is_building_permit_target": True, "contains_building": True},
     [{"document": "착공신고서"}],
     []),  # 착공만 대상이고 제출됨 → 위반 0 (단 산안관리비 4천만↑면 대상). 500000000>=40000000 → 산안관리비 대상
]
# 두번째 케이스는 산안관리비 대상(5억>4천만)이므로 미제출 1건 기대로 보정
cases_doc[1] = (cases_doc[1][0], cases_doc[1][1], cases_doc[1][2], ["구조안전확인서", "산업안전보건관리비_사용내역서"])

for label, proj, sub, expect in cases_doc:
    got = doc_viol(proj, sub)
    ok = got == sorted(expect)
    fails += not ok
    print(f"{'✓' if ok else '✗ FAIL'} [문서] {label}: {got}")

# --- prerequisites ---
def prereq_viol(work, decisions):
    return [r for r in P.check_all(work, decisions) if r["verdict"] == "violated"]

w = {"name": "타설", "work_kind": "콘크리트타설", "event_date": "2026-09-15", "component_ref": "c1"}
miss = prereq_viol(w, [{"kind": "시공검측", "checkpoint": "거푸집검측", "result": "합격", "event_date": "2026-09-14", "target_component_ref": "c1"}])
ok = len(miss) == 1 and miss[0]["missing_holdpoints"] == ["철근배근검측"]
fails += not ok
print(f"{'✓' if ok else '✗ FAIL'} [선행] 철근검측 누락 → {miss[0]['missing_holdpoints'] if miss else '없음'}")

full = prereq_viol(w, [
    {"kind": "시공검측", "checkpoint": "거푸집검측", "result": "합격", "event_date": "2026-09-14", "target_component_ref": "c1"},
    {"kind": "시공검측", "checkpoint": "철근배근검측", "result": "합격", "event_date": "2026-09-13", "target_component_ref": "c1"},
])
ok2 = len(full) == 0
fails += not ok2
print(f"{'✓' if ok2 else '✗ FAIL'} [선행] 둘다 선행 → 위반 {len(full)}")

print(f"\n{'ALL PASS' if not fails else str(fails)+' FAILED'}")
sys.exit(1 if fails else 0)
