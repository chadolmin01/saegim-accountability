"""saegim 온톨로지 → Ontology-Guided Extraction SchemaConfig 생성.

생성물 `rag/extraction_schema.yaml` — LLM이 문서를 추출할 때 *정의된 Class/Relationship만* 쓰도록
강제하는 제약 스키마(일반 GraphRAG의 자유추출 노이즈 차단). types/ + opencrab_pack/edges.yaml에서
파생 → 온톨로지가 바뀌면 재생성(드리프트 없음).

saegim 특이점(일반 ontology-GraphRAG와 차이):
  - 추출은 **factual 노드·엣지만** (관측된 사실: 누가·언제·무엇·측정값).
  - **verdict(violates·responsible_for)는 추출 금지** — saegim 결정적 엔진이 *계산*한다.
  - 기준층(LegalRequirement·Law·FacilityClass)은 추출 대상이 아니라 *링크 대상*(고정 온톨로지).
"""
from __future__ import annotations
import glob
import yaml
import paths

REFERENCE = {"LegalRequirement", "Law", "FacilityClass"}  # 기준층 — 추출 안 함, 링크/판정 대상


def load_classes():
    classes = []
    files = sorted(glob.glob(str(paths.ROOT / "types" / "*.yaml")) +
                   glob.glob(str(paths.ROOT / "opencrab_pack" / "types" / "*.yaml")))
    for f in files:
        d = yaml.safe_load(open(f, encoding="utf-8"))
        name = d.get("type")
        if not name:
            continue
        classes.append({
            "name": name,
            "space": d.get("space"),
            "role": "reference" if name in REFERENCE else "extractable",
            "properties": list((d.get("properties") or {}).keys()),
            "description": (d.get("description") or "").strip().splitlines()[0] if d.get("description") else "",
        })
    return classes


def load_relations():
    d = yaml.safe_load(open(paths.ROOT / "opencrab_pack" / "edges.yaml", encoding="utf-8"))
    out = []
    for r in d["relations"]:
        kind = r.get("kind")
        out.append({
            "name": r["name"], "kind": kind, "role": r.get("role"),
            "from": r.get("from"), "to": r.get("to"),
            "mode": {"factual": "EXTRACT", "verdict": "COMPUTED(엔진)", "type": "PACK구조"}.get(kind, "?"),
            "semantics": (r.get("semantics") or "").strip(),
        })
    return out


def main():
    classes = load_classes()
    relations = load_relations()
    schema = {
        "schema": "saegim-extraction-schema-v1",
        "purpose": "Ontology-Guided Extraction — 문서→typed graph 추출 시 이 Class/Relationship만 허용(자유추출 금지).",
        "classes": classes,
        "relationships": relations,
        "constraints": [
            "정의된 Class/Relationship만 사용 — 새 타입·관계를 발명하지 말 것(정의 안 된 것은 추출 대상 아님).",
            "각 노드는 고유한 id 필수.",
            "관계는 from/to 타입 제약을 지킬 것(예: targets는 Decision/WorkRecord → BuildingComponent만).",
            "mode=EXTRACT(factual) 관계·노드만 추출. mode=COMPUTED 관계(violates·responsible_for)는 절대 추출하지 말 것 — saegim 평가기가 계산한다.",
            "기준층 Class(LegalRequirement·Law·FacilityClass)는 새로 만들지 말고 *_ref로 링크만(고정 온톨로지).",
            "불확실하면 만들지 말고 생략. 원문에서 확인 안 된 수치는 넣지 말 것(추측금지).",
        ],
        "validation": "추출 그래프는 load_to_opencrab의 grammar 검증(허용 from→to 쌍)을 통과해야 적재 — SHACL 대응. 통과 후 엔진이 verdict 계산.",
        "counts": {"classes": len(classes), "extractable": sum(c["role"] == "extractable" for c in classes),
                   "relationships": len(relations), "extract_relations": sum(r["mode"] == "EXTRACT" for r in relations)},
    }
    out = paths.ROOT / "rag" / "extraction_schema.yaml"
    out.parent.mkdir(exist_ok=True)
    out.write_text("# 자동생성 — `python build_extraction_schema.py`. 직접 수정 말 것(types/·edges.yaml에서 파생).\n"
                   + yaml.safe_dump(schema, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
    print(f"✓ {out}")
    print(f"  클래스 {schema['counts']['classes']}(추출가능 {schema['counts']['extractable']}·기준층 {len(REFERENCE)})"
          f" / 관계 {schema['counts']['relationships']}(추출 {schema['counts']['extract_relations']}·계산 2·구조 2)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
