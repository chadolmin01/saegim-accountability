"""
사고 책임 보고서 — 배치 적정성(audit) + 의사결정 권한 트레일(trail)을 하나로 통합.

책임추적의 최종 산출물. 사고 1건 입력 → 두 차원을 모두 평가하여
"사고 당일 이 현장의 책임 가중 지점"을 단일 보고서로 회수한다.

Usage:
  python report.py examples/report_full.yaml
"""
from __future__ import annotations

import sys
import yaml

from engine import audit as A
from engine import trail as T
from engine import conditions as C
from engine import prerequisites as P
from engine import documents as D
from engine import maintenance as M

sys.stdout.reconfigure(encoding="utf-8")


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "examples/report_full.yaml"
    doc = yaml.safe_load(open(path, encoding="utf-8"))
    project, incident = doc["project"], doc.get("incident", {})

    print("#" * 78)
    print(f"# 사고 책임 보고서")
    print(f"# 현장: {project.get('name')}")
    print(f"# 사고: {incident.get('name')} ({incident.get('event_date')}, {incident.get('incident_kind','')})")
    amt = project.get("contract_amount_krw") or project.get("total_contract_amount_krw") or 0
    print(f"# 규모: {amt:,}원 / 연면적 {project.get('gross_floor_area_m2','?')}㎡")
    print("#" * 78)

    # I. 배치 적정성
    findings = A.audit(doc)
    staffing_viol = [f for f in findings if f["verdict"] in ("understaffed", "unqualified")]
    print("\n[ I. 배치 적정성 ] — 사고 당일 법정 인원·자격 충족 여부")
    print("-" * 78)
    mark = {"compliant": "적정", "understaffed": "✗인원미달", "unqualified": "✗자격미달", "not_required": "—"}
    for f in findings:
        if f["verdict"] == "not_required":
            continue
        rq = f"{f['required']}/{f['effective']}" if f["required"] is not None else ""
        det = f["detail"] if f["verdict"] in ("understaffed", "unqualified") else ""
        print(f"  {f['role']:<20}{mark[f['verdict']]:<10}{rq:<8}{det}")

    # II. 의사결정 권한 트레일
    tr = T.build_trail(doc)
    authority_defect = [t for t in tr["trail"] if not t["appointment_valid"]]
    print("\n[ II. 의사결정 권한 ] — 사고 부재 결정 이력 + 시점별 권한 유효성")
    print("-" * 78)
    if tr["trail"]:
        for t in tr["trail"]:
            ok = "✓" if t["appointment_valid"] else "✗무효"
            print(f"  {t['date']:<12}{t['kind']:<12}{t['person']}/{t['role'] or '-':<12} {ok}")
    else:
        print("  대상 부재 결정 기록 없음")

    # III. 작업 조건 적법성 (work_record 단일 또는 work_records 리스트 — 다공종 사고)
    cond_viol = []
    wrs = doc.get("work_records") or [w for w in (incident.get("work_record"), doc.get("work_record")) if w]
    print("\n[ III. 작업 조건 적법성 ] — 사고 작업의 온도·기상·자재 등 조건 충족 여부")
    print("-" * 78)
    if wrs:
        for wr in wrs:
            for r in C.check_all(wr):
                if r["verdict"] == "not_applicable":
                    continue
                tag = "적합" if r["verdict"] == "compliant" else "✗위반"
                print(f"  [{wr.get('work_kind','-')}|{r['dimension']}] {r['title']:<22}{tag}")
                if r["verdict"] == "violated":
                    cond_viol.append(r)
                    print(f"      └─ {r.get('reason','')}")
    else:
        print("  작업 기록(work_record) 미입력 — 조건 판정 생략")

    # IV. 선행요건 (Hold Point) — 사고 작업의 검측 선행 여부 (work_records 순회; 빈 검측이면 미통과)
    prereq_viol = []
    decisions = (doc.get("decisions", []) or []) + (doc.get("design_decisions", []) or [])
    print("\n[ IV. 선행요건(Hold Point) ] — 사고 작업 전 필수 검측 선행 여부")
    print("-" * 78)
    seen_iv = False
    for wr in (wrs or []):
        for r in P.check_all(wr, decisions):
            seen_iv = True
            tag = "적합" if r["verdict"] == "compliant" else "✗위반"
            print(f"  [{wr.get('work_kind','-')}] {r['title']:<34}{tag}")
            if r["verdict"] == "violated":
                prereq_viol.append(r)
                print(f"      └─ 미통과 정지점: {r['missing_holdpoints']}")
    if not seen_iv:
        print("  해당 선행요건 없음")

    # V. 문서 제출 의무
    doc_viol = []
    submitted = doc.get("submitted_documents", [])
    print("\n[ V. 문서 제출 의무 ] — 제출 대상 문서 이행 여부")
    print("-" * 78)
    for r in D.check_all(project, submitted):
        if r["verdict"] == "not_required":
            continue
        tag = "제출됨" if r["verdict"] == "compliant" else "✗미제출"
        print(f"  {r['document']:<22}{tag}")
        if r["verdict"] == "violated":
            doc_viol.append(r)

    # VI. 유지관리 (유지단계 점검→보수이행)
    mres = M.judge(doc)
    if any(r["verdict"] != "not_applicable" for r in mres):
        print("\n[ VI. 유지관리 ] — 점검·진단 결과 보수·보강 이행 (유지단계)")
        print("-" * 78)
        for r in mres:
            if r["verdict"] == "not_applicable":
                continue
            tag = {"compliant": "이행", "violated": "✗위반",
                   "기한내미착수_제도공백": "⚠기한내미착수(제도공백)"}.get(r["verdict"], r["verdict"])
            print(f"  {r['title']}{tag}")
            print(f"      └─ {r['reason']}")

    # 종합
    maint_viol = [r for r in mres if r["verdict"] not in ("not_applicable", "compliant")]
    print("\n" + "#" * 78)
    print("# 종합 — 책임 가중 지점")
    print("#" * 78)
    n = len(staffing_viol) + len(authority_defect) + len(cond_viol) + len(prereq_viol) + len(doc_viol) + len(maint_viol)
    if not n:
        print("위반·결함 없음.")
        return 0
    if staffing_viol:
        print(f"\n· 배치 위반 {len(staffing_viol)}건 (관계법령 위반 + 중대재해처벌법 책임 가중):")
        for v in staffing_viol:
            print(f"    - {v['role']}: {v['verdict']} → 책임주체 {v.get('responsible_party','—')} ({v['detail']})")
    if authority_defect:
        print(f"\n· 권한 결함 {len(authority_defect)}건 (무권한 결정 — 결정효력·책임귀속 다툼):")
        for t in authority_defect:
            print(f"    - {t['date']} {t['kind']} by {t['person']} (해당시점 {t['role']} 유효선임 아님)")
    if cond_viol:
        print(f"\n· 작업조건 위반 {len(cond_viol)}건 (시공기준 미준수 — 결함의 직접 원인):")
        for r in cond_viol:
            print(f"    - [{r['dimension']}] {r['title']}: {r.get('reason','')}")
    if prereq_viol:
        print(f"\n· 선행요건 위반 {len(prereq_viol)}건 (정지점 미통과 타설 — 결함 은폐):")
        for r in prereq_viol:
            print(f"    - {r['title']}: 미통과 {r['missing_holdpoints']}")
    if doc_viol:
        print(f"\n· 문서 미제출 {len(doc_viol)}건 (사전 위험·품질관리 부재):")
        for r in doc_viol:
            print(f"    - {r['document']} 미제출")
    if maint_viol:
        print(f"\n· 유지관리 {len(maint_viol)}건 (점검·진단 후 보수 미이행 — 관리주체 책임):")
        for r in maint_viol:
            print(f"    - {r['title'].strip()}: {r.get('reason','')}")
    print(f"\n>>> 총 {n}건. 사고 당시 이 시설은 법정 요건을 다차원에서 미충족.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
