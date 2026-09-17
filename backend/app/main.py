from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def _frontend() -> Path:
    if (HERE / "index.html").is_file():
        return HERE
    return ROOT / "prospectividad"


FRONTEND = _frontend()

app = FastAPI(
    title="GeoIA — Prospectividad",
    description="Análisis prospectivo minero para el Perú: teledetección, DEM y ML espacial",
    version="0.1.0",
)


def _file(rel: str, media: str) -> FileResponse:
    path = FRONTEND / rel
    if not path.is_file():
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    return FileResponse(path, media_type=media)


def _inlined_index() -> str:
    html = (FRONTEND / "index.html").read_text(encoding="utf-8")
    css = (FRONTEND / "css" / "style.css").read_text(encoding="utf-8")
    js = (FRONTEND / "js" / "map.js").read_text(encoding="utf-8")
    html = html.replace(
        '<link rel="stylesheet" href="css/style.css">',
        "<style>\n" + css + "\n</style>",
    )
    html = html.replace(
        '<script src="js/map.js"></script>',
        "<script>\n" + js + "\n</script>",
    )
    return html


@app.on_event("startup")
def _startup():
    print("GeoIA visor: HTML en GET / (css+js inline)", flush=True)


def _index_response() -> HTMLResponse:
    return HTMLResponse(
        _inlined_index(),
        headers={"X-GeoIA-Visor": "datasets", "Cache-Control": "no-store"},
    )


@app.get("/health")
@app.head("/health")
def health():
    return {"status": "ok", "service": "prospectividad"}


@app.get("/")
@app.head("/")
def index():
    return _index_response()


@app.get("/index.html")
def index_html():
    return _index_response()


@app.get("/css/style.css")
def css_file():
    return _file("css/style.css", "text/css")


@app.get("/js/map.js")
def js_file():
    return _file("js/map.js", "text/javascript")


@app.get("/data/ingemmet_superficie.geojson")
def geojson_file():
    return _file("data/ingemmet_superficie.geojson", "application/geo+json")


class JobResult(BaseModel):
    status: str
    output_path: str | None = None
    metrics: dict | None = None
    detail: str | None = None


class IndexRequest(BaseModel):
    scene_id: str
    indices: list[str] = Field(default_factory=lambda: ["arcillas", "oxidos_hierro", "propilitica"])


class LineamentRequest(BaseModel):
    dem_id: str
    min_length_m: float = 300.0
    cell_size_m: float = 250.0


class WeightedOverlayRequest(BaseModel):
    layer_ids: list[str]
    weights: dict[str, float] | None = None
    output_name: str = "favorabilidad_overlay"


class TrainRequest(BaseModel):
    positive_points_path: str
    background_points_path: str
    feature_cols: list[str]
    model_name: str = "prospectividad_xgb"


class PredictRequest(BaseModel):
    layer_ids: list[str]
    model_name: str
    feature_order: list[str]
    output_name: str = "favorabilidad_ml"


def _demo_job(name: str) -> JobResult:
    return JobResult(
        status="demo",
        detail=(
            f"{name}: el visor ya interpola INGEMMET en el navegador. "
            "El procesamiento raster/XGBoost completo vive en el backend original."
        ),
        metrics={"mode": "frontend-demo"},
    )


@app.post("/raster/indices", tags=["raster"])
def compute_indices(body: IndexRequest):
    return _demo_job("índices " + body.scene_id)


@app.post("/raster/lineaments", tags=["raster"])
def compute_lineaments(body: LineamentRequest):
    return _demo_job("lineamientos " + body.dem_id)


@app.post("/vector/distance-to-structures", tags=["vector"])
def distance_to_structures(
    layer_id: str = Query(...),
    reference_raster_id: str = Query(...),
):
    return _demo_job(f"distancia {layer_id} → {reference_raster_id}")


@app.post("/model/weighted-overlay", tags=["model"])
def run_weighted_overlay(body: WeightedOverlayRequest):
    return _demo_job("overlay " + body.output_name)


@app.post("/model/train", tags=["model"])
def train(body: TrainRequest):
    return _demo_job("train " + body.model_name)


@app.post("/model/predict", tags=["model"])
def predict(body: PredictRequest):
    return _demo_job("predict " + body.output_name)
