FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.0

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_BREAK_SYSTEM_PACKAGES=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-pip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY app ./app
RUN mkdir -p /app/data/raw /app/data/processed /app/data/models

EXPOSE 8003

# Coolify arranca gunicorn (no uvicorn a pelo). Sin --root-path: nginx ya quita /prospectividad.
CMD ["sh", "-c", "gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:${STREAMLIT_SERVER_PORT:-8003} --workers ${WEB_CONCURRENCY:-2} --timeout 120"]
