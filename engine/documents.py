"""
문서 제출 의무 판정 — 프로젝트 조건상 제출 의무 문서가 실제 제출됐고 시점이 맞는가.

안전관리계획서·유해위험방지계획서·품질관리계획서 등. 제출 대상인데 미제출 → 위반(사전 위험관리 부재).

입력: { project{...조건...}, submitted_documents[ {document, submit_date} ] }
Usage:
  python documents.py examples/doc_project.yaml
"""
from __future__ import annotations
import paths

import glob
import sys

import yaml

from engine import lifecycle

sys.stdout.reconfigure(encoding="utf-8")

_OPS = {"__gte": lambda a, b: a >= b, "__gt": lambda a, b: a > b,
        "__lte": lambda a, b: a <= b, "__lt": lambda a, b: a < b, "__eq": lambda a, b: a == b}


def eval_clause(clause, p: dict):
    """3-값 논리. 반환 (state, missing): state ∈ {True, False, None(미상)}.
    참조 필드가 project 에 없으면 그 절은 미상(None) — '대상 아님'과 구분.
    any: 한 갈래라도 확정 참이면 참(미상 무시); 아니면 미상 있으면 미상; 아니면 거짓.
    all: 한 갈래라도 거짓이면 거짓; 아니면 미상 있으면 미상; 아니면 참.
    """
    if isinstance(clause, str):
        return (None, {clause}) if clause not in p else (bool(p[clause]), set())
    if isinstance(clause, dict):
        if "any" in clause:
            miss, indet = set(), False
            for c in clause["any"]:
                s, m = eval_clause(c, p)
                if s is True:
                    return True, set()
                if s is None:
                    indet = True; miss |= m
            return (None, miss) if indet else (False, set())
        if "all" in clause:
            miss, indet = set(), False
            for c in clause["all"]:
                s, m = eval_clause(c, p)
                if s is False:
                    return False, set()
                if s is None:
                    indet = True; miss |= m
            return (None, miss) if indet else (True, set())
        for k, v in clause.items():
            for suf, fn in _OPS.items():
                if k.endswith(suf):
                    base = k[: -len(suf)]
                    return (None, {base}) if base not in p else (fn(p[base], v), set())
            return (None, {k}) if k not in p else (bool(p[k]) == bool(v), set())
    return False, set()


def check_all(project: dict, submitted: list) -> list[dict]:
    names = {s.get("document") for s in submitted}
    out = []
    for f in paths.rule_glob("document_rules"):
        rule = yaml.safe_load(open(f, encoding="utf-8"))
        if not lifecycle.applies(project, rule):
            continue  # 유지단계 시나리오에 시공 전용 문서룰(착공신고 등) 오발 차단
        # 시설 게이트: 건축물-class/토목시설-class 룰은 해당 시설이 현장에 있을 때만 대상.
        # 게이트 필드 미상이면 판정보류(시설 유무 자체를 모름).
        gate_field = {"건축물": "contains_building", "토목시설": "contains_civil_facility"}.get(
            rule.get("applies_to_facility_class"))
        if gate_field:
            flag = project.get(gate_field)
            if flag is None:
                out.append({"document": rule["document"], "verdict": "indeterminate",
                            "missing_fields": [gate_field],
                            "submit_before": rule.get("submit_before"), "submit_to": rule.get("submit_to"),
                            "authority": rule["authority"]})
                continue
            if flag is False:
                out.append({"document": rule["document"], "verdict": "not_required"})
                continue
        state, missing = eval_clause(rule.get("required_when", {}), project)
        if state is None:
            out.append({"document": rule["document"], "verdict": "indeterminate",
                        "missing_fields": sorted(missing),
                        "submit_before": rule.get("submit_before"), "submit_to": rule.get("submit_to"),
                        "authority": rule["authority"]})
            continue
        if state is False:
            out.append({"document": rule["document"], "verdict": "not_required"})
            continue
        verdict = "compliant" if rule["document"] in names else "violated"
        out.append({"document": rule["document"], "verdict": verdict,
                    "submit_before": rule.get("submit_before"), "submit_to": rule.get("submit_to"),
                    "authority": rule["authority"]})
    return out


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "examples/doc_project.yaml"
    doc = yaml.safe_load(open(path, encoding="utf-8"))
    project, submitted = doc["project"], doc.get("submitted_documents", [])
    print("=" * 72)
    print(f"문서 제출 의무 판정 — {project.get('name')}")
    print("=" * 72)
    viol, indet = [], []
    tag = {"compliant": "제출됨", "violated": "✗ 미제출", "not_required": "—대상아님", "indeterminate": "? 판정보류"}
    for r in check_all(project, submitted):
        print(f"  {r['document']:<22}{tag[r['verdict']]}")
        if r["verdict"] == "violated":
            viol.append(r)
            print(f"    └─ 제출의무({r['submit_before']}, {r['submit_to']}) 미이행")
        elif r["verdict"] == "indeterminate":
            indet.append(r)
            print(f"    └─ 입력 미상: {', '.join(r['missing_fields'])} → 설계도서/투입계획 확인 필요")
    parts = []
    if viol:
        parts.append(f"✗ 미제출 {len(viol)}건 — 문서 측면 책임 가중")
    if indet:
        need = sorted({m for r in indet for m in r["missing_fields"]})
        parts.append(f"? 판정보류 {len(indet)}건 — 결론 닫으려면 필요 데이터: {', '.join(need)}")
    print("\n" + ("\n".join(parts) if parts else "제출 의무 모두 이행"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
