# datagusto

Trace, Diagnose and Prevent AI Agents Unpredictability

## 1. Project Overview

datagusto is a platform designed to trace, diagnose, and prevent AI agent unpredictability. It integrates with LangFuse to provide step-by-step visibility into AI agent failures and implements automated guardrails to prevent issues in real-time.

## 2. Requirements

- **Git**: For cloning the repository
- **Docker**: Container runtime environment
- **Docker Compose**: Multi-container application management

### Tested Environment
- Docker: 20.10 or higher
- Docker Compose: v2.0 or higher

## 3. Environment Variables Setup

### 3.1. Create Environment File

```bash
cp .env.example .env
```

### 3.2. Configure Required Variables

Edit the `.env` file and set the following required values:

```bash
# Database Configuration (Required)
POSTGRES_PASSWORD=your_secure_password_here

# JWT Configuration (Required)
JWT_SECRET_KEY=your_jwt_secret_key_here
JWT_REFRESH_SECRET_KEY=your_jwt_refresh_secret_key_here
```

**Generate JWT Secret Keys:**
```bash
openssl rand -hex 32
```

### 3.3. Optional Variables

You can also configure the following optional settings:

```bash
# Port Configuration
POSTGRES_PORT=5432
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Application Configuration
ENABLE_REGISTRATION=true
DEBUG=false
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 4. Starting the Application

### 4.1. Basic Startup

```bash
docker compose up -d
```

Services that will be started:
- **PostgreSQL**: Database (Port: 5432)
- **Backend Migrations**: Database migration (runs once on initial startup)
- **Backend API**: FastAPI application (Port: 8000)
- **Frontend**: Next.js web application (Port: 3000)

### 4.2. Verify Startup Status

```bash
docker compose ps
```

Confirm that all services are in the `Up` state.

## 5. Service Verification

### 5.1. Access URLs

After startup, you can access the services at the following URLs:

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Web Application |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Swagger UI |
| PostgreSQL | localhost:5432 | Database |

### 5.2. Health Check

**Backend API Verification:**
```bash
curl http://localhost:8000/api/health
```

**Frontend Verification:**
Access http://localhost:3000 in your browser

### 5.3. Initial Setup

1. Access http://localhost:3000/sign-up to create an account
2. After logging in, register your AI agent

## 6. Stopping the Application

### 6.1. Normal Shutdown

```bash
docker compose down
```

### 6.2. Complete Removal (Including Data)

**Warning**: This will also delete database data

```bash
docker compose down -v
```

### 6.3. Stop Specific Service Only

```bash
docker compose stop <service_name>
```

Example:
```bash
docker compose stop frontend
```
