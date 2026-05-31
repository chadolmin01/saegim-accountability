# 현장 문서 → saegim 입력 스키마 매핑

표준 현장 문서(시공일지·검측체크리스트 등)의 필드를 saegim typed 입력으로 옮기는 규칙이다. 두 축으로 나눈다:

- **양식(필드 구조)** — 표준 문서의 필드 구조를 그대로 따른다.
- **수치(합격기준)** — 권위 있는 공개 표준(KS·KDS·KCS 등)에서 재검증한 값만 쓰고, 출처가 불확실한 값은 채택하지 않는다.

향후 ingestion 변환기가 이 매핑을 따라 현장 문서 텍스트를 typed JSON 으로 옮긴다.

## 1. 시공일지 양식 → WorkRecord + appointments

| 시공일지 필드 | saegim | 판정 차원 |
|---|---|---|
| 일자 | WorkRecord.event_date | (전 차원 시점 기준) |
| 날씨/최고·최저기온 | daily_avg_temp_c, daily_max_temp_c | 작업조건 (한중/서중) |
| 강수량 mm | rainfall_mm | 작업조건 (강우 타설) |
| 풍속 m/s | wind_speed_ms | 작업조건 (강풍) |
| 작업가능시간대 | (참고) | — |
| 작업자 직종·인원·자격증 | appointments[] (role·qualification) | 인적배치 |
| 시공사·감리단 | Organization (org_role) | 책임귀속 |
| 공종/부위 | work_kind, component_ref/location_ref | 선행요건·조건 |

## 2. 검측체크리스트(콘크리트타설) → Decision + WorkRecord.test_values

| 체크리스트 항목 | saegim | 판정 |
|---|---|---|
| 머리행(검측일자·공종·위치·공사량) | Decision(kind=시공검측, event_date, target) | 의사결정 권한 |
| 검측자(감리) | Decision.performed_by_ref·via_role | 권한 유효성 교차검증 |
| 항목 거푸집 수직도 ±3mm | Decision(checkpoint=거푸집검측, result) | 선행요건 Hold Point |
| 항목 철근배근(간격·피복·정착) | Decision(checkpoint=철근배근검측, result) | 선행요건 + 검측 합격기준 |
| 슬럼프/공기량/온도/염화물 (KS F 2402/4009) | WorkRecord.test_values{slump_mm,air_pct,chloride_kg_m3} | 작업조건(재료) |
| 적합/부적합 + 측정값 | result(합격/불합격) + 수치 | 판정 |

## 3. 검측체크리스트(철근) 합격기준 → 검측 condition rule

검측체크리스트가 명시한 합격기준(설계도서 + KDS 인용)을 condition rule 로 직렬화:
- 피복두께: 기초 80 / 기둥·보 40 / 슬래브 20 mm (부재별)
- 철근 간격: 설계 ±20mm (KDS 14 20 50)

→ `condition_rules/rebar_cover_thickness.yaml`, `rebar_spacing_tolerance.yaml`

## 자재 합격기준(수치)의 출처 원칙

- 자재 합격기준 수치는 **권위 출처(e나라 표준인증·KATS·ASTM 등)에서 재검증한 값만** 쓴다. 출처가 불확실하거나 구버전(예: SD400 인장강도 560 — 2016 개정 전 값)인 수치는 채택하지 않는다.
- 재료 적합성은 재료 condition rule(concrete_chloride·concrete_air_ae·hot_weather_pour_temp 등)로 판정한다.
- 설계 규격(부재별 fck·철근규격)은 Drawing/Specification → BuildingComponent.material_summary 로 들어오며, 검측 측정값을 그 설계값과 대조하는 것이 재료 적합성의 마지막 차원(미구현).

## 미구현 (다음 단계)
- 변환기: 시공일지/검측서 텍스트 → 위 매핑대로 typed JSON 자동 추출
- 설계 규격 대조: Drawing/Specification ↔ 검측 측정값
