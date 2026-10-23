"""The distributable archive leaves audit logs behind."""

import zipfile
from pathlib import Path

from financial_data_automation.packaging import build_toolkit_zip


def test_toolkit_zip_contains_the_sample_and_omits_evidence(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    destination = tmp_path / "kozphy-financial-automation-toolkit.zip"
    build_toolkit_zip(root, destination)
    with zipfile.ZipFile(destination) as archive:
        names = set(archive.namelist())
    assert "data/sample/sample_transactions.csv" in names
    assert "docs/USER_GUIDE.md" in names
    assert not any(name.startswith("evidence/") or name.endswith("audit.jsonl") for name in names)
