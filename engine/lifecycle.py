"""유지/시공 단계 게이트 — 시공단계 룰이 유지단계 시나리오에 오발하지 않도록.

시나리오 `project.lifecycle_stage`(기본 '시공')와 룰 `lifecycle_stage`(기본 '시공')를 대조.
같은 단계만 적용하고, '전체'는 양쪽 모두 적용한다. 유지단계 사건에서
공사감리자·착공신고서 등 시공 전용 룰이 not_applicable로 빠지게 해 false positive를 제거한다.

기본값이 '시공'이라 일반(시공) 시나리오·룰은 영향 0 — 유지단계 시나리오에만 게이트가 작동.
"""
DEFAULT_STAGE = "시공"
ALL_STAGES = "전체"


def scenario_stage(project: dict) -> str:
    return ((project or {}).get("lifecycle_stage") or DEFAULT_STAGE)


def applies(project: dict, rule: dict) -> bool:
    """이 룰이 이 시나리오의 생애단계에 적용되나."""
    s = scenario_stage(project)
    r = rule.get("lifecycle_stage", DEFAULT_STAGE)
    return r == ALL_STAGES or s == ALL_STAGES or s == r
