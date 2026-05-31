"""org_rules/ 평가 — Organization 단위 도급책임 판정.

다른 차원(work/person/document/condition)이 작업·사람·문서를 대상으로 하는 것과 달리,
이건 *조직(도급단계)*과 *사고(시점)*를 대상으로 판정한다.
  - illegal_subcontracting: 건산법§29③ 재하도급 원칙 금지
  - serious_accident_corporate_duty: 중대재해법 경영책임자 — 시행일(2022-01-27) 게이트

근거는 corpus/ 검증 원문. 미입력은 판정보류(3-값), 시행 전은 not_applicable(시점 유효성).
"""
from __future__ import annotations
import paths
import glob
import yaml
from datetime import date

RULES = [yaml.safe_load(open(f, encoding="utf-8")) for f in paths.rule_glob("org_rules")]


def _d(s):
    if not s:
        return None
    y, m, dd = map(int, str(s).split("-"))
    return date(y, m, dd)


def _v(r, verdict, reason, org):
    return {"rule_id": r["rule_id"], "title": r.get("title", r["rule_id"]),
            "verdict": verdict, "reason": reason, "org": org.get("id"),
            "regime": r.get("regime"), "corpus_ref": (r.get("authority") or {}).get("corpus_ref")}


def judge_org(org: dict, incident: dict) -> list[dict]:
    """조직 1개 × 사고 → 도급책임 판정 목록."""
    out = []
    inc_date = _d(incident.get("event_date"))
    role = org.get("org_role")
    tier = org.get("subcontract_tier") or 0
    fatalities = incident.get("fatalities", 0)
    for r in RULES:
        rid = r["rule_id"]
        # ── 시행일 게이트 (시점 유효성) ──
        eff = _d(r.get("effective_date"))
        if eff and inc_date and inc_date < eff:
            out.append(_v(r, "not_applicable", f"{r['effective_date']} 시행 전 사고({incident.get('event_date')}) — 소급 불가", org))
            continue
        roles = r.get("applies_to_org_role") or []

        if rid.startswith("illegal_subcontracting"):
            if tier >= 2 or role == "재하도급":
                if org.get("written_consent") is True:
                    out.append(_v(r, "compliant", "서면승낙 예외 충족(입력 신뢰) — §29③ 단서", org))
                else:
                    out.append(_v(r, "violated", "재하도급(서면승낙 예외 없음) — 건산법§29③ 위반·§96 처벌", org))
            else:
                out.append(_v(r, "not_applicable", "재하도급(tier≥2) 아님", org))

        elif rid.startswith("serious_accident_corporate_duty"):
            # 시행일 게이트 통과(eff 이후) 경우만 도달
            if role not in roles:
                out.append(_v(r, "not_applicable", "경영책임자(원도급) 아님", org))
            elif fatalities < 1:
                out.append(_v(r, "not_applicable", "사망 중대재해 아님(또는 사망자 미입력)", org))
            elif org.get("safety_health_system") is True:
                out.append(_v(r, "compliant", "안전보건관리체계 구축·이행(입력)", org))
            elif org.get("safety_health_system") is False:
                out.append(_v(r, "violated", "경영책임자 안전보건확보의무 미이행 — 중대재해법§4/§9", org))
            else:
                out.append(_v(r, "판정보류", "경영책임자 안전보건체계 데이터 미입력", org))
    return out


if __name__ == "__main__":
    # 자기검증 — 재하도급 tier2(중대재해법 시행 전 사례) + 가상 post-시행
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    sub = {"id": "org_sub", "org_role": "재하도급", "subcontract_tier": 2}
    prime = {"id": "org_prime", "org_role": "원도급", "subcontract_tier": 0}
    pre = {"event_date": "2021-03-01", "fatalities": 9}
    post = {"event_date": "2024-03-01", "fatalities": 1}
    print("=== 시행 전(2021) 재하도급사 ===")
    for v in judge_org(sub, pre):
        print(f"  [{v['verdict']}] {v['rule_id']} — {v['reason']}")
    print("=== 시행 전(2021) 원도급사 — 중대재해법 시점 ===")
    for v in judge_org(prime, pre):
        print(f"  [{v['verdict']}] {v['rule_id']} — {v['reason']}")
    print("=== 가상 post-시행(2024) 원도급사(체계 미입력) ===")
    for v in judge_org(prime, post):
        print(f"  [{v['verdict']}] {v['rule_id']} — {v['reason']}")
