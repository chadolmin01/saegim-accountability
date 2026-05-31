"""
온톨로지 팩 완결성 게이트 — export 산출물이 룰 소스와 정합하는지 결정적으로 검사.

검사 불변식(invariant):
  INV1  rule yaml(rule_id 보유) 수 == 전 모듈 LegalRequirement 노드 수 (1:1 reify)
  INV2  rule_id 전부 존재·유일
  INV3  각 모듈 graph + composed_graph 에 dangling 엣지 0 (모든 from/to_id 가 노드)
  INV4  Law 노드 ID 결정적 == md5(name)[:10] (PYTHONHASHSEED 무관 재현성)
  INV5  Law 노드명 atomic (복합 'A / B' 잔존 0)
  INV6  LegalRequirement 노드 property ⊆ 스키마 정의 + dimension ∈ enum
  INV7  composed 요건 차원분포 == 룰 디렉토리 개수

권위 게이트가 아니라 *구조 정합* 게이트 — 규정 충실도는 fidelity_suite, 사실대조는 ground-truth 가 담당.
Usage: python opencrab_pack/check_pack_completeness.py   (saegim repo 루트에서)
"""
from __future__ import annotations

import glob
import hashlib
import json
import sys

import yaml

sys.stdout.reconfigure(encoding="utf-8")

RULE_DIRS = ["placement_rules", "condition_rules", "document_rules", "prerequisite_rules", "appropriateness_rules", "org_rules", "maintenance_rules"]
DIR_DIM = {"document_rules": "문서제출", "placement_rules": "인적배치", "condition_rules": "작업조건",
           "prerequisite_rules": "선행요건", "appropriateness_rules": "의사결정권한", "org_rules": "도급책임", "maintenance_rules": "유지관리"}
MODULES = ["core_construction", "building_act", "civil_facility"]
PACK = "opencrab_pack"


def _load(p):
    return json.load(open(p, encoding="utf-8"))


def _module_graph(m):
    return _load(f"{PACK}/modules/{m}/graph/graph.json")


