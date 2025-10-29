FROM node:18-alpine AS frontend-builder

WORKDIR /ui

COPY ai_agents/ui/ ./
RUN npm ci

RUN npm run build

# Stage 2: Setup Backend with Frontend
FROM python:3.11-alpine3.21
WORKDIR /app

# Install system dependencies for Alpine.
# We use apk instead of apt-get. build-base includes gcc and other common build tools.
RUN apk update && apk upgrade && \
    apk add --no-cache \
        build-base \
        curl \
        g++ \
        gcc \
        git \
        libffi-dev \
        librdkafka-dev \
        openssh \
        openssl-dev \
        protobuf-dev \
        libmagic \
        && rm -rf /var/cache/apk/*

# Copy backend requirements and install Python dependencies
COPY . .

ARG AZURE_PRIVATE_TOKEN_BASE64

# Configure SSH for Git operations
RUN mkdir -p /root/.ssh && \
    touch /root/.ssh/id_rsa && \
    curl -H "Authorization: Basic $AZURE_PRIVATE_TOKEN_BASE64" "https://dev.azure.com/Gofynd/Infrastructure/_apis/git/repositories/kube-infrastructure/items?scopePath=gitlab%2Fid_rsa&versionDescriptor.version=master" -o /root/.ssh/id_rsa && \
    chmod 600 /root/.ssh/id_rsa && \
    echo "Host dev.azure.com\n\tHostName dev.azure.com\n\tUser git\n\tStrictHostKeyChecking no\n" >> /root/.ssh/config && \
    ssh-keyscan -t rsa ssh.dev.azure.com >> /root/.ssh/known_hosts

RUN pip install --upgrade --no-cache-dir pip setuptools

RUN pip install --no-cache-dir -r requirements.txt
# Copy built frontend from the frontend-builder stage
COPY --from=frontend-builder /ui/dist /app/static


# Create necessary directories
RUN mkdir -p /app/documents /app/logs /app/static


# Environment variables
ENV PYTHONUNBUFFERED=1
ENV SERVE_STATIC=true
ENV STATIC_PATH=/app/static

# Expose port
EXPOSE 80

RUN chmod +x ci-test.sh && \
    mkdir -p /var/log/fynd && chmod 777 /var/log/fynd


# Run the application
ENTRYPOINT ["python", "server.py"]
