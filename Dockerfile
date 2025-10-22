# Use a slim, stable Python base image for a smaller footprint
FROM python:3.10-slim

# Set environment variables to prevent Python from writing .pyc files to disc
# and to buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# --- Dependency Installation Stage ---

# Copy only the requirements file first to leverage Docker's layer caching.
# This ensures dependencies are only re-downloaded if requirements.txt changes.
COPY requirements.txt .

# Install dependencies. The --no-cache-dir flag helps keep the image size small.
RUN pip install --upgrade pip && \
    pip install -r requirements.txt --no-cache-dir

# --- Application Setup Stage ---

# Copy the rest of the application code into the container
COPY . /app

# --- Security and Permissions ---

# Create a non-root user to run the application (best practice for security)
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Expose the port if your application uses a web server (like Flask)
# If SeykotaBot is purely a CLI script, this line can be removed.
EXPOSE 5000

# Command to run the application
# Replace 'your_bot_script.py' with the actual entry point script for SeykotaBot.
# If your app uses Flask, this should be the gunicorn/waitress/etc. command.
CMD ["python", "app.py"]