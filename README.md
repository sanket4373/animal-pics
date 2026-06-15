# Animal Picture Microservice

A production-ready FastAPI microservice that fetches, stores, and serves animal pictures from external APIs. Built with modern Python best practices, containerization, and Kubernetes deployment support.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-helm-326CE5.svg)](https://helm.sh/)

---

## Table of Contents

- [Background](#background)
- [Architecture](#architecture)
- [Running Application locally (Docker Compose)](#quick-start-docker-compose)
- [Running Application in Production Deployment (Kubernetes)](#production-deployment-kubernetes)
- [Technology Stack](#technology-stack)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Design Decisions](#design-decisions)
- [Contributing](#contributing)

---

## Background

This microservice was built to demonstrate modern Python web development practices, cloud-native architecture patterns, and production deployment strategies. It showcases:

- **RESTful API design** with automatic OpenAPI documentation
- **Asynchronous programming** for concurrent external API calls
- **Separation of concerns** with proper layering (router → service → storage)
- **Cloud-native storage patterns** (object storage + relational database)
- **Container orchestration** with Docker Compose and Kubernetes
- **Infrastructure as Code** using Helm charts

### Problem Statement

Fetch animal pictures from external APIs (Dog CEO API, Bear API), store them efficiently, and provide a simple interface to retrieve them. The challenge is to handle binary data correctly, support concurrent fetching, and deploy in both local and production environments.

---

## Architecture

### High-Level Architecture Diagram

```mermaid
flowchart TB
    subgraph CLIENT["CLIENT LAYER"]
        UI[Web UI<br/>Browser]
        API[API Clients<br/>curl, Postman]
    end

    subgraph APP["APPLICATION LAYER"]
        subgraph FASTAPI["FastAPI Application"]
            ROUTER[Router<br/>Endpoints]
            SERVICE[Service Layer<br/>Business Logic]
            CLIENTS[Animal Clients<br/>httpx async]
        end
    end

    subgraph EXTERNAL["EXTERNAL APIS"]
        DOG[Dog CEO API]
        BEAR[Bear API]
    end

    subgraph PERSIST["PERSISTENCE LAYER"]
        POSTGRES[(PostgreSQL<br/>Metadata Storage)]
        MINIO[(MinIO<br/>Object Storage)]
    end

    subgraph DEPLOY["DEPLOYMENT LAYER"]
        COMPOSE[Docker Compose<br/>Development]
        K8S[Kubernetes + Helm<br/>Production]
    end

    UI --> ROUTER
    API --> ROUTER
    ROUTER --> SERVICE
    SERVICE --> CLIENTS
    SERVICE --> POSTGRES
    SERVICE --> MINIO
    CLIENTS --> DOG
    CLIENTS --> BEAR

    style CLIENT fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    style APP fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    style FASTAPI fill:#ede7f6,stroke:#311b92,stroke-width:2px
    style EXTERNAL fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style PERSIST fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    style DEPLOY fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    
    style UI fill:#bbdefb,stroke:#0277bd
    style API fill:#bbdefb,stroke:#0277bd
    style ROUTER fill:#ce93d8,stroke:#6a1b9a
    style SERVICE fill:#ce93d8,stroke:#6a1b9a
    style CLIENTS fill:#ce93d8,stroke:#6a1b9a
    style DOG fill:#ffcc80,stroke:#e65100
    style BEAR fill:#ffcc80,stroke:#e65100
    style POSTGRES fill:#a5d6a7,stroke:#2e7d32
    style MINIO fill:#a5d6a7,stroke:#2e7d32
    style COMPOSE fill:#f48fb1,stroke:#c2185b
    style K8S fill:#f48fb1,stroke:#c2185b
```

### Data Flow

1. **Fetch Request**: Client sends POST `/animals/fetch` with animal type and count
2. **Concurrent Fetching**: Service layer uses `asyncio.gather()` to fetch N images in parallel from external APIs
3. **Storage**: Each image is:
   - Uploaded to MinIO object storage (binary data)
   - Metadata saved to PostgreSQL (URL, key, timestamp)
4. **Retrieval**: Client requests GET `/animals/last/{type}`
5. **Response**: Service queries PostgreSQL for metadata, retrieves image from MinIO, returns binary response

### Storage Architecture

**PostgreSQL stores:**
- `animal_type` - Type of animal (dog, bear)
- `image_url` - Original source URL
- `minio_object_key` - Key to retrieve from MinIO
- `fetched_at` - UTC timestamp

**MinIO stores:**
- Raw image bytes
- Bucket: `animal-pictures`
- Key format: `{animal_type}/{uuid4}.jpg`

---

## Quick Start (Docker Compose)

Get the application running locally in minutes with Docker Compose. No need to install Python, Poetry, or any dependencies on your machine.

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/animal-pics.git

# Navigate to the project directory
cd animal-pics
```

### Step 2: Build and Start Services

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f app
```

### Step 3: Verify Services

```bash
# Check running containers
docker-compose ps

# Test the health endpoint
curl http://localhost:8000/health
```

### Step 4: Access the Application

- **Web UI**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

### Step 5: Stop Services

```bash
# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes (deletes data)
docker-compose down -v
```

### What's Running?

Docker Compose starts three services automatically:

- **FastAPI Application** (Port 8000) - The main microservice
- **PostgreSQL Database** (Port 5432) - Stores metadata
- **MinIO Object Storage** (Ports 9000, 9001) - Stores images

---

## Production Deployment (Kubernetes)

### Prerequisites

- Kubernetes cluster (minikube, kind, GKE, EKS, AKS)
- kubectl configured
- Helm 3 installed

### Step 1: Build and Push Docker Image

```bash
# Build the image
docker build -t your-registry/animal-pics:v1.0.0 .

# Push to container registry
docker push your-registry/animal-pics:v1.0.0
```

### Step 2: Update Helm Values

Edit `helm/animal-pics/values.yaml`:

```yaml
image:
  repository: your-registry/animal-pics
  tag: v1.0.0
  pullPolicy: IfNotPresent

replicaCount: 3  # Scale as needed

database:
  url: "postgresql://user:password@postgres-service:5432/animals"

minio:
  endpoint: "minio-service:9000"
  accessKey: "your-access-key"
  secretKey: "your-secret-key"
```

### Step 3: Install with Helm

```bash
# Install the chart
helm install animal-pics ./helm/animal-pics

# Or upgrade if already installed
helm upgrade animal-pics ./helm/animal-pics

# Check deployment status
kubectl get pods -l app=animal-pics
kubectl get svc animal-pics
```

### Step 4: Access the Application

```bash
# Port forward to access locally
kubectl port-forward svc/animal-pics 8000:8000

# Or expose via LoadBalancer/Ingress (production)
kubectl expose deployment animal-pics --type=LoadBalancer --port=80 --target-port=8000
```

### Step 5: Monitor and Debug

```bash
# View logs
kubectl logs -f deployment/animal-pics

# Check health
kubectl exec -it deployment/animal-pics -- curl localhost:8000/health

# Describe pod for troubleshooting
kubectl describe pod <pod-name>
```

### Helm Chart Structure

```
helm/animal-pics/
├── Chart.yaml              # Chart metadata
├── values.yaml             # Configurable values
└── templates/
    ├── deployment.yaml     # Pod specification
    ├── service.yaml        # Service definition
    ├── configmap.yaml      # Non-sensitive config
    └── secret.yaml         # Sensitive credentials
```

---

## Technology Stack

| Layer | Technology | Why This Choice |
|-------|-----------|-----------------|
| **Language** | Python 3.11+ | Modern async/await support, excellent ecosystem |
| **Web Framework** | FastAPI | Auto-generates OpenAPI docs, async-native, type-safe with Pydantic |
| **ORM** | SQLAlchemy 2.0 | Database-agnostic (SQLite for dev, PostgreSQL for prod), mature and reliable |
| **Database** | PostgreSQL 15 | Industry-standard relational DB for structured metadata |
| **Object Storage** | MinIO | S3-compatible, perfect for binary data, avoids bloating PostgreSQL |
| **HTTP Client** | httpx | Async-native, same API for external calls and testing |
| **Package Manager** | Poetry | Modern dependency management with lockfile, replaces pip + requirements.txt |
| **Containerization** | Docker + Compose | Portable deployment, ships app + dependencies as one unit |
| **Orchestration** | Kubernetes + Helm | Production-ready deployment with declarative configuration |
| **Testing** | pytest + pytest-asyncio | Standard Python testing with async support |
| **Templating** | Jinja2 | Simple HTML rendering without separate frontend build |
| **Linting** | Ruff | Fast, modern linter replacing flake8 + isort |

### Why MinIO Instead of Storing Images in PostgreSQL?

PostgreSQL **can** store binary data via `bytea` columns, but this is an **antipattern**:

- **Bloats the database** with large unstructured blobs
- **Degrades query performance** over time
- **Makes backups slow** and wasteful
- **Defeats the purpose** of a relational database

MinIO is an **object store** — the architecturally correct tool for binary files:

- **Mirrors AWS S3 + RDS pattern** used in production systems
- **Keeps PostgreSQL lean** (only structured metadata)
- **Scales independently** from the database
- **S3-compatible API** for easy cloud migration

---

## Features

- Fetch dog pictures from Dog CEO API
- Fetch bear pictures from Bear API  
- Store images in MinIO object storage (S3-compatible)
- Track fetch history in PostgreSQL
- RESTful API with automatic OpenAPI documentation
- Async concurrent fetching using `asyncio.gather()`
- Simple web UI for testing (no build step required)
- Docker Compose for local development
- Kubernetes Helm chart for production deployment
- Comprehensive test suite with mocked external dependencies
- Health check endpoint for monitoring
- Type-safe with Pydantic schemas

---

## Prerequisites

### For Local Development (Docker Compose)

- Docker 20.10+
- Docker Compose 2.0+
- OR Colima (Docker Desktop alternative for macOS)

### For Production Deployment (Kubernetes)

- kubectl
- Helm 3
- Access to a Kubernetes cluster (minikube, kind, or cloud provider)
- Container registry access (Docker Hub, GCR, ECR, etc.)

---

## API Reference

### Base URL

- Local: `http://localhost:8000`
- Docker: `http://localhost:8000`
- Kubernetes: `http://<service-ip>:8000`

### Endpoints

#### 1. Fetch Animal Pictures

```http
POST /animals/fetch
Content-Type: application/json

{
  "animal_type": "dog",
  "count": 3
}
```

**Response:**

```json
{
  "fetched": [
    {
      "id": 1,
      "animal_type": "dog",
      "image_url": "https://images.dog.ceo/breeds/hound-afghan/n02088094_1003.jpg",
      "minio_object_key": "dog/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg",
      "fetched_at": "2026-06-15T13:45:30.123456"
    }
  ]
}
```

**Supported animal types:** `dog`, `bear`

#### 2. Get Last Picture

```http
GET /animals/last/{animal_type}
```

**Response:** Binary image data (JPEG)

**Example:**

```bash
curl http://localhost:8000/animals/last/dog --output dog.jpg
```

#### 3. Get Fetch History

```http
GET /animals/history/{animal_type}?limit=10
```

**Response:**

```json
{
  "history": [
    {
      "id": 5,
      "animal_type": "dog",
      "image_url": "https://...",
      "fetched_at": "2026-06-15T13:45:30.123456"
    }
  ]
}
```

#### 4. Health Check

```http
GET /health
```

**Response:**

```json
{
  "status": "ok"
}
```

#### 5. Web UI

```http
GET /
```

Returns HTML interface for testing the API.

### Interactive API Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Testing

### Run Tests in Docker

```bash
# Run tests inside a container
docker-compose run --rm app poetry run pytest -v

# Run with coverage
docker-compose run --rm app poetry run pytest -v --cov=app --cov-report=html

# Run specific test file
docker-compose run --rm app poetry run pytest tests/test_api.py -v
```

### Test Structure

```
tests/
├── conftest.py          # Fixtures (test DB, client, mocks)
├── test_api.py          # Integration tests for endpoints
└── test_service.py      # Unit tests for business logic
```

### Key Testing Features

- **In-memory SQLite** for fast test database
- **Mocked MinIO** storage (no external dependencies)
- **Mocked external APIs** using `respx`
- **Async test support** with `pytest-asyncio`
- **Fixtures** for dependency injection

### Example Test

```python
def test_fetch_animals(client, mock_external_apis):
    response = client.post(
        "/animals/fetch",
        json={"animal_type": "dog", "count": 2}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["fetched"]) == 2
```

### Linting and Code Quality

```bash
# Run Ruff linter in Docker
docker-compose run --rm app poetry run ruff check .

# Auto-fix issues
docker-compose run --rm app poetry run ruff check --fix .

# Format code
docker-compose run --rm app poetry run ruff format .
```

---

## Project Structure

```
animal-pics/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entrypoint
│   ├── config.py            # Settings (pydantic-settings)
│   ├── database.py          # SQLAlchemy engine + session
│   ├── models.py            # ORM models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── router.py            # API route definitions
│   ├── service.py           # Business logic layer
│   ├── animal_clients.py    # External API clients (httpx)
│   ├── storage.py           # MinIO wrapper
│   └── templates/
│       └── index.html       # Web UI
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Test fixtures
│   ├── test_api.py          # API integration tests
│   └── test_service.py      # Service unit tests
│
├── helm/
│   └── animal-pics/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           ├── deployment.yaml
│           ├── service.yaml
│           ├── configmap.yaml
│           └── secret.yaml
│
├── .env.example             # Environment variable template
├── .dockerignore
├── docker-compose.yml       # Local development stack
├── Dockerfile               # Multi-stage container build
├── pyproject.toml           # Poetry dependencies
├── poetry.lock              # Locked dependencies
└── README.md
```

---

## Design Decisions

### 1. Async/Await Throughout

**Why:** External API calls are I/O-bound. Using `asyncio.gather()` allows fetching multiple images concurrently, reducing total latency from `N × latency` to `max(latency)`.

```python
# Sequential: 3 seconds total for 3 images
for i in range(3):
    await fetch_image()  # 1 second each

# Concurrent: 1 second total for 3 images
await asyncio.gather(*[fetch_image() for _ in range(3)])
```

### 2. Service Layer Separation

**Why:** Keeps business logic separate from HTTP concerns. Makes testing easier and allows reusing logic across different interfaces (REST, GraphQL, CLI).

```
Router (HTTP) → Service (Logic) → Storage/Database (Persistence)
```

### 3. Multi-Stage Dockerfile

**Why:** Keeps production image small (~150MB vs ~800MB). Builder stage has Poetry and build tools; runtime stage only has the application.

```dockerfile
FROM python:3.11-slim AS builder  # Install dependencies
FROM python:3.11-slim AS runtime  # Copy only what's needed
```

### 4. Pydantic for Configuration

**Why:** Type-safe settings with validation. Reads from environment variables or `.env` file. Fails fast on misconfiguration.

```python
class Settings(BaseSettings):
    database_url: str
    minio_endpoint: str
    # Automatically reads from DATABASE_URL, MINIO_ENDPOINT env vars
```

### 5. Health Check Endpoint

**Why:** Essential for production. Used by Docker Compose, Kubernetes liveness probes, and load balancers to determine service health.

### 6. Helm Chart Included

**Why:** Demonstrates production-readiness. Helm is the standard for Kubernetes deployments. Shows understanding of cloud-native patterns.

### 7. OpenAPI Documentation

**Why:** FastAPI generates interactive docs automatically. Improves discoverability and reduces documentation burden.

---

## Acknowledgments

- [Dog CEO API](https://dog.ceo/dog-api/) - Free dog pictures
- [Bear API](https://github.com/public-apis/public-apis) - Bear pictures
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [MinIO](https://min.io/) - High-performance object storage
- [Poetry](https://python-poetry.org/) - Python dependency management

---

## Support

- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/animal-pics/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YOUR_USERNAME/animal-pics/discussions)

---