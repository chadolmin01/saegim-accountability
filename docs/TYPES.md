# civil-accountability — 타입 카탈로그

DESIGN.md 의 3원칙(시간 1급 / 결정별 법정책임 / rule이 심장)에 따라 책임추적에 **필요한 것만** 정의한다. 기존 토목 백과사전식 39 types 와 달리, 목표 B(건축물 책임추적)에서 실제 질의에 쓰이는 타입으로 한정.

판정 흐름:
```
사고(Incident) → 발생 장소·부재·시점 → 그 시점 그 현장의 결정·선임 → 법정 규칙 대조 → 판정(ComplianceFinding)
```

---

## 핵심 타입 (첫 slice: 안전관리자 선임 적정성에 바로 필요)

| 타입 | space | 역할 | 시간 속성 |
|---|---|---|---|
| **Project** | concept | 현장/공사 — 판정의 모(母)단위 | construction_start_date, construction_end_date |
| **Person** | subject | 개인 행위자 — 보유 자격 | — (자격 취득일 선택) |
| **Organization** | subject | 회사 — 도급단계 | — |
| **Appointment** | resource | 선임 — 누가·어떤역할·어느현장, 유효구간 | **start_date, end_date(nullable)** |
| **Incident** | evidence | 사고/하자 — audit 진입점 | **event_date** |
| **ComplianceFinding** | claim | 규칙 대조 판정 결과 | assessment_date |

## 축 타입 (DESIGN — 첫 slice는 얕게, 후속 확장; 공종축은 WorkRecord.work_kind enum)

| 타입 | space | 역할 | 시간 |
|---|---|---|---|
| **Location** | concept | 장소 트리 노드 (건물>층>실>부위), self-ref parent — **DORMANT**(평면 location_ref만 trail 매칭에 사용, 트리·계층 미순회·그래마 미등록) | — |
| **BuildingComponent** | concept | 부재 인스턴스 — "이 위치의 이 부재" (공종은 WorkRecord.work_kind enum) | event_date(설치/타설) |

## 결정 타입 (책임 anchor — 기존 재사용, 단 시간·장소·책임자 ref 보강)

| 타입 | space | 비고 |
|---|---|---|
| ConstructionInspectionDecision | decision | 검측 결정. event_date + targets(component) + accountable(person) |
| MaterialReceiptDecision | decision | 자재반입 |
| SafetyInspectionDecision | decision | 안전점검 |
| (기타 기존 결정 타입) | decision | 필요 시 동일 패턴으로 편입 |

> 기존 39 types 중 책임추적에 안 쓰이는 것(Drawing·Specification·TestReport·PrecisionDiagnosisDecision 등)과 OpenCRAB base noise(User·Team·Claim·Entity…)는 본 팩에서 제외.

---

## 관계 (meta-edges)

행위자 ↔ 조직 ↔ 선임:
- `Person —belongs_to→ Organization`
- `Organization —subcontracts_under→ Organization`  (도급단계, 옵션2 깊이. 무한 트리 X)
- `Person —holds→ Appointment`
- `Appointment —for_project→ Project`
- `Appointment —as_role→ (role enum: 안전관리자·책임감리원·현장대리인·…)`  ← 역할은 선임의 속성

결정 ↔ 장소·부재·책임:
- `Decision —performed_by→ Person`        (실행/책임 — RACI 구분은 relation 속성 role_in_decision)
- `Decision —targets→ BuildingComponent | Location`
- `Decision —based_on→ (문서/근거)`
- `Decision —at_project→ Project`
- `BuildingComponent —located_at→ Location`
- `Location —part_of→ Location`           (트리)

사고 ↔ 판정:
- `Incident —occurred_at→ Location`
- `Incident —on_component→ BuildingComponent`
- `Incident —at_project→ Project`
- `ComplianceFinding —evaluates→ Project`     (또는 Appointment 집합)
- `ComplianceFinding —against_rule→ (rule_id: rules/*.yaml)`
- `ComplianceFinding —triggered_by→ Incident`

---

## 첫 slice 에 실제 동원되는 최소 그래프

```
Incident(event_date=사고일, at_project→P)
P(Project: 공사금액, 착공·준공일)
  ← Appointment(role=안전관리자, start/end) ─holds─ Person(자격)
                                            ─for_project→ P
ComplianceFinding
  ─against_rule→ safety_manager_staffing__osha
  ─triggered_by→ Incident
  ─evaluates→ P
  = rule.evaluate(P.공사금액, P.착공·준공, Incident.event_date, [Appointment…])
    → compliant / understaffed / unqualified / not_required
```

장소·부재(Location/BuildingComponent)는 첫 slice 판정엔 직접 안 쓰임(현장 단위 판정). Location 트리/계층은 **dormant** — 활성 용도는 평면 location_ref를 trail.py 가 사고↔결정 매칭에 쓰는 것뿐. 계층 공간추적(부위별 시공검측 책임 후속 slice)은 *그걸 요구하는 실사고가 끌 때* 활성화(투기적 트리 빌드 금지 — 목표 견인 없는 schema-first=가짜).

---

## 갱신 (자율 세션) — 9 역할 직렬화 완료

### 역할 → rule 매핑 (Appointment.role → rules/*.yaml)

| Appointment.role | rule_id | requirement_shape |
|---|---|---|
| 안전관리자 | safety_manager_staffing__osha | simple_count |
| 보건관리자 | health_manager_staffing__osha | simple_count(+increment) |
| 안전보건관리책임자 | safety_health_manager_in_charge__osha | threshold_binary |
| 안전보건총괄책임자 | safety_health_supervisor_overall__osha | threshold_binary |
| 안전보건조정자 | safety_health_coordinator__osha | threshold_binary |
| 현장대리인 | site_agent_placement__cibc | qualification |
| 품질관리자 | quality_manager_staffing__citp | graded_slots |
| 책임건설사업관리기술인 | cm_engineer_in_charge__citp | qualification |
| 공사감리자 | building_supervisor_placement__bldg | field_slots |

audit.py 가 Appointment.role 로 선임을 그룹핑하여 각 rule 적용 → 현장 전체 일괄 감사.

### 축 타입 (DESIGN) — 작성 완료

- Location (장소 트리: building>floor>space>element, self-ref parent)
- BuildingComponent (부재 인스턴스 = Location × 공종(WorkRecord.work_kind) 교차점, event_date 보유)

첫 배치-적정성 slice 엔 직접 미사용. 부위별 시공검측 책임(후속 slice)의 기반.
