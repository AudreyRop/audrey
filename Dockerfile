FROM ubuntu:latest
LABEL authors="tj"

ENTRYPOINT ["top", "-b"]
# Use a base image with Python installed for building stage
FROM python:3.10.12 AS builder

# Set up a working directory
WORKDIR /app

# Copy just the requirements file to leverage Docker cache
COPY ./requirements.txt /app/requirements.txt

# Install virtualenv
RUN pip install --no-cache-dir virtualenv

# Create a virtual environment
RUN virtualenv /venv

# Activate the virtual environment
ENV PATH="/venv/bin:$PATH"

# Install dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Specify the production image
FROM python:3.10.12-slim

# Create a non-root user and group
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Set up a working directory
WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /venv /venv

# Change ownership of the application directory to the non-root user
RUN chown -R appuser:appgroup /app

# Change to the non-root user
USER appuser

# Set the PATH to include the virtual environment
ENV PATH="/venv/bin:$PATH"

# Install curl for health check
RUN apt-get update && apt-get install -y curl

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Health chec
HEALTHCHECK --interval=30s --timeout=5s CMD curl --fail http://localhost:5000/health || exit 1

# Copy the application code
COPY . /app

# Run the Flask application
CMD ["python", "app.py"]
