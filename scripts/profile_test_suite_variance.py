"""
Profile test suite execution time across 5 consecutive runs and isolate top 10 slowest tests.
"""

import subprocess
import time

durations = []
for i in range(1, 6):
    t0 = time.perf_counter()
    res = subprocess.run(
        ["python", "-m", "pytest", "-p", "no:deepeval", "-p", "no:langsmith", "tests/", "-q", "--durations=10"],
        capture_output=True,
        text=True,
    )
    elapsed = time.perf_counter() - t0
    durations.append((i, elapsed, res.returncode, res.stdout))
    print(f"Run {i}: {elapsed:.2f}s (Exit code: {res.returncode})")

print("\n--- DETAILED PROFILING BREAKDOWN OF RUN 5 ---")
print(durations[-1][3])
