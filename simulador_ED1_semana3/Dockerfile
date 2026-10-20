FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLET_FORCE_WEB_SERVER=true \
    FLET_SERVER_PORT=8000 \
    FLET_SERVER_IP=0.0.0.0 \
    ED1_DB_PATH=:memory:

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --create-home --uid 10001 ed1 && chown -R ed1:ed1 /app
USER ed1
EXPOSE 8000
CMD ["python", "main.py"]
