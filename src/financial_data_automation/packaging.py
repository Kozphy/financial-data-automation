"""Build a source ZIP that excludes audit logs and local environments."""

from __future__ import annotations

import zipfile
from pathlib import Path

INCLUDED = (
    "src",
    "tests",
    "data/sample",
    "docs",
    "pyproject.toml",
    "requirements.txt",
    "README.md",
    "run_pipeline.py",
)
EXCLUDED_PARTS = {".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".venv", "evidence"}


def build_toolkit_zip(root: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for relative in INCLUDED:
            path = root / relative
            if path.is_file():
                archive.write(path, relative.replace("\\", "/"))
                continue
            for file_path in path.rglob("*"):
                if not file_path.is_file():
                    continue
                if EXCLUDED_PARTS.intersection(file_path.parts):
                    continue
                arcname = file_path.relative_to(root).as_posix()
                archive.write(file_path, arcname)
    return destination