def main():
    fails = []

    def check(cond, ok, bad):
        (print(f"  ✓ {ok}") if cond else (fails.append(bad), print(f"  ✗ {bad}")))

    # 룰 소스 스캔
    rule_files = sorted(f for d in RULE_DIRS for f in glob.glob(d + "/*.yaml"))
    rules, dir_of, ids = [], {}, []
    for f in rule_files:
        r = yaml.safe_load(open(f, encoding="utf-8"))
        rid = r.get("rule_id")
        if rid:
            rules.append(r); ids.append(rid); dir_of[rid] = f.replace("\\", "/").split("/")[0]
    src_dim = {}
    for rid in ids:
        src_dim[DIR_DIM[dir_of[rid]]] = src_dim.get(DIR_DIM[dir_of[rid]], 0) + 1

    # 모듈 그래프 집계
    all_reqs, all_laws = [], []
    for m in MODULES:
        g = _module_graph(m)
        nodes = {n["node_id"] for n in g["nodes"]}
        miss = [(e["relation"], e.get("from_id"), e.get("to_id")) for e in g["edges"]
                if e.get("from_id") not in nodes or e.get("to_id") not in nodes]
        check(not miss, f"INV3 {m}: dangling 0", f"INV3 {m}: dangling {len(miss)} {miss[:3]}")
        all_reqs += [n for n in g["nodes"] if n["node_type"] == "LegalRequirement"]
        all_laws += [n for n in g["nodes"] if n["node_type"] == "Law"]

    print("--- 완결성 불변식 ---")
    # INV1
    check(len(rules) == len(all_reqs), f"INV1 1:1 reify — 룰 {len(rules)} == LegalRequirement {len(all_reqs)}",
          f"INV1 불일치 — 룰 {len(rules)} != 노드 {len(all_reqs)}")
    # INV2
    dups = sorted({x for x in ids if ids.count(x) > 1})
    check(len(set(ids)) == len(ids), f"INV2 rule_id 유일 — {len(ids)}건", f"INV2 중복 rule_id {dups}")
    node_ids = {n["node_id"] for n in all_reqs}
    check(node_ids == set(ids), "INV2b 룰↔노드 id 집합 동일",
          f"INV2b 차집합 src-node={sorted(set(ids)-node_ids)[:3]} node-src={sorted(node_ids-set(ids))[:3]}")
    # INV4 결정성
    nondet = [n["node_id"] for n in all_laws
              if n["node_id"] != "law_" + hashlib.md5(n["properties"]["name"].encode()).hexdigest()[:10]]
    check(not nondet, f"INV4 Law ID 결정적(md5) — {len(all_laws)}개", f"INV4 비결정 ID {nondet[:3]}")
    # INV5 atomic
    compound = [n["properties"]["name"] for n in all_laws if "/" in n["properties"]["name"]]
    check(not compound, "INV5 Law 노드명 atomic", f"INV5 복합 regime 잔존 {compound}")
    # INV6 스키마
    schema = yaml.safe_load(open(f"{PACK}/types/LegalRequirement.yaml", encoding="utf-8"))
    allowed = set(schema["properties"]) | {"requirement_id"}
    dim_enum = set(schema["properties"]["dimension"]["enum"])
    badprop = {k for n in all_reqs for k in n["properties"] if k not in allowed}
    baddim = sorted({n["properties"]["dimension"] for n in all_reqs if n["properties"]["dimension"] not in dim_enum})
    check(not badprop, "INV6a property ⊆ 스키마", f"INV6a 미정의 property {badprop}")
    check(not baddim, "INV6b dimension ∈ enum", f"INV6b enum 외 {baddim}")
    # INV7 차원분포
    comp = _load(f"{PACK}/composed_graph.json")
    comp_reqs = [n for n in comp["nodes"] if n["node_type"] == "LegalRequirement"]
    comp_dim = {}
    for n in comp_reqs:
        comp_dim[n["properties"]["dimension"]] = comp_dim.get(n["properties"]["dimension"], 0) + 1
    check(comp_dim == src_dim, f"INV7 composed 차원분포 == 디렉토리 {src_dim}",
          f"INV7 분포 불일치 composed={comp_dim} src={src_dim}")
    miss_c = [(e.get("from_id"), e.get("to_id")) for e in comp["edges"]
              if e.get("from_id") not in {n["node_id"] for n in comp["nodes"]}
              or e.get("to_id") not in {n["node_id"] for n in comp["nodes"]}]
    check(not miss_c, "INV3 composed: dangling 0", f"INV3 composed dangling {len(miss_c)}")
    # INV8 엣지 온톨로지 완전성 — 그래프가 쓰는 모든 relation 이 edges.yaml 에 선언됐나
    declared = {r["name"] for r in yaml.safe_load(open(f"{PACK}/edges.yaml", encoding="utf-8"))["relations"]}
    used = set(e["relation"] for e in comp["edges"])
    for m in MODULES:
        used |= {e["relation"] for e in _module_graph(m)["edges"]}
    try:
        used |= {e["relation"] for e in _load(f"{PACK}/instance_graph.json")["edges"]}
    except FileNotFoundError:
        pass
    undeclared = sorted(used - declared)
    check(not undeclared, f"INV8 엣지 온톨로지 완전 — 사용관계 {len(used)} ⊆ edges.yaml 선언 {len(declared)}",
          f"INV8 edges.yaml 미선언 관계 {undeclared}")

    print()
    if fails:
        print(f"=== 완결성 FAIL — {len(fails)}건 ===")
        return 1
    print(f"=== 완결성 PASS — 룰 {len(rules)} / 요건노드 {len(all_reqs)} / Law {len(all_laws)} / dangling 0 ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
