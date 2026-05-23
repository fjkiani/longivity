"""Render entry point — Render clones to /opt/render/project/src/ which IS the repo root."""
import sys
import os

# Render's working directory is the repo root (/opt/render/project/src/)
# Add src/ subdirectory so 'longivity' package is importable
_repo_root = os.path.dirname(os.path.abspath(__file__))
_src_dir = os.path.join(_repo_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from longivity.app import app  # noqa: F401, E402

__all__ = ["app"]
