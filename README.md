# geoia-datasets

Datos de GeoIA y visores para Coolify: **prospectividad** y **Dominios ML**.

## Dominios ML (producción)

Recurso Coolify **Dominios ML** — no uses el Dockerfile de prospectividad.

1. Repositorio Git: `jhon21geo/geoia-datasets`
2. Rama: `main`
3. Base Directory: vacío (raíz del repo)
4. Dockerfile: `Dockerfile`
5. Puerto: `8004` (`STREAMLIT_SERVER_PORT=8004`)
6. Start command (si Coolify no usa el `CMD` de la imagen):

```
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8004 --workers 1 --timeout 180
```

7. Dominio / ruta: `https://geoia.site/dominios-ml`
8. Healthcheck: `GET /health` → `{"status":"ok","service":"dominios-ml"}`

Luego **Rebuild**. En Coolify → Dominios ML → Domains, monta `geoia.site` con el path `/dominios-ml`.

La tarjeta de la landing (Landing App) es otro servicio: hay que añadir el enlace a `/dominios-ml/`.

## Prospectividad App

No cambies este recurso al Dockerfile de la raíz (ahora es Dominios ML).

1. Repositorio Git: `jhon21geo/geoia-datasets`
2. Rama: `main`
3. Dockerfile: `backend/Dockerfile`
4. Puerto: `8003`
5. Start command:

```
uvicorn app.main:app --host 0.0.0.0 --port 8003 --root-path /prospectividad
```

- Si el contexto es la raíz del repo → hace falta `./app` (está en `backend/app` cuando el contexto es `backend`)
- Si el Base Directory es `backend` → Dockerfile: `Dockerfile` dentro de `backend/`
