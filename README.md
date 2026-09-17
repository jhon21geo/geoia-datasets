# geoia-datasets

Datos de GeoIA y visor de **prospectividad** para Coolify.

## El log de Gunicorn no es un error

Esto es arranque correcto:

```
Starting gunicorn 23.0.0
Listening at: http://0.0.0.0:8003
Application startup complete.
```

Si en el log **no** aparece `GeoIA visor: HTML en GET /`, Gunicorn está cargando el API sin el visor. Entonces `https://geoia.site/prospectividad/` responde `{"detail":"Not Found"}`.

Start command en Coolify:

```
gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8003 --workers 2
```

Sin `--root-path`. Nginx ya antepone `/prospectividad`.
