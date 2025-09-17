# ----------------------
# Stage 1: Build + Install deps
# ----------------------
FROM python:3.11-slim-bullseye AS builder

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install system build deps (needed for psycopg2, PyMuPDF, tokenizers if wheel not found)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential gcc g++ git curl libpq-dev ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Rust (for tokenizers if it must build)
RUN curl https://sh.rustup.rs -sSf > /tmp/rustup.sh \
    && chmod +x /tmp/rustup.sh \
    && /tmp/rustup.sh -y --no-modify-path \
    && rm /tmp/rustup.sh
ENV PATH="/root/.cargo/bin:${PATH}"

# Upgrade pip / setuptools / wheel
RUN python -m pip install --upgrade pip setuptools wheel

WORKDIR /app

# Copy requirements and install into venv
COPY requirements.txt /app/requirements.txt

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Install requirements
RUN pip install --no-cache-dir -r /app/requirements.txt


# ----------------------
# Stage 2: Runtime image
# ----------------------
FROM python:3.11-slim-bullseye AS runtime

ENV DEBIAN_FRONTEND=noninteractive

# Install runtime system deps (no compilers here!)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       libpq-dev ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy Python venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Copy app source code
WORKDIR /app
COPY . /app

# Expose port
ENV PORT=8000
EXPOSE 8000

# Start FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
