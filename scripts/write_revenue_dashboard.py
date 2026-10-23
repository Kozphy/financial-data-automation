"""Write docs/commercial/revenue-dashboard.xlsx."""

from pathlib import Path

from financial_data_automation.dashboard import write_dashboard

if __name__ == "__main__":
    destination = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "commercial"
        / "revenue-dashboard.xlsx"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    write_dashboard(destination)
