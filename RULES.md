# 규칙 카탈로그 (자동생성: generate_rules_index.py)

saegim-accountability 의 전체 법정 판정 규칙. 각 규칙은 근거 법령(authority)을 가지며, 미검증은 pending 표기.

## 인적 배치 (rules/) — 11개

| rule_id | 제목 | 규제 | 근거 | pending |
|---|---|---|---|---|
| `building_supervisor_placement__bldg` | 건축법 공사감리자 배치 기준 | 건축법 | 제19조 (공사감리) | 2 |
| `cm_engineer_in_charge__citp` | 책임건설사업관리기술인 배치 기준 | 건설기술진흥법 | 별표 2 (건설사업관리기술인 배치기준 — 상주/기술지원 인원은 | 2 |
| `structural_engineer_collaboration__bldg` | 건축구조기술사 협력(관계전문기술자) 의무 배치 | 건축법 | 건축물의 구조기준 등에 관한 규칙 §58(6층↑ 건축구조기술사 | 1 |
| `facility_inspection_engineer__siteul` | 시설물 안전점검·정밀안전진단 책임기술자 배치 기준 | 시설물안전법 | 별표5 책임기술자 자격 — 점검종류별(시설등급별 아님). 20 | 2 |
| `health_manager_staffing__osha` | 건설업 보건관리자 선임 기준 | 산업안전보건법 | 별표 5 (보건관리자를 두어야 하는 사업의 종류·규모·인원), | 3 |
| `quality_manager_staffing__citp` | 건설공사 품질관리 건설기술인(품질관리자) 배치 기준 | 건설기술진흥법 | 별표 5 (건설공사 품질관리를 위한 시설 및 건설기술인의 배치 | 3 |
| `safety_health_coordinator__osha` | 안전보건조정자 선임 기준 | 산업안전보건법 | 제56조(선임)·제57조(업무)·제58조 | 1 |
| `safety_health_manager_in_charge__osha` | 안전보건관리책임자 선임 기준 | 산업안전보건법 | 별표 2 (안전보건관리책임자를 두어야 하는 사업의 종류·규모) | 1 |
| `safety_health_supervisor_overall__osha` | 안전보건총괄책임자 지정 기준 | 산업안전보건법 | 제52조 | 1 |
| `safety_manager_staffing__osha` | 건설업 안전관리자 선임 기준 | 산업안전보건법 | 별표 3 (안전관리자를 두어야 하는 사업의 종류 및 사업장의  | 2 |
| `site_agent_placement__cibc` | 건설공사 현장대리인(건설기술인) 배치 기준 | 건설산업기본법 | 별표 5 (건설기술인의 현장배치기준, 제35조) | 2 |

## 작업 조건 (condition_rules/) — 113개

| rule_id | 제목 | 규제 | 근거 | pending |
|---|---|---|---|---|
| `admixture_air_change__ksf2560` | 화학혼화제 공기량 변화량 합격 (고성능AE감수제) | KS F 2560 | KS F 2560:2019 표2 | 0 |
| `admixture_bleeding_ratio__ksf2560` | 화학혼화제 블리딩양의 비 합격 (종류별) | KS F 2560 | KS F 2560:2019 표2(요구성능) | 0 |
| `admixture_final_set_max__ksf2560` | 화학혼화제 응결 종결시간차 상한 (종류별) | KS F 2560 | KS F 2560:2019 표2(응결시간의 차) | 0 |
| `admixture_freeze_thaw__ksf2560` | 화학혼화제 동결융해 저항성 합격 (AE계) | KS F 2560 | KS F 2560:2019 표2 | 0 |
| `admixture_initial_set_max__ksf2560` | 화학혼화제 응결 초결시간차 상한 (종류별) | KS F 2560 | KS F 2560:2019 표2(응결시간의 차) | 0 |
| `admixture_length_change__ksf2560` | 화학혼화제 길이변화비 합격 (종류별) | KS F 2560 | KS F 2560:2019 표2(요구성능) | 0 |
| `admixture_slump_loss__ksf2560` | 화학혼화제 슬럼프 손실 합격 (고성능AE감수제) | KS F 2560 | KS F 2560:2019 표2 | 0 |
| `admixture_strength_ratio_28d__ksf2560` | 화학혼화제 압축강도비(28일) 합격 (종류별) | KS F 2560 | KS F 2560:2019 표2(요구성능) | 0 |
| `admixture_strength_ratio_3d__ksf2560` | 화학혼화제 압축강도비(3일) 합격 (종류별) | KS F 2560 | KS F 2560:2019 표2 | 0 |
| `admixture_strength_ratio_7d__ksf2560` | 화학혼화제 압축강도비(7일) 합격 (종류별) | KS F 2560 | KS F 2560:2019 표2 | 0 |
| `admixture_total_alkali__ksf2560` | 화학혼화제 전체 알칼리양 합격 | KS F 2560 | KS F 2560:2019 5.2(전체 알칼리양) | 0 |
| `admixture_water_reduction__ksf2560` | 화학혼화제 감수율 합격 (종류별) | KS F 2560 | KS F 2560:2019 표2(요구성능) | 0 |
| `aggregate_absorption__ksf2526` | 콘크리트용 골재 흡수율 합격 | KS F 2526 | KS F 2526(콘크리트용 골재) / 별표2 | 0 |
| `aggregate_la_abrasion__ksf2526` | 굵은골재 마모율(L.A.) 합격 | KS F 2526 | KS F 2526 / KS F 2508(마모) / 별표2 | 0 |
| `aggregate_max_size__kcs142010` | 굵은골재 최대치수(Gmax) 상한 (부재별) | KCS 표준시방서 | KCS 14 20 10(일반콘크리트) | 0 |
| `aggregate_soundness__ksf2526` | 콘크리트용 골재 안정성(황산나트륨 손실률) 합격 | KS F 2526 | KS F 2526 / 별표2 | 0 |
| `asphalt_compaction__kcs445010` | 아스팔트 포장 다짐도 합격 | KCS 표준시방서 | KCS 44 50 10:2023 / 건설공사 품질관리 업무지침 | 0 |
| `asphalt_flatness__kcs445010` | 아스팔트 포장 평탄성(PrI) 한도 | KCS 표준시방서 | KCS 44 50 10:2023 §3.5.13(2) (7.6m | 0 |
| `asphalt_marshall__ksf2337` | 아스팔트 혼합물 마샬 안정도·흐름·공극 합격 | KCS 표준시방서 | KCS 44 50 10:2023 표2.4-3·2.5-2 / K | 0 |
| `asphalt_thickness__kcs445010` | 아스팔트 포장 두께 허용오차 | KCS 표준시방서 | KCS 44 50 10:2023 §3.4.14(2) | 0 |
| `bored_pile_verticality__kcs245115` | 현장타설말뚝 공내 연직도·슬라임 검측 | KCS 표준시방서 | KCS 24 51 15 (현장타설콘크리트말뚝기초) / KCS  | 1 |
| `cbr_subgrade__ksf2320` | 노상·보조기층 CBR 합격 | KCS 표준시방서 | 건설공사 품질관리 업무지침 별표2 / KCS 44 50 05  | 1 |
| `cement_compressive_strength__ksl5201` | 포틀랜드 시멘트 압축강도(28일) 합격 (종류별) | KS L 5201 | KS L 5201(포틀랜드 시멘트) / 별표2 | 0 |
| `cold_weather_concrete__kcs` | 한중콘크리트 시공기준 적용 의무 | KCS 표준시방서 | KCS 14 20 40 | 0 |
| `cold_weather_fly_ash_limit__kcs142040` | 한중콘크리트 플라이애시 치환율 상한 (2024 개정) | KCS 표준시방서 | KCS 14 20 40:2024 | 0 |
| `cold_weather_slag_limit__kcs142040` | 한중콘크리트 고로슬래그 치환율 상한 (2024 개정) | KCS 표준시방서 | KCS 14 20 40:2024 | 0 |
| `compaction_degree__byeolpyo2` | 흙쌓기 다짐도(현장밀도) 층별 기준 | KCS 표준시방서 | 건설공사 품질관리 업무지침 별표2 / KCS 11 20 20  | 0 |
| `concrete_air_ae__ksf4009` | AE콘크리트 공기량 허용 범위 | KS F 4009 | KS F 4009 | 1 |
| `concrete_chloride__ksf4009` | 콘크리트 염화물량 허용 기준 | KS F 4009 | KS F 4009 | 0 |
| `concrete_core_strength__ksf2422` | 콘크리트 코어 강도 합격 (압축강도 불합격 시) | KCS 표준시방서 | KCS 14 20 10 / KS F 2422 (코어 채취·강도 | 0 |
| `concrete_flexural_strength__ksf2408` | 콘크리트 휨강도 합격 (도로포장) | KCS 표준시방서 | KCS 44 50 15 (시멘트콘크리트 포장) / KS F 2 | 0 |
| `concrete_mix_strength__kcs142010` | 콘크리트 배합강도 fcr 확보 (배합 ≥ 요구 fcr) | KCS 표준시방서 | KCS 14 20 10 §2.2 (배합강도) | 1 |
| `concrete_moist_curing_period__kcs142010` | 콘크리트 습윤양생 최소기간 (시멘트종류×기온) | KCS 표준시방서 | KCS 14 20 10 표3.4-1 (= 2016 콘크리트 표 | 0 |
| `concrete_slump_tolerance__ksf4009` | 콘크리트 슬럼프 허용오차 (지정값 대비) | KS F 4009 | KS F 4009 (레디믹스트 콘크리트) — 슬럼프 허용차 | 0 |
| `concrete_strength_acceptance__ksf4009` | 콘크리트 압축강도 합격 판정 (1회 0.85fck) | KS F 4009 | KS F 4009 / KS F 2405 | 1 |
| `concrete_test_frequency__kcs142010` | 콘크리트 품질시험 빈도 (타설량 대비) | KCS 표준시방서 | KCS 14 20 10 (콘크리트공사 표준시방서) / 건설공사 | 0 |
| `concrete_unit_water__kcs142010` | 콘크리트 단위수량 상한 | KCS 표준시방서 | KCS 14 20 10 / 건설공사 품질관리 업무지침 별표2  | 0 |
| `confined_space_gas__osha` | 밀폐공간 유해가스 농도 기준 | 산업안전보건기준에 관한 규칙 | 제619조 이하 | 1 |
| `confined_space_oxygen__osha` | 밀폐공간 산소농도·작업 전 측정 의무 | 산업안전보건기준에 관한 규칙 | 제619조 | 2 |
| `construction_noise__nvca` | 공사장 생활소음 규제기준 | 소음진동관리법 | 제21조 | 1 |
| `corrective_order_escalation__cmguide` | 시정지시 반복 미이행 시 공사중지 의무 | 건설사업관리 업무수행지침 | 건설공사 사업관리방식 검토기준 및 업무수행지침 (국토부고시) | 0 |
| `de_energized_work_protection__osha` | 정전작업 안전조치 의무 (전로 차단·잠금·검전·접지) | 산업안전보건기준에 관한 규칙 | 제319조(정전전로에서의 전기작업) | 0 |
| `demolition_safety_compliance__bam` | 해체작업자 안전조치 의무 (해체계획서 준수·붕괴예방·통행확보) | 건축물관리법 | 해체작업자는 ①승인된 해체계획서에 따라 해체 | 0 |
| `durability_exposure_fck__kds142040` | 내구성 노출등급별 최소 설계기준강도(fck) | KDS 설계기준 | KDS 14 20 40(콘크리트 내구성 설계) 표4.1-3 | 0 |
| `durability_exposure_wb__kds142040` | 내구성 노출등급별 물-결합재비(W/B) 상한 | KDS 설계기준 | KDS 14 20 40(콘크리트 내구성 설계) 표4.1-3 | 0 |
| `elcb_installation__osha` | 가설전기 누전차단기 설치 의무 | 산업안전보건기준에 관한 규칙 | 제304조 | 0 |
| `electrical_live_work_protection__osha` | 활선작업 감전방지 조치 의무 | 산업안전보건기준에 관한 규칙 | 제313~321조(충전전로 작업·전기작업) | 0 |
| `excavation_displacement__kosha` | 흙막이 수평변위 계측 관리기준 | KOSHA Guide | KOSHA C-103-2014 | 1 |
| `excavation_slope__osha` | 굴착 안전기울기 기준 | 산업안전보건기준에 관한 규칙 | 별표11 | 0 |
| `fall_protection__osha` | 추락방지 조치 의무 (2m 이상 작업) | 산업안전보건기준에 관한 규칙 | 제42~44조 | 0 |
| `fiber_aspect_ratio__kcs142022` | 강섬유보강 콘크리트 강섬유 형상비(L/D) | KCS 표준시방서 | KCS 14 20 22(섬유보강 콘크리트) | 0 |
| `fine_aggregate_chloride__ksf2526` | 잔골재 염화물(NaCl) 함유량 합격 | KS F 2526 | KS F 2526 / 별표2 | 0 |
| `fire_watch__osha` | 화기작업 화재감시자 배치 의무 | 산업안전보건기준에 관한 규칙 | 제241조의2 | 0 |
| `fly_ash_activity_index__ksl5405` | 플라이애시 활성도지수(28일) 합격 (종류별) | KS L 5405 | KS L 5405(플라이애시) / 별표2 | 0 |
| `fly_ash_loss_on_ignition__ksl5405` | 플라이애시 강열감량(LOI) 합격 (종류별) | KS L 5405 | KS L 5405(플라이애시) / 별표2 | 0 |
| `formwork_striking_strength__kcs` | 거푸집 해체(존치기간) 최소강도 기준 | KCS 표준시방서 | KCS 14 20 12 | 2 |
| `formwork_strip_age__kcs142012` | 거푸집 측면 존치 재령 기준 (강도시험 미실시) | KCS 표준시방서 | KCS 14 20 12 표3.3-2 | 0 |
| `foundation_bearing_pbt__ksf2444` | 확대기초 지내력 평판재하 합격 (측정 ≥ 설계지내력) | KS F 2444 | 건설공사 품질관리 업무지침 별표2 / KS F 2444 (얕은 | 0 |
| `guardrail_height__osha` | 안전난간 상부난간대 높이 기준 | 산업안전보건기준에 관한 규칙 | 제13조 | 0 |
| `heat_outdoor_stop__osha` | 체감온도 35℃ 무더위시간대 옥외작업 중지 | 산업안전보건기준에 관한 규칙 | 체감온도 35℃↑ 14~17시 옥외작업 중지 | 0 |
| `heat_work_stoppage__osha` | 폭염 체감온도 작업중지·휴식 의무 | 산업안전보건법(안전보건규칙) | 체감온도 31℃↑ 조치, 33℃↑ 매 2시간 | 2 |
| `high_strength_min_fck__kcs142033` | 고강도 콘크리트 최소 설계기준강도 (골재별) | KCS 표준시방서 | KCS 14 20 33(고강도 콘크리트) | 0 |
| `hot_weather_concrete__kcs` | 서중콘크리트 시공기준 적용 의무 | KCS 표준시방서 | KCS 14 20 44 | 2 |
| `hot_weather_pour_temp__kcs` | 서중콘크리트 타설온도 상한 | KCS 표준시방서 | KCS 14 20 44 | 0 |
| `insulation_conductivity__ksl9016` | 단열재 열전도율 등급 합격 | KS L 9016 | 건축물 에너지절약설계기준 별표2 / KS L 9016 (열전도 | 0 |
| `lightweight_concrete_unit_mass__kcs142020` | 경량골재 콘크리트 기건단위질량 상한 (종별) | KCS 표준시방서 | KCS 14 20 20(경량골재 콘크리트) | 0 |
| `marine_concrete_cover__kds142050` | 해양콘크리트 최소 피복두께 (노출등급별) | KDS 설계기준 | KDS 14 20 50(피복두께) / KDS 14 20 40( | 0 |
| `mass_concrete_thermal_crack_index__kcs142042` | 매스콘크리트 온도균열지수(Icr) 합격 | KCS 표준시방서 | KCS 14 20 42(매스콘크리트) | 0 |
| `pile_dynamic_integrity__ksf2591` | 말뚝 동재하·건전도 시험 빈도 (전체 1% 이상) | KS F 2591 | 건설공사 품질관리 업무지침 별표2 / KS F 2591 (동재 | 0 |
| `pile_static_load__ksf2445` | 말뚝 정재하시험 (설계하중 2배) | KS F 2445 | 건설공사 품질관리 업무지침 별표2 / KS F 2445 (말뚝 | 0 |
| `pile_steel_pipe_material__ksf4602` | 강관말뚝 재료 인장강도 합격 (강종별) | KS F 4602 | KS F 4602 (강관말뚝) | 0 |
| `plate_bearing_test__kcs112020` | 평판재하시험(PBT) 지지력계수 K30 층별 기준 | KCS 표준시방서 | 건설공사 품질관리 업무지침 별표2 / KCS 11 20 20  | 1 |
| `proof_rolling__roadspec` | 프루프롤링 소성변형 한도 (층별) | KCS 표준시방서 | 도로공사 표준시방서 / KCS 44 (포장 토공) | 1 |
| `ps_elongation_tolerance__kcs142053` | 프리스트레싱 신장량 허용오차 | KCS 표준시방서 | KCS 14 20 53 / LHCS 14 20 53:2020 | 0 |
| `ps_grout_bleeding__kcs142053` | PS 그라우트 블리딩률 합격 | KCS 표준시방서 | KCS 14 20 53 / KCI-PS102 | 0 |
| `ps_grout_expansion__kcs142053` | PS 그라우트 팽창률 합격 | KCS 표준시방서 | KCS 14 20 53 / KCI-PS102:2017 | 0 |
| `ps_grout_strength_28d__kcs142053` | PS 그라우트 28일 압축강도 합격 | KCS 표준시방서 | KCS 14 20 53 / KCI-PS102 | 0 |
| `ps_min_strength_at_tensioning__kcs142053` | 프리스트레싱 시 최소 콘크리트 압축강도 | KCS 표준시방서 | KCS 14 20 53(프리스트레스트 콘크리트) / LHCS  | 0 |
| `rain_concrete_pour__kcs` | 강우 시 콘크리트 타설 제한 | KCS 표준시방서 | KCS 14 20 00 | 1 |
| `rebar_bend_test__ksd3504` | 철근 굽힘시험 합격 (균열 없음) | KS D 3504 | KS D 3504 / KS B 0804 (굽힘시험방법) | 0 |
| `rebar_cover_thickness__kds` | 철근 피복두께 최소 기준 | KDS 설계기준 | KDS 14 20 50 | 2 |
| `rebar_development_splice__kds142052` | 철근 정착·이음 길이 확보 (확보 ≥ 요구) | KDS 설계기준 | KDS 14 20 52 (정착 및 이음) / KDS 14 20 | 1 |
| `rebar_elongation__ksd3504` | 철근 연신율 합격 (강종별) | KS D 3504 | KS D 3504 (철근콘크리트용 봉강) / KS B 0802 | 0 |
| `rebar_gas_pressure_weld__kcs142011` | 철근 가스압접 이음 검사 (외관·인장·초음파) | KCS 표준시방서 | KCS 14 20 11 (철근공사) / KS D 0244 (가 | 0 |
| `rebar_mechanical_splice__kcs142011` | 철근 기계적 이음 성능 (1급 인장·잔류변형) | KCS 표준시방서 | KCS 14 20 11 (2024.12 개정) / KDS 14 | 0 |
| `rebar_spacing_tolerance__kds` | 철근 배근 간격 허용오차 | KDS 설계기준 | KDS 14 20 50 | 2 |
| `rebar_tensile_ratio__ksd3504` | 철근 인장강도 합격 (항복 대비 배수, 강종별) | KS D 3504 | KS D 3504 (철근콘크리트용 봉강) / KS B 0802 | 0 |
| `rebar_welded_splice__kcs142011` | 철근 용접이음 검사 (인장·외관·초음파) | KCS 표준시방서 | KCS 14 20 11 / KS B 0896 (용접부 외관·초 | 0 |
| `rebar_yield_strength__ksd3504` | 철근 항복강도 강종별 합격 기준 | KS D 3504 | KS D 3504 | 1 |
| `recycled_aggregate_replacement__kcs142021` | 순환골재 치환율 상한 | KCS 표준시방서 | KCS 14 20 21(순환골재 콘크리트) / 순환골재 품질기 | 0 |
| `scaffold_post_spacing__osha` | 강관비계 기둥 간격 기준 | 산업안전보건기준에 관한 규칙 | 제60조 | 0 |
| `scc_box_filling__kcs142032` | 고유동 콘크리트 U형 충전성(충전높이) | KCS 표준시방서 | KCS 14 20 32(고유동 콘크리트) / KCI-CT 10 | 0 |
| `scc_slump_flow__kcs142032` | 고유동 콘크리트 슬럼프플로 합격 | KCS 표준시방서 | KCS 14 20 32(고유동 콘크리트) | 0 |
| `scc_t500__kcs142032` | 고유동 콘크리트 T500(슬럼프플로 500mm 도달시간) | KCS 표준시방서 | KCS 14 20 32(고유동 콘크리트) | 0 |
| `shoring_horizontal_tie__osha` | 동바리 수평연결재 설치 의무 | 산업안전보건기준에 관한 규칙 | 제332조의2 | 0 |
| `shotcrete_accelerator_set__kcs273000` | 숏크리트 급결제 응결시간 합격 | KCS 표준시방서 | KCS 27 30 00(터널 숏크리트):2023 | 0 |
| `shotcrete_bond_strength__kcs273000` | 숏크리트 부착강도(암반) 합격 | KCS 표준시방서 | KCS 27 30 00(터널 숏크리트):2023 / LHCS  | 0 |
| `shotcrete_early_strength_1d__kcs273000` | 숏크리트 초기강도(1일) 합격 | KCS 표준시방서 | KCS 27 30 00(터널 숏크리트):2023 | 0 |
| `shotcrete_layer_thickness__kcs273000` | 숏크리트 1회 타설 최대두께 | KCS 표준시방서 | KCS 27 30 00(터널 숏크리트):2023 | 0 |
| `shotcrete_rebound_rate__kcs273000` | 숏크리트 리바운드율 상한 (공법별) | KCS 표준시방서 | KCS 27 30 00(터널 숏크리트) | 0 |
| `shotcrete_strength_28d__kcs273000` | 숏크리트 28일 압축강도 합격 (등급별) | KCS 표준시방서 | KCS 27 30 00(터널 숏크리트):2023 | 0 |
| `slag_activity_index__ksf2563` | 고로슬래그 미분말 활성도지수(28일) 합격 (등급별) | KS F 2563 | KS F 2563(고로슬래그 미분말) / 별표2 | 0 |
| `steel_weld_inspection__byeolpyo2` | 강구조 용접부 검사 (외관·비파괴) | KCS 표준시방서 | 건설공사 품질관리 업무지침 별표2(철강구조물) / KS B 0 | 0 |
| `structural_steel_strength__ksd3503` | 구조강재 항복강도 합격 (강종별) | KS D 3503 | 건설공사 품질관리 업무지침 별표2 / KS D 3503(SS) | 1 |
| `thermal_transmittance_wall__energy` | 외벽 열관류율 지역별 한도 (외기직접) | 건축물 에너지절약설계기준 | 건축물 에너지절약설계기준 별표1 (국토부고시) | 1 |
| `tower_crane_work_plan__osha` | 타워크레인 설치·해체 작업계획서·작업지휘자 의무 | 산업안전보건기준에 관한 규칙 | 제38조(사전조사 및 작업계획서)·별표4 제1호 | 0 |
| `underwater_antiwashout_slump_flow__kcs142043` | 수중불분리성 콘크리트 슬럼프플로 합격 | KCS 표준시방서 | KCS 14 20 43(수중콘크리트) | 0 |
| `underwater_concrete_wb__kcs142043` | 수중콘크리트 W/B 상한 (환경별) | KCS 표준시방서 | KCS 14 20 43(수중콘크리트) / KCS 24 11 0 | 0 |
| `waterproof_ponding__kcs414001` | 방수 담수(누수)시험 합격 | KCS 표준시방서 | KCS 41 40 01:2021 §3.7.4(5) | 0 |
| `watertight_concrete_wb__kcs142030` | 수밀콘크리트 W/B 상한 | KCS 표준시방서 | KCS 14 20 30(수밀콘크리트) | 0 |
| `weekly_work_hours__lsa` | 주 52시간 근로시간 상한 | 근로기준법 | 제50조·제53조 | 1 |
| `wind_lifting_stoppage__osha` | 강풍 시 양중·타워크레인 작업중지 | 산업안전보건기준에 관한 규칙 | 제37조 | 1 |
| `wind_steelwork_stoppage__osha` | 강풍 시 철골·고소작업 중지 | 산업안전보건기준에 관한 규칙 | 제383조 | 0 |

## 선행요건 (prerequisite_rules/) — 8개

| rule_id | 제목 | 규제 | 근거 | pending |
|---|---|---|---|---|
| `commencement_after_permit__bldg` | 착공 전 인허가(건축허가/실시계획인가) 선행 의무 | 건축법 / 국토계획법 | 착공신고는 건축허가·신고(건축물) 또는 실시 | 0 |
| `concealment_after_mep_inspection__kcs` | 마감·은폐 전 설비(배관·배선)·방수 검측 선행 의무 | KCS 표준시방서 / 건설사업관리(감리) 업무수행지침 | KCS 31 기계설비 / KCS 31 65 전기설비 / KCS | 0 |
| `concrete_pour_holdpoints__kcs` | 콘크리트 타설 전 정지점(Hold Point) 검측 선행 의무 | KCS 표준시방서 / 사업관리방식 업무수행지침 | KCS 14 20 11/12 | 0 |
| `design_after_geotech_survey__citp` | 구조·기초 설계 전 지반조사 선행 의무 | 건설기술진흥법 / KCS | 별표7 현장특성분석(지반조건·지하수위) | 0 |
| `excavation_after_shoring__kcs` | 굴착 전 흙막이(지보공) 설치·검측 선행 의무 | KCS 표준시방서 / 산업안전보건기준에 관한 규칙 | KCS 11 10 15 흙막이공 | 0 |
| `safety_plan_review_before_commencement__cmguide` | 착공 전 안전관리계획서 감리 적정성검토 선행 의무 | 건설사업관리 업무수행지침 / 건설기술진흥법 | 건설사업관리기술인은 시공자 안전관리계획서를  | 0 |
| `structural_review_before_method_change__bldg` | 구조 영향 공법변경 전 건축구조기술사 검토·안전관리계획 변경승인 선행 | 건축법 / 건설기술진흥법 | 구조에 영향을 주는 공법·구조 변경은 건축구 | 0 |
| `usage_approval_after_completion__bldg` | 사용승인 전 감리완료보고·공종검측 선행 의무 | 건축법 | 제22조(사용승인) · 제25조(공사감리) | 0 |

## 문서 제출 (document_rules/) — 22개

| rule_id | 제목 | 규제 | 근거 | pending |
|---|---|---|---|---|
| `asbestos_survey__osha` | 기관석면조사 의무 | 산업안전보건법 | 제119조 | 0 |
| `building_fire_facility__fire` | 건축물 소방시설(스프링클러 등) 설치 의무 | 소방시설법 | 시행령 별표4 | 1 |
| `construction_commencement__bldg` | 착공신고(착공계) 제출 의무 | 건축법 | 제21조 | 0 |
| `demolition_plan__bmgt` | 건축물 해체계획서 제출 + 해체감리 배치 의무 | 건축물관리법 | 제30조·제31조 | 0 |
| `dust_emission_report__caca` | 비산먼지 발생사업 신고 의무 | 대기환경보전법 | 제43조 | 0 |
| `elevator_inspection__elsa` | 승강기 설치·정기검사 의무 | 승강기안전관리법 | 제31조·제32조 | 0 |
| `environmental_assessment__eia` | (소규모)환경영향평가 협의 의무 | 환경영향평가법 | 제43조·제59조 | 1 |
| `facility_safety_inspection__sfma` | 시설물 정기안전점검 의무 (시특법) | 시설물안전법 | 시행령 별표3 | 1 |
| `hazard_prevention_plan__osha` | 유해위험방지계획서 제출 의무 | 산업안전보건법 | 제42조 | 0 |
| `lifting_equipment_inspection__osha` | 양중기 안전검사(건설현장 6개월) 의무 | 산업안전보건법 | 시행규칙 제126조 | 0 |
| `quality_management_plan__citp` | 품질관리계획서/품질시험계획서 제출 의무 | 건설기술진흥법 | 제55조 | 0 |
| `rest_facility__osha` | 휴게시설 설치 의무 | 산업안전보건법 | 제128조의2 | 1 |
| `road_construction_permit__dorc` | 비도로관리청 도로공사 시행허가 | 도로법 | 제36조 | 0 |
| `road_occupancy_permit__dorr` | 도로점용허가 | 도로법 | 제61조 | 0 |
| `safety_cost_usage__osha` | 산업안전보건관리비 사용내역서 작성·보존 의무 | 산업안전보건법 | 제72조 | 0 |
| `safety_management_plan__citp` | 안전관리계획서 제출 의무 | 건설기술진흥법 | 제62조 | 0 |
| `serious_accident_safety_system__sapa` | 중대재해처벌법 안전보건관리체계 구축 의무 | 중대재해처벌법 | 제4조 | 0 |
| `structural_safety_confirmation__bldg` | 건축물 구조안전확인서 제출 의무 | 건축법 | 제48조·시행령 제32조 | 0 |
| `temp_fire_facility__fire` | 공사장 임시소방시설 설치 의무 | 소방시설법 | 시행령 제18조·별표8 | 0 |
| `urban_planning_facility_implementation_plan__nakp` | 도시·군계획시설사업 실시계획 인가 | 국토계획법 | 제88조 | 0 |
| `usage_approval__bldg` | 건축물 사용승인 의무 | 건축법 | 제22조 | 0 |
| `waste_disposal_plan__cwra` | 건설폐기물 처리계획서 제출 의무 | 건설폐기물재활용법 | 제17조 | 1 |

---
**총 154개 규칙** · 5개 책임 차원 (배치·권한·작업조건·선행요건·문서)