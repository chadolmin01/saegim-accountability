"""모든 rule 디렉토리를 스캔해 RULES.md 카탈로그 생성. python generate_rules_index.py"""
import glob, yaml, sys
sys.stdout.reconfigure(encoding="utf-8")

DIRS = [("인적 배치", "rules"), ("작업 조건", "condition_rules"),
        ("선행요건", "prerequisite_rules"), ("문서 제출", "document_rules")]

lines = ["# 규칙 카탈로그 (자동생성: generate_rules_index.py)", "",
         "saegim-accountability 의 전체 법정 판정 규칙. 각 규칙은 근거 법령(authority)을 가지며, 미검증은 pending 표기.", ""]
total = 0
for dim_label, d in DIRS:
    files = sorted(glob.glob(f"{d}/*.yaml"))
    lines.append(f"## {dim_label} ({d}/) — {len(files)}개\n")
    lines.append("| rule_id | 제목 | 규제 | 근거 | pending |")
    lines.append("|---|---|---|---|---|")
    for f in files:
        r = yaml.safe_load(open(f, encoding="utf-8"))
        auth = r.get("authority", {})
        ref = auth.get("table") or auth.get("article") or auth.get("standard") or auth.get("rule", "")[:24]
        npend = len(r.get("pending", []) or [])
        lines.append(f"| `{r.get('rule_id','')}` | {r.get('title','')} | {r.get('regime','')} | {str(ref)[:34]} | {npend} |")
        total += 1
    lines.append("")
lines.append(f"---\n**총 {total}개 규칙** · 5개 책임 차원 (배치·권한·작업조건·선행요건·문서)")
open("RULES.md", "w", encoding="utf-8").write("\n".join(lines))
print(f"RULES.md 생성 — {total}개 규칙")
