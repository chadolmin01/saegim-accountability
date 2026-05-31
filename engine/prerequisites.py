"""
선행요건(Hold Point) 판정 — 작업(예 콘크리트타설) 전에 필수 검측이 합격으로 선행됐는가.

검측 ITP 의 정지점(H): 감리 합격 없이 다음 공정 진행 불가. 타설 전 철근배근·거푸집 검측.
누락·불합격·타설 이후 검측 → 정지점 미통과 = 구조결함 은폐의 직접 원인.

입력: { work_record{work_kind, event_date, component_ref}, decisions[] }
Usage:
  python prerequisites.py examples/prereq_pour.yaml
"""
from __future__ import annotations
import paths

import glob
import sys
from datetime import date

import yaml

sys.stdout.reconfigure(encoding="utf-8")


def d(s):
    if not s:
        return None
    if isinstance(s, date):
        return s
    y, m, dd = map(int, str(s).split("-"))
    return date(y, m, dd)


def _matches(dec: dict, req: dict, comp, at) -> bool:
    """dec 가 선행요건 req 를 충족하나 (kind + checkpoint(있으면) + result + 부재 + 시점<=트리거)."""
    dd = d(dec.get("event_date"))
    return (dec.get("kind") == req["kind"]
            and ("checkpoint" not in req or dec.get("checkpoint") == req["checkpoint"])
            and dec.get("result") == req.get("result", "합격")
            and (comp is None or dec.get("target_component_ref") == comp)
            and dd is not None and dd <= at)


def check(work: dict, decisions: list, rule: dict) -> dict:
    """트리거 = work_kind(작업) 또는 decision_kind(마일스톤 게이트: 사용승인·설계 등).
    트리거 시점 이전에 requires_prior 가 모두 선행 충족돼야 한다. (하위호환: work_kind 경로 동일)"""
    wk, dk = rule.get("applies_to_work_kind"), rule.get("applies_to_decision_kind")
    triggers = []  # (event_date, component)
    if wk:
        if not work or work.get("work_kind") != wk:
            return {"verdict": "not_applicable"}
        triggers = [(d(work["event_date"]), work.get("component_ref"))]
    elif dk:
        tds = [x for x in decisions if x.get("kind") == dk]
        if not tds:
            return {"verdict": "not_applicable"}
        triggers = [(d(x.get("event_date")), x.get("target_component_ref")) for x in tds]
    else:
        return {"verdict": "not_applicable"}

    missing = []
    for at, comp in triggers:
        if at is None:
            continue
        for req in rule["requires_prior"]:
            key = req.get("checkpoint") or req["kind"]
            if not any(_matches(dec, req, comp, at) for dec in decisions) and key not in missing:
                missing.append(key)
    verdict = "compliant" if not missing else "violated"
    return {"verdict": verdict, "missing_holdpoints": missing}


def check_all(work: dict, decisions: list) -> list[dict]:
    out = []
    for f in paths.rule_glob("prerequisite_rules"):
        rule = yaml.safe_load(open(f, encoding="utf-8"))
        r = check(work, decisions, rule)
        if r["verdict"] != "not_applicable":
            out.append({"rule_id": rule["rule_id"], "title": rule["title"], **r})
    return out


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "examples/prereq_pour.yaml"
    doc = yaml.safe_load(open(path, encoding="utf-8"))
    work = doc.get("work_record", {})
    decisions = (doc.get("decisions", []) or []) + (doc.get("design_decisions", []) or [])
    print("=" * 72)
    print(f"선행요건(Hold Point) 판정 — {work.get('name') or doc.get('project',{}).get('name','(현장)')}")
    print("=" * 72)
    for r in check_all(work, decisions):
        tag = "적합" if r["verdict"] == "compliant" else "✗ 위반"
        print(f"  {r['title']}  {tag}")
        if r["missing_holdpoints"]:
            print(f"    └─ 미통과 정지점: {r['missing_holdpoints']} → 선행요건 미충족 (결함 은폐·상류 누락 소지)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
