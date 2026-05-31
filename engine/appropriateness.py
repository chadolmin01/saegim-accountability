"""
적절성 판정기 — 상류 DesignDecision 이 SiteContext(주어진 조건)를 반영했는가.

5차원의 '의사결정권한'을 *상류 결정의 적절성*까지 확장. 기존 conditions.py 가 '실행 시점'
조건을 보는 반면, 여기는 '설계 결정 × 현장 givens' 정합성을 본다.
  triggers_when(site 조건) 충족 → decision_kind 결정을 찾아 → planned_mitigations 가 충분한가.
근거: 건진법 시행규칙 별표7 현장특성분석 + KCS.

Usage: python appropriateness.py examples/incident_rainfall_curing.yaml
"""
from __future__ import annotations
import paths

import glob
import sys
import yaml

sys.stdout.reconfigure(encoding="utf-8")

_OPS = {"__gte": lambda a, b: a >= b, "__gt": lambda a, b: a > b,
        "__lte": lambda a, b: a <= b, "__lt": lambda a, b: a < b, "__eq": lambda a, b: a == b}


def eval_site(clause, site: dict) -> bool:
    if isinstance(clause, str):
        return bool(site.get(clause))
    if isinstance(clause, dict):
        if "any" in clause:
            return any(eval_site(c, site) for c in clause["any"])
        if "all" in clause:
            return all(eval_site(c, site) for c in clause["all"])
        for k, v in clause.items():
            # 필드 vs 필드 비교 (예 groundwater_level_m__lt_field: planned_excavation_depth_m)
            for suf, fn in _OPS.items():
                if k.endswith(suf + "_field"):
                    base = k[: -len(suf + "_field")]
                    a, b = site.get(base), site.get(v)
                    return False if a is None or b is None else fn(a, b)
                if k.endswith(suf):
                    pv = site.get(k[: -len(suf)])
                    return False if pv is None else fn(pv, v)
            return bool(site.get(k)) == bool(v)
    return False


def evaluate(rule: dict, site: dict, decisions: list) -> dict:
    if not eval_site(rule.get("triggers_when", {}).get("site", {}), site):
        return {"verdict": "not_applicable", "reason": "현장여건 미해당"}
    kind = rule["decision_kind"]
    matched = [d for d in decisions if d.get("kind") == kind]
    auth = rule["authority"]
    if not matched:
        return {"verdict": "violated", "reason": f"'{kind}' 결정 자체 부재 (현장여건 반영 결정 없음)",
                "authority": auth, "responsible": None}
    req = rule.get("requires_mitigation", {})
    need_any = set(req.get("any") or [])
    need_all = set(req.get("all") or [])
    for d in matched:
        mit = set(d.get("planned_mitigations") or [])
        ok = (bool(mit & need_any) if need_any else True) and (need_all.issubset(mit) if need_all else True)
        if ok:
            return {"verdict": "compliant", "authority": auth, "decision": d.get("name")}
    d = matched[0]
    return {"verdict": "violated",
            "reason": rule.get("on_violation", f"{kind} 대책 미반영"),
            "authority": auth, "decision": d.get("name"),
            "responsible": d.get("performed_by_ref"), "approved_by": d.get("approved_by_ref")}


def check_all(site: dict, decisions: list) -> list:
    out = []
    for f in paths.rule_glob("appropriateness_rules"):
        rule = yaml.safe_load(open(f, encoding="utf-8"))
        r = evaluate(rule, site, decisions)
        out.append({"rule_id": rule["rule_id"], "title": rule.get("title"),
                    "phase": rule.get("phase"), **r})
    return out


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "examples/incident_rainfall_curing.yaml"
    doc = yaml.safe_load(open(path, encoding="utf-8"))
    site = doc.get("site_context", {})
    decisions = doc.get("design_decisions", [])
    print("=" * 72)
    print(f"상류 결정 적절성 — 현장 {site.get('name')}")
    print("=" * 72)
    viol = []
    for r in check_all(site, decisions):
        if r["verdict"] == "not_applicable":
            continue
        tag = {"compliant": "적절", "violated": "✗ 부적절"}[r["verdict"]]
        print(f"  [{r['phase']}] {r['title']:<28}{tag}")
        if r["verdict"] == "violated":
            viol.append(r)
            print(f"      └─ {r.get('reason','')}  (책임 {r.get('responsible') or '?'} / 승인 {r.get('approved_by') or '?'})")
    print("\n" + (f"✗ 상류 결정 부적절 {len(viol)}건" if viol else "상류 결정 적절"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
