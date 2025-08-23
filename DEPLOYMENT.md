# 🚀 Deployment Guide

This guide covers deploying DocaCast in various environments, from development to production.

## Development Deployment

### Local Development Setup

The simplest way to run DocaCast for development:

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8001

# Frontend (in new terminal)
cd frontend/pdf-reader-ui
npm install
npm run dev
```

### Development with Docker

Create `docker-compose.dev.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8001:8001"
    volumes:
      - ./backend:/app
      - ./backend/document_library:/app/document_library
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - DEBUG=true
    command: uvicorn main:app --host 0.0.0.0 --port 8001 --reload

  frontend:
    build:
      context: ./frontend/pdf-reader-ui
      dockerfile: Dockerfile.dev
    ports:
      - "5173:5173"
    volumes:
      - ./frontend/pdf-reader-ui:/app
      - /app/node_modules
    environment:
      - VITE_API_BASE_URL=http://localhost:8001
    command: npm run dev -- --host
```

### Development Dockerfile Examples

Backend `Dockerfile.dev`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
```

Frontend `Dockerfile.dev`:
```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm install

# Copy source code
COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
```

## Production Deployment

### Docker Production Setup

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - frontend_build:/usr/share/nginx/html
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://docastapp:${DB_PASSWORD}@postgres:5432/docastapp
      - CORS_ORIGINS=https://yourdomain.com
      - LOG_LEVEL=INFO
    volumes:
      - document_storage:/app/document_library
      - audio_storage:/app/generated_audio
      - logs:/app/logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend/pdf-reader-ui
      dockerfile: Dockerfile
    environment:
      - VITE_API_BASE_URL=https://yourdomain.com/api
      - VITE_ADOBE_CLIENT_ID=${ADOBE_CLIENT_ID}
    volumes:
      - frontend_build:/app/dist
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=docastapp
      - POSTGRES_USER=docastapp
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  document_storage:
  audio_storage:
  logs:
  frontend_build:
  prometheus_data:
  grafana_data:
```

### Production Dockerfiles

Backend `Dockerfile`:
```dockerfile
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /root/.local

# Create non-root user
RUN useradd --create-home --shell /bin/bash docastapp

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p document_library generated_audio logs && \
    chown -R docastapp:docastapp .

# Switch to non-root user
USER docastapp

# Add local packages to PATH
ENV PATH=/root/.local/bin:$PATH

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "4"]
```

Frontend `Dockerfile`:
```dockerfile
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code and build
COPY . .
RUN npm run build

FROM nginx:alpine

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Configuration

Create `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8001;
    }

    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # Frontend
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }

        # Backend API
        location /api/ {
            proxy_pass http://backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Increase timeout for audio generation
            proxy_read_timeout 300;
            proxy_connect_timeout 300;
            proxy_send_timeout 300;
        }

        # WebSocket support
        location /ws {
            proxy_pass http://backend/ws;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
        }
    }
}
```

## Cloud Deployment

### AWS Deployment

#### Using AWS ECS with Fargate

Create `aws/task-definition.json`:

```json
{
  "family": "docastapp",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/docastapp-backend:latest",
      "portMappings": [
        {
          "containerPort": 8001,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "REDIS_URL",
          "value": "redis://elasticache-endpoint:6379"
        }
      ],
      "secrets": [
        {
          "name": "GOOGLE_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:docastapp/google-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/docastapp",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### AWS CDK Stack Example

```typescript
import * as cdk from 'aws-cdk-lib';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as elasticache from 'aws-cdk-lib/aws-elasticache';
import * as rds from 'aws-cdk-lib/aws-rds';

export class DocaCastStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // VPC
    const vpc = new ec2.Vpc(this, 'DocaCastVPC', {
      maxAzs: 2
    });

    // ECS Cluster
    const cluster = new ecs.Cluster(this, 'DocaCastCluster', {
      vpc
    });

    // Redis
    const redis = new elasticache.CfnCacheCluster(this, 'DocaCastRedis', {
      cacheNodeType: 'cache.t3.micro',
      engine: 'redis',
      numCacheNodes: 1
    });

    // PostgreSQL
    const database = new rds.DatabaseInstance(this, 'DocaCastDB', {
      engine: rds.DatabaseInstanceEngine.postgres({
        version: rds.PostgresEngineVersion.VER_15
      }),
      instanceType: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
      vpc,
      credentials: rds.Credentials.fromGeneratedSecret('docastapp')
    });

    // Task Definition
    const taskDefinition = new ecs.FargateTaskDefinition(this, 'TaskDef', {
      memoryLimitMiB: 2048,
      cpu: 1024
    });

    const container = taskDefinition.addContainer('backend', {
      image: ecs.ContainerImage.fromRegistry('your-repo/docastapp-backend'),
      environment: {
        REDIS_URL: `redis://${redis.attrRedisEndpointAddress}:6379`,
        DATABASE_URL: `postgresql://docastapp:${database.secret?.secretValueFromJson('password')}@${database.instanceEndpoint.hostname}:5432/docastapp`
      },
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: 'docastapp'
      })
    });

    container.addPortMappings({
      containerPort: 8001
    });

    // Service
    new ecs.FargateService(this, 'DocaCastService', {
      cluster,
      taskDefinition,
      desiredCount: 2
    });
  }
}
```

### Google Cloud Platform

#### Using Cloud Run

Create `cloudbuild.yaml`:

```yaml
steps:
  # Build backend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/docastapp-backend', './backend']
  
  # Build frontend
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/docastapp-frontend', './frontend/pdf-reader-ui']
  
  # Push images
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/docastapp-backend']
  
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/docastapp-frontend']
  
  # Deploy to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'docastapp-backend'
      - '--image'
      - 'gcr.io/$PROJECT_ID/docastapp-backend'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
