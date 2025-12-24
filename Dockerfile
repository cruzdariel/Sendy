# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY pages/ ./pages/
COPY util/ ./util/
COPY ui_components/ ./ui_components/
COPY data/ ./data/

# Create directory for persistent storage
RUN mkdir -p data/user_datasets

# Expose port 8080
EXPOSE 8080

# Run the application
CMD ["python", "app.py"]
