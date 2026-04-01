FROM python:3.10-slim

# Install system dependencies for Chrome and Selenium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    libglib2.0-0 \
    libnss3 \
    libfontconfig1 \
    libxrender1 \
    libxtst6 \
    libxi6 \
    libxcursor1 \
    libxdamage1 \
    libxcomposite1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libgtk-3-0 \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Install Chromium and ChromeDriver
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set up work directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Environment variables
ENV PORT=7860
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 7860

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