```

### Azure Deployment

#### Using Azure Container Instances

Create `azure-deploy.yml`:

```yaml
apiVersion: '2019-12-01'
location: eastus
name: docastapp
properties:
  containers:
  - name: backend
    properties:
      image: your-registry.azurecr.io/docastapp-backend:latest
      ports:
      - port: 8001
      environmentVariables:
      - name: GOOGLE_API_KEY
        secureValue: your-api-key
      - name: REDIS_URL
        value: redis://redis-cache:6379
      resources:
        requests:
          cpu: 1
          memoryInGb: 2
  
  - name: frontend
    properties:
      image: your-registry.azurecr.io/docastapp-frontend:latest
      ports:
      - port: 80
      resources:
        requests:
          cpu: 0.5
          memoryInGb: 1
  
  osType: Linux
  ipAddress:
    type: Public
    ports:
    - protocol: tcp
      port: 80
    - protocol: tcp
      port: 8001
  restartPolicy: Always
```

## Kubernetes Deployment

### Kubernetes Manifests

Create `k8s/namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: docastapp
```

Create `k8s/backend-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: docastapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/docastapp-backend:latest
        ports:
        - containerPort: 8001
        env:
        - name: GOOGLE_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: google-api-key
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5

---
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  namespace: docastapp
spec:
  selector:
    app: backend
  ports:
  - port: 8001
    targetPort: 8001
  type: ClusterIP
```

Create `k8s/frontend-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: docastapp
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: your-registry/docastapp-frontend:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"

---
apiVersion: v1
kind: Service
metadata:
  name: frontend-service
  namespace: docastapp
spec:
  selector:
    app: frontend
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

Create `k8s/ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: docastapp-ingress
  namespace: docastapp
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-body-size: "50m"
spec:
  tls:
  - hosts:
    - yourdomain.com
    secretName: docastapp-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend-service
            port:
              number: 8001
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend-service
            port:
              number: 80
```

### Helm Chart

Create `helm/docastapp/Chart.yaml`:

```yaml
apiVersion: v2
name: docastapp
description: DocaCast Helm Chart
type: application
version: 0.1.0
appVersion: "1.0.0"
```

Create `helm/docastapp/values.yaml`:

```yaml
backend:
  image:
    repository: your-registry/docastapp-backend
    tag: latest
    pullPolicy: Always
  
  replicas: 3
  
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1000m"
  
  env:
    REDIS_URL: "redis://redis-service:6379"
  
  secrets:
    GOOGLE_API_KEY: "your-api-key"

frontend:
  image:
    repository: your-registry/docastapp-frontend
    tag: latest
    pullPolicy: Always
  
  replicas: 2
  
  resources:
    requests:
      memory: "256Mi"
      cpu: "100m"
    limits:
      memory: "512Mi"
      cpu: "200m"

ingress:
  enabled: true
  host: yourdomain.com
  tls:
    enabled: true
    secretName: docastapp-tls

redis:
  enabled: true
  auth:
    enabled: false

postgresql:
  enabled: true
  auth:
    postgresPassword: "secure-password"
    database: "docastapp"
```

## Monitoring and Logging

### Prometheus Configuration

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'docastapp-backend'
    static_configs:
      - targets: ['backend:8001']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']
```

### Grafana Dashboard

Create `monitoring/grafana/dashboards/docastapp.json`:

```json
{
  "dashboard": {
    "title": "DocaCast Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Audio Generation Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(audio_generation_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

## CI/CD Pipeline

### GitHub Actions

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy DocaCast

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          cd backend
          python -m pytest tests/

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build and push backend image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: docastapp-backend
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG ./backend
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster docastapp --service backend --force-new-deployment
```

## Environment-Specific Configurations

### Staging Environment

```bash
# staging.env
GOOGLE_API_KEY=staging_api_key
DATABASE_URL=postgresql://staging_user:pass@staging_db:5432/docastapp_staging
REDIS_URL=redis://staging_redis:6379
LOG_LEVEL=DEBUG
CORS_ORIGINS=https://staging.yourdomain.com
```

### Production Environment

```bash
# production.env
GOOGLE_API_KEY=production_api_key
DATABASE_URL=postgresql://prod_user:secure_pass@prod_db:5432/docastapp
REDIS_URL=redis://prod_redis:6379
LOG_LEVEL=WARNING
CORS_ORIGINS=https://yourdomain.com
ENABLE_MONITORING=true
```

## Security Considerations

1. **API Keys**: Use secrets management (AWS Secrets Manager, Azure Key Vault)
2. **Network Security**: Implement VPC/network segmentation
3. **SSL/TLS**: Use valid certificates (Let's Encrypt, commercial)
4. **Authentication**: Implement proper user authentication if needed
5. **Rate Limiting**: Configure appropriate rate limits
6. **File Scanning**: Enable virus/malware scanning for uploads
7. **Monitoring**: Set up security monitoring and alerts

## Scaling Strategies

1. **Horizontal Scaling**: Multiple backend instances with load balancer
2. **Vertical Scaling**: Increase CPU/memory for resource-intensive operations
3. **Caching**: Redis for caching processed documents and audio
4. **CDN**: CloudFront/CloudFlare for static assets and audio files
5. **Database Scaling**: Read replicas for analytics queries
6. **Auto-scaling**: Based on CPU/memory usage and queue length

This deployment guide covers various scenarios from development to large-scale production deployments. Choose the approach that best fits your infrastructure and scaling requirements.
