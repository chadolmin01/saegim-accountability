"""전체 회귀 — staffing/trail + conditions. python run_all_tests.py"""
import sys, subprocess
sys.stdout.reconfigure(encoding="utf-8")
codes = []
# 테스트는 tests 패키지 모듈(-m, 루트 cwd에서 engine·paths 해석); check_pack은 engine 의존 없는 스크립트
TASKS = [["-m", "tests.test_rules"], ["-m", "tests.test_conditions"], ["-m", "tests.test_extra"],
         ["-m", "tests.test_depth"], ["-m", "tests.fidelity_suite"],
         ["opencrab_pack/check_pack_completeness.py"]]
for t in TASKS:
    print(f"\n### {t[-1]} ###")
    r = subprocess.run([sys.executable, *t], capture_output=True, text=True, encoding="utf-8")
    print(r.stdout.strip().splitlines()[-1] if r.stdout else r.stderr[-200:])
    codes.append(r.returncode)
print("\n" + ("=== 전체 PASS ===" if not any(codes) else "=== 실패 있음 ==="))
sys.exit(1 if any(codes) else 0)
