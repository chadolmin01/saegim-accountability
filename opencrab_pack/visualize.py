"""
civil_accountability 팩 그래프 → 인터랙티브 HTML.
nodes_edges.json 을 읽어 pyvis 로 시각화. space별 색(OpenCRAB 9-space 관례).
Usage: python opencrab_pack/visualize.py  → opencrab_pack/graph/graph.html
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from pyvis.network import Network

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
# 기본은 compose.py 가 만든 조합 그래프; 인자로 특정 모듈 graph.json 지정 가능
src = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "composed_graph.json"
G = json.load(open(src, encoding="utf-8"))

# node_type → 색/모양 (법 그래프 + 인스턴스 그래프 공용, 9-space 관례)
TYPE_STYLE = {
    "Law":              ("#6366f1", "diamond", 28),
    "LegalRequirement": ("#ef4444", "dot", 16),
    "FacilityClass":    ("#10b981", "box", 34),
    "Person":           ("#f59e0b", "dot", 22),     # subject
    "Appointment":      ("#fbbf24", "box", 16),
    "Decision":         ("#ef4444", "diamond", 20),  # decision
    "DesignDecision":   ("#f97316", "diamond", 22),
    "WorkRecord":       ("#3b82f6", "dot", 18),       # resource
    "BuildingComponent":("#10b981", "box", 18),       # concept
    "SiteContext":      ("#14b8a6", "box", 22),
    "ConstructionPhase":("#84cc16", "box", 16),
    "Incident":         ("#a855f7", "star", 30),      # outcome
}
REL_COLOR = {"governed_by": "#6366f1", "gated_by": "#10b981",
             "violates": "#ef4444", "responsible_for": "#a855f7", "caused_by": "#f472b6"}

net = Network(height="820px", width="100%", directed=True, bgcolor="#0f172a", font_color="#e2e8f0")
net.barnes_hut(gravity=-9000, spring_length=160)

for n in G["nodes"]:
    p, nt = n["properties"], n["node_type"]
    color, shape, size = TYPE_STYLE.get(nt, ("#94a3b8", "dot", 14))
    label = p.get("name") or p.get("title") or p.get("document") or p.get("requirement_id") or n["node_id"]
    tip = f"[{nt}] {n['node_id']}\n" + "\n".join(f"{k}: {v}" for k, v in list(p.items())[:8])
    net.add_node(n["node_id"], label=str(label)[:24], title=tip, color=color, shape=shape, size=size)

for e in G["edges"]:
    net.add_edge(e["from_id"], e["to_id"], label=e["relation"], title=e["relation"],
                 color=REL_COLOR.get(e["relation"], "#64748b"), arrows="to")

out = HERE / "graph.html"
net.write_html(str(out), notebook=False)
print(f"→ {out}")
print(f"노드 {len(G['nodes'])} / 엣지 {len(G['edges'])}")
