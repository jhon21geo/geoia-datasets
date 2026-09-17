from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "prospectividad"}


def test_index_inlines_css_and_js():
    r = client.get("/")
    assert r.status_code == 200
    html = r.text
    assert "app-shell" in html
    assert ".sidebar" in html
    assert "function mulberry32" in html
    assert 'href="css/style.css"' not in html
    assert 'src="js/map.js"' not in html
    assert r.headers.get("x-geoia-visor") == "datasets"


def test_static_assets():
    css = client.get("/css/style.css")
    assert css.status_code == 200
    assert "app-shell" in css.text
    js = client.get("/js/map.js")
    assert js.status_code == 200
    assert "L.map" in js.text
    geo = client.get("/data/ingemmet_superficie.geojson")
    assert geo.status_code == 200
    assert geo.json()["type"] == "FeatureCollection"
