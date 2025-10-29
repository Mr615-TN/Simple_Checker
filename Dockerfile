# Use a secure, optimized Python image
FROM python:3.11-slim as base

# Install necessary system dependencies for compilation and cleaning up the cache
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        # CORRECTED: Changed libpcre3-dev to libpcre2-dev for modern Debian systems
        libpcre2-dev \
        libffi-dev \
        pkg-config \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- Build Stage ---
FROM base as builder

WORKDIR /app

# Copy requirements and install them, including Gunicorn for production server
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# --- Final Stage ---
FROM base as final

WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the rest of the application code
COPY app.py .
COPY simple_checker.py .
# MANDATORY: Copy the frontend directory where index.html and script.js reside
COPY frontend frontend/ 

# Create a non-root user for security (Render best practice)
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Expose the port (Render handles mapping this)
EXPOSE 5000

# Command to run the application using Gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

