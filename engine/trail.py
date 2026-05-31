"""
의사결정 책임 트레일 — 사고 부재/위치에 대한 결정 이력을 시간순 회수하고,
각 결정 수행자가 '그 결정 시점에 유효 선임 상태였는가'를 교차 검증한다.

배치 적정성(audit.py)이 "누가 있어야 했나"라면, 이것은 "실제 누가 무엇을 언제 결정했나
+ 그 권한이 그때 유효했나". 둘을 합치면 완전한 책임추적.

입력: { project, appointments[], decisions[], incident{location_ref|component_ref, event_date} }
출력: 대상 부재/위치의 결정 시간순 + 각 결정의 [수행자 / 역할 / 그 시점 유효선임 여부].

Usage:
  python trail.py examples/trail_incident.yaml
"""
from __future__ import annotations

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


def valid_appointment(appts, person, role, at):
    """그 사람이 그 역할로 at 시점에 유효 선임 상태였는지."""
    for a in appts:
        if a.get("person") == person and (role is None or a.get("role") == role):
            s, e = d(a["start_date"]), d(a.get("end_date"))
            if s <= at and (e is None or at <= e):
                return True, a
    return False, None


def build_trail(doc: dict) -> dict:
    incident = doc["incident"]
    appts = doc.get("appointments", [])
    decisions = doc.get("decisions", [])
    target_comp = incident.get("component_ref")
    target_loc = incident.get("location_ref")

    # 대상 부재/위치에 관련된 결정만
    related = [
        dec for dec in decisions
        if (target_comp and dec.get("target_component_ref") == target_comp)
        or (target_loc and dec.get("target_location_ref") == target_loc)
    ]
    related.sort(key=lambda x: d(x["event_date"]))

    trail = []
    for dec in related:
        at = d(dec["event_date"])
        person = dec.get("performed_by_ref")
        role = dec.get("via_role")
        ok, appt = valid_appointment(appts, person, role, at)
        trail.append({
            "date": dec["event_date"],
            "kind": dec["kind"],
            "result": dec.get("result"),
            "person": person,
            "role": role,
            "appointment_valid": ok,
            "legal_basis": dec.get("legal_basis"),
            "flag": None if ok else "결정 시점에 해당 역할 유효 선임 아님 — 권한 없는 결정",
        })
    return {"incident": incident, "trail": trail}


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "examples/trail_incident.yaml"
    doc = yaml.safe_load(open(path, encoding="utf-8"))
    r = build_trail(doc)
    inc = r["incident"]

    print("=" * 78)
    print(f"의사결정 책임 트레일 — {inc.get('name')}")
    print(f"사고 시점 {inc.get('event_date')} / 대상 {inc.get('component_ref') or inc.get('location_ref')}")
    print("=" * 78)
    if not r["trail"]:
        print("대상 부재/위치에 기록된 의사결정 없음.")
        return 0
    print(f"\n{'일자':<12}{'결정':<12}{'결과':<10}{'수행자/역할':<22}{'선임유효'}")
    print("-" * 78)
    for t in r["trail"]:
        pr = f"{t['person']}/{t['role'] or '-'}"
        ok = "✓" if t["appointment_valid"] else "✗ 무효"
        print(f"{t['date']:<12}{t['kind']:<12}{str(t['result']):<10}{pr:<22}{ok}")
        if t["flag"]:
            print(f"{'':12}└─ ⚠ {t['flag']} (근거 {t['legal_basis']})")

    invalid = [t for t in r["trail"] if not t["appointment_valid"]]
    print("\n" + "=" * 78)
    if invalid:
        print(f">>> 권한 결함 {len(invalid)}건 — 유효 선임 아닌 자의 결정:")
        for t in invalid:
            print(f"    · {t['date']} {t['kind']} by {t['person']} → 책임 귀속·결정 효력 다툼 소지")
    else:
        print(">>> 모든 결정이 유효 선임자에 의해 수행됨.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
