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

# Coolify usa STREAMLIT_SERVER_PORT=8003 aunque el proceso es uvicorn.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${STREAMLIT_SERVER_PORT:-8003} --root-path ${ROOT_PATH:-/prospectividad}"]
