"""
유동적 모듈 조합 — project 프로파일에 따라 적용 모듈을 골라 union 그래프를 만든다.

  core_construction : 항상 (모든 건설공사)
  building_act      : contains_building==True 일 때만 (건축법 §2 건축물 포함)
  civil_facility    : 토목 시설 인허가 (현재 비어있음, gap)

각 모듈은 export_opencrab_pack.py 가 만든 독립 산출물. 여기선 선택·union 만 한다.
Usage: python compose.py examples/real_civil_internal_estimate.yaml
"""
from __future__ import annotations
import paths

import json
import os
import sys

import yaml

sys.stdout.reconfigure(encoding="utf-8")
BASE = paths.P("opencrab_pack", "modules")


def load_graph(mod):
    p = f"{BASE}/{mod}/graph/graph.json"
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"nodes": [], "edges": []}


def _gate(project, field, mod, on, off, unknown):
    v = project.get(field)
    if v is False:
        return None, off
    return mod, (on if v is True else unknown)


def select_modules(project: dict):
    sel = ["core_construction"]            # 모든 건설공사 공통
    notes = []
    b, nb = _gate(project, "contains_building", "building_act",
                  "contains_building=true → 건축물 축 포함", "contains_building=false → 건축법 축 제외",
                  "contains_building 미상 → 건축법 축 포함(판정보류)")
    notes.append(nb)
    if b:
        sel.append(b)
    c, nc = _gate(project, "contains_civil_facility", "civil_facility",
                  "contains_civil_facility=true → 토목시설 축 포함", "contains_civil_facility=false → 토목 축 제외",
                  "contains_civil_facility 미상 → 토목 축 포함(판정보류)")
    notes.append(nc)
    if c:
        sel.append(c)
    return sel, "; ".join(notes)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "examples/real_civil_internal_estimate.yaml"
    doc = yaml.safe_load(open(path, encoding="utf-8"))
    project = doc.get("project", doc)
    sel, gate_notes = select_modules(project)

    nodes, edges, seen = [], [], set()
    for m in sel:
        g = load_graph(m)
        for n in g["nodes"]:
            if n["node_id"] not in seen:
                seen.add(n["node_id"]); nodes.append(n)
        edges.extend(g["edges"])

    print("=" * 72)
    print(f"유동적 모듈 조합 — {project.get('name')}")
    print("=" * 72)
    print(f"게이트: {gate_notes}\n")
    print("선택 모듈:")
    for m in sel:
        man = f"{BASE}/{m}/manifest.yaml"
        meta = yaml.safe_load(open(man, encoding="utf-8")) if os.path.exists(man) else {}
        print(f"  ✓ {m:18} 요건 {meta.get('requirement_count', 0):2d}  ({meta.get('title','')})")
    reqs = [n for n in nodes if n["node_type"] == "LegalRequirement"]
    laws = sorted({n["properties"]["name"] for n in nodes if n["node_type"] == "Law"})
    dims = {}
    for n in reqs:
        dims[n["properties"]["dimension"]] = dims.get(n["properties"]["dimension"], 0) + 1
    print(f"\n조합 그래프: 노드 {len(nodes)} / 엣지 {len(edges)}")
    print(f"  적용 요건 {len(reqs)}건 — 차원별 {dims}")
    print(f"  관여 법 {len(laws)}: {', '.join(laws)}")

    out = paths.P("opencrab_pack", "composed_graph.json")
    json.dump({"nodes": nodes, "edges": edges}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n→ {out}  (saegim 런타임이 이 요건 집합에 대해 충족 판정 수행)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
