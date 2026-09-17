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
    assert "basemaps.cartocdn.com" not in html
    assert "World_Light_Gray_Base" in html
    assert 'href="css/style.css"' not in html
    assert 'src="js/map.js"' not in html
    assert "Seleccionar archivo" not in html or "upload-zone" in html


def test_static_assets():
    css = client.get("/css/style.css")
    assert css.status_code == 200
    assert "app-shell" in css.text
    js = client.get("/js/map.js")
    assert js.status_code == 200
    assert "L.map" in js.text
    assert "basemaps.cartocdn.com" not in js.text
    assert "World_Light_Gray_Base" in js.text
    geo = client.get("/data/ingemmet_superficie.geojson")
    assert geo.status_code == 200
    assert geo.json()["type"] == "FeatureCollection"
