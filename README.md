# geoia-datasets

Datos de GeoIA y visor de **prospectividad** para Coolify.

## Error `COPY app ./app` → `"/app": not found`

Coolify construye con `backend/Dockerfile`. Esa instrucción toma `app/` **desde el contexto de build**, no desde donde está el Dockerfile.

- Si el contexto es la raíz del repo → hace falta `./app`
- Si el Base Directory / contexto es `backend` → hace falta `./backend/app`

Este repo tiene **las dos**:

```
app/                 # contexto = raíz
backend/app/         # contexto = carpeta backend
requirements.txt
backend/requirements.txt
backend/Dockerfile   # COPY requirements.txt .  y  COPY app ./app
```

En Coolify (Prospectividad App):

1. Repositorio Git: `jhon21geo/geoia-datasets`
2. Rama: `main` (no un commit viejo)
3. Base Directory: vacío, **o** `backend` (las dos valen ahora)
4. Dockerfile: `backend/Dockerfile` si la base es la raíz; `Dockerfile` si la base es `backend`
5. Puerto: `8003`
6. Start command: `uvicorn app.main:app --host 0.0.0.0 --port 8003 --root-path /prospectividad`

Luego **Rebuild** (no solo Restart).
