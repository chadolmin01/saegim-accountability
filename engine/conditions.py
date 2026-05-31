"""
조건 판정기 — WorkRecord(시공 행위 기록)를 condition_rules/*.yaml 에 대조.

배치(staffing)·결정권한(trail) 외 세 번째 차원: 작업 시점의 조건(온도·기상·자재·근무 등)이
법정 의무/금지를 충족했는가. "그날 그 작업이 그 조건에서 적법했나".

mode:
  obligation — applicable_when 충족 시 requires(특정 조치) 의무. 미적용 → violated.
  prohibition — applicable_when 충족 시 작업 자체 금지. 수행됨 → violated.

Usage:
  python conditions.py examples/work_cold_pour.yaml         # 단일 작업 × 적용 가능한 모든 조건 rule
"""
from __future__ import annotations
import paths

import glob
import sys
import yaml

sys.stdout.reconfigure(encoding="utf-8")

_OPS = {"__gte": lambda a, b: a >= b, "__gt": lambda a, b: a > b,
        "__lte": lambda a, b: a <= b, "__lt": lambda a, b: a < b, "__eq": lambda a, b: a == b}


def _resolve(rec: dict, key: str):
    """dotted key 지원 (예 test_values.slump_mm)."""
    cur = rec
    for part in key.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def eval_clause(clause, rec: dict) -> bool:
    if isinstance(clause, str):
        return bool(_resolve(rec, clause))
    if isinstance(clause, dict):
        if "any" in clause:
            return any(eval_clause(c, rec) for c in clause["any"])
        if "all" in clause:
            return all(eval_clause(c, rec) for c in clause["all"])
        for k, v in clause.items():
            for suf, fn in _OPS.items():
                if k.endswith(suf):
                    pv = _resolve(rec, k[: -len(suf)])
                    return False if pv is None else fn(pv, v)
            return bool(_resolve(rec, k)) == bool(v)
    return False


