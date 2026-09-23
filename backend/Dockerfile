FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MODEL_CACHE_DIR=/srv/models

WORKDIR /srv

RUN useradd --create-home --uid 10001 app \
    && mkdir -p /srv/models \
    && chown app /srv/models

COPY pyproject.toml ./
COPY app ./app
RUN pip install .

USER app

RUN python -c "from app.core.config import Settings; from app.runtime import build_embedder, build_reranker; settings = Settings(); build_embedder(settings).model; build_reranker(settings).model"

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips '*'"]
