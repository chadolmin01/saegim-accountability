"""40칸 매트릭스 실측 재확인 — 실제 룰 파일에서 (단계×차원) 채움 추출."""
import glob
import paths, yaml, sys
sys.stdout.reconfigure(encoding="utf-8")

PHASES = ["기획·입지","조사·설계","착공준비","토공·기초","골조·구체","마감·설비","준공·검수","유지관리"]
DIMS = ["인적배치","의사결정","작업조건","선행요건","문서제출"]
grid = {(p,d): [] for p in PHASES for d in DIMS}
cross = []

WK_PHASE = {"굴착":"토공·기초","비계설치":"토공·기초","밀폐공간작업":"토공·기초",
  "콘크리트타설":"골조·구체","철근배근":"골조·구체","거푸집설치":"골조·구체","거푸집해체":"골조·구체",
  "용접":"골조·구체","양중":"골조·구체","고소작업":"골조·구체",
  "방수":"마감·설비","마감":"마감·설비","설비설치":"마감·설비","활선작업":"마감·설비","정전작업":"마감·설비","시운전":"마감·설비"}
DOC_PHASE = {"실시계획인가서":"착공준비","도로점용허가서":"착공준비","도로공사시행허가서":"착공준비",
  "착공신고서":"착공준비","안전관리계획서":"착공준비","유해위험방지계획서":"착공준비","품질관리계획서":"착공준비",
  "산업안전보건관리비_사용내역서":"착공준비","휴게시설":"착공준비","안전보건관리체계":"착공준비",
  "비산먼지발생사업신고서":"착공준비","건설폐기물처리계획서":"착공준비","임시소방시설":"착공준비",
  "환경영향평가_협의서":"조사·설계","구조안전확인서":"조사·설계",
  "사용승인서":"준공·검수","소방시설_준공":"준공·검수","승강기_검사증명":"준공·검수","양중기_안전검사증명":"골조·구체",
  "정기안전점검결과서":"유지관리","기관석면조사서":"유지관리","해체계획서":"유지관리"}
STAFF_PHASE = {"designer_structural_engineer":"조사·설계","facility_inspection_engineer":"유지관리"}
PREQ_PHASE = {"design_after_geotech_survey":"조사·설계","commencement_after_permit":"착공준비",
  "excavation_after_shoring":"토공·기초","concrete_pour_holdpoints":"골조·구체",
  "concealment_after_mep_inspection":"마감·설비","usage_approval_after_completion":"준공·검수"}

def stem(f): return f.replace("\\","/").split("/")[-1][:-5]

for f in paths.rule_glob("placement_rules"):
    r=yaml.safe_load(open(f,encoding="utf-8")); s=stem(f)
    grid[(STAFF_PHASE.get(s,"착공준비"),"인적배치")].append(r.get("title",s)[:22])
for f in paths.rule_glob("condition_rules"):
    r=yaml.safe_load(open(f,encoding="utf-8")); wk=r.get("applies_to_work_kind"); ph=WK_PHASE.get(wk)
    if ph: grid[(ph,"작업조건")].append(r.get("title","")[:18])
    else: cross.append(("작업조건",r.get("title","")[:22]+f" (wk={wk})"))
for f in paths.rule_glob("prerequisite_rules"):
    r=yaml.safe_load(open(f,encoding="utf-8")); ph=PREQ_PHASE.get(stem(f),"?")
    if ph in PHASES: grid[(ph,"선행요건")].append(r.get("title","")[:18])
    else: cross.append(("선행요건",stem(f)))
for f in paths.rule_glob("appropriateness_rules"):
    r=yaml.safe_load(open(f,encoding="utf-8"))
    grid[(r.get("phase","조사·설계"),"의사결정")].append(r.get("title","")[:18])
for f in paths.rule_glob("document_rules"):
    r=yaml.safe_load(open(f,encoding="utf-8")); doc=r.get("document","")
    grid[(DOC_PHASE.get(doc,"착공준비"),"문서제출")].append(doc)

print("칸별 룰 개수 (행=차원 / 열=단계 0~7):\n")
print("차원\\단계  " + "".join(f"{i}:{p[:3]:<4}" for i,p in enumerate(PHASES)))
for d in DIMS:
    print(f"{d:<8}" + "".join(f"  {(len(grid[(p,d)]) or '·'):<4}" for p in PHASES))
print("\n=== 칸별 실제 룰 ===")
for d in DIMS:
    for i,p in enumerate(PHASES):
        rs=grid[(p,d)]
        if rs: print(f"[{i}.{p}×{d}]({len(rs)}): {', '.join(rs)}")
print("\n=== 전공정/다단계(특정 칸 귀속 애매) ===")
for dim,t in cross: print(f"  ({dim}) {t}")
print(f"\n총 룰: {sum(len(v) for v in grid.values())} (칸 배치) + {len(cross)} (전공정)")