def evaluate_condition(rec: dict, rule: dict) -> dict:
    if rule.get("applies_to_work_kind") and rec.get("work_kind") != rule["applies_to_work_kind"]:
        return {"verdict": "not_applicable", "reason": "작업종류 불일치"}
    aw = rule.get("applicable_when")
    if aw and not eval_clause(aw, rec):   # applicable_when 부재 시 work_kind 일치만으로 적용
        return {"verdict": "not_applicable", "reason": "조건 미해당"}

    mode = rule.get("mode", "obligation")
    if mode == "prohibition":
        # 조건 충족 = 작업 금지인데 수행됨 → 위반
        return {"verdict": "violated", "reason": rule.get("on_violation", "금지 조건에서 작업 수행"),
                "authority": rule["authority"]}
    # obligation
    req = rule.get("requires", {})
    # (a) 조치 적용 의무
    if "measures_any" in req or "measures_all" in req:
        applied = set(rec.get("applied_measures") or [])
        ok = (bool(applied & set(req["measures_any"])) if "measures_any" in req
              else set(req["measures_all"]).issubset(applied))
        if ok:
            return {"verdict": "compliant", "authority": rule["authority"]}
        return {"verdict": "violated", "reason": f"의무 조치 미적용 (요구: {req})", "authority": rule["authority"]}
    # (c) 범주별 기준 lookup (예 부재별 존치강도, 지반별 안전기울기)
    if "lookup_bounds" in req:
        lb = req["lookup_bounds"]
        cat = _resolve(rec, lb["by"])
        table = lb.get("min_table") or {}
        if cat not in table:
            return {"verdict": "not_applicable", "reason": f"{lb['by']}={cat} 기준표 없음"}
        need = table[cat]
        val = _resolve(rec, lb["key"])
        if val is None:
            return {"verdict": "violated", "reason": f"{lb['key']} 미측정 (요구 {cat}≥{need})", "authority": rule["authority"]}
        if val >= need:
            return {"verdict": "compliant", "authority": rule["authority"]}
        return {"verdict": "violated", "reason": f"{lb['key']}={val} < 요구({cat}) {need}", "authority": rule["authority"]}
    # (c-2) 범주별 상한 lookup (예 프루프롤링 층별 소성변형 ≤ 한도)
    if "lookup_max" in req:
        lm = req["lookup_max"]
        cat = _resolve(rec, lm["by"])
        table = lm.get("max_table") or {}
        if cat not in table:
            return {"verdict": "not_applicable", "reason": f"{lm['by']}={cat} 기준표 없음"}
        cap = table[cat]
        val = _resolve(rec, lm["key"])
        if val is None:
            return {"verdict": "violated", "reason": f"{lm['key']} 미측정 (요구 {cat}≤{cap})", "authority": rule["authority"]}
        if val <= cap:
            return {"verdict": "compliant", "authority": rule["authority"]}
        return {"verdict": "violated", "reason": f"{lm['key']}={val} > 한도({cat}) {cap}", "authority": rule["authority"]}
    # (d) 비율 기준 (예 압축강도 ≥ 0.85×설계fck)
    if "ratio_bound" in req:
        rb = req["ratio_bound"]
        val = _resolve(rec, rb["key"])
        ref = _resolve(rec, rb["of"])
        if val is None or ref is None:
            return {"verdict": "violated", "reason": f"{rb['key']} 또는 {rb['of']} 미측정", "authority": rule["authority"]}
        need = ref * rb["ratio"]
        if val >= need:
            return {"verdict": "compliant", "authority": rule["authority"]}
        return {"verdict": "violated", "reason": f"{rb['key']}={val} < {rb['ratio']}×{rb['of']}({ref}) = {need:.1f}", "authority": rule["authority"]}
    # (e) 편차 허용 (지정값 대비 ±, 밴드별 허용오차 — 예 슬럼프 KS F 4009)
    if "deviation_bound" in req:
        db = req["deviation_bound"]
        m, t = _resolve(rec, db["measured"]), _resolve(rec, db["target"])
        if m is None or t is None:
            return {"verdict": "violated", "reason": f"{db['measured']} 또는 {db['target']} 미측정", "authority": rule["authority"]}
        tol = next((b["tol"] for b in db["bands"] if b.get("spec_lte") is None or t <= b["spec_lte"]), None)
        if tol is not None and abs(m - t) <= tol:
            return {"verdict": "compliant", "authority": rule["authority"]}
        return {"verdict": "violated", "reason": f"슬럼프 측정{m} vs 지정{t} 편차 {abs(m-t)} > 허용±{tol}", "authority": rule["authority"]}
    # (f) 시험 빈도 (타설량 대비 시험 횟수 — 예 KCS 120㎥/회)
    if "frequency_bound" in req:
        import math
        fb = req["frequency_bound"]
        vol, cnt = _resolve(rec, fb["volume"]), _resolve(rec, fb["count"])
        if vol is None or cnt is None:
            return {"verdict": "violated", "reason": f"{fb['volume']} 또는 {fb['count']} 미기록", "authority": rule["authority"]}
        need = max(1, math.ceil(vol / fb["interval_m3"]))
        if cnt >= need:
            return {"verdict": "compliant", "authority": rule["authority"]}
        return {"verdict": "violated", "reason": f"타설 {vol}㎥ → 필요 {need}회(매{fb['interval_m3']}㎥), 실시 {cnt}회", "authority": rule["authority"]}
    # (b) 수치 허용범위 의무 (재료시험 등)
    if "value_bounds" in req:
        breaches = []
        for vb in req["value_bounds"]:
            val = _resolve(rec, vb["key"])
            if val is None:
                breaches.append(f"{vb['key']} 미측정")
            elif "min" in vb and val < vb["min"]:
                breaches.append(f"{vb['key']}={val} < {vb['min']}")
            elif "max" in vb and val > vb["max"]:
                breaches.append(f"{vb['key']}={val} > {vb['max']}")
        if not breaches:
            return {"verdict": "compliant", "authority": rule["authority"]}
        return {"verdict": "violated", "reason": "; ".join(breaches), "authority": rule["authority"]}
    return {"verdict": "not_applicable", "reason": "요구 정의 없음"}


def check_all(rec: dict) -> list[dict]:
    out = []
    for f in paths.rule_glob("condition_rules"):
        rule = yaml.safe_load(open(f, encoding="utf-8"))
        r = evaluate_condition(rec, rule)
        out.append({"rule_id": rule["rule_id"], "dimension": rule.get("dimension"),
                    "title": rule.get("title"), **r})
    return out


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else "examples/work_cold_pour.yaml"
    rec = yaml.safe_load(open(path, encoding="utf-8"))
    print("=" * 72)
    print(f"작업 조건 적법성 — {rec.get('name')} ({rec.get('work_kind')}, {rec.get('event_date')})")
    cond = []
    for k in ("daily_avg_temp_c", "daily_max_temp_c", "apparent_temp_c", "rainfall_mm", "wind_speed_ms"):
        if rec.get(k) is not None:
            cond.append(f"{k}={rec[k]}")
    print("조건:", ", ".join(cond) or "—", "| 조치:", rec.get("applied_measures") or "없음")
    print("=" * 72)
    results = check_all(rec)
    mark = {"compliant": "적합", "violated": "✗ 위반", "not_applicable": "—해당없음"}
    viol = []
    for r in results:
        if r["verdict"] == "not_applicable":
            continue
        print(f"  [{r['dimension']}] {r['title']:<28}{mark[r['verdict']]}")
        if r["verdict"] == "violated":
            viol.append(r)
            print(f"      └─ {r.get('reason','')} (근거 {r['authority'].get('standard') or r['authority'].get('name')})")
    print("\n" + ("✗ 위반 %d건 — 작업 조건 측면 책임 가중 지점" % len(viol)) if viol else "조건 위반 없음")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
