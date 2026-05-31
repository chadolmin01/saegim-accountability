"""
saegim 룰 → OpenCRAB typed 그래프, **모듈식 산출물**로 환원(reify).

monolith 대신 적용범위별 standalone 모듈로 분리해 유동적으로 조합한다.
  core_construction : 건설공사 공통(토목+건축 동일) — 작업조건·공통문서·공통배치·선행
  building_act      : 건축물 전용(건축법 §2 충족시) — 건축허가 축 문서·건축감리
  civil_facility    : 토목 시설법(도로법·하천법·국토계획법) — 현재 미작성(gap, 솔직 표기)

각 모듈 = 독립 산출물: modules/<m>/graph.json + manifest.yaml.
project 프로파일로 적용 모듈을 골라 union 하는 건 compose.py.
임계값·트리거는 노드 property(데이터). 충족 판정은 saegim 런타임.

Usage: python export_opencrab_pack.py
"""
from __future__ import annotations
import paths

import glob
import hashlib
import json
import os
import sys

import yaml

sys.stdout.reconfigure(encoding="utf-8")

RULE_DIRS = ["document_rules", "condition_rules", "prerequisite_rules", "placement_rules", "appropriateness_rules", "org_rules", "maintenance_rules"]
LAW_SCOPE = {
    "건축법": "건축물전용", "건축물관리법": "건축물전용",
    "승강기안전관리법": "건축물전용", "소방시설법": "건축물전용",
}  # 그 외 regime 은 건설공사공통
COMMON_BASIS = "건산법 §2: 건설공사 = 토목+건축+산업설비+조경+환경시설 → 토목 현장에도 적용"

FACILITY_CLASSES = {
    "건축물": {"class_id": "geonchukmul", "name": "건축물",
             "discriminator": "토지정착 + 지붕 + (기둥 또는 벽) 충족 (건축법 §2①2)",
             "legal_basis": "건축법 제2조제1항제2호", "governed_regime": "건축법"},
    "토목시설": {"class_id": "tomok_siseol", "name": "토목시설",
              "discriminator": "지붕+기둥/벽 불충족 — 교량·터널·도로·댐·옹벽 등 공작물",
              "legal_basis": "건축법 §2 미해당 → 개별 시설법", "governed_regime": "도로법·하천법·국토계획법 등"},
}
MODULES = {
    "core_construction": {"title": "건설공사 공통 요건", "gate": "전체",
                          "desc": "토목·건축 무관하게 모든 건설공사에 적용 (건산법 §2). 작업조건·공통 문서·공통 인적배치·선행요건."},
    "building_act": {"title": "건축물 전용 요건", "gate": "건축물",
                     "desc": "건축법 §2 건축물 충족 현장에만 적용. 건축허가 축 문서·건축 감리."},
    "civil_facility": {"title": "토목 시설법 요건", "gate": "토목시설",
                       "desc": "도로법·하천법·국토계획법 등 토목시설 인허가. 미작성(gap) — 다음 단계."},
}


def _refs(clause, acc):
    if isinstance(clause, str):
        acc.add(clause)
    elif isinstance(clause, dict):
        for k, v in clause.items():
            if k in ("any", "all"):
                for c in v:
                    _refs(c, acc)
            elif k not in ("measures_any", "measures_all", "value_bounds", "lookup_bounds", "ratio_bound"):
                acc.add(k.split("__")[0])
    return acc


def law_id(name):
    # 결정적 ID — Python hash()는 PYTHONHASHSEED로 run마다 달라져 그래프가 재현 불가·dangling 발생.
    return "law_" + hashlib.md5(name.encode("utf-8")).hexdigest()[:10]


def atomic_regimes(regime):
    # 복합 regime "건축법 / 건설기술진흥법" → ['건축법','건설기술진흥법'] (요건이 여러 법의 지배를 받음)
    parts = [a.strip() for a in str(regime).split("/") if a.strip()]
    return parts or ["미상"]


# 세부 라벨(또는 dir) → 5대 책임차원 정규화
DIM5 = {
    "문서·보고": "문서제출",
    "온도·기상": "작업조건", "재료": "작업조건", "공법": "작업조건", "작업환경": "작업조건",
    "환경": "작업조건", "기상·근로": "작업조건", "근로시간": "작업조건",
    "시공순서·선행요건": "선행요건",
}
DIR_DIM = {"document_rules": "문서제출", "rules": "인적배치",
           "condition_rules": "작업조건", "prerequisite_rules": "선행요건",
           "appropriateness_rules": "의사결정권한", "org_rules": "도급책임", "maintenance_rules": "유지관리"}


