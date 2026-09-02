"""Run entire test suite cleanly and report exact count.
"""

import sys
import pytest


def main():
    print("Executing full KuberRecon test suite...")
    code = pytest.main([
        "-q",
        "--tb=short",
        "-p", "no:deepeval",
        "-p", "no:langsmith",
        "tests",
    ])
    print(f"\nPytest exited with code: {code}")
    sys.exit(code)


if __name__ == "__main__":
    main()
