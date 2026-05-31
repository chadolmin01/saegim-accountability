"""OpenCRAB Cloud Pack(opencrab-cloud-pack-v1) ZIP 빌더.

typed graph를 *납작하게 만들지 않고* 그대로 싣는 경로. MCP ingest_text(텍스트→RAG 재추출)와 달리
graph/nodes·edges.jsonl로 typed 노드/엣지를 직접 적재한다.

ZIP 레이아웃 (spec):
  manifest.json                 format=opencrab-cloud-pack-v1 (있으면 Cloud Pack 우선)
  graph/nodes.jsonl             기준층(composed)+사건층(instance) 노드. node.id 필수
  graph/edges.jsonl             from/to + relation. 끊긴 엣지는 ingester가 skip 가능
  cloud/documents.jsonl         RAG 문서 — 코퍼스 원문 + 룰별 검증 진술
  cloud/chunks.jsonl            문서 청크 (document_id 연결)

검증 규칙 자체점검: node.id 필수 / edge from·to / JSONL 한 줄=valid JSON / 빈 텍스트 제외 /
숨김경로 없음 / 엔트리 ≤500 / 파일 ≤5MB / readable doc ≥1.

주의: graph 노드/엣지 키(id·from·to)는 spec 고정. cloud(documents/chunks) 내부 키(id·title·text·
document_id)는 spec에 명시 안 돼 관례값 사용 — ingester가 다른 키 요구하면 여기만 바꿔 재빌드.
"""
from __future__ import annotations
import json, glob, os, sys, zipfile
import paths

PUBLISH = "--publish" in sys.argv  # 발행용: 사건층(데모 사고)·코퍼스 원문(표준 IP) 제외 — 순수 기준층

ROOT = paths.ROOT
OUT_DIR = ROOT / "dist"
PACK_ID = "saegim_civil_concrete"
VERSION = "0.1.0"
OUT = OUT_DIR / f"{PACK_ID}_cloud_pack_v{VERSION}.zip"

RULE_DIRS = ["condition_rules", "document_rules", "prerequisite_rules", "placement_rules",
             "appropriateness_rules", "org_rules", "maintenance_rules"]

# ── 법·시설클래스 id 정규화 ───────────────────────────────────────────────
# opaque law_<md5> → 안정 law:<약칭>. 같은 법은 항상 같은 id(결정적 수렴) — 결정적 단일-ID 체인.
# 테이블이 단일 출처 — 같은 법이 두 약칭으로 갈리지 않게 코드에 고정. 미등록 법은 fallback+경고.
LAW_ID = {
    "KCS": "law:KCS", "KCS 표준시방서": "law:KCS표준시방서", "KDS 설계기준": "law:KDS",
    "KOSHA Guide": "law:KOSHA가이드",
    "KS D 3503": "law:KS_D_3503", "KS D 3504": "law:KS_D_3504", "KS F 2444": "law:KS_F_2444",
    "KS F 2445": "law:KS_F_2445", "KS F 2526": "law:KS_F_2526", "KS F 2560": "law:KS_F_2560",
    "KS F 2563": "law:KS_F_2563", "KS F 2591": "law:KS_F_2591", "KS F 4009": "law:KS_F_4009",
    "KS F 4602": "law:KS_F_4602", "KS L 5201": "law:KS_L_5201", "KS L 5405": "law:KS_L_5405",
    "KS L 9016": "law:KS_L_9016",
    "건설기술진흥법": "law:건진법", "건설산업기본법": "law:건산법", "건설폐기물재활용법": "law:건폐법",
    "건축물 에너지절약설계기준": "law:에너지절약설계기준", "건축물관리법": "law:건축물관리법",
    "건축법": "law:건축법", "국토계획법": "law:국토계획법", "근로기준법": "law:근로기준법",
    "대기환경보전법": "law:대기환경보전법", "도로법": "law:도로법",
    "산업안전보건기준에 관한 규칙": "law:산안규칙", "산업안전보건법": "law:산안법",
    "산업안전보건법(안전보건규칙)": "law:산안법_안전보건규칙",
    "소방시설법": "law:소방시설법", "소음진동관리법": "law:소음진동관리법",
    "승강기안전관리법": "law:승강기안전관리법", "시설물안전법": "law:시설물안전법",
    "중대재해처벌법": "law:중처법", "환경영향평가법": "law:환경영향평가법",
    "건설사업관리 업무수행지침": "law:건설사업관리지침",
    "건설사업관리(감리) 업무수행지침": "law:건설사업관리감리지침",
    "사업관리방식 업무수행지침": "law:사업관리방식지침",
}
_warns = []


