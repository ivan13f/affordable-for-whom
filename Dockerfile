# Use a slim, modern Python base image
FROM python:3.13.5-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies (for compiling some Python packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

# Expose Streamlit default port
EXPOSE 8501

# Health check for Cloud Run
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Set Streamlit environment variables
ENV STREAMLIT_THEME_BASE=light \
    PYTHONUNBUFFERED=1

# Run the Streamlit app
ENTRYPOINT ["streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]