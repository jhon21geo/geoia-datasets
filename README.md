# geoia-datasets

Datos de GeoIA (espectros, superficie INGEMMET y sondajes sintéticos) y visor de **prospectividad**.

## Por qué geoia.site/prospectividad se veía en crudo

Coolify levanta **Prospectividad App** con `backend/Dockerfile`. Ese contenedor es FastAPI (`GET /health` → `{"service":"prospectividad"}`) y **sí devuelve el HTML**, pero **no publica** `css/style.css` ni `js/map.js` (404 JSON). El navegador entonces muestra el markup sin layout: botón nativo «Seleccionar archivo», títulos apilados, sin mapa.

Este repositorio no era el Git source de Coolify, así que copiar archivos aquí no cambiaba la URL pública.

## Cómo publicarlo

En Coolify, **Prospectividad App** debe construir **este** repositorio:

- Git: `https://github.com/jhon21geo/geoia-datasets`
- Dockerfile: `backend/Dockerfile`
- Puerto: `8003` (`STREAMLIT_SERVER_PORT=8003` ya lo usa el CMD)
- Path del proxy: `/prospectividad`

El FastAPI ahora:

1. Incrusta CSS y JS dentro del HTML de `GET /` (así el visor funciona aunque fallen las rutas estáticas).
2. Sirve `/css/style.css`, `/js/map.js` y `/data/ingemmet_superficie.geojson`.
3. Mantiene `/health` y las rutas `/raster/*` `/model/*` en modo demo.

Local:

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8003
```

Abre `http://127.0.0.1:8003`.
