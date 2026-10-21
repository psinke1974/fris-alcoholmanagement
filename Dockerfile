# Container-image voor Fris. Geschikt voor de openbare demo (DEMO_MODE=true) en voor
# een eigen installatie. Zie docs/deployment.md en docs/demo.md.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt gunicorn==23.0.0

COPY app ./app
COPY migrations ./migrations
COPY run.py ./

# Draai niet als root; data/ is de enige map waarin de app schrijft.
RUN useradd --create-home --uid 10001 fris \
    && mkdir -p /app/data \
    && chown fris:fris /app/data \
    && chmod 700 /app/data
USER fris

EXPOSE 8080

# Eén worker: SQLite en de inlog-rem (in-memory) gaan uit van één proces. Threads voor gelijktijdigheid.
CMD ["sh", "-c", "exec gunicorn --workers 1 --threads 4 --bind 0.0.0.0:${PORT} --access-logfile - 'app:create_app()'"]
