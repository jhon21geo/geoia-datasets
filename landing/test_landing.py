from pathlib import Path

ROOT = Path(__file__).resolve().parent
HTML = (ROOT / "index.html").read_text(encoding="utf-8")


def test_landing_links_dominios_ml():
    assert 'href="/dominios-ml/"' in HTML
    assert "<h3>Dominios ML</h3>" in HTML
    assert "Cinco herramientas, un mismo flujo" in HTML
    assert 'href="/prospectividad/"' in HTML
    assert (ROOT / "img" / "card-rqd.jpg").is_file()
