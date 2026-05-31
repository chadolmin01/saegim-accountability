"""깊이 보강 회귀 — 등급표(구조기술사·시특법 책임기술자) + 신규 조건(정전·타워·활선). python test_depth.py"""
from __future__ import annotations
import sys, yaml
from engine import evaluate as E
from engine import conditions as C
sys.stdout.reconfigure(encoding="utf-8")

fails = 0
def chk(label, got, exp):
    global fails
    ok = got == exp
    fails += not ok
    print(f"{'✓' if ok else '✗ FAIL'} {label}: {got}" + ("" if ok else f" (기대 {exp})"))

DSG = yaml.safe_load(open("placement_rules/designer_structural_engineer.yaml", encoding="utf-8"))
FAC = yaml.safe_load(open("placement_rules/facility_inspection_engineer.yaml", encoding="utf-8"))
def q(rule, proj, mgr):
    sc = {"project": dict(proj, assessment_date="2026-05-01", construction_end_date="2026-12-01"),
          "appointed_managers": mgr}
    return E.eval_qualification(sc, rule)["verdict"]

# 건축구조기술사 협력 (건축법 시행령 §91의3)
chk("구조기술사 6층·건축사만", q(DSG, {"floor_count": 6}, [{"person": "김", "license": "건축사", "start_date": "2026-01-01"}]), "unqualified")
chk("구조기술사 6층·구조기술사", q(DSG, {"floor_count": 6}, [{"person": "이", "license": "건축구조기술사", "start_date": "2026-01-01"}]), "compliant")
chk("구조기술사 특수구조·구조기술사", q(DSG, {"is_special_structure": True}, [{"person": "이", "license": "건축구조기술사", "start_date": "2026-01-01"}]), "compliant")
chk("구조기술사 3층 비대상", q(DSG, {"floor_count": 3}, []), "not_required")

# 시특법 책임기술자 (별표5, 점검종류별)
chk("시특법 1·2종·중급", q(FAC, {"is_facility_grade_1_or_2": True}, [{"person": "박", "grade": "중급", "start_date": "2026-01-01"}]), "compliant")
chk("시특법 1·2종·초급", q(FAC, {"is_facility_grade_1_or_2": True}, [{"person": "정", "grade": "초급", "start_date": "2026-01-01"}]), "unqualified")
chk("시특법 비대상", q(FAC, {}, []), "not_required")

# 신규 조건 (정전·타워크레인·활선)
def cviol(rec):
    return sorted(r["rule_id"].split("__")[0] for r in C.check_all(rec) if r["verdict"] == "violated")
