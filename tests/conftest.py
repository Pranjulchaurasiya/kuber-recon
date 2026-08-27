"""Pytest configuration and shared fixtures for KuberRecon."""

import sys
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from kuber_recon.generator import ChaosDataGenerator


@pytest.fixture
def chaos_generator():
    return ChaosDataGenerator(seed=42)
