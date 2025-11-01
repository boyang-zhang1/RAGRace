# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for Python packages and Prisma
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (needed for HTML to PDF conversion)
RUN playwright install --with-deps chromium

# Copy the entire backend code
COPY . .

# Generate Prisma client
RUN prisma generate

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# Run database migrations and start the server
# Railway provides PORT environment variable
CMD prisma migrate deploy && uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
