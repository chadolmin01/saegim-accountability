# 왜 온톨로지 엔진인가 — 검색·LLM과 무엇이 다른가

**한 줄 요약** — 법령·기준 텍스트를 *검색*해 답하는 방식(RAG)이나 LLM 단독은, 한도가 문장에
숫자로 적힌 질문은 맞힌다. 그러나 **한도를 계산해야 하거나(예: 0.85×설계강도), 조건에 따라
한도가 달라지거나, 법 시행일이 걸리는 질문에서는 그럴듯하게 틀린다.** 이 저장소의 온톨로지
엔진은 같은 질문 8개에 **항상 같은 판정 + 근거 조항(§)** 을 낸다.

---

## 1. 무엇을, 어떻게 비교했나

콘크리트·안전 검측 질문 8개를 두 방식에 똑같이 넣었다.

| 분류 | 방식 | 판정하는 주체 |
|---|---|---|
| 텍스트 | **LLM 단독** (모델 기억으로 답) · **검색기반 RAG** (기준 텍스트를 찾아 LLM이 서술) | LLM |
| 구조 | **온톨로지 엔진** (이 저장소 — 측정값을 규칙으로 계산) | 결정적 규칙 |

- 엔진 결과는 **아래 §6 의 스크립트로 그대로 재현된다(8/8, 키 불필요).**
- 텍스트 방식 결과는 같은 질문을 RAG·범용 LLM에 넣어 **관측한 값**이다.

## 2. 한눈에 — 어디서 갈리나

| 질문 유형 | 예 | 검색·LLM | 엔진 |
|---|---|---|---|
| **단일 임계값** — 한도가 문장에 숫자로 | 공기량 2% < 3.0? | ✅ 맞힘 | ✅ |
| **계산 임계값** — 한도가 *식* | 21 ≥ 0.85×24? | ❌ 거짓 불합격 | ✅ |
| **범주별 한도** — 조건 따라 한도가 달라짐 | W/B 0.55, 등급 따라 합/부 | ⚠️ 들쭉날쭉·회피 | ✅ |
| **시점 게이트** — 법 시행일 | 2021 사고에 2022 법? | ❌ 판단 불가 | ✅ |

아래는 각 유형의 실제 질문과 답이다.

---

## 3. 사례

### ① 단일 임계값 — 둘 다 맞힌다

한도가 기준 문장에 숫자로 그대로 있고 판정이 "측정값 > 한도?" 한 줄이면, 텍스트 방식도 맞힌다.

| 질문 | 엔진 판정 | 검색·LLM |
|---|---|---|
| AE 공기량 **2%** | ✗ 부적합 — 2.0 < 3.0 (KS F 4009) | ✗ 부적합 |
| 염화물 **0.45** | ✗ 부적합 — 0.45 > 0.30 (KS F 4009) | ✗ 부적합 |

> **교훈:** 단순 조회 질문은 굳이 엔진이 아니어도 된다.

### ② 계산 임계값 — 텍스트가 무너지는 지점

콘크리트 압축강도의 합격 한도는 문장에 숫자로 **없다.** `0.85 × 설계강도` 를 **계산**해야 나온다.

> **설계강도 24MPa, 28일 시험값 21MPa — 합격인가?**
> - 검색·LLM: "21은 24보다 작으니 미달 → **불합격**"  ❌
> - 엔진: `21 ≥ 0.85 × 24 = 20.4` → **✓ 합격**

21MPa는 기준(20.4)을 통과한다. 텍스트 방식은 0.85를 적용하지 못해 **합격품을 불합격으로 오판**했다.

> **교훈:** 한도가 *식*이면 검색은 무력하다. 실무에선 합격품 거짓 불합격 = 불필요한 철거·재시공·분쟁. (KS F 4009)

### ③ 범주별 한도 — 같은 값, 조건 따라 뒤집힘

물–결합재비(W/B) 한도는 노출등급마다 다르다. 측정값을 **0.55로 동일**하게 두고 등급만 바꾼다.

| 노출등급 | 한도 (KDS 14 20 40) | 엔진 판정 |
|---|---|---|
| **EC2** | 0.55 | ✓ 합격 — 0.55 ≤ 0.55 |
| **EC4** | 0.45 | ✗ 부적합 — 0.55 > 0.45 |

엔진은 등급별 한도표를 들고 양쪽 결정적으로 판정한다. 텍스트 방식은 등급 표를 찾으면 답하고
못 찾으면 "판단 불가"로 회피해 — **질문 한 글자 차이로 결과가 들쭉날쭉**했다.