def canon_id(node):
    """Law/FacilityClass 노드 → 안정 id. 그 외 노드는 원래 id 유지."""
    nt = node.get("node_type")
    nid = node.get("node_id") or node.get("id")
    if nt == "Law":
        nm = ((node.get("properties") or {}).get("name") or "").strip()
        cid = LAW_ID.get(nm)
        if not cid:
            cid = "law:" + nm.replace(" ", "_")
            _warns.append(f"미등록 법 '{nm}' → fallback {cid} (LAW_ID에 추가 권장)")
        return cid
    if nt == "FacilityClass":
        nm = ((node.get("properties") or {}).get("name") or nid).strip()
        return "facility_class:" + nm
    return nid


def load(p):
    return json.load(open(p, encoding="utf-8"))


def chunk_text(text, size=800):
    paras, buf, out = [p.strip() for p in text.split("\n\n") if p.strip()], "", []
    for p in paras:
        if len(buf) + len(p) + 2 > size and buf:
            out.append(buf); buf = p
        else:
            buf = (buf + "\n\n" + p) if buf else p
    if buf:
        out.append(buf)
    return out or ([text] if text.strip() else [])


def build_nodes_edges():
    comp = load(ROOT / "opencrab_pack" / "composed_graph.json")
    inst = {"nodes": [], "edges": []} if PUBLISH else load(ROOT / "opencrab_pack" / "instance_graph.json")
    # 안정 id remap (Law/FacilityClass) — 노드와 엣지 양쪽에 동일 적용해야 연결 유지
    remap = {}
    for n in comp["nodes"] + inst["nodes"]:
        old = n.get("node_id") or n.get("id")
        new = canon_id(n)
        if old and new != old:
            remap[old] = new
    rid = lambda x: remap.get(x, x)
    nodes = {}
    for n in comp["nodes"] + inst["nodes"]:
        old = n.get("node_id") or n.get("id")
        if not old:
            continue
        nid = rid(old)
        nodes[nid] = {"id": nid, "type": n.get("node_type"),
                      "space": n.get("space"), "properties": n.get("properties", {})}
    edges, seen = [], set()
    for e in comp["edges"] + inst["edges"]:
        f = rid(e.get("from_id") or e.get("from") or e.get("source"))
        t = rid(e.get("to_id") or e.get("to") or e.get("target"))
        rel = e.get("relation")
        if not f or not t:
            continue
        k = (f, rel, t)
        if k in seen:
            continue
        seen.add(k)
        ed = {"from": f, "to": t, "relation": rel}
        if e.get("from_type"):
            ed["from_type"] = e["from_type"]
        if e.get("to_type"):
            ed["to_type"] = e["to_type"]
        edges.append(ed)
    return list(nodes.values()), edges


def rule_document(d):
    """룰 yaml → 검증된 규범 진술 문서 텍스트."""
    a = d.get("authority") or {}
    parts = [d.get("title", d.get("rule_id"))]
    if d.get("regime"):
        parts.append(f"규정: {d['regime']} ({d.get('source_type','')})")
    if a.get("standard"):
        parts.append(f"표준: {a['standard']}")
    if a.get("rule"):
        parts.append(f"기준: {a['rule']}")
    if a.get("test_method"):
        parts.append(f"시험방법: {a['test_method']}")
    if a.get("source"):
        parts.append(f"검증출처: {a['source']}")
    ev = d.get("evaluation") or {}
    if ev.get("audit_significance"):
        parts.append(f"감사의의: {ev['audit_significance']}")
    return "\n".join(str(p) for p in parts if p)


def build_documents_chunks(nodes):
    docs, chunks = [], []
    # 1) 코퍼스 원문 (발행 시 제외 — 표준 원문 IP·메타 노트)
    for f in ([] if PUBLISH else sorted(glob.glob(str(ROOT / "corpus" / "*.md")))):
        text = open(f, encoding="utf-8").read().strip()
        if not text:
            continue
        did = "corpus/" + os.path.basename(f)
        docs.append({"id": did, "title": os.path.basename(f), "text": text,
                     "source_type": "corpus"})
        for i, ck in enumerate(chunk_text(text)):
            chunks.append({"id": f"{did}#{i}", "document_id": did, "text": ck})
    # 2) 룰별 검증 진술 (RAG 검색 대상)
    for d_ in RULE_DIRS:
        for f in sorted(glob.glob(str(ROOT / d_ / "*.yaml"))):
            import yaml
            d = yaml.safe_load(open(f, encoding="utf-8"))
            rid = d.get("rule_id")
            text = rule_document(d).strip()
            if not rid or not text:
                continue
            docs.append({"id": rid, "title": d.get("title", rid), "text": text,
                         "source_type": d.get("source_type"), "regime": d.get("regime"),
                         "dimension": d.get("dimension")})
            chunks.append({"id": f"{rid}#0", "document_id": rid, "text": text})
    # 3) Law·FacilityClass 노드도 문서로 — ingester가 노드를 materialize하도록(dangling 방지 + canonical 씨앗)
    for n in nodes:
        if n["type"] == "Law":
            nm = n["properties"].get("name", n["id"])
            text = (f"{nm}\n유형: 근거 법령·표준\nid: {n['id']}\n"
                    f"토목·콘크리트 책임추적 온톨로지에서 요건들이 governed_by로 참조하는 소관 규범.")
            docs.append({"id": n["id"], "title": nm, "text": text, "source_type": "law_node"})
            chunks.append({"id": f"{n['id']}#0", "document_id": n["id"], "text": text})
        elif n["type"] == "FacilityClass":
            p = n["properties"]; nm = p.get("name", n["id"])
            text = (f"{nm}\n{p.get('discriminator','')}\n근거: {p.get('legal_basis','')}\n"
                    f"id: {n['id']}\n요건이 gated_by로 적용되는 시설 클래스.").strip()
            docs.append({"id": n["id"], "title": nm, "text": text, "source_type": "facility_class_node"})
            chunks.append({"id": f"{n['id']}#0", "document_id": n["id"], "text": text})
    return docs, chunks


