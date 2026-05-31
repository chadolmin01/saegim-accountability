"""
단계 추적기(spine walker) — 사고를 생애주기 backbone 따라 상류→하류로 걸으며
'어느 단계 어느 요소에서 끊겼나 + 누가 책임인가'를 회수한다.

상류(조사·설계): appropriateness.py — DesignDecision × SiteContext 적절성.
하류(토공·골조): conditions.py — WorkRecord 실행 조건 적법성.
두 차원을 phase order로 정렬 → 가장 상류의 끊김(root) + 책임주체.

Usage: python phase_trace.py examples/incident_rainfall_curing.yaml
"""
from __future__ import annotations
import paths

import sys
import yaml

from engine import appropriateness as A
from engine import conditions as C

sys.stdout.reconfigure(encoding="utf-8")

PHASES = {p["name"]: p["order"] for p in yaml.safe_load(open(paths.P("phases.yaml"), encoding="utf-8"))}
WORKKIND_PHASE = {
    "굴착": "토공·기초", "비계설치": "토공·기초",
    "콘크리트타설": "골조·구체", "철근배근": "골조·구체",
    "거푸집설치": "골조·구체", "거푸집해체": "골조·구체", "용접": "골조·구체",
    "양중": "골조·구체", "고소작업": "골조·구체", "밀폐공간작업": "토공·기초",
}


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "examples/incident_rainfall_curing.yaml"
    doc = yaml.safe_load(open(path, encoding="utf-8"))
    site = doc.get("site_context", {})
    designs = doc.get("design_decisions", [])
    works = doc.get("work_records", [])
    incident = doc.get("incident", {})

    findings = []
    # 상류 — 설계 적절성
    for r in A.check_all(site, designs):
        if r["verdict"] == "violated":
            findings.append({"phase": r.get("phase", "조사·설계"), "layer": "상류 결정",
                             "what": r["title"], "why": r.get("reason", ""),
                             "who": r.get("responsible"), "appr": r.get("approved_by")})
    # 하류 — 실행 조건
    for w in works:
        ph = WORKKIND_PHASE.get(w.get("work_kind"), "골조·구체")
        for r in C.check_all(w):
            if r["verdict"] == "violated":
                findings.append({"phase": ph, "layer": "하류 실행", "what": r["title"],
                                 "why": r.get("reason", ""), "who": "시공자(현장)", "appr": None,
                                 "record": w.get("name")})

    findings.sort(key=lambda f: PHASES.get(f["phase"], 99))

    print("=" * 74)
    print(f"사고 추적 — {incident.get('name')} ({incident.get('event_date')})")
    print(f"현장: {site.get('name')} | 연강수 {site.get('region_annual_rainfall_mm')}mm, 지하수위 {site.get('groundwater_level_m')}m")
    print("=" * 74)
    if not findings:
        print("끊긴 지점 없음 (모든 단계 적합).")
        return 0
    print("생애주기 backbone 따라 끊긴 지점 (상류→하류):\n")
    for f in findings:
        order = PHASES.get(f["phase"], "?")
        print(f"  [{order}.{f['phase']}] ({f['layer']}) {f['what']}")
        print(f"        └─ {f['why']}")
        print(f"        └─ 책임: {f['who']}" + (f" / 승인: {f['appr']}" if f.get("appr") else ""))
    root = findings[0]
    print("\n" + "─" * 74)
    print(f"★ 사고의 뿌리(최상류 끊김): [{PHASES.get(root['phase'])}.{root['phase']}] {root['what']}")
    print(f"   1차 책임: {root['who']}" + (f" (승인 {root['appr']})" if root.get("appr") else ""))
    print(f"   → 하류 실행 책임과 결합: 상류 {sum(1 for f in findings if f['layer']=='상류 결정')}건 + 하류 {sum(1 for f in findings if f['layer']=='하류 실행')}건")
    print("   해석: 사고는 하류 시공만의 문제가 아니라 상류 설계결정이 현장여건을 반영 못한 데서 시작.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
