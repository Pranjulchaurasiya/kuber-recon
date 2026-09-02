"""Run pytest programmatically and export machine-readable reports/test_results.json.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import pytest


class TestReportCollector:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def pytest_runtest_logreport(self, report):
        if report.when == "call" or (report.when == "setup" and report.skipped):
            outcome = "PASSED" if report.passed else ("SKIPPED" if report.skipped else "FAILED")
            self.tests.append({
                "nodeid": report.nodeid,
                "outcome": outcome,
                "duration_seconds": round(report.duration, 4),
            })
            if report.passed:
                self.passed += 1
            elif report.failed:
                self.failed += 1
            elif report.skipped:
                self.skipped += 1


def main():
    collector = TestReportCollector()
    root_dir = Path(__file__).parent.parent
    tests_dir = root_dir / "tests"

    start_time = datetime.now(timezone.utc)
    ret_code = pytest.main(["-q", str(tests_dir)], plugins=[collector])
    end_time = datetime.now(timezone.utc)

    report = {
        "timestamp": end_time.isoformat(),
        "duration_seconds": round((end_time - start_time).total_seconds(), 2),
        "total_tests": len(collector.tests),
        "passed": collector.passed,
        "failed": collector.failed,
        "skipped": collector.skipped,
        "pass_rate": f"{(collector.passed / len(collector.tests) * 100):.1f}%" if collector.tests else "0%",
        "exit_code": ret_code,
        "all_passed": collector.failed == 0 and collector.passed > 0,
        "classification": "VERIFIED_TEST_CORPUS",
        "tests": collector.tests,
    }

    out_file = root_dir / "reports" / "test_results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Test results saved to: {out_file.resolve()}")
    print(f"Summary: {collector.passed} passed, {collector.failed} failed, {collector.skipped} skipped.")


if __name__ == "__main__":
    main()
