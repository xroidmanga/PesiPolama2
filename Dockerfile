# Use official Python image
FROM python:3.10-slim

# Create and set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Expose Flask port
EXPOSE 3000

# Run the application 

# 😮‍💨 Le ab video upload hoga 
CMD ["python", "Desi_video.py"]

# CMD ["python", "desi.py"]


