"""경로 앵커 — 모든 룰/데이터 경로를 repo 루트 기준(CWD 독립)으로.

왜: 로더들이 CWD-상대 glob("condition_rules/*.yaml")이라, 루트 아닌 곳에서 실행하면
빈 리스트 → 룰 0개 → 위반 0건인데 크래시 없음(조용한 실패). ROOT 앵커로 차단.

루트 탐지는 *이 파일 위치가 아니라 sentinel(condition_rules/ 또는 .git)* 기준 →
나중에 모듈을 engine/ 등 하위폴더로 옮겨도 안 깨짐.
"""
from __future__ import annotations
import glob as _glob
from pathlib import Path


def _find_root() -> Path:
    start = Path(__file__).resolve().parent
    for cand in [start, *start.parents]:
        if (cand / "condition_rules").is_dir() or (cand / ".git").is_dir():
            return cand
    return start


ROOT = _find_root()


def P(*parts) -> str:
    """루트 기준 절대경로 문자열."""
    return str(ROOT.joinpath(*parts))


def rule_glob(family: str):
    """룰 패밀리 yaml 목록 (정렬, 루트 앵커)."""
    return sorted(_glob.glob(str(ROOT / family / "*.yaml")))
