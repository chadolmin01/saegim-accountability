"""작업조건(condition_rules) 회귀 테스트. python test_conditions.py"""
from __future__ import annotations
import sys
from engine import conditions as C
sys.stdout.reconfigure(encoding="utf-8")

CASES = [
    ("영하 타설 무조치", {"work_kind": "콘크리트타설", "daily_avg_temp_c": -2, "applied_measures": []}, ["cold_weather_concrete"]),
    ("30℃+강우5mm 무조치", {"work_kind": "콘크리트타설", "daily_avg_temp_c": 30, "rainfall_mm": 5, "applied_measures": []}, ["hot_weather_concrete", "rain_concrete_pour"]),
    ("염화물 0.5 초과", {"work_kind": "콘크리트타설", "daily_avg_temp_c": 15, "test_values": {"chloride_kg_m3": 0.5}}, ["concrete_chloride"]),
    ("공기량 2.0 미달", {"work_kind": "콘크리트타설", "daily_avg_temp_c": 15, "applied_measures": [], "test_values": {"air_pct": 2.0}}, ["concrete_air_ae"]),
    ("적정 타설(조치+범위내)", {"work_kind": "콘크리트타설", "daily_avg_temp_c": -2, "applied_measures": ["한중콘크리트_양생"], "test_values": {"air_pct": 4.5, "chloride_kg_m3": 0.2}}, []),
    ("순간풍속 18 양중", {"work_kind": "양중", "wind_speed_ms": 18}, ["wind_lifting_stoppage"]),
    ("풍속 12 고소", {"work_kind": "고소작업", "wind_speed_ms": 12}, ["wind_steelwork_stoppage"]),
    ("체감34 고소 무조치", {"work_kind": "고소작업", "apparent_temp_c": 34, "applied_measures": []}, ["heat_work_stoppage"]),
    ("밀폐 산소17+가스미측정", {"work_kind": "기타", "is_confined_space": True, "test_values": {"oxygen_pct": 17}}, ["confined_space_gas", "confined_space_oxygen"]),
    ("밀폐 정상(산소·가스 측정·범위내)", {"work_kind": "기타", "is_confined_space": True, "test_values": {"oxygen_pct": 20.5, "h2s_ppm": 2, "co_ppm": 5, "co2_pct": 0.3}}, []),
    ("거푸집존치 강도부족 슬래브", {"work_kind": "거푸집해체", "component_category": "슬래브", "test_values": {"strength_mpa": 10}}, ["formwork_striking_strength"]),
    ("굴착 모래 1:1.0 급경사", {"work_kind": "굴착", "soil_type": "모래", "slope_ratio_horizontal": 1.0}, ["excavation_slope"]),
    ("주 53시간 초과", {"weekly_work_hours": 53}, ["weekly_work_hours"]),
    ("체감36 무더위시간대 고소", {"work_kind": "고소작업", "apparent_temp_c": 36, "is_afternoon_peak": True}, ["heat_outdoor_stop", "heat_work_stoppage"]),
    ("비계 띠장 2.0m 초과", {"work_kind": "비계설치", "scaffold_post_spacing_ledger_m": 2.0, "scaffold_post_spacing_transverse_m": 1.4}, ["scaffold_post_spacing"]),
    ("동바리 4m 무연결재", {"work_kind": "거푸집설치", "shoring_height_m": 4.0, "applied_measures": []}, ["shoring_horizontal_tie"]),
    ("서중 타설온도 38℃ 초과", {"work_kind": "콘크리트타설", "daily_avg_temp_c": 28, "applied_measures": ["서중콘크리트_양생"], "test_values": {"pour_temp_c": 38}}, ["hot_weather_pour_temp"]),
    ("피복두께 기둥30 미달", {"work_kind": "철근배근", "component_category": "기둥", "cover_thickness_mm": 30}, ["rebar_cover_thickness"]),
    ("철근간격 편차30 초과", {"work_kind": "철근배근", "rebar_spacing_dev_mm": 30}, ["rebar_spacing_tolerance"]),
    ("SD400 항복380 미달", {"work_kind": "철근배근", "rebar_grade": "SD400", "test_values": {"yield_strength_mpa": 380}}, ["rebar_yield_strength"]),
    ("콘크리트 fck24 강도19 미달", {"work_kind": "콘크리트타설", "design_fck_mpa": 24, "test_values": {"strength_mpa": 19}}, ["concrete_strength_acceptance"]),
]


def run() -> int:
    fails = 0
    for label, rec, expect in CASES:
        viol = sorted(r["rule_id"].split("__")[0] for r in C.check_all(rec) if r["verdict"] == "violated")
        ok = viol == sorted(expect)
        fails += not ok
        print(f"{'✓' if ok else '✗ FAIL'} {label:28s} 위반={viol}")
    print(f"\n{'ALL PASS' if not fails else str(fails)+' FAILED'} — {len(CASES)} condition cases")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(run())
