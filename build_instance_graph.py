"""
인스턴스 그래프 어댑터 — saegim 사고 시나리오 → OpenCRAB 타입드 노드+엣지.

edges.yaml 단위 정의대로:
  factual 엣지 = 시나리오의 *_ref 를 따라 생성 (performed_by·targets·in_phase·constrained_by·caused_by·acts_via·holds·requires)
  verdict 엣지 = saegim 평가기(conditions·appropriateness·prerequisites) 판정 → violates, 그리고 책임 합성 → responsible_for
순회·시각화는 OpenCRAB(local 그래프)이 담당. 여기선 그래프를 '조립'만 한다.

Usage: python build_instance_graph.py examples/incident_graph_demo.yaml
출력: opencrab_pack/instance_graph.json (+ 책임체인 출력)
"""
from __future__ import annotations
import paths
import json, sys, glob, yaml
from datetime import date
from engine import conditions as C
from engine import appropriateness as A
from engine import prerequisites as P
from engine import org_judgment as OJ
from engine import maintenance as M
from engine import evaluate as E
sys.stdout.reconfigure(encoding="utf-8")

SPACE = {"Person": "subject", "Appointment": "subject", "Organization": "subject",
         "Decision": "decision", "DesignDecision": "decision", "CustodyTransfer": "decision", "WorkRecord": "resource",
         "Batch": "resource", "Sample": "resource", "Incident": "outcome",
         "SiteContext": "concept", "BuildingComponent": "concept", "ConstructionPhase": "concept",
         "LegalRequirement": "concept", "Defect": "concept"}

# 포렌식 원인범주 → 전형 책임주체 (ASCE GFI / ASTM E678)
CAUSE_ROLE = {"Design": "설계자", "Material": "제조사·공급", "Construction": "시공자", "Maintenance": "유지관리자"}

RULE_TITLE = {}
for f in (paths.rule_glob("condition_rules") + paths.rule_glob("appropriateness_rules")
          + paths.rule_glob("prerequisite_rules") + paths.rule_glob("org_rules")):
    r = yaml.safe_load(open(f, encoding="utf-8"))
    RULE_TITLE[r["rule_id"]] = r.get("title", r["rule_id"])


