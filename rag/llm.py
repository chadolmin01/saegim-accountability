"""LLM 백엔드 — 슬롯필러(a)·생성층(b)이 Anthropic API 에 닿는 유일한 통로.

설계 원칙
  · 키는 환경변수 ANTHROPIC_API_KEY 또는 ROOT/.env(gitignore)에서만. **코드·커밋에 절대 하드코딩 안 함.**
  · available()=False(키·SDK 없음)면 (a)는 정규식, (b)는 템플릿으로 결정적 폴백 → 키 없는 CI·로컬도 그대로 동작.
  · **LLM 은 슬롯 채우기·결과 서술만. 판정은 절대 안 한다**(판정은 결정적 엔진 몫).
  · 호출은 timeout·max_retries 로 감싸고, 실패 시 호출부가 폴백하도록 예외를 그대로 올린다.

환경변수
  ANTHROPIC_API_KEY        필수(활성화)
  SAEGIM_LLM_MODEL         전체 기본 모델 (기본: haiku — 슬롯추출·서술은 경량이면 충분)
  SAEGIM_LLM_MODEL_SLOTS   (a) 슬롯필러 전용 오버라이드
  SAEGIM_LLM_MODEL_NARRATE (b) 생성층 전용 오버라이드
  SAEGIM_LLM_TIMEOUT       초 (기본 30)
  SAEGIM_LLM_RETRIES       SDK 재시도 횟수 (기본 2)
"""
from __future__ import annotations
import json
import os
import re

DEFAULT_MODEL = "claude-haiku-4-5-20251001"


def _load_dotenv():
    """ROOT/.env(gitignore)에서 키 로드 — 이미 환경에 있으면 건드리지 않음(setdefault)."""
    try:
        import paths
        path = paths.P(".env")
    except Exception:
        return
    if not os.path.exists(path):
        return
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except OSError:
        pass


_load_dotenv()


def model(task=None):
    """작업별 모델 — SAEGIM_LLM_MODEL_<TASK> > SAEGIM_LLM_MODEL > 기본."""
    if task:
        m = os.environ.get(f"SAEGIM_LLM_MODEL_{task.upper()}")
        if m:
            return m
    return os.environ.get("SAEGIM_LLM_MODEL") or DEFAULT_MODEL


def available():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False
    try:
        import anthropic  # noqa: F401
        return True
    except ImportError:
        return False


_client = None


def _get_client():
    global _client
    if _client is None:
        import anthropic
        _client = anthropic.Anthropic(
            timeout=float(os.environ.get("SAEGIM_LLM_TIMEOUT", "30")),
            max_retries=int(os.environ.get("SAEGIM_LLM_RETRIES", "2")),
        )
    return _client


def complete(system, user, max_tokens=600, task=None):
    """문자열 응답. available()=True 일 때만 호출. API 오류는 그대로 올림(호출부가 폴백)."""
    msg = _get_client().messages.create(
        model=model(task), max_tokens=max_tokens, system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


def complete_json(system, user, max_tokens=600, task=None):
    """응답에서 JSON 객체만 파싱. 파싱 실패 시 {} (호출부가 검증/폴백 책임)."""
    txt = complete(system, user, max_tokens, task)
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group())
    except json.JSONDecodeError:
        return {}


def selfcheck():
    """라이브 점검 — 키로 1콜 왕복. (ok: bool, detail: str). 비용 최소(짧은 프롬프트)."""
    if not available():
        return False, "available()=False (ANTHROPIC_API_KEY 또는 anthropic SDK 없음)"
    try:
        out = complete("간결한 점검기.", "OK 한 단어만 답하라.", max_tokens=8)
        return True, f"model={model()} resp={out!r}"
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
