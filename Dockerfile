# Dockerfile for the Vyastrovidi engine on Fly.io
FROM python:3.13-slim

# System libs needed by pyswisseph if it has to build from source
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install deps first (better Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the engine source (main.py, calculations/, ephe/, data/)
COPY . .

# Fly sets PORT; default 8080 for local Docker runs
ENV PORT=7860
EXPOSE 7860

# Start the FastAPI app
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
