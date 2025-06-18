# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🔨 Most Important Rule - Process for Adding New Rules

When receiving instructions from users that seem to require constant response rather than just one-time handling:

1. Ask "Should this be made a standard rule?"
2. If you get a YES response, record it as an additional rule in CLAUDE.md
3. From then on, always apply it as a standard rule

Through this process, we will continuously improve the project rules.

## Project Overview

datagusto is a **Data Quality Layer for AI agent systems** that ensures reliable data access and processing. The platform connects with observability platforms like Langfuse to monitor AI agent data interactions, measure data quality, detect incidents, and provide automated guardrails to prevent data-related failures.

## Core Product Features

### 1. Observability Platform Integration
- **Langfuse Integration**: Connects to Langfuse and other observation platforms to sync AI agent logs
- **Real-time Data Sync**: Continuously monitors AI agent execution traces and data access patterns
- **Multi-platform Support**: Extensible architecture for connecting to various observability tools

### 2. Data Quality Measurement
- **Automated Quality Assessment**: Analyzes data accessed by AI agents during tool calling and processing
- **Quality Metrics**: Measures completeness, accuracy, consistency, and validity of agent data
- **Historical Tracking**: Monitors data quality trends over time to identify degradation patterns

### 3. Incident Detection & Management
- **Smart Alerting**: Automatically detects data quality issues and flags them as incidents
- **Severity Classification**: Categorizes incidents based on impact on AI agent performance
- **Dashboard Visualization**: Provides clear incident overview and status tracking

### 4. Root Cause Analysis
- **Step-by-Step Analysis**: Identifies which specific step in the AI agent workflow caused data quality issues
- **Data Source Tracing**: Pinpoints exact data sources, fields, or records responsible for problems
- **AI-Powered Insights**: Uses OpenAI integration to provide detailed root cause explanations
- **Impact Assessment**: Shows how data quality issues affect downstream agent behavior

### 5. Data Guardrails SDK
- **Custom Guardrail Creation**: SDK for implementing data validation rules in AI agent systems
- **Null Handling**: Automatically exclude or handle null values in tool calling responses
- **Data Filtering**: Remove problematic records or fields before processing
- **Execution Control**: Option to halt agent execution when critical data quality thresholds are violated
- **Runtime Protection**: Real-time data validation during AI agent execution

## Tech Stack

- **Frontend**: Next.js (App Router + Server Components), TypeScript, shadcn/ui, Zustand, CSR
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, Alembic, Simple JWT auth, REST API, Lightweight async
- **Database**: PostgreSQL
- **Development**: Docker Compose
- **Production**: VM + Docker Compose
- **CI/CD**: Manual deployment (no automation)
- **Monitoring**: Docker standard logs only
- **Testing**: Minimal (pytest for critical APIs, Jest/Vitest for key components)

## Frontend Development Guidelines

### Next.js App Router + Server Components Strategy

This project follows strict guidelines for optimal Next.js App Router implementation to ensure maximum performance and maintainability.

#### Server Components vs Client Components

| Feature | Server Component | Client Component |
|---------|------------------|------------------|
| Declaration | Default (no declaration needed) | `"use client"` at file top |
| Execution | Server | Browser |
| JS Bundle | Not included ✅ | Included ❌ |
| Data Access | Direct DB access ✅ | Not possible ❌ |
| React Hooks | Not available ❌ | Available ✅ |
| Event Handlers | Not available ❌ | Available ✅ |

#### Mandatory Rules for Component Implementation

**Rule 1: Server Components by Default**
- All components MUST be Server Components unless interactivity is required
- Only use `"use client"` when absolutely necessary for React Hooks, event handlers, or browser APIs

**Rule 2: Client Components at Leaf Nodes Only**
- Place Client Components as deep as possible in the component tree
- Keep parent components as Server Components to minimize bundle size

**Rule 3: Data Fetching in Server Components**
- Perform all API requests and external data fetching in Server Components
- Pass only necessary, serializable data to Client Components

