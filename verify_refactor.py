"""디버그 보험 — 리팩터(경로 앵커링·패키지 이동) 전후 회귀 가드.
핵심 위험 = '조용한 실패'(CWD-상대 glob이 빈 리스트 → 룰 0개 → 위반 0건인데 크래시 없음).
이 스크립트는 그 실패를 *시끄럽게* 만든다.

  python verify_refactor.py           # 검증 — 골든 대비 diff, 불일치 시 exit 1
  python verify_refactor.py --update  # 현 상태를 골든으로 저장 (반드시 known-good에서만)

가드 3종:
  ① 룰 패밀리별 개수 == 골든 (빈 로드/누락 즉시 적발)
  ② 카논 예제 출력(node/edge/relation별/violators) == 골든
  ③ *다른 CWD*에서 build 실행해도 같은 violators (앵커링 핵심 증명 — Step A 후 통과해야 함)
"""
from __future__ import annotations
import sys, os, glob, json, subprocess, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GOLDEN = ROOT / "verify_golden.json"
RULE_DIRS = ["condition_rules", "document_rules", "prerequisite_rules", "placement_rules",
             "appropriateness_rules", "org_rules", "maintenance_rules", "material_specs"]
CANON = ["examples/incident_graph_demo.yaml", "examples/incident_graph_acceptance.yaml"]


def rule_counts() -> dict:
    return {d: len(glob.glob(str(ROOT / d / "*.yaml"))) for d in RULE_DIRS}


def _snapshot_from_json(path: Path) -> dict:
    g = json.load(open(path, encoding="utf-8"))
    rels: dict = {}
    for e in g["edges"]:
        rels[e["relation"]] = rels.get(e["relation"], 0) + 1
    violators = sorted({e["from_id"] for e in g["edges"] if e["relation"] == "violates"})
    return {"nodes": len(g["nodes"]), "edges": len(g["edges"]),
            "by_relation": dict(sorted(rels.items())), "violators": violators}


def build_snapshot(example: str, cwd: Path) -> dict:
    """build_instance_graph를 cwd에서 실행 → 쓰인 json 스냅샷. example은 절대경로로 넘긴다.
    앵커링(Step A) 후 출력은 항상 ROOT/opencrab_pack 이므로 거기서 읽는다 — cross_cwd면
    cwd가 달라도 ROOT에 써져야(=룰 제대로 로드돼야) 골든과 일치한다."""
    out_json = ROOT / "opencrab_pack" / "instance_graph.json"
    if out_json.exists():
        out_json.unlink()  # 이전 결과 제거 — 빈 로드를 '갱신 안 됨'으로 못 숨기게
    r = subprocess.run([sys.executable, str(ROOT / "build_instance_graph.py"), str(ROOT / example)],
                       cwd=str(cwd), capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0 or not out_json.exists():
        raise SystemExit(f"  ✗ BUILD 실패 ({example}, cwd={cwd})\n{(r.stderr or '')[-600:]}")
    return _snapshot_from_json(out_json)


def collect(cross_cwd: bool = False) -> dict:
    snap = {"rule_counts": rule_counts(), "examples": {}}
    for ex in CANON:
        snap["examples"][ex] = build_snapshot(ex, ROOT)
    if cross_cwd:
        with tempfile.TemporaryDirectory() as td:
            snap["cross_cwd"] = {ex: build_snapshot(ex, Path(td)) for ex in CANON}
    return snap


def diff(golden: dict, cur: dict, key_path="") -> list:
    out = []
    if isinstance(golden, dict) and isinstance(cur, dict):
        for k in sorted(set(golden) | set(cur)):
            out += diff(golden.get(k, "<누락>"), cur.get(k, "<누락>"), f"{key_path}.{k}")
    elif golden != cur:
        out.append(f"  {key_path}: 골든={golden}  현재={cur}")
    return out


def main():
    if "--update" in sys.argv:
        json.dump(collect(cross_cwd=False), open(GOLDEN, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        g = json.load(open(GOLDEN, encoding="utf-8"))
        print(f"골든 저장: {GOLDEN.name}")
        print(f"  룰 개수: {g['rule_counts']}")
        for ex, s in g["examples"].items():
            print(f"  {ex}: 노드{s['nodes']}/엣지{s['edges']} violators={s['violators']}")
        return 0
    if not GOLDEN.exists():
        raise SystemExit("골든 없음 — 먼저 `python verify_refactor.py --update` (known-good에서)")
    golden = json.load(open(GOLDEN, encoding="utf-8"))
    # ① 룰 개수 가드 (조용한 빈 로드 적발)
    rc = rule_counts()
    empties = [d for d, n in rc.items() if n == 0]
    if empties:
        raise SystemExit(f"  ✗✗ 룰 0개 로드!! {empties} — CWD/경로 깨짐 (조용한 실패 차단됨)")
    cross = "--cross-cwd" in sys.argv
    cur = collect(cross_cwd=cross)
    problems = diff(golden, {k: cur[k] for k in golden}, "")
    if cross:
        # 골든엔 cross_cwd가 없으니 examples 골든과 대조
        for ex in CANON:
            problems += diff(golden["examples"][ex], cur["cross_cwd"][ex], f".cross_cwd.{ex}")
    if problems:
        print("=== ✗ 회귀 감지 ===")
        print("\n".join(problems))
        return 1
    print(f"=== ✓ 보험 통과 — 룰 {sum(rc.values())}개 / 카논 {len(CANON)}예제 동일"
          + (" / 다른 CWD에서도 동일(앵커링 OK)" if cross else "") + " ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
