"""The cash workbook keeps forecasts off the actuals sheet."""

from pathlib import Path

from openpyxl import load_workbook

from financial_data_automation.dashboard import write_dashboard


def test_actuals_start_at_zero_and_forecasts_are_labeled(tmp_path: Path) -> None:
    path = tmp_path / "revenue-dashboard.xlsx"
    write_dashboard(path)
    workbook = load_workbook(path)
    actuals = workbook["Actuals"]
    assert actuals["H4"].value == 0
    assert actuals["L4"].value == "=H4-I4-J4-K4"
    assert actuals["E4"].value == '=IF(C4=0,"",D4/C4)'
    note = workbook["Hypothetical"]["A1"].value
    assert "Hypothetical" in note
    assert "Do not add this sheet into Actuals." in note
