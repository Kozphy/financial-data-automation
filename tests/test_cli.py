"""CLI help and argument errors."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "run_pipeline.py"
SAMPLE = ROOT / "data" / "sample" / "sample_transactions.csv"
ZH_SAMPLE = ROOT / "data" / "sample" / "sample_transactions_zh_tw.csv"


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_help_is_not_an_input_file() -> None:
    for flag in ("--help", "-h"):
        result = _run([flag])
        assert result.returncode == 0
        assert "Pipeline failed" not in result.stderr
        assert "usage" in result.stdout.lower()
        assert "--mapping" in result.stdout
        assert "zh-TW" in result.stdout


def test_missing_and_unknown_arguments() -> None:
    missing = _run([])
    assert missing.returncode == 2
    assert "Pipeline failed" not in missing.stderr

    unknown = _run([str(SAMPLE), "--not-a-real-flag"])
    assert unknown.returncode == 2
    assert "Pipeline failed" not in unknown.stderr

    bad_language = _run([str(SAMPLE), "--language", "fr"])
    assert bad_language.returncode == 2
    assert "Unsupported language" in bad_language.stderr
    assert "Pipeline failed" not in bad_language.stderr


def test_cli_runs_sample_and_chinese_report(tmp_path: Path) -> None:
    english = _run(
        [
            str(SAMPLE),
            "--output-dir",
            str(tmp_path / "en"),
            "--evidence",
            str(tmp_path / "en.jsonl"),
        ]
    )
    assert english.returncode == 0
    assert "Pipeline completed successfully." in english.stdout
    assert "Quality score:" in english.stdout

    chinese = _run(
        [
            str(ZH_SAMPLE),
            "--language",
            "zh-TW",
            "--output-dir",
            str(tmp_path / "zh"),
            "--evidence",
            str(tmp_path / "zh.jsonl"),
        ]
    )
    assert chinese.returncode == 0, chinese.stderr
    assert "清理完成" in chinese.stdout
    assert "品質分數" in chinese.stdout
    assert "交易編號 → transaction_id" in chinese.stdout
    assert (tmp_path / "zh" / "cleaned_data.xlsx").exists()
