"""Render entry point — adds src/ to sys.path so longivity is importable without pip install -e ."""
import sys
import os

# Make src/ importable without editable install
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from longivity.app import app  # noqa: F401, E402

__all__ = ["app"]
