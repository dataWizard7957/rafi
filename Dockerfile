# Rafi API for Cloud Run. Build from the repo root:
#   gcloud run deploy rafi-api --source . --region us-central1 --allow-unauthenticated
FROM python:3.12-slim
WORKDIR /app
COPY api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY api/ ./
COPY seed/ ./seed/
ENV SEED_DIR=/app/seed
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
