"""
현장 전체 배치 적정성 감사 — 사고 1건 입력 → 모든 역할 rule 일괄 판정.

책임추적의 실제 산출물: "이 사고 당일, 이 현장의 법정 배치가 역할별로 적정했나"를
한 번에 회수한다. understaffed/unqualified 역할이 곧 책임 가중 지점.

입력(project audit file): { project:{...전 파라미터...}, appointments:[{role,...,start_date,end_date}], incident:{event_date,...} }
각 rule 은 자기 role 에 해당하는 선임만 골라 평가.

Usage:
  python audit.py examples/audit_full_project.yaml
"""
from __future__ import annotations
import paths

import glob
import sys

import yaml

from engine import evaluate as E
from engine import lifecycle

sys.stdout.reconfigure(encoding="utf-8")


# 역할별 선임/지정 주체 = 위반 시 1차 책임 주체 (도급 family).
RESPONSIBLE_PARTY = {
    "안전관리자": "시공사(원도급)",
    "보건관리자": "시공사(원도급)",
    "안전보건관리책임자": "시공사(원도급)",
    "현장대리인": "시공사(원도급)",
    "품질관리자": "시공사(원도급)",
    "안전보건총괄책임자": "도급인(원청)",
    "안전보건조정자": "발주자",
    "책임건설사업관리기술인": "발주청",
    "공사감리자": "건축주",
    "감리원": "사업주체(주택)",
    "책임감리원": "발주청",
    "안전점검책임기술자": "관리주체",
}


def load_rules() -> list[dict]:
    rules = []
    for f in paths.rule_glob("placement_rules"):
        r = yaml.safe_load(open(f, encoding="utf-8"))
        if r.get("rule_id") and r.get("role"):
            rules.append(r)
    return rules


def audit(doc: dict) -> list[dict]:
    project = doc["project"]
    incident = doc.get("incident", {})
    appts = doc.get("appointments") or doc.get("appointed_managers") or []
    findings = []
    for rule in load_rules():
        if not lifecycle.applies(project, rule):
            continue  # 유지단계 시나리오에 시공 전용 배치룰 오발 차단
        role = rule["role"]
        role_appts = [a for a in appts if a.get("role") == role]
        scenario = {"project": project, "appointed_managers": role_appts, "incident": incident}
        result = E.evaluate(scenario, rule)
        findings.append({
            "role": role,
            "rule_id": rule["rule_id"],
            "verdict": result["verdict"],
            "required": result.get("required_count") or result.get("total_required"),
            "effective": result.get("effective_count"),
            "responsible_party": RESPONSIBLE_PARTY.get(role, "—"),
            "detail": result.get("unfilled_slots") or result.get("rationale", "")[:200],
        })
    return findings


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "examples/audit_full_project.yaml"
    doc = yaml.safe_load(open(path, encoding="utf-8"))
    project, incident = doc["project"], doc.get("incident", {})

    print("=" * 78)
    print(f"현장 배치 적정성 감사 — {project.get('name')}")
    print(f"사고: {incident.get('name')} ({incident.get('event_date')}, {incident.get('incident_kind','')})")
    print(f"공사금액: {project.get('contract_amount_krw', project.get('total_contract_amount_krw',0)):,}원"
          f" / 연면적 {project.get('gross_floor_area_m2','?')}㎡")
    print("=" * 78)

    findings = audit(doc)
    violations = [f for f in findings if f["verdict"] in ("understaffed", "unqualified")]

    print(f"\n{'역할':<22}{'판정':<16}{'요구/유효':<10}{'비고'}")
    print("-" * 78)
    mark = {"compliant": "적정", "understaffed": "✗인원미달", "unqualified": "✗자격미달", "not_required": "—의무없음"}
    for f in findings:
        rq = f"{f['required']}/{f['effective']}" if f["required"] is not None else "—"
        det = f["detail"] if f["verdict"] in ("understaffed", "unqualified") else ""
        print(f"{f['role']:<22}{mark.get(f['verdict'],'?'):<16}{rq:<10}{det}")

    print("\n" + "=" * 78)
    if violations:
        print(f">>> 위반 {len(violations)}건 — 사고 당일 법정 배치 미충족 역할:")
        for v in violations:
            print(f"    · {v['role']}: {v['verdict']} ({v['detail']})")
        print(">>> 위 역할들은 중대재해처벌법·관계법령상 책임 가중 지점.")
    else:
        print(">>> 전 역할 배치 적정. 배치 측면 위반 없음.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
