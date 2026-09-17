FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

COPY backend /app/backend
COPY prospectividad /app/prospectividad

EXPOSE 8003

# Coolify pasa STREAMLIT_SERVER_PORT=8003 aunque el servicio es FastAPI.
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${STREAMLIT_SERVER_PORT:-8003} --root-path ${ROOT_PATH:-/prospectividad}"]
