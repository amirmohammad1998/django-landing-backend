FROM python:3.12-slim-bookworm

# ─── ENVIRONMENT ─────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# ─── SYSTEM DEPENDENCIES ─────────────────────
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ─── WORKDIR ─────────────────────────────────
WORKDIR /app

# ─── DEPENDENCIES ────────────────────────────
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ─── COPY PROJECT FILES ──────────────────────
COPY . /app/

# ─── STATIC FILES ────────────────────────────
RUN python manage.py collectstatic --noinput || true

# ─── ENTRYPOINT ──────────────────────────────
COPY scripts/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8000
CMD ["/usr/local/bin/entrypoint.sh"]
