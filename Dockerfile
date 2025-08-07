# LinkedIn SDR Service Dockerfile (Root Level for SIT Deployment)
# This builds the LinkedIn SDR service from the ai_agents/linkedin_sdr subdirectory

# Define the Python version and base image variant (Following Vector's Pattern)
ARG PYTHON_VERSION=3.10.15-alpine3.20

# Use the specified Python base image for the builder stage
FROM python:${PYTHON_VERSION} AS builder

# Ensure Python output is unbuffered
ENV PYTHONUNBUFFERED=1

# Install build dependencies and necessary packages (Following Vector's Pattern)
RUN apk update && apk upgrade && \
    apk add --no-cache \
        build-base \
        cmake \
        curl \
        g++ \
        gcc \
        git \
        libffi-dev \
        librdkafka-dev \
        openssh \
        openssl-dev \
        protobuf-dev \
        && rm -rf /var/cache/apk/*

RUN git clone --recurse-submodules -b main https://github.com/google/crc32c.git && \
    cd crc32c &&  \
    mkdir build &&  \
    cd build &&  \
    cmake -DCRC32C_BUILD_TESTS=0 -DCRC32C_BUILD_BENCHMARKS=0 .. &&  \
    make all install

# Set the working directory (Following Vector's Pattern)
WORKDIR /srv/linkedin_sdr

# Copy the requirements file from LinkedIn SDR subdirectory (Copy requirements first for better Docker caching)
COPY ./ai_agents/linkedin_sdr/requirements.txt .

ARG AZURE_PRIVATE_TOKEN_BASE64

# Configure SSH for Git operations (Following Vector's Exact SSH Pattern)
RUN mkdir -p /root/.ssh && \
    touch /root/.ssh/id_rsa && \
    curl -H "Authorization: Basic $AZURE_PRIVATE_TOKEN_BASE64" "https://dev.azure.com/Gofynd/Infrastructure/_apis/git/repositories/kube-infrastructure/items?scopePath=gitlab%2Fid_rsa&versionDescriptor.version=master" -o /root/.ssh/id_rsa && \
    chmod 600 /root/.ssh/id_rsa && \
    echo "Host dev.azure.com\n\tHostName dev.azure.com\n\tUser git\n\tStrictHostKeyChecking no\n" >> /root/.ssh/config && \
    ssh-keyscan -t rsa ssh.dev.azure.com >> /root/.ssh/known_hosts

# Create and activate a virtual environment (Following Vector's Pattern)
RUN python -m venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Upgrade pip and install Python dependencies (Following Vector's Pattern)
RUN pip install --upgrade --no-cache-dir pip wheel && \
    pip install --upgrade --no-cache-dir setuptools && \
    pip install --no-cache-dir -r requirements.txt

# Copy the LinkedIn SDR application code from subdirectory
COPY ./ai_agents/linkedin_sdr/ .

# Store the current Git commit hash and remove the .git directory (Following Vector's Pattern)
# Handle case where git repo might not be available in CI/CD context
RUN if git rev-parse --git-dir > /dev/null 2>&1; then \
        git rev-parse HEAD > gitsha && rm -rf .git; \
    else \
        echo "unknown-commit-$(date +%s)" > gitsha; \
    fi

# Use the specified Python base image for the runtime stage
FROM python:${PYTHON_VERSION}

# Ensure Python output is unbuffered
ENV PYTHONUNBUFFERED=1

# Install runtime dependencies (Following Vector's Pattern)
RUN apk update && apk upgrade && \
    apk add --no-cache \
        crc32c \
        crc32c-dev \
        librdkafka \
        && rm -rf /var/cache/apk/*

RUN pip install --upgrade --no-cache-dir pip setuptools

# Set the working directory
WORKDIR /srv/linkedin_sdr

# Copy application files and the virtual environment from the builder stage (Following Vector's Pattern)
COPY --from=builder /srv/linkedin_sdr /srv/linkedin_sdr
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /usr/local/lib/libcrc32c* /usr/local/lib/
COPY --from=builder /usr/local/include/crc32c /usr/local/include/crc32c

# Activate the virtual environment
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Expose port 80 (Following Vector's Pattern)
EXPOSE 80

# Make the ci-test.sh script executable and set permissions for the log directory (Following Vector's Pattern)
RUN chmod +x ci-test.sh && \
    mkdir -p /var/log/fynd && chmod 777 /var/log/fynd && \
    mkdir -p /mnt/artifacts && chmod 777 /mnt/artifacts

# Define the entrypoint (Following Vector's Pattern)
ENTRYPOINT ["python", "main.py"] 


FROM node:18-alpine AS frontend-builder

WORKDIR /ai_agents/ui

# Copy package files and install dependencies
COPY ai_agents/ui/package*.json ./
RUN npm ci

# Copy frontend source code
COPY ai_agents/ui/ ./

# Build the React application
RUN npm run build

# Stage 2: Setup Backend with Frontend
FROM python:3.11.13-alpine3.22

WORKDIR /ai_agents/leadgen/api/

# Install system dependencies for Alpine.
# We use apk instead of apt-get. build-base includes gcc and other common build tools.
RUN apk add --no-cache \
    build-base \
    libmagic

# Copy backend requirements and install Python dependencies
COPY ai_agents/leadgen/api .
COPY ci-test.sh .
COPY dump_coverage.py .
COPY main.py .

RUN pip install --upgrade --no-cache-dir pip setuptools

RUN pip install --no-cache-dir -r requirements.txt

# Copy built frontend from the frontend-builder stage
COPY --from=frontend-builder /ai_agents/ui/build /app/static


# Create necessary directories
RUN mkdir -p /ai_agents/leadgen/api/documents /ai_agents/leadgen/api/logs /ai_agents/leadgen/api/static


# Environment variables
ENV PYTHONUNBUFFERED=1
ENV SERVE_STATIC=true
ENV STATIC_PATH=/app/static

# Expose port
EXPOSE 80

RUN chmod +x ci-test.sh && \
    mkdir -p /var/log/fynd && chmod 777 /var/log/fynd


# Run the application
ENTRYPOINT ["python", "main.py"]
