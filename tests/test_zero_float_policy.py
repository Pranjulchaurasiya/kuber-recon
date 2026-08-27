"""AST Test Suite: Enforcing Zero-Float Policy across all codebase files."""

import ast
import os
from pathlib import Path


def test_no_floats_in_source_code():
    """Verify that no `float()` calls exist in `src/kuber_recon/`."""
    src_dir = Path(__file__).parent.parent / "src" / "kuber_recon"
    assert src_dir.exists()

    violations = []

    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith(".py") and file != "cli.py":  # CLI can use float for perf timer
                file_path = Path(root) / file
                with open(file_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(file_path))

                for node in ast.walk(tree):
                    # Check for float() constructor calls
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                        if node.func.id == "float":
                            violations.append(f"{file_path}:{node.lineno} - float() call detected")

    assert len(violations) == 0, f"Zero-Float AST Policy Violations detected:\n" + "\n".join(violations)
