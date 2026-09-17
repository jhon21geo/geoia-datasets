# geoia-datasets

Datos de GeoIA y visor de **prospectividad** para Coolify.

## Error de Coolify: `COPY app ./app` → `"/app": not found`

El `backend/Dockerfile` original (imagen `ghcr.io/osgeo/gdal:ubuntu-small-3.9.0`) hace:

```
COPY requirements.txt .
COPY app ./app
```

El contexto de build es la **raíz del repo**. Sin la carpeta `app/` y sin `requirements.txt` en la raíz, el build se cancela.

Este repo ahora incluye exactamente eso:

```
requirements.txt
app/main.py
app/index.html
app/css/style.css
app/js/map.js
app/data/ingemmet_superficie.geojson
backend/Dockerfile
```

`GET /` incrusta CSS y JS en el HTML, así el visor no queda en crudo aunque fallen rutas estáticas.

En Coolify: Git `jhon21geo/geoia-datasets`, Dockerfile `backend/Dockerfile`, puerto `8003`, path `/prospectividad`. Luego redesplegar.