**Rule 4: Minimize Server-to-Client Data Transfer**
- Extract only essential data before passing to Client Components
- Avoid passing large objects, functions, or non-serializable data

**Rule 5: Use Server Actions for Form Handling**
- Prefer Server Actions over client-side state management for form submissions
- Implement data mutations on the server side when possible

**Rule 6: Implement Suspense for Progressive Loading**
- Use Suspense boundaries for better user experience
- Show loading states for slow-loading content sections

#### Component Structure Guidelines

```
/components
  /client       # Client Components ("use client" required)
    /forms      # Interactive forms and inputs
    /buttons    # Click handlers and interactive elements
  /server       # Server Components (default)
    /layout     # Static layout components
    /display    # Data display components
  /ui           # shadcn/ui components (mixed)
    /primitives # Base UI components
```

#### Performance Optimization Requirements

**For Client Components:**
- Use `memo()` to prevent unnecessary re-renders
- Implement `useCallback()` for event handlers
- Use `useMemo()` for expensive computations
- Minimize prop drilling and state updates

**For Server Components:**
- Implement parallel data fetching where possible
- Use streaming and Suspense for progressive enhancement
- Cache expensive operations appropriately

#### Code Generation Checklist

When implementing or reviewing frontend code, verify:

- [ ] Server Components used by default unless interactivity needed
- [ ] `"use client"` only added when React Hooks/events required
- [ ] Client Components positioned at component tree leaves
- [ ] Data fetching implemented in Server Components
- [ ] Minimal, serializable data passed to Client Components
- [ ] Server Actions used for form submissions
- [ ] Suspense boundaries implemented for loading states
- [ ] Proper component structure maintained
- [ ] Performance optimizations applied to Client Components
- [ ] No unnecessary client-side bundles created

## Architecture

### Backend Architecture (FastAPI)

The backend follows layered architecture:
1. **API Layer** (`app/api/`): HTTP endpoints and routing
2. **Service Layer** (`app/services/`): Business logic and core functionality
3. **Repository Layer** (`app/repositories/`): Data access abstraction
4. **Model Layer** (`app/models/`, `app/schemas/`): Data models and validation

Key integrations:
- **Langfuse**: AI agent trace data collection and analysis
- **OpenAI**: Root cause analysis for data quality incidents
- **PostgreSQL**: Primary database for application data
- **Simple JWT**: Lightweight authentication without external dependencies
- **Guardrails SDK**: Custom SDK for implementing data quality controls

### Frontend Architecture (Next.js)

- **App Router**: Next.js with Server Components and CSR (Client-Side Rendering)
- **Authentication**: Simple JWT-based authentication
- **UI Components**: shadcn/ui components with Radix UI primitives
- **State Management**: Zustand for lightweight global state management
- **Styling**: Tailwind CSS with custom component variants

## Development Commands

### Full Stack Development
```bash
# Start all services (recommended for development)
docker compose up

# Start specific services
docker compose up backend
docker compose up frontend
docker compose up postgres
```

### Backend Development

```bash
# Navigate to backend directory
cd backend

# Install dependencies (requires Python 3.10+)
uv install

# Run database migrations
uv run alembic upgrade head

# Start development server
uv run uvicorn app.main:app --reload

# Run tests
uv run pytest

# Generate new migration
uv run alembic revision --autogenerate -m "description"
```

### Frontend Development

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Run linting
npm run lint
```

## Environment Configuration

### Backend Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET_KEY`: Secret key for JWT token generation
- `ENABLE_REGISTRATION`: Boolean to enable/disable user registration
- `OPENAI_API_KEY`: Required for root cause analysis functionality

### Frontend Environment Variables
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)
- `NEXT_PUBLIC_API_VERSION`: API version (default: v1)

## Key Features and Flows

