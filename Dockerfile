FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for PDF processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    # PDF processing dependencies
    libgl1-mesa-glx \
    libglib2.0-0 \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY src/ src/
COPY scripts/ scripts/

# Install the package
RUN pip install -e .

# Create data directories
RUN mkdir -p data/chroma data/regulations data/sanctions logs

# Default command runs the server
CMD ["export-control-mcp"]
