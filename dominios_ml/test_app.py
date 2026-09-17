from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "dominios-ml"}


def test_index_inlines_css_and_js():
    r = client.get("/")
    assert r.status_code == 200
    html = r.text
    assert "Dominios ML" in html
    assert "app-shell" in html
    assert ".sidebar" in html
    assert "function boot" in html
    assert 'href="css/style.css"' not in html
    assert 'src="js/app.js"' not in html
    assert r.headers.get("x-geoia-visor") == "dominios-ml"


def test_summary_kpis():
    r = client.get("/api/summary")
    assert r.status_code == 200
    data = r.json()
    assert data["n"] == 2928
    assert data["holes"] == 24
    assert data["labeled"] == 2393
    assert data["unlabeled"] == 535
    assert len(data["domains"]) == 6
    codes = {d["code"] for d in data["domains"]}
    assert codes == {"Arg", "ArgAvd", "Fil", "Oxd", "Pro", "Sk"}


def test_scatter_and_hole():
    scatter = client.get("/api/scatter")
    assert scatter.status_code == 200
    body = scatter.json()
    assert body["n"] == 2928
    assert len(body["pc1"]) == 2928
    holeid = body["holeid"][0]
    hole = client.get(f"/api/hole/{holeid}")
    assert hole.status_code == 200
    assert hole.json()["n"] > 0


def test_models_rank_random_forest():
    r = client.get("/api/models")
    assert r.status_code == 200
    data = r.json()
    assert data["best_model"] == "random_forest"
    names = [row["modelo"] for row in data["ranking"]]
    assert names[0] == "random_forest"
    assert set(names) == {"random_forest", "knn", "neural_network", "svm"}
