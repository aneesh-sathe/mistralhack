FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ffmpeg \
    pkg-config \
    libcairo2-dev \
    libpango1.0-dev \
    libffi-dev \
    tesseract-ocr \
    tesseract-ocr-eng \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./pyproject.toml
RUN pip install --upgrade pip

COPY . .
RUN pip install -e .[dev]

RUN chmod +x /app/backend/entrypoint.sh

CMD ["/app/backend/entrypoint.sh"]