def requirement_node(r, src_dir):
    auth = r.get("authority", {}) or {}
    basis = " ".join(str(auth.get(k)) for k in ("law", "article", "related", "standard", "name") if auth.get(k))
    fields = sorted(_refs(r.get("required_when", {}), set()) | _refs(r.get("applicable_when", {}), set()))
    topic = r.get("dimension")                       # 세부 라벨 (온도·기상 등)
    dim5 = DIM5.get(topic) or DIR_DIM.get(src_dir, "문서제출")
    return {"space": "concept", "node_type": "LegalRequirement", "node_id": r["rule_id"],
            "properties": {
                "requirement_id": r["rule_id"], "document": r.get("document"),
                "dimension": dim5, "topic": topic or "", "regime": r.get("regime", "미상"),
                "facility_subtype": r.get("facility_subtype", ""),
                "applies_to_facility_class": r.get("applies_to_facility_class", "전체"),
                "trigger_summary": auth.get("rule", ""), "threshold_fields": ", ".join(fields),
                "submit_before": r.get("submit_before"), "submit_to": r.get("submit_to"),
                "legal_basis": basis.strip()}}


def build_modules():
    mods = {m: {"nodes": [], "edges": [], "laws": {}} for m in MODULES}
    for d in RULE_DIRS:
        for f in sorted(glob.glob(d + "/*.yaml")):
            r = yaml.safe_load(open(f, encoding="utf-8"))
            if "rule_id" not in r:
                continue
            gate = r.get("applies_to_facility_class", "전체")
            mod = {"건축물": "building_act", "토목시설": "civil_facility"}.get(gate, "core_construction")
            M = mods[mod]
            rid = r["rule_id"]
            M["nodes"].append(requirement_node(r, d))
            for regime in atomic_regimes(r.get("regime", "미상")):
                if regime not in M["laws"]:
                    lid = law_id(regime)
                    scope = LAW_SCOPE.get(regime, "건설공사공통")
                    M["laws"][regime] = lid
                    M["nodes"].append({"space": "concept", "node_type": "Law", "node_id": lid,
                                       "properties": {"law_id": lid, "name": regime, "scope": scope,
                                                      "authority_basis": COMMON_BASIS if scope == "건설공사공통" else ""}})
                M["edges"].append({"from_space": "concept", "from_type": "LegalRequirement", "from_id": rid,
                                   "relation": "governed_by", "to_space": "concept", "to_type": "Law",
                                   "to_id": M["laws"][regime]})
            targets = {"건축물": ["건축물"], "토목시설": ["토목시설"]}.get(gate, ["건축물", "토목시설"])
            for t in targets:
                M["edges"].append({"from_space": "concept", "from_type": "LegalRequirement", "from_id": rid,
                                   "relation": "gated_by", "to_space": "concept", "to_type": "FacilityClass",
                                   "to_id": FACILITY_CLASSES[t]["class_id"]})
    return mods


def main():
    mods = build_modules()
    base = paths.P("opencrab_pack", "modules")
    summary = []
    for name, meta in MODULES.items():
        d = f"{base}/{name}"
        os.makedirs(f"{d}/graph", exist_ok=True)
        M = mods.get(name, {"nodes": [], "edges": []})
        # 모듈별 그래프엔 자신이 게이트하는 FacilityClass 노드만 포함
        gate_targets = set()
        for e in M["edges"]:
            if e["relation"] == "gated_by":
                gate_targets.add(e["to_id"])
        fc_nodes = [{"space": "concept", "node_type": "FacilityClass", "node_id": v["class_id"], "properties": v}
                    for v in FACILITY_CLASSES.values() if v["class_id"] in gate_targets]
        graph = {"nodes": fc_nodes + M["nodes"], "edges": M["edges"]}
        json.dump(graph, open(f"{d}/graph/graph.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        reqs = [n for n in M["nodes"] if n["node_type"] == "LegalRequirement"]
        laws = sorted({n["properties"]["name"] for n in M["nodes"] if n["node_type"] == "Law"})
        manifest = {"module": name, "title": meta["title"], "gate": meta["gate"], "description": meta["desc"],
                    "requirement_count": len(reqs), "laws": laws,
                    "dimensions": sorted({n["properties"]["dimension"] for n in reqs})}
        yaml.safe_dump(manifest, open(f"{d}/manifest.yaml", "w", encoding="utf-8"), allow_unicode=True, sort_keys=False)
        summary.append((name, meta["gate"], len(reqs), len(M["edges"]), laws))

    print("모듈식 산출물 → opencrab_pack/modules/<module>/{graph/graph.json, manifest.yaml}\n")
    for name, gate, nr, ne, laws in summary:
        print(f"  [{name:18}] gate={gate:6} 요건 {nr:2d} / 엣지 {ne:3d}  법: {', '.join(laws) or '— (gap)'}")
    print("\n유동적 조합: python compose.py <project.yaml> 로 프로파일별 모듈 선택·union")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
