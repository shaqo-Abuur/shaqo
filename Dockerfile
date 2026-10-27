FROM python:3.12-slim
WORKDIR /app
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/
ENV PORT=8080 DB_PATH=/data/shaqo.db
VOLUME /data
CMD ["python", "backend/server.py"]
