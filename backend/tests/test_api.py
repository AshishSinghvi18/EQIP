import os
import sys
from pathlib import Path

DB_PATH = Path("backend/tests/test_eqip.db")
if DB_PATH.exists():
    DB_PATH.unlink()

os.environ["EQIP_DATABASE_URL"] = "sqlite:///./backend/tests/test_eqip.db"
os.environ["EQIP_RESET_DEMO_DATA"] = "true"

sys.path.insert(0, str(Path("backend").resolve()))

from fastapi.testclient import TestClient
from app.main import app


def test_dashboard_overview_and_heatmap():
    with TestClient(app) as client:
        overview = client.get("/api/dashboard/overview")
        assert overview.status_code == 200
        cards = overview.json()["cards"]
        assert any(card["label"] == "quality_index" for card in cards)

        heatmap = client.get("/api/dashboard/module-heatmap")
        assert heatmap.status_code == 200
        items = heatmap.json()["items"]
        assert len(items) >= 8
        auth = next(item for item in items if item["module"] == "Auth")
        payment = next(item for item in items if item["module"] == "Payment")
        assert auth["bug_count"] >= 6
        assert payment["severity_index"] >= auth["severity_index"]


def test_breakdowns_and_scoring():
    with TestClient(app) as client:
        breakdown = client.get("/api/dashboard/bug-breakdown", params={"module": "Auth"})
        assert breakdown.status_code == 200
        labels = {item["label"] for item in breakdown.json()["items"]}
        assert "Validation" in labels

        leaderboard = client.get("/api/scoring/leaderboard")
        assert leaderboard.status_code == 200
        assert len(leaderboard.json()["items"]) > 0

        chain = client.get("/api/dashboard/chain-view", params={"module": "Payment"})
        assert chain.status_code == 200
        assert len(chain.json()["items"]) > 0
