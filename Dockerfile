# Official lightweight Python image
FROM python:3.12-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libc-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . /app/

COPY entrypoint.prod.sh /app/
RUN chmod +x /app/entrypoint.prod.sh

EXPOSE 8000

# Use entrypoint script to initialize the container
ENTRYPOINT ["/app/entrypoint.prod.sh"]