chk("정전작업 무조치", cviol({"work_kind": "정전작업", "applied_measures": []}), ["de_energized_work_protection"])
chk("정전작업 6조치", cviol({"work_kind": "정전작업", "applied_measures": ["전원차단확인", "단로기개방확인", "잠금장치_꼬리표", "잔류전하방전", "검전확인", "단락접지"]}), [])
chk("타워크레인 설치 무계획", cviol({"work_kind": "양중", "is_tower_crane_erection": True, "applied_measures": []}), ["tower_crane_work_plan"])
chk("활선작업 무조치", cviol({"work_kind": "활선작업", "applied_measures": []}), ["electrical_live_work_protection"])
# 슬럼프 허용오차 (KS F 4009) · 시험빈도 (KCS 120㎥)
chk("슬럼프 지정120 측정150(편차30>±25)", "concrete_slump_tolerance" in cviol({"work_kind": "콘크리트타설", "spec_slump_mm": 120, "test_values": {"slump_mm": 150}}), True)
chk("슬럼프 지정120 측정130(편차10≤±25)", "concrete_slump_tolerance" in cviol({"work_kind": "콘크리트타설", "spec_slump_mm": 120, "test_values": {"slump_mm": 130}}), False)
chk("시험빈도 300㎥ 2회(<3)", "concrete_test_frequency" in cviol({"work_kind": "콘크리트타설", "pour_volume_m3": 300, "strength_tests_count": 2}), True)
chk("시험빈도 300㎥ 3회(=3)", "concrete_test_frequency" in cviol({"work_kind": "콘크리트타설", "pour_volume_m3": 300, "strength_tests_count": 3}), False)
# 별표2 battery 우선순위 룰
chk("가스압접 편심0.3(>d/5)", "rebar_gas_pressure_weld" in cviol({"work_kind": "철근이음", "test_values": {"bulge_dia_ratio": 1.5, "bulge_len_ratio": 1.3, "eccentricity_ratio": 0.3, "tensile_yield_ratio": 1.3}}), True)
chk("기계적이음 잔류0.2(>0.1)", "rebar_mechanical_splice" in cviol({"work_kind": "철근이음", "test_values": {"mech_residual_def_mm": 0.2, "tensile_yield_ratio": 1.4}}), True)
chk("다짐 노상92%(<95)", "compaction_degree" in cviol({"work_kind": "다짐", "fill_layer": "노상", "test_values": {"compaction_degree_pct": 92}}), True)
chk("다짐 노체92%(≥90)", "compaction_degree" in cviol({"work_kind": "다짐", "fill_layer": "노체", "test_values": {"compaction_degree_pct": 92}}), False)
chk("말뚝 정재하1.5배(<2)", "pile_static_load" in cviol({"work_kind": "말뚝", "test_values": {"test_load_kn": 1500, "design_load_kn": 1000}}), True)
chk("말뚝 동재하 200본1회(<2)", "pile_dynamic_integrity" in cviol({"work_kind": "말뚝", "pile_count": 200, "dynamic_test_count": 1}), True)
chk("단위수량 190(>185)", "concrete_unit_water" in cviol({"work_kind": "콘크리트타설", "test_values": {"unit_water_kg_m3": 190}}), True)
chk("코어 평균0.82(<0.85)", "concrete_core_strength" in cviol({"work_kind": "콘크리트타설", "test_values": {"core_avg_ratio": 0.82, "core_min_ratio": 0.78}}), True)
chk("인장 SD400 배수1.05(<1.08)", "rebar_tensile_ratio" in cviol({"work_kind": "철근배근", "rebar_grade": "SD400", "test_values": {"tensile_ratio": 1.05}}), True)
chk("인장 SD400S 배수1.2(<1.25)", "rebar_tensile_ratio" in cviol({"work_kind": "철근배근", "rebar_grade": "SD400S", "test_values": {"tensile_ratio": 1.2}}), True)
chk("연신 SD500 10%(<12)", "rebar_elongation" in cviol({"work_kind": "철근배근", "rebar_grade": "SD500", "test_values": {"elongation_pct": 10}}), True)
# wave3: 정착이음·굽힘·용접·휨·CBR·강관말뚝·연직도·K30
chk("정착길이 0.9배(<요구)", "rebar_development_splice" in cviol({"work_kind": "철근배근", "test_values": {"devel_length_provided_mm": 450, "devel_length_required_mm": 500}}), True)
chk("굽힘 균열(미조치)", "rebar_bend_test" in cviol({"work_kind": "철근배근", "test_values": {"bend_tested": True}, "applied_measures": []}), True)
chk("용접이음 1.2배(<1.25)", "rebar_welded_splice" in cviol({"work_kind": "철근이음", "test_values": {"weld_tensile_yield_ratio": 1.2}}), True)
chk("휨강도 4.0(<4.5)", "concrete_flexural_strength" in cviol({"work_kind": "콘크리트타설", "test_values": {"flexural_strength_mpa": 4.0}}), True)
chk("CBR 노상8(<10)", "cbr_subgrade" in cviol({"work_kind": "다짐", "fill_layer": "노상", "test_values": {"cbr_value": 8}}), True)
chk("강관말뚝 SKK490 450(<490)", "pile_steel_pipe_material" in cviol({"work_kind": "말뚝", "pile_steel_grade": "SKK490", "test_values": {"pile_tensile_mpa": 450}}), True)
chk("연직도 1/80(>1/100)", "bored_pile_verticality" in cviol({"work_kind": "말뚝", "test_values": {"verticality_ratio": 0.0125}}), True)
chk("K30 노상180(<196.1)", "plate_bearing_test" in cviol({"work_kind": "다짐", "fill_layer": "노상", "test_values": {"k30_value": 180}}), True)
# wave4: 프루프롤링·지내력·배합강도
chk("프루프롤링 노상6(>5)", "proof_rolling" in cviol({"work_kind": "다짐", "fill_layer": "노상", "test_values": {"rut_depth_mm": 6}}), True)
chk("지내력 180(<설계200)", "foundation_bearing_pbt" in cviol({"work_kind": "굴착", "test_values": {"bearing_capacity_kpa": 180, "design_bearing_kpa": 200}}), True)
chk("배합강도 26(<요구30)", "concrete_mix_strength" in cviol({"work_kind": "콘크리트타설", "test_values": {"mix_design_strength_mpa": 26, "required_fcr_mpa": 30}}), True)
# wave5: 강구조·아스팔트포장·방수단열
chk("강재 SM355 항복340(<355)", "structural_steel_strength" in cviol({"work_kind": "강구조", "steel_grade": "SM355", "test_values": {"yield_strength_mpa": 340}}), True)
chk("용접검사 미실시", "steel_weld_inspection" in cviol({"work_kind": "강구조", "test_values": {"weld_inspected": True}, "applied_measures": []}), True)
chk("아스팔트 다짐 94%(<96)", "asphalt_compaction" in cviol({"work_kind": "포장", "test_values": {"compaction_pct": 94}}), True)
chk("마샬 안정도 7000(<7500)", "asphalt_marshall" in cviol({"work_kind": "포장", "test_values": {"marshall_stability_n": 7000, "flow_value_001cm": 30, "air_void_pct": 4}}), True)
chk("평탄성 일반 120(>100)", "asphalt_flatness" in cviol({"work_kind": "포장", "road_class": "일반", "test_values": {"pri_mm_km": 120}}), True)
chk("담수 미실시", "waterproof_ponding" in cviol({"work_kind": "방수", "test_values": {"ponding_tested": True}, "applied_measures": []}), True)
chk("단열 나등급 0.042(>0.040)", "insulation_conductivity" in cviol({"work_kind": "단열", "insulation_grade": "나", "test_values": {"conductivity_w_mk": 0.042}}), True)
chk("외벽U 중부2 0.30(>0.24)", "thermal_transmittance_wall" in cviol({"work_kind": "단열", "climate_region": "중부2", "test_values": {"u_value_w_m2k": 0.30}}), True)
chk("시정지시 3회 미이행+미중지", "corrective_order_escalation" in cviol({"uncorrected_directive_count": 3, "applied_measures": []}), True)

print(f"\n{'ALL PASS' if not fails else str(fails)+' FAILED'} — depth 보강 회귀")
sys.exit(1 if fails else 0)
