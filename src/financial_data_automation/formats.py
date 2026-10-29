"""Taiwan-friendly date and amount parsing.

Gregorian dates and plain numbers keep the previous pandas behavior.
Additional accepted forms:

- ROC (民國) dates such as ``113/05/01``, ``099/01/05``, ``民國113年5月1日``
- Gregorian dates written with Chinese units, such as ``2024年5月1日``
- TWD and other currency amounts: ``NT$1,234.50``, full-width digits,
  and accounting parentheses for negatives ``(1,234.50)``
"""

from __future__ import annotations

import math
import re
from datetime import datetime
from typing import Any

import pandas as pd

# Returned by ROC/CJK parsers when the text is not that shape at all.
_NOT_THIS_SHAPE = object()

_ROC_SEPARATED = re.compile(
    r"^\s*(?:民國\s*)?(?P<year>\d{3})\s*[/\-.]\s*(?P<month>\d{1,2})\s*[/\-.]\s*"
    r"(?P<day>\d{1,2})\s*日?"
    r"(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?\s*$"
)
_ROC_PREFIXED = re.compile(
    r"^\s*民國\s*(?P<year>\d{1,3})\s*[/\-.]\s*(?P<month>\d{1,2})\s*[/\-.]\s*"
    r"(?P<day>\d{1,2})\s*日?"
    r"(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?\s*$"
)
_CJK_YMD = re.compile(
    r"^\s*(?:(?P<era>民國)\s*)?(?P<year>\d{1,4})\s*年\s*(?P<month>\d{1,2})\s*月\s*"
    r"(?P<day>\d{1,2})\s*日?"
    r"(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?\s*$"
)
_CURRENCY_RE = re.compile(
    r"NT\$|US\$|HK\$|NTD|TWD|USD|RMB|CNY|JPY|EUR|元|圓",
    re.IGNORECASE,
)


def to_halfwidth(text: str) -> str:
    """Convert full-width ASCII (digits, punctuation, letters) to half-width."""
    chars: list[str] = []
    for ch in text:
        code = ord(ch)
        if code == 0x3000:
            chars.append(" ")
        elif 0xFF01 <= code <= 0xFF5E:
            chars.append(chr(code - 0xFEE0))
        else:
            chars.append(ch)
    return "".join(chars)


def _timestamp(year: int, month: int, day: int) -> pd.Timestamp:
    try:
        return pd.Timestamp(year=year, month=month, day=day)
    except (ValueError, pd.errors.OutOfBoundsDatetime):
        return pd.NaT


def _from_roc_parts(year_text: str, month_text: str, day_text: str, *, era: bool) -> pd.Timestamp:
    year = int(year_text)
    # Years below 1911 are 民國. A 3-digit field such as 099 is ROC even though
    # the numeric value is 99. Western years (1911+) stay Gregorian.
    if era or len(year_text) >= 3 or year < 1911:
        if year < 1911:
            year += 1911
    return _timestamp(year, int(month_text), int(day_text))


def parse_localized_date(text: str) -> pd.Timestamp | object:
    """
    Parse an ROC or Chinese Y-M-D string.

    Returns ``_NOT_THIS_SHAPE`` when ``text`` is not one of those patterns so
    the caller can fall back to Gregorian parsing.
    """
    separated = _ROC_SEPARATED.match(text)
    if separated is not None:
        return _from_roc_parts(
            separated.group("year"),
            separated.group("month"),
            separated.group("day"),
            era=text.strip().startswith("民國"),
        )
    prefixed = _ROC_PREFIXED.match(text)
    if prefixed is not None:
        return _from_roc_parts(
            prefixed.group("year"),
            prefixed.group("month"),
            prefixed.group("day"),
            era=True,
        )
    cjk = _CJK_YMD.match(text)
    if cjk is not None:
        return _from_roc_parts(
            cjk.group("year"),
            cjk.group("month"),
            cjk.group("day"),
            era=cjk.group("era") is not None,
        )
    return _NOT_THIS_SHAPE


def parse_date_value(value: Any) -> pd.Timestamp:
    """Parse one date cell, including ROC dates. Unparseable values become NaT."""
    if value is None:
        return pd.NaT
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return pd.NaT
        return value
    if isinstance(value, datetime):
        return pd.Timestamp(value)
    try:
        if not isinstance(value, str) and pd.isna(value):
            return pd.NaT
    except TypeError:
        pass

    if isinstance(value, str):
        text = to_halfwidth(value).strip()
        if text == "":
            return pd.NaT
        localized = parse_localized_date(text)
        if localized is not _NOT_THIS_SHAPE:
            return localized  # type: ignore[return-value]
        parsed = pd.to_datetime(text, errors="coerce")
        if pd.isna(parsed):
            return pd.NaT
        return pd.Timestamp(parsed)

    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return pd.NaT
    return pd.Timestamp(parsed)


def parse_date_series(series: pd.Series) -> pd.Series:
    """Parse a date column. Index is preserved. Failures are NaT."""
    values = [parse_date_value(value) for value in series.tolist()]
    return pd.to_datetime(pd.Series(values, index=series.index), errors="coerce")


def _is_missing_amount(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    try:
        return bool(pd.isna(value))
    except TypeError:
        return False


def parse_amount_value(value: Any) -> float:
    """
    Parse one amount cell.

    Accounting parentheses and a leading or trailing minus sign become negative.
    Currency symbols and thousands separators are ignored. Blank cells are NaN.
    """
    if isinstance(value, bool) or _is_missing_amount(value):
        return float("nan")
    if isinstance(value, (int, float)):
        number = float(value)
        if math.isnan(number):
            return float("nan")
        return number

    text = to_halfwidth(str(value)).strip()
    text = text.replace("\u2212", "-").replace("\u2013", "-")
    if text == "" or text.lower() in {"nan", "none", "null", "nat", "-"}:
        return float("nan")

    negative = False
    while text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()

    text = text.replace(",", "").replace(" ", "")
    text = _CURRENCY_RE.sub("", text)
    text = text.replace("$", "").strip()
    while text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()

    if text.startswith("+"):
        text = text[1:].strip()
    if text.startswith("-"):
        negative = True
        text = text[1:].strip()
    if text.endswith("-"):
        negative = True
        text = text[:-1].strip()
    if text == "" or text == "-":
        return float("nan")

    try:
        number = float(text)
    except ValueError:
        return float("nan")
    if negative:
        return -abs(number)
    return number


def parse_amount_series(series: pd.Series) -> pd.Series:
    """Parse an amount column to float64. Unparseable cells are NaN."""
    values = [parse_amount_value(value) for value in series.tolist()]
    return pd.Series(values, index=series.index, dtype="float64")
