# civil_accountability — OpenCRAB 법정요건 지식그래프 팩 (모듈식)

saegim 판정엔진의 **법 지식**을 OpenCRAB 9-space 타입드 그래프로 환원(reify)한 팩.
monolith가 아니라 **적용범위별 독립 모듈**로 만들어 project 프로파일에 따라 유동적으로 조합한다.

## 두 계층

| | 이 팩 (OpenCRAB) | saegim 런타임 |
|---|---|---|
| 정체 | 타입 온톨로지 + 타입드 지식그래프 | 판정 엔진 |
| 담는 것 | "어느 법 → 어느 요건 → 어느 시설분류" (노드·엣지) | "이 현장이 그날 적법했나" (임계 비교·3-값·시점) |

임계값·트리거는 **노드 property(데이터)**. 충족 판정은 saegim 런타임이 수행.

## 모듈 (각개 산출물)

분석 결과 토목/건축은 두 평행 온톨로지가 아니라 **공통 코어 + 건축 확장** 구조 → 모듈로 분리가 자연스럽다.

| 모듈 | 게이트 | 요건 | 내용 |
|---|---|---|---|
| `core_construction` | 전체 | **47** | 건설공사 공통(건산법 §2). 작업조건 27·공통문서 11·공통배치 8·선행 1 |
| `building_act` | 건축물 | **9** | 건축법 §2 건축물 충족시. 건축허가 축 문서 8·건축감리 1 |
| `civil_facility` | 토목시설 | 0 | 도로법·하천법·국토계획법 — **미작성(gap)**, 다음 단계 |

각 모듈 = `modules/<m>/{manifest.yaml, graph/graph.json}` 독립 산출물.

## 유동적 조합

```
python export_opencrab_pack.py                 # 룰 → 모듈별 그래프 산출
python compose.py <project.yaml>               # 프로파일로 모듈 선택·union → composed_graph.json
python opencrab_pack/visualize.py              # composed_graph.json → graph.html
```

`contains_building` 으로 building_act 가 켜지고 꺼진다:

| 프로파일 | 선택 모듈 | 요건 | 관여 법 |
|---|---|---|---|
| 복합현장 (`contains_building: true`) | core + building_act + civil_facility | 56 | 22 |
| 순수 토목 (`contains_building: false`) | core + civil_facility | 47 | 18 |

→ 같은 모듈을 끼웠다 뺐다 하며 현장 성격에 맞는 요건 집합을 즉석 구성. 건축법·소방·승강기·건축물관리법 축이 토목에선 자동 제외된다.

## 핵심 축: 건축 vs 토목 게이트 (건축법 §2)

```
LegalRequirement ──governed_by──▶ Law (scope: 건축물전용 | 건설공사공통)
       └──gated_by──▶ FacilityClass { 건축물(지붕+기둥/벽+정착) / 토목시설 }
```
**진짜 토목/건축 차이는 둘뿐**: ① 건축전용 9건, ② 같은 요건의 트리거 변수(건축=연면적·층수 / 토목=부지·연장·시설등급). 요건의 존재 자체는 대부분 공통.

## 제약

타입드 그래프는 **OpenCRAB 로컬 빌더 전용**. SaaS MCP ingest는 RAG+키워드로 납작해진다 — 공개 시 로컬 빌더 + 이 HTML로 보여야 한다.
