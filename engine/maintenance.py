"""maintenance_rules/ 평가 — 유지단계(점검→보수이행) 전담 평가기.

시공 위주 5차원이 못 보는 단계7(유지관리)을 담당. 입력: 점검 결과(inspection_findings)·
보수 이행(maintenance_action)·사고. 근거 시특법 §24·시행령§19. 시점(권고~사고)으로 기한 판정하고,
'기한 내 미착수'면 제도 공백(긴 법정기한이 사고 못 막음)을 정직하게 드러낸다.
"""
from __future__ import annotations
import paths
import glob
import yaml
from datetime import date

RULES = [yaml.safe_load(open(f, encoding="utf-8")) for f in paths.rule_glob("maintenance_rules")]


def _d(s):
    if not s:
        return None
    y, m, dd = map(int, str(s).split("-"))
    return date(y, m, dd)


def _months(a, b):
    if not a or not b:
        return None
    return (b.year - a.year) * 12 + (b.month - a.month)


def judge(doc: dict) -> list[dict]:
    out = []
    findings = doc.get("inspection_findings") or []
    ma = doc.get("maintenance_action") or {}
    inc = doc.get("incident", {})
    inc_d = _d(inc.get("event_date"))
    for r in RULES:
        rid, title = r["rule_id"], r.get("title", r["rule_id"])
        dl = (r.get("authority") or {}).get("deadline_at_incident", {})
        start_yrs = dl.get("start_within_years", 2)
        rec = next((f for f in findings if f.get("recommendation") or str(f.get("grade")) in ("C", "D", "E")), None)
        if not rec:
            out.append({"rule_id": rid, "title": title, "verdict": "not_applicable", "reason": "보수권고/중대결함 없음"})
            continue
        if ma.get("repair_started") is True:
            out.append({"rule_id": rid, "title": title, "verdict": "compliant", "reason": "보수 착수·이행"})
            continue
        m = _months(_d(rec.get("report_date")), inc_d)
        if m is not None and m < start_yrs * 12:
            out.append({"rule_id": rid, "title": title, "verdict": "기한내미착수_제도공백",
                        "reason": f"권고~사고 {m}개월 < 착수기한 {start_yrs}년 → 시특법 형식상 적법이나 기한이 사고 못 막음(제도공백). 사고발생→업무상 과실 책임"})
        else:
            out.append({"rule_id": rid, "title": title, "verdict": "violated",
                        "reason": f"보수 미착수 {m}개월 ≥ 착수기한 {start_yrs}년 → 시특법§24 위반·§65①"})
    return out


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    import sys as _s
    path = _s.argv[1] if len(_s.argv) > 1 else paths.P("examples", "maintenance_demo.yaml")
    doc = yaml.safe_load(open(path, encoding="utf-8"))
    print("=== 유지단계 판정 (예제) ===")
    for v in judge(doc):
        print(f"  [{v['verdict']}] {v['rule_id']} — {v['reason']}")