def jsonl(records):
    return "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records)


def main():
    nodes, edges = build_nodes_edges()
    docs, chunks = build_documents_chunks(nodes)
    for w in _warns:
        print("  ⚠", w)
    manifest = {
        "format": "opencrab-cloud-pack-v1",
        "id": PACK_ID,
        "title": "토목·콘크리트 시공 책임추적 온톨로지",
        "version": VERSION,
        "description": "토목·콘크리트 시공 법정 기준 책임추적 온톨로지. 요건(LegalRequirement) "
                       "→ 근거 법(governed_by)·시설 게이트(gated_by) typed graph + 요건별 검증 진술(RAG). "
                       "법·시설 노드는 안정 id(law:·facility_class:)로 정규화.",
        "counts": {"nodes": len(nodes), "edges": len(edges),
                   "documents": len(docs), "chunks": len(chunks)},
    }
    files = {
        "manifest.json": json.dumps(manifest, ensure_ascii=False, indent=1),
        "graph/nodes.jsonl": jsonl(nodes),
        "graph/edges.jsonl": jsonl(edges),
        "cloud/documents.jsonl": jsonl(docs),
        "cloud/chunks.jsonl": jsonl(chunks),
    }
    # ── 검증 자체점검 ──
    assert all(n.get("id") for n in nodes), "node.id 누락"
    assert all(e.get("from") and e.get("to") for e in edges), "edge from/to 누락"
    assert len(docs) >= 1, "readable document 0"
    for path, content in files.items():
        assert len(content.encode("utf-8")) < 5 * 1024 * 1024, f"{path} ≥5MB"
        if path.endswith(".jsonl"):
            for ln in content.splitlines():
                json.loads(ln)  # 각 줄 valid JSON
    assert len(files) <= 500
    OUT_DIR.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for path, content in files.items():
            z.writestr(path, content)
    # unzipped pack 디렉토리 (= 공개 repo 내용 그대로)
    pack_dir = OUT_DIR / "pack"
    for path, content in files.items():
        fp = pack_dir / path
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")
    print(f"  unzipped pack 디렉토리: {pack_dir}  (= repo 내용)")
    print(f"  모드: {'PUBLISH(기준층만, 코퍼스·사건층 제외)' if PUBLISH else 'DEV(전체)'}")
    print(f"✓ Cloud Pack 생성: {OUT}")
    print(f"  format=opencrab-cloud-pack-v1")
    import collections as _c
    tc = _c.Counter(n["type"] for n in nodes)
    n_corpus = sum(1 for d in docs if d.get("source_type") == "corpus")
    n_lawfc = sum(1 for d in docs if d.get("source_type") in ("law_node", "facility_class_node"))
    print(f"  graph/nodes.jsonl   {len(nodes)}  요건 {tc.get('LegalRequirement',0)}·법 {tc.get('Law',0)}·시설 {tc.get('FacilityClass',0)}" + (f"·사건층 {len(nodes)-sum(tc[t] for t in ('LegalRequirement','Law','FacilityClass'))}" if not PUBLISH else ""))
    print(f"  graph/edges.jsonl   {len(edges)}")
    print(f"  cloud/documents.jsonl {len(docs)}  룰 {len(docs)-n_corpus-n_lawfc}·법시설 {n_lawfc}·코퍼스 {n_corpus}")
    print(f"  cloud/chunks.jsonl  {len(chunks)}")
    print(f"  크기 {OUT.stat().st_size/1024:.0f} KB / 엔트리 {len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
