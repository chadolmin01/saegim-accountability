"""
instance_graph.json → OpenCRAB local 그래프(SQLite) 적재 + 순회 데모.

saegim 어댑터가 만든 인스턴스 그래프를 OpenCRAB local store 에 올려,
OpenCRAB 의 find_neighbors / find_path 로 책임체인을 '순회'한다.
(순회·저장은 OpenCRAB 담당 — 여기서 직접 traversal 코드 안 짬)

saegim types 는 OpenCRAB 스키마 미등록이라 store.upsert_node/upsert_edge 직접 호출(add_edge 버그·검증 우회).
Usage (saegim repo 에서): python load_to_opencrab.py
"""
from __future__ import annotations
import paths
import json, sys
from pathlib import Path

sys.path.insert(0, r"C:\project\OpenCrab")   # opencrab 패키지
sys.stdout.reconfigure(encoding="utf-8")

from opencrab.config import get_settings
from opencrab.stores.factory import make_graph_store
from opencrab.grammar.validator import validate_node, validate_edge   # 검증 정상 사용(우회 제거)

GRAPH = json.load(open(paths.P("opencrab_pack", "instance_graph.json"), encoding="utf-8"))
TYPE = {n["node_id"]: n["node_type"] for n in GRAPH["nodes"]}
SPACE = {n["node_id"]: n["space"] for n in GRAPH["nodes"]}


def main():
    g = make_graph_store(get_settings())
    print("스토어:", type(g).__name__)
    # 적재 — 그래마 검증 ON (saegim 타입·관계가 manifest 에 등록됨)
    nn = ne = errs = 0
    for n in GRAPH["nodes"]:
        validate_node(n["space"], n["node_type"]).raise_if_invalid()   # 노드 타입 검증
        g.upsert_node(n["node_type"], n["node_id"], n.get("properties", {}), space_id=n["space"])
        nn += 1
    for e in GRAPH["edges"]:
        fs, ts = SPACE.get(e["from_id"]), SPACE.get(e["to_id"])
        ft, tt = TYPE.get(e["from_id"], "Unknown"), TYPE.get(e["to_id"], "Unknown")
        try:
            validate_edge(fs, ts, e["relation"]).raise_if_invalid()    # 엣지 관계 검증(우회 X)
            if g.upsert_edge(ft, e["from_id"], e["relation"], tt, e["to_id"], e.get("properties", {})):
                ne += 1
        except Exception as exc:
            print(f"  [edge invalid] {e['from_id']}-{e['relation']}->{e['to_id']}: {exc}")
            errs += 1
    print(f"적재(검증 ON): 노드 {nn} / 엣지 {ne} / 검증실패 {errs}. DB 총 노드 {g.count_nodes()}")

    # ── OpenCRAB 순회로 책임 추적 ──
    print("\n── OpenCRAB find_neighbors(inc1) — 사고에 직접 연결된 노드 ──")
    for nb in g.find_neighbors("inc1", direction="both", depth=1, limit=20):
        print("  ", {k: nb.get(k) for k in ("node_id", "node_type", "relation") if k in nb} or nb)

    print("\n── responsible_for 엣지 (누가 사고 책임) ──")
    rows = g.run_cypher(
        "MATCH (p)-[r:responsible_for]->(i) RETURN p.id AS who, i.id AS incident") if hasattr(g, "run_cypher") else []
    for r in rows:
        print("  ", r)

    print("\n── find_path(설계자_김 → inc1) — 상류 책임 경로 ──")
    path = g.find_path("설계자_김", "inc1", max_depth=4)
    for step in path:
        print("  ", step)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