> **교훈:** 조건 분기가 있는 한도는 "표를 찾았는지"에 운명이 갈린다. 엔진은 표를 규칙으로 들고 있다.

### ④ 시점 게이트 — 사고 당시, 그 법이 유효했나

책임 귀속은 "사고가 난 날 그 법이 시행 중이었나"에 달렸다. 중대재해처벌법 시행일은 **2022-01-27**.

| 사고 시점 | 엔진 판정 |
|---|---|
| **2021-06-01** 사망사고 | `not_applicable` — 시행 전, **소급 불가** |
| **2024-06-01** 사망사고 (체계 미이행) | `violated` — §4 / §9 |

텍스트 방식엔 "시행일"이라는 **시간 축 자체가 없어**, 두 사고를 구분하지 못하고 "판단 불가"로 답했다.

> **교훈:** 시간은 책임추적의 1급 축이다. 시행일을 한 번 틀리면 책임 귀속이 통째로 어긋난다.

---

## 4. LLM 단독은 왜·어디서 틀리나

범용 LLM은 널리 알려진 값(0.85fck, 시행일 2022-01-27)은 잘 맞힌다. 무너진 곳은 **일정했다.**

1. **시점 드리프트** — 개정된 기준을 *바뀐 줄 모르고* 옛 값으로 답한다.
   예: 굴착 안전기울기는 2021-11-19에 4분류로 재편됐는데, 폐지된 "보통흙 건지/습지" 분류로 답.
2. **프레임 혼동** — 같은 항목에 기준 체계가 둘 이상일 때 다른 축의 값을 섞는다.
   예: 철근 피복두께를 부재기반(기초·기둥) 대신 노출기반(흙접촉·수중) 값으로 답 — 둘 다 실재해 더 안 걸린다.
3. **틀려도 표시가 없다** — 위 둘 다 *확신 있게, 출처·개정일 없이* 답한다.
   엔진은 같은 규칙에 `revision: 2021-11-19` · `pending: [원문 대조 필요]` 를 들고 있어 "개정됨 / 미검증"을 구분한다.

핵심은 정확도가 아니다. **LLM도 자주 맞는다. 다만 맞았는지 보장·증명·재현할 수 없다.**

---

## 5. 정리

| 기준 | 검색·LLM 단독 | 온톨로지 엔진 |
|---|---|---|
| 단일 임계값 정확도 | 자주 맞음 | 항상 |
| 계산·범주·시점 | 거짓 판정·회피·불가 | 결정적 |
| 같은 입력 → 같은 결과 (보장) | ✗ | ✅ |
| 검증 가능 출처 (§·개정일) | ✗ | ✅ |
| 모르는 것을 표시 | ✗ — 그럴듯하게 채움 | ✅ — `not_applicable` / `pending` |

검측·책임추적에서 *"가끔 맞는 그럴듯한 답"* 은 실격이다. 합격품을 한 번 거짓 불합격하면
철거·분쟁으로, 시행일을 한 번 틀리면 책임 귀속 오판으로 이어진다. 그래서 이 저장소는
**LLM이 판정하는 것을 구조적으로 막고**(자연어 슬롯 채우기·결과 서술만 허용), 판정은 항상 엔진이 한다.

## 6. 직접 재현 — 이 문서 하나로

아래 스크립트를 저장소 루트에서 `why_ontology_demo.py` 로 저장해 실행하면, 위 엔진 판정 8/8 이
**결정적으로 재현된다(키 불필요).** `ANTHROPIC_API_KEY`(또는 `.env`)가 설정돼 있으면 'LLM
직접판정' 대조 열도 함께 출력된다. **판정은 언제나 엔진이 하며, LLM 열은 대조군일 뿐 어떤 판정에도 쓰이지 않는다.**

```bash
python why_ontology_demo.py          # 엔진 판정 8/8 — 키 불필요·결정적
python why_ontology_demo.py --json   # 기계가독 결과(JSON)
```

<details>
<summary><b>why_ontology_demo.py</b> — 전체 스크립트 (펼치기)</summary>