def build(doc):
    nodes, edges, seen = [], [], set()
    def node(ntype, nid, props=None):
        if nid and nid not in seen:
            seen.add(nid)
            nodes.append({"space": SPACE.get(ntype, "concept"), "node_type": ntype, "node_id": nid, "properties": props or {}})
        return nid
    def edge(fid, rel, tid, props=None):
        if fid and tid:
            e = {"from_id": fid, "relation": rel, "to_id": tid}
            if props:
                e["properties"] = props
            edges.append(e)

    site = doc.get("site_context", {})
    if site.get("id"):
        node("SiteContext", site["id"], {k: site[k] for k in site if k != "id"})
        node("ConstructionPhase", site.get("phase_ref"))
        edge(site["id"], "in_phase", site.get("phase_ref"))

    for o in doc.get("organizations", []):
        node("Organization", o["id"], {k: o[k] for k in o if k != "id"})
        edge(o["id"], "subcontracts_under", o.get("subcontracts_under_ref"))

    # ── 사건층: 레미콘 배치(BCOM/EPCIS) + 공시체(SOSA) ──
    for b in doc.get("batches", []):
        node("Batch", b["id"], {k: b[k] for k in b if k != "id"})
        edge(b["id"], "supplied_by", b.get("supplier_org_ref"))
        if b.get("pour_component_ref"):
            node("BuildingComponent", b["pour_component_ref"]); edge(b["id"], "delivered_for", b["pour_component_ref"])
    for s in doc.get("samples", []):
        node("Sample", s["id"], {k: s[k] for k in s if k != "id"})
        if s.get("sampled_component_ref"):
            node("BuildingComponent", s["sampled_component_ref"]); edge(s["id"], "sampled_from", s["sampled_component_ref"])
    # 책임 트랙 handover: 책임이전 사건 (양도자→인수자, 검수자 자격)
    for ct in doc.get("custody_transfers", []):
        node("CustodyTransfer", ct["id"], {k: ct[k] for k in ct if k != "id"})
        edge(ct["id"], "custody_from", ct.get("from_org_ref"))
        edge(ct["id"], "custody_to", ct.get("to_org_ref"))
        edge(ct["id"], "transfers", ct.get("batch_ref"))
        edge(ct["id"], "performed_by", ct.get("performed_by_ref"))

    for p in doc.get("persons", []):
        node("Person", p["id"], {"name": p.get("name")})
        edge(p["id"], "belongs_to", p.get("affiliation_org"))
        for ap in p.get("appointments", []):
            node("Appointment", ap["id"], {k: ap[k] for k in ap if k != "id"})
            edge(p["id"], "holds", ap["id"])

    def add_decision(d, ntype):
        node(ntype, d["id"], {k: d[k] for k in d if k not in ("id",)})
        edge(d["id"], "performed_by", d.get("performed_by_ref"))
        edge(d["id"], "performed_by", d.get("approved_by_ref"))  # 승인자도 행위주체
        edge(d["id"], "acts_via", d.get("via_role"))
        edge(d["id"], "targets", d.get("component_ref") or d.get("target_component_ref"))
        edge(d["id"], "constrained_by", d.get("site_ref"))
        node("ConstructionPhase", d.get("phase_ref")); edge(d["id"], "in_phase", d.get("phase_ref"))
        if d.get("component_ref") or d.get("target_component_ref"):
            node("BuildingComponent", d.get("component_ref") or d.get("target_component_ref"))

    for d in doc.get("design_decisions", []):
        add_decision(d, "DesignDecision")
    for d in doc.get("decisions", []):
        add_decision(d, "Decision")
    for w in doc.get("work_records", []):
        node("WorkRecord", w["id"], {k: w[k] for k in w if k != "id"})
        edge(w["id"], "performed_by", w.get("performed_by_ref"))
        node("BuildingComponent", w.get("component_ref")); edge(w["id"], "targets", w.get("component_ref"))
        node("ConstructionPhase", w.get("phase_ref")); edge(w["id"], "in_phase", w.get("phase_ref"))
        for req in w.get("requires_prior", []):
            pass  # requires 엣지는 prereq 판정과 함께 처리

    # ── 유지단계: 점검·보수 사건 (관리주체 직접책임 — Decision으로 모델, 새 타입 불필요) ──
    for mr in doc.get("maintenance_records", []):
        node("Decision", mr["id"], {k: mr[k] for k in mr if k not in ("id", "inspection_findings", "maintenance_action")})
        edge(mr["id"], "performed_by", mr.get("performed_by_ref"))
        if mr.get("manager_org_ref"):
            node("Organization", mr["manager_org_ref"])
        if mr.get("component_ref"):
            node("BuildingComponent", mr["component_ref"]); edge(mr["id"], "targets", mr["component_ref"])

    inc = doc.get("incident", {})
    if inc.get("id"):
        node("Incident", inc["id"], {k: inc[k] for k in inc if k != "id"})
        node("ConstructionPhase", inc.get("phase_ref")); edge(inc["id"], "in_phase", inc.get("phase_ref"))
        for ref in inc.get("caused_by_refs", []):
            edge(inc["id"], "caused_by", ref)
        # cause축(Defect): 사고가 드러낸 결함 → 부재 발현 (포렌식). cause_category는 책임주체 시사.
        for d in inc.get("defects", []):
            node("Defect", d["id"], {k: d[k] for k in d if k != "id"})
            edge(inc["id"], "exhibits", d["id"])
            if d.get("component_ref"):
                node("BuildingComponent", d.get("component_ref")); edge(d["id"], "manifests_in", d.get("component_ref"))

    # ── verdict 엣지 (평가기) ──
    def rule_node(rid):
        node("LegalRequirement", rid, {"title": RULE_TITLE.get(rid, rid)}); return rid
    violators = []
    meta = {}  # 위반노드 → {person, date(행위시점), approver}
    for w in doc.get("work_records", []):
        for r in C.check_all(w):
            if r["verdict"] == "violated":
                edge(w["id"], "violates", rule_node(r["rule_id"])); violators.append(w["id"])
        meta[w["id"]] = {"person": w.get("performed_by_ref"), "date": w.get("event_date"), "approver": w.get("approved_by_ref")}
    # 사건층 deferred: 공시체 28일 결과(result_value 입력 시점 T2) → 강도 합부판정(기존 검측룰 재사용)
    for s in doc.get("samples", []):
        if s.get("result_value") is None:
            continue
        rec = {"work_kind": "콘크리트타설", "design_fck_mpa": s.get("design_fck_mpa"),
               "test_values": {"strength_mpa": s["result_value"]}}
        for r in C.check_all(rec):
            if r["verdict"] == "violated":
                edge(s["id"], "violates", rule_node(r["rule_id"]))
                if s["id"] not in violators:
                    violators.append(s["id"])
                meta[s["id"]] = {"person": s.get("performed_by_ref"), "date": s.get("test_date")}
    site_d = doc.get("site_context", {}); dds = doc.get("design_decisions", [])
    for r in A.check_all(site_d, dds):
        if r["verdict"] == "violated":
            dd = next((d for d in dds if d.get("name") == r.get("decision")), None)
            if dd:
                edge(dd["id"], "violates", rule_node(r["rule_id"])); violators.append(dd["id"])
                meta[dd["id"]] = {"person": dd.get("performed_by_ref"), "date": dd.get("event_date"), "approver": dd.get("approved_by_ref")}
    for w in doc.get("work_records", []):
        decs = doc.get("decisions", []) + dds
        for f in paths.rule_glob("prerequisite_rules"):
            if P.check(w, decs, yaml.safe_load(open(f, encoding="utf-8")))["verdict"] == "violated":
                edge(w["id"], "violates", rule_node(yaml.safe_load(open(f, encoding="utf-8"))["rule_id"]))
                if w["id"] not in violators:
                    violators.append(w["id"])
    # 유지단계 판정: 보수이행(maintenance) + 점검책임기술자 시점공백(qualification) → 관리주체 직접귀속
    for mr in doc.get("maintenance_records", []):
        fired = False
        mdoc = {"project": doc.get("project", {}), "inspection_findings": mr.get("inspection_findings"),
                "maintenance_action": mr.get("maintenance_action"), "incident": inc}
        for r in M.judge(mdoc):
            if r["verdict"] in ("violated", "기한내미착수_제도공백"):
                edge(mr["id"], "violates", rule_node(r["rule_id"])); fired = True
        if mr.get("is_facility_grade_1_or_2"):   # 점검책임기술자 선임 시점유효성(사고일 기준)
            appts = [{**ap, "person": p["id"]} for p in doc.get("persons", []) for ap in p.get("appointments", [])
                     if ap.get("role") == "안전점검책임기술자"]
            scen = {"project": {**doc.get("project", {}), "is_facility_grade_1_or_2": True},
                    "appointed_managers": appts, "incident": inc}
            for f in paths.rule_glob("placement_rules"):
                rule = yaml.safe_load(open(f, encoding="utf-8"))
                if rule.get("rule_id", "").startswith("facility_inspection_engineer") \
                        and E.evaluate(scen, rule)["verdict"] in ("understaffed", "unqualified"):
                    edge(mr["id"], "violates", rule_node(rule["rule_id"])); fired = True
        if fired:
            if mr["id"] not in violators:
                violators.append(mr["id"])
            meta[mr["id"]] = {"org": mr.get("manager_org_ref"), "date": inc.get("event_date")}

    # ── 행위시점 선임 유효성 판단 (행위일 기준 존재+시간; 자격은 부분) ──
    def _d(s):
        if not s:
            return None
        y, m, dd_ = map(int, str(s).split("-")); return date(y, m, dd_)
    APPT = {}  # person → [(start, end, ap_id, role)]
    for p in doc.get("persons", []):
        for ap in p.get("appointments", []):
            APPT.setdefault(p["id"], []).append((_d(ap.get("start_date")), _d(ap.get("end_date")), ap["id"], ap.get("role")))

    def validity_at(person, action_date):
        """행위시점 선임 유효성 → (valid, appointment_id, reason)."""
        at = _d(action_date)
        aps = APPT.get(person, [])
        if not aps:
            return False, None, "선임 없음(공백) — 무권한 행위"
        if at is None:
            return True, aps[0][2], "행위일 미상(시간검증 생략)"
        for s, e, ap_id, _role in aps:
            if s and s <= at and (e is None or at <= e):
                return True, ap_id, "유효선임 직접행위책임"
        return False, None, f"행위일 {action_date} 선임 유효구간 밖 — 무권한 행위"

    # ── responsible_for 합성 (유효성으로 주체·종류 분기) ──
    PERSON_ORG = {p["id"]: p.get("affiliation_org") for p in doc.get("persons", [])}
    ORG = {o["id"]: o for o in doc.get("organizations", [])}
    chain = []
    seen_org = set()
    if inc.get("id"):
        for v in dict.fromkeys(violators):
            mt = meta.get(v, {}); pid = mt.get("person")
            if not pid:
                # 유지단계: 책임주체가 관리주체(org) 직접 — 행위자(person) 없이 org로 귀속
                org = mt.get("org")
                if org and (org, v) not in seen_org:
                    seen_org.add((org, v))
                    node("Organization", org)
                    legal = []
                    for jv in OJ.judge_org(ORG.get(org, {"id": org}), inc):
                        short = jv["rule_id"].split("__")[0]
                        if jv["verdict"] == "violated":
                            edge(org, "violates", rule_node(jv["rule_id"])); legal.append(f"{short}:위반")
                        elif jv["verdict"] == "not_applicable":
                            legal.append(f"{short}:미적용")
                        elif jv["verdict"] == "판정보류":
                            legal.append(f"{short}:판정보류")
                    legal_type = "; ".join(legal) if legal else "해당없음"
                    edge(org, "responsible_for", inc["id"],
                         {"basis": "관리주체 유지관리 의무 위반(직접 귀속)", "structural": False,
                          "legal_type": legal_type, "via_node": v, "action_date": mt.get("date")})
                    chain.append((org, v, None, f"관리주체 직접귀속(유지관리) [{legal_type}]"))
                continue
            valid, ap_id, reason = validity_at(pid, mt.get("date"))
            edge(pid, "responsible_for", inc["id"],
                 {"basis": reason, "valid_at_action": valid, "appointment": ap_id, "via_node": v, "action_date": mt.get("date")})
            chain.append((pid, v, valid, reason))
            # 소속 도급조직으로 구조적 귀속 + 도급책임 판정(org_judgment ⑤): 건산법§29·중대재해법
            org = PERSON_ORG.get(pid)
            if org and (org, v) not in seen_org:
                seen_org.add((org, v))
                legal = []
                for jv in OJ.judge_org(ORG.get(org, {"id": org}), inc):
                    short = jv["rule_id"].split("__")[0]
                    if jv["verdict"] == "violated":
                        edge(org, "violates", rule_node(jv["rule_id"])); legal.append(f"{short}:위반")
                    elif jv["verdict"] == "not_applicable":
                        legal.append(f"{short}:미적용")
                    elif jv["verdict"] == "판정보류":
                        legal.append(f"{short}:판정보류")
                legal_type = "; ".join(legal) if legal else "해당없음"
                edge(org, "responsible_for", inc["id"],
                     {"basis": "소속 도급조직 구조적 귀속(행위자 책임)", "structural": True,
                      "legal_type": legal_type, "via_person": pid, "via_node": v})
                chain.append((org, v, None, f"소속조직 구조귀속 [{legal_type}]"))
            if not valid and mt.get("approver"):   # 무효/공백 → 선임권자·승인자로 상향
                edge(mt["approver"], "responsible_for", inc["id"],
                     {"basis": "선임/승인 책임(행위자 무권한)", "valid_at_action": True, "via_node": v})
                chain.append((mt["approver"], v, None, "선임/승인 책임(상향)"))
    return {"nodes": nodes, "edges": edges}, chain, violators


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "examples/incident_graph_demo.yaml"
    doc = yaml.safe_load(open(path, encoding="utf-8"))
    g, chain, violators = build(doc)
    import os; os.makedirs(paths.P("opencrab_pack"), exist_ok=True)
    json.dump(g, open(paths.P("opencrab_pack", "instance_graph.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    rel = {}
    for e in g["edges"]:
        rel[e["relation"]] = rel.get(e["relation"], 0) + 1
    print(f"→ opencrab_pack/instance_graph.json  (OpenCRAB local 그래프 적재용)")
    print(f"노드 {len(g['nodes'])} / 엣지 {len(g['edges'])}: {rel}")
    inc = doc.get("incident", {})
    print(f"\n★ 책임 체인 — 사고 [{inc.get('name')}] 추적 (행위시점 선임 유효성 반영):")
    for pid, v, valid, reason in chain:
        tag = "✓유효" if valid is True else ("↑상향" if valid is None else "✗무권한")
        print(f"   {pid:<10} ──responsible_for──▶ {inc.get('id')}  [{tag}] {reason}  (경유 {v})")
    print(f"\n위반 {len(set(violators))} → 책임주체 {len(set(p for p,_,_,_ in chain))}명. 순회·시각화는 OpenCRAB local 그래프.")
    defects = inc.get("defects", [])
    if defects:
        print(f"\n★ cause축 — 결함 → 원인범주 → 전형 책임주체 (포렌식 ASCE GFI/ASTM E678):")
        for d in defects:
            cc = d.get("cause_category")
            print(f"   {inc.get('id')} ──exhibits──▶ {d['id']}({d.get('defect_type')}/{d.get('mechanism')}) "
                  f"──manifests_in──▶ {d.get('component_ref')}  | 원인 {cc} → {CAUSE_ROLE.get(cc, '?')}")
    deferred = [s for s in doc.get("samples", []) if s.get("result_value") is not None]
    if deferred:
        print(f"\n★ deferred 결과 — 공시체 T1 채취 → T2(28일) 결과 → 합부 (하나의 사건, 두 시점):")
        for s in deferred:
            fck = s.get("design_fck_mpa")
            cap = round(0.85 * fck, 1) if fck else "?"
            tag = "✗미달" if (fck and s["result_value"] < 0.85 * fck) else "합격"
            print(f"   {s['id']}: 채취 {s.get('sampling_date')}(T1) → 결과 {s.get('test_date')}(T2) "
                  f"강도 {s['result_value']} vs 0.85×{fck}={cap} [{tag}] → 부재 {s.get('sampled_component_ref')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