### Data Quality Monitoring Flow
1. **Agent Registration**: User creates account and adds AI agent information
2. **Platform Connection**: Agent details include Langfuse credentials (public_key, secret_key, server)
3. **Data Sync**: Platform continuously syncs trace data and tool calling logs from Langfuse
4. **Quality Analysis**: System analyzes data accessed by agents for quality issues
5. **Incident Detection**: Automatic flagging of data quality problems as incidents
6. **Root Cause Analysis**: AI-powered analysis identifies specific data sources and steps causing issues
7. **Guardrail Activation**: SDK-based guardrails automatically handle or prevent data quality issues

### SDK Integration Flow
1. **SDK Installation**: Developers integrate the datagusto SDK into their AI agent systems
2. **Guardrail Configuration**: Define data quality rules and handling strategies
3. **Runtime Monitoring**: SDK monitors data quality during tool calling and processing
4. **Automatic Remediation**: Configured guardrails automatically filter, clean, or halt processing based on data quality

### Data Models
- **Agent**: AI agent configuration and observability platform integration
- **Trace**: Individual AI agent execution traces with data access logs
- **DataQualityMetric**: Quality measurements for data accessed by agents
- **Incident**: Data quality incidents with severity and impact assessment
- **RootCauseAnalysis**: Detailed analysis of data quality issue origins
- **Guardrail**: SDK-based data quality rules and remediation strategies
- **User/Organization**: User management and multi-tenancy

## Testing

Testing approach is minimal, focusing on critical functionality:

### Backend Testing
- Uses pytest for critical API endpoints only
- Test configuration in `pytest.ini`
- Run tests: `pytest`

### Frontend Testing
- Jest/Vitest for key components only
- Minimal test coverage focusing on essential functionality

### Database Migrations
- Uses Alembic for database schema management
- Migration files in `backend/alembic/versions/`
- Create migration: `alembic revision --autogenerate -m "description"`
- Apply migrations: `alembic upgrade head`

## API Structure

### Current Endpoints
- `/api/v1/auth/*`: Authentication endpoints
- `/api/v1/users/*`: User management
- `/api/v1/agents/*`: AI agent management and observability platform connections
- `/api/v1/traces/*`: Trace data and data quality analysis
- `/api/v1/incidents/*`: Data quality incident management
- `/api/v1/quality/*`: Data quality metrics and measurements
- `/api/v1/guardrails/*`: Guardrail configuration and management
- `/api/v1/sdk/*`: SDK integration and runtime data quality controls

### API Versioning
- All endpoints prefixed with `/api/v1`
- Versioned router structure supports future API versions

## Deployment & Operations

### Development
- Docker Compose for local development environment
- Hot reload enabled for both frontend and backend

### Production
- VM deployment with Docker Compose
- Manual deployment process (no CI/CD automation)
- Docker standard logs for monitoring
- No advanced monitoring or observability tools

## Important Notes

- Simple, lightweight architecture focused on data quality monitoring
- Manual deployment workflow - no automated CI/CD pipeline
- Minimal testing strategy focusing on critical paths only
- Uses Simple JWT for authentication (no external auth providers)
- Docker standard logging - no advanced monitoring setup
- **Primary Focus**: Data quality measurement and incident prevention for AI agents
- **SDK-First Approach**: Provides both monitoring platform and runtime protection SDK
- **Extensible Platform Support**: Currently supports Langfuse with architecture for additional platforms
- **Real-time Guardrails**: Proactive data quality protection during AI agent execution

## Git Commit Message Rules

### IMPORTANT: Never include Claude Code information in commits
- **NEVER** include "🤖 Generated with [Claude Code]" in commit messages
- **NEVER** include "Co-Authored-By: Claude" in commit messages
- **NEVER** mention AI assistance or code generation tools in commits
- Keep commit messages focused on the changes made, not how they were made

### Commit Message Format
Follow conventional commits format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert

Example:
```
fix: improve data quality analysis performance

- Deferred analysis until after trace commit
- Batch analyze traces for better performance
- Fixed UI alignment issues
```