```python
"""why_ontology_demo — 같은 콘크리트·안전 질문을 두 방식에 돌려 차이를 실측한다.

  ① LLM 직접판정 (비신뢰 기준선) — 검색·엔진 없이 모델이 바로 합/부를 말함. 키 있을 때만.
  ② 온톨로지 엔진 (이 저장소) — 측정값을 결정적 규칙으로 계산해 판정 + 근거 §.

요지: 한도가 문장에 숫자로 적힌 단순 조회는 ①도 맞히지만, 한도를 '계산'해야 하거나
(0.85·fck), 범주에 따라 한도가 달라지거나(노출등급), 시점 게이트(법 시행일)가 걸리면
①은 그럴듯하게 빗나간다. ②는 같은 입력에 항상 같은 판정 + 개정일·출처를 들고 있다.

실행 (저장소 루트에서):
  python why_ontology_demo.py            # 엔진 판정만(키 불필요·결정적)
  python why_ontology_demo.py --json     # 결과를 JSON 으로
  # ANTHROPIC_API_KEY(또는 .env) 설정 시 'LLM 직접판정' 열이 함께 출력된다.

판정은 언제나 엔진이 한다. LLM 열은 '엔진이 왜 필요한지'를 보여주기 위한 대조군일 뿐,
이 저장소의 어떤 판정에도 쓰이지 않는다.
"""
from __future__ import annotations
import json
import os
import sys

sys.path.insert(0, os.getcwd())   # 저장소 루트에서 실행하는 것을 가정
sys.stdout.reconfigure(encoding="utf-8")

import yaml
import paths                       # 루트 sentinel 기반 — condition_rules/ 위치 자동 탐색
from engine import conditions as C
from engine import org_judgment as O

# ── 트랩 배터리 ────────────────────────────────────────────────────────────
# 각 항목: 자연어 질문 + 엔진 입력(조건 rec 또는 조직×사고) + 정답 메모.
# 4 범주: A 단일임계값 / B 계산임계값 / C 범주별 한도 / D 시점 게이트.
BATTERY = [
    {"cat": "A 단일임계값", "q": "AE 콘크리트 공기량 측정값이 2%다. 적합한가?",
     "kind": "condition", "rule": "concrete_air_ae",
     "rec": {"work_kind": "콘크리트타설", "test_values": {"air_pct": 2.0}},
     "truth": "부적합 — 2.0 < 3.0 (KS F 4009)"},
    {"cat": "A 단일임계값", "q": "콘크리트 염화물 함유량이 0.45 kg/㎥다. 적합한가?",
     "kind": "condition", "rule": "concrete_chloride",
     "rec": {"work_kind": "콘크리트타설", "test_values": {"chloride_kg_m3": 0.45}},
     "truth": "부적합 — 0.45 > 0.30 (KS F 4009)"},
    {"cat": "B 계산임계값", "q": "설계기준강도 24MPa인데 28일 압축강도 시험값이 19MPa다. 합격인가?",
     "kind": "condition", "rule": "concrete_strength_acceptance",
     "rec": {"work_kind": "콘크리트타설", "design_fck_mpa": 24, "test_values": {"strength_mpa": 19.0}},
     "truth": "부적합 — 19 < 0.85×24 = 20.4 (KS F 4009)"},
    {"cat": "B 계산임계값", "q": "설계기준강도 24MPa인데 28일 압축강도 시험값이 21MPa다. 합격인가?",
     "kind": "condition", "rule": "concrete_strength_acceptance",
     "rec": {"work_kind": "콘크리트타설", "design_fck_mpa": 24, "test_values": {"strength_mpa": 21.0}},
     "truth": "합격 — 21 ≥ 0.85×24 = 20.4 (naive 21<24 비교는 거짓 불합격)"},
    {"cat": "C 범주별 한도", "q": "EC2(탄산화) 노출환경인데 물결합재비가 0.55다. 적합한가?",
     "kind": "condition", "rule": "durability_exposure_wb",
     "rec": {"work_kind": "콘크리트타설", "exposure_class": "EC2", "test_values": {"wb_ratio": 0.55}},
     "truth": "합격 — EC2 상한 0.55, 0.55 ≤ 0.55 (KDS 14 20 40)"},
    {"cat": "C 범주별 한도", "q": "EC4(탄산화) 노출환경인데 물결합재비가 0.55다. 적합한가?",
     "kind": "condition", "rule": "durability_exposure_wb",
     "rec": {"work_kind": "콘크리트타설", "exposure_class": "EC4", "test_values": {"wb_ratio": 0.55}},
     "truth": "부적합 — EC4 상한 0.45, 0.55 > 0.45 (같은 0.55인데 등급만 다름)"},
    {"cat": "D 시점 게이트", "q": "2021-06-01 발생한 사망 2명 건설사고. 원도급사 경영책임자가 중대재해처벌법 위반인가?",
     "kind": "org", "rule": "serious_accident_corporate_duty",
     "org": {"id": "원도급사", "org_role": "원도급", "subcontract_tier": 0, "safety_health_system": False},
     "incident": {"event_date": "2021-06-01", "fatalities": 2},
     "truth": "not_applicable — 2022-01-27 시행 전 사고, 소급 불가 (중대재해처벌법 부칙)"},
    {"cat": "D 시점 게이트", "q": "2024-06-01 발생한 사망 2명 건설사고. 원도급사 경영책임자(체계 미이행)가 중대재해처벌법 위반인가?",
     "kind": "org", "rule": "serious_accident_corporate_duty",
     "org": {"id": "원도급사", "org_role": "원도급", "subcontract_tier": 0, "safety_health_system": False},
     "incident": {"event_date": "2024-06-01", "fatalities": 2},
     "truth": "violated — 시행 후·경영책임자·사망재해·체계 미이행 (중대재해처벌법 §4/§9)"},
]

MARK = {"compliant": "✓ 합격", "violated": "✗ 부적합", "not_applicable": "— 해당없음", "판정보류": "? 판정보류"}


def _load_condition_rule(name: str) -> dict:
    return yaml.safe_load(open(paths.P("condition_rules", f"{name}.yaml"), encoding="utf-8"))


def engine_verdict(item: dict) -> dict:
    """온톨로지 엔진 판정 — 결정적. 키·네트워크 불필요."""
    if item["kind"] == "condition":
        rule = _load_condition_rule(item["rule"])
        r = C.evaluate_condition(item["rec"], rule)
        std = (r.get("authority") or rule.get("authority") or {}).get("standard") \
            or (rule.get("authority") or {}).get("law") or ""
        return {"verdict": r["verdict"], "reason": r.get("reason", ""), "basis": std}
    # org × incident
    for v in O.judge_org(item["org"], item["incident"]):
        if v["rule_id"].startswith(item["rule"]):
            return {"verdict": v["verdict"], "reason": v.get("reason", ""),
                    "basis": v.get("regime") or "중대재해처벌법"}
    return {"verdict": "not_applicable", "reason": "해당 룰 미도달", "basis": ""}


_LLM_SYS = (
    "너는 한국 건설 검측 보조다. 다음 질문에 '합격'·'부적합'·'판정불가' 중 하나로 먼저 답하고, "
    "근거가 된 기준(표준번호)과 한도 수치를 한 줄로 덧붙여라. 확실하지 않으면 추측이라고 밝혀라. "
    "(이 답은 결정적 엔진 판정과 대조하기 위한 참고용이다.)"
)


def llm_verdict(item: dict):
    """LLM 직접판정 — 검색·엔진 없이 모델이 바로 답함. 키 있을 때만, 없으면 None.
    이 저장소의 판정엔 절대 쓰이지 않는다(대조군)."""
    try:
        from rag import llm
    except Exception:
        return None
    if not llm.available():
        return None
    try:
        return (llm.complete(_LLM_SYS, item["q"], max_tokens=200) or "").strip().replace("\n", " ")
    except Exception as e:
        return f"(LLM 호출 실패: {type(e).__name__})"


def run():
    rows = []
    for it in BATTERY:
        eng = engine_verdict(it)
        rows.append({"category": it["cat"], "question": it["q"],
                     "engine": eng, "truth": it["truth"], "llm": llm_verdict(it)})
    return rows


def print_table(rows):
    has_llm = any(r["llm"] is not None for r in rows)
    print("=" * 78)
    print(" 온톨로지 없이(LLM 직접판정) vs 온톨로지 엔진 — 콘크리트·안전 검측")
    print("=" * 78)
    if not has_llm:
        print(" * LLM 열 생략: ANTHROPIC_API_KEY 미설정 (엔진 판정만 표시 — 결정적).")
        print("   키를 .env 에 넣으면 'LLM 직접판정' 대조가 함께 나온다.")
    print()
    cat = None
    for r in rows:
        if r["category"] != cat:
            cat = r["category"]
            print(f"\n[{cat}]")
        eng = r["engine"]
        v = MARK.get(eng["verdict"], eng["verdict"])
        detail = eng["reason"] or eng["verdict"]
        print(f"  Q. {r['question']}")
        print(f"     ├ 엔진     : {v}  ({detail})  근거 {eng['basis']}")
        if r["llm"] is not None:
            print(f"     ├ LLM 직접 : {r['llm']}")
        print(f"     └ 정답     : {r['truth']}")
    print("\n" + "=" * 78)
    print(" 엔진: 8/8 결정적 판정 + 근거 §. 같은 입력 → 항상 같은 결과.")
    print(" LLM 직접판정은 A(단일임계값)는 맞혀도 B(계산)·C(범주)·D(시점)에서 빗나간다.")
    print("=" * 78)


if __name__ == "__main__":
    rows = run()
    if "--json" in sys.argv:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print_table(rows)
```

</details>

설계 배경은 [`../rag/README.md`](../rag/README.md) 참조.
