"""Mutation Test Suite: Proving Non-LLM Decoupling in Arithmetic and Tax Solvers."""

import ast
import os
from pathlib import Path


def test_no_llm_imports_in_solvers_and_tax():
    """Verify that `engine.py`, `tax.py`, and `actions.py` NEVER import an LLM library."""
    src_dir = Path(__file__).parent.parent / "src" / "kuber_recon"
    forbidden_modules = {
        "openai", "anthropic", "langchain", "llama_index", "litellm",
        "google.generativeai", "transformers", "crewai", "autogen", "mistralai", "cohere",
    }

    violations = []
    core_files = ["engine.py", "tax.py", "actions.py", "types.py", "assurance.py", "escrow.py"]

    for file_name in core_files:
        file_path = src_dir / file_name
        if not file_path.exists():
            continue
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(alias.name.startswith(m) for m in forbidden_modules):
                        violations.append(f"{file_name} imports forbidden LLM: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module and any(node.module.startswith(m) for m in forbidden_modules):
                    violations.append(f"{file_name} imports forbidden LLM: {node.module}")

    assert len(violations) == 0, f"Non-LLM Math Decoupling Violations detected:\n" + "\n".join(violations)
