# Deployment Architecture — Unit 1: Auth Microservice

---

## Docker Configuration

**Dockerfile** (`sabhyakriti-auth-service/Dockerfile`):
```dockerfile
FROM python:3.11-slim@sha256:<pinned-digest>

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run as non-root user (SECURITY-09)
RUN adduser --disabled-password --gecos '' appuser
USER appuser

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8001/health').raise_for_status()"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]
```

---

## Local Development (Docker Compose)

**`docker-compose.dev.yml`** (in `sabhyakriti-auth-service/`):
```yaml
version: "3.9"
services:
  auth-service:
    build: .
    ports: ["8001:8001"]
    environment:
      DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/sabhyakriti_auth
      REDIS_URL: redis://redis:6379/0
      LOG_LEVEL: DEBUG
    depends_on: [db, redis]

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: sabhyakriti_auth
      POSTGRES_PASSWORD: postgres
    ports: ["5433:5432"]

  redis:
    image: redis:7-alpine
    ports: ["6380:6379"]
```

---

## CI/CD Pipeline (`.github/workflows/auth-service.yml`)

```
Trigger: push to main, PR to main

Jobs:
  test:
    - checkout
    - setup-python 3.11
    - pip install -r requirements-dev.txt
    - ruff check .
    - mypy . --strict
    - docker-compose -f docker-compose.test.yml up -d (starts test DB + Redis)
    - pytest --cov=. --cov-fail-under=80 --cov-report=xml
    - upload coverage to Codecov (optional)

  build-push (only on main):
    - Configure AWS credentials via OIDC (no long-lived keys)
    - docker build --platform linux/amd64 --tag $ECR_REPO:$SHA --tag $ECR_REPO:latest .
    - docker push both tags to ECR

  deploy (only on main, after build-push):
    - aws ssm send-command to EC2 instance:
        docker pull $ECR_REPO:$SHA
        docker stop auth-service || true
        docker rm auth-service || true
        docker run -d --name auth-service -p 8001:8001 \
          --env-file /etc/sabhyakriti/auth.env \
          --restart unless-stopped \
          $ECR_REPO:$SHA
    - Poll ALB target health for 60s → fail pipeline if unhealthy
```

---

## IAM Role (EC2 Instance Profile for Auth Service)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["secretsmanager:GetSecretValue"],
      "Resource": [
        "arn:aws:secretsmanager:ap-south-1:*:secret:sabhyakriti/auth/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["ses:SendEmail", "ses:SendRawEmail"],
      "Resource": "arn:aws:ses:ap-south-1:*:identity/sabhyakriti.com"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:ap-south-1:*:log-group:/sabhyakriti/auth-service:*"
    },
    {
      "Effect": "Allow",
      "Action": ["cloudwatch:PutMetricData"],
      "Resource": "*",
      "Condition": {
        "StringEquals": { "cloudwatch:namespace": "Sabhyakriti/Auth" }
      }
    },
    {
      "Effect": "Allow",
      "Action": ["ecr:GetAuthorizationToken", "ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["ssm:GetParameter"],
      "Resource": "arn:aws:ssm:ap-south-1:*:parameter/sabhyakriti/auth/*"
    }
  ]
}
```

**Note**: No wildcard actions. No wildcard resources except where AWS API does not support resource-level permissions (`ecr:GetAuthorizationToken`, `cloudwatch:PutMetricData`). Compliant with SECURITY-06.
