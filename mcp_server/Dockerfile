FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY mcp_server/ ./mcp_server/

RUN pip install --no-cache-dir -e .

EXPOSE 8765

CMD ["python", "-m", "mcp_server.server", "--transport", "sse", "--host", "0.0.0.0", "--port", "8765"]
