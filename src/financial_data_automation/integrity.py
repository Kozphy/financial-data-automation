"""SHA-256 evidence for input and output artifacts.

Hashes detect byte changes against a trusted record. They do not make local
JSONL immutable, prove authorship, or provide secure remote attestation.
"""
from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def hash_outputs(output_dir: str | Path, filenames: list[str]) -> dict[str, str]:
    root = Path(output_dir)
    return {name: sha256_file(root / name) for name in filenames}


def verify_hashes(output_dir: str | Path, hashes: dict[str, str]) -> list[str]:
    """Return missing or modified artifact names, without trusting filenames blindly."""
    root = Path(output_dir).resolve()
    mismatches: list[str] = []
    for name, expected in hashes.items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file() or sha256_file(path) != expected:
            mismatches.append(name)
    return mismatches
