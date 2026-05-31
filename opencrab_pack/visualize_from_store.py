"""
OpenCRAB local 그래프(graph.db)에서 직접 읽어 사고 인스턴스 그래프 시각화.
= JSON 이 아니라 OpenCRAB 스토어가 가진 노드/엣지를 읽음(라운드트립 증명).
우리 사고 서브그래프(instance_graph.json 의 node_id)만 필터.
Usage (saegim repo): python opencrab_pack/visualize_from_store.py
"""
from __future__ import annotations
import json, sqlite3, sys
from pathlib import Path
from pyvis.network import Network

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
# 로더가 saegim cwd 기준 ./opencrab_data/graph.db 에 적재 (OpenCRAB LocalGraphStore)
DB = str(HERE.parent / "opencrab_data" / "graph.db")
IDS = {n["node_id"] for n in json.load(open(HERE / "instance_graph.json", encoding="utf-8"))["nodes"]}

TYPE_STYLE = {
    "Person": ("#f59e0b", "dot", 24), "Appointment": ("#fbbf24", "box", 16),
    "Decision": ("#ef4444", "diamond", 20), "DesignDecision": ("#f97316", "diamond", 22),
    "WorkRecord": ("#3b82f6", "dot", 18), "BuildingComponent": ("#10b981", "box", 18),
    "SiteContext": ("#14b8a6", "box", 22), "ConstructionPhase": ("#84cc16", "box", 16),
    "Incident": ("#a855f7", "star", 32), "LegalRequirement": ("#ef4444", "dot", 15),
}
REL_COLOR = {"violates": "#ef4444", "responsible_for": "#a855f7", "caused_by": "#f472b6",
             "performed_by": "#f59e0b", "in_phase": "#84cc16"}

con = sqlite3.connect(DB)
nodes = [r for r in con.execute("SELECT node_type,node_id,space_id,properties FROM graph_nodes") if r[1] in IDS]
edges = [r for r in con.execute("SELECT from_id,relation,to_id FROM graph_edges") if r[0] in IDS and r[2] in IDS]

net = Network(height="820px", width="100%", directed=True, bgcolor="#0f172a", font_color="#e2e8f0")
net.barnes_hut(gravity=-9000, spring_length=170)
for nt, nid, space, props in nodes:
    p = json.loads(props) if props else {}
    color, shape, size = TYPE_STYLE.get(nt, ("#94a3b8", "dot", 14))
    label = p.get("name") or p.get("title") or nid
    tip = f"[{nt} / {space}] {nid}\n" + "\n".join(f"{k}: {v}" for k, v in list(p.items())[:8])
    net.add_node(nid, label=str(label)[:24], title=tip, color=color, shape=shape, size=size)
for fid, rel, tid in edges:
    net.add_edge(fid, tid, label=rel, title=rel, color=REL_COLOR.get(rel, "#64748b"), arrows="to")

out = HERE / "instance_graph_from_store.html"
net.write_html(str(out), notebook=False)
print(f"→ {out}")
print(f"OpenCRAB 스토어에서 읽음: 노드 {len(nodes)} / 엣지 {len(edges)} (사고 서브그래프)")
print("관계:", {})
from collections import Counter
print("  ", dict(Counter(r[1] for r in edges)))
