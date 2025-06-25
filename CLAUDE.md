# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🔨 Most Important Rule - Process for Adding New Rules

When receiving instructions from users that seem to require constant response rather than just one-time handling:

1. Ask "Should this be made a standard rule?"
2. If you get a YES response, record it as an additional rule in CLAUDE.md
3. From then on, always apply it as a standard rule

Through this process, we will continuously improve the project rules.

## Project Overview

datagusto is a **Data Quality Layer for AI agent systems** that ensures reliable data access and processing. The platform connects with observability platforms like Langfuse to monitor AI agent data interactions, measure data quality, and provide automated guardrails to prevent data-related failures.

## Core Product Features

### 1. Observability Platform Integration
- **Langfuse Integration**: Connects to Langfuse and other observation platforms to sync AI agent logs
- **Real-time Data Sync**: Continuously monitors AI agent execution traces and data access patterns
- **Multi-platform Support**: Extensible architecture for connecting to various observability tools

### 2. Data Quality Measurement
- **Automated Quality Assessment**: Analyzes data accessed by AI agents during tool calling and processing
- **Quality Metrics**: Measures completeness, accuracy, consistency, and validity of agent data
- **Historical Tracking**: Monitors data quality trends over time to identify degradation patterns

### 3. Data Quality Analysis
- **Quality Scoring**: Automated calculation of data quality scores for traces
- **Trend Monitoring**: Historical tracking of data quality patterns over time
- **Quality Insights**: Detailed analysis of data completeness, accuracy, and consistency

### 5. Data Guardrails SDK
- **Custom Guardrail Creation**: SDK for implementing data validation rules in AI agent systems
- **Null Handling**: Automatically exclude or handle null values in tool calling responses
- **Data Filtering**: Remove problematic records or fields before processing
- **Execution Control**: Option to halt agent execution when critical data quality thresholds are violated
- **Runtime Protection**: Real-time data validation during AI agent execution

## Tech Stack

- **Frontend**: Next.js (App Router + Server Components), TypeScript, shadcn/ui, TanStack Query, React Context API
- **Backend**: Python 3.10+, FastAPI, SQLAlchemy, Alembic, Simple JWT auth, REST API, Lightweight async
- **Database**: PostgreSQL
- **Development**: Docker Compose
- **Production**: VM + Docker Compose
- **CI/CD**: Manual deployment (no automation)
- **Monitoring**: Docker standard logs only
- **Testing**: Strategic testing with pytest (backend) and Vitest (frontend), 70% coverage target

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

### Directory Structure

#### Feature-based Organization with Server/Client Separation

```
src/
├── app/                      # Next.js App Router
│   ├── (auth)/              # Authentication route group
│   └── (dashboard)/         # Dashboard route group
├── features/                 # Feature modules
│   ├── projects/
│   │   ├── components/      # Feature-specific components
│   │   │   ├── project-list.tsx        # Server Component (default)
│   │   │   └── project-actions.tsx     # Client Component ("use client")
│   │   ├── hooks/          # Custom hooks
│   │   ├── api/            # API related functions
│   │   └── types/          # Type definitions
│   └── traces/
├── components/              # Shared components
│   ├── ui/                 # shadcn/ui components
│   └── common/            # Other shared components
└── lib/                    # Utilities and configurations
```

#### Naming Conventions
- **Server Components**: Default, no special suffix
- **Client Components**: Consider `.client.tsx` suffix or clear "use client" directive
- **Files**: kebab-case (e.g., `project-card.tsx`)
- **Components**: PascalCase (e.g., `ProjectCard`)

### State Management

#### TanStack Query for Server State
- Use TanStack Query for server state management
- Implement proper cache invalidation strategies
- Set appropriate stale times for data freshness

#### Zustand for Client State
- Use Zustand for lightweight global state management
- Keep client state minimal and focused on UI concerns

### API Communication

#### Unified API Client
- Implement a centralized API client for all HTTP requests
- Include authentication headers and error handling
- Use proper TypeScript typing for requests and responses

### Styling with Tailwind CSS and shadcn/ui

#### Component Variants with CVA
- Use Class Variance Authority (CVA) for component variants
- Define base styles and variant options clearly
- Implement proper TypeScript types for variant props

#### Tailwind Class Organization
- Organize classes in logical groups (layout, sizing, spacing, colors, effects)
- Use responsive prefixes appropriately
- Handle conditional classes with proper logic

#### Dark Mode Guidelines
- Use CSS variables for colors: `bg-background`, `text-foreground`
- Avoid hardcoded colors: ~~`bg-white dark:bg-gray-900`~~
- Let shadcn/ui handle theme switching

### Form Handling

#### Complex Forms with React Hook Form + Zod
- Use React Hook Form with Zod validation for complex forms
- Implement proper schema validation and error handling
- Use shadcn/ui Form components for consistent styling

#### Simple Forms with Server Actions
- Prefer Server Actions for simple form submissions
- Implement server-side validation with Zod schemas
- Handle form errors and redirects appropriately

### Error Handling

#### Error Types and Boundaries
- Create custom ApiError class with status codes
- Implement Next.js error.tsx for route-level error handling
- Use React Error Boundaries for component-level error handling

#### API Error Handling with TanStack Query
- Configure retry strategies based on error types
- Implement global error handling for mutations
- Handle authentication errors with proper redirects

### TypeScript Configuration

#### Strict TypeScript Settings
- Enable strict mode and all strict type checking options
- Use noUncheckedIndexedAccess for safer array/object access
- Configure path mapping for clean imports (@/*)

#### Type Definition Guidelines
- Use `interface` for object shapes, `type` for unions and utilities
- Implement proper generic types for reusable components
- Use const assertions for literal types and discriminated unions
- Extend React types properly for component props
- Declare global types for environment variables

### Testing Strategy

#### Test Setup with Vitest
- Configure Vitest with jsdom environment for React testing
- Set up Testing Library with proper cleanup
- Configure path aliases to match project structure

#### Testing Priorities
1. **Critical Business Logic** - Data quality calculations, core algorithms
2. **Authentication Flows** - Login, registration, token handling
3. **Form Validation** - User input validation and error handling

#### What NOT to Test
- UI appearance/styling
- External library behavior  
- Simple prop passing
- Generated types

### Performance Optimization

#### Next.js Built-in Optimizations
- Use Next.js Image component with proper sizing and lazy loading
- Optimize fonts with next/font for better loading performance
- Implement dynamic imports for code splitting heavy components
- Use parallel data fetching in Server Components with Promise.all
- Implement Streaming with Suspense for better UX
- Use React.memo and useMemo for expensive computations

#### Bundle Size Optimization
- Use bundle analyzer to identify large dependencies
- Implement code splitting for route-based and component-based chunks
- Tree-shake unused library code

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
- `JWT_REFRESH_SECRET_KEY`: Secret key for refresh token generation
- `ENABLE_REGISTRATION`: Boolean to enable/disable user registration
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: Access token expiration time (default: 30)
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token expiration time (default: 7)

### Frontend Environment Variables
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)
- `NEXT_PUBLIC_API_VERSION`: API version (default: v1)

## Key Features and Flows

### Data Quality Monitoring Flow
1. **Project Setup**: User creates account, organization, and project configuration
2. **Platform Connection**: Project includes Langfuse credentials (public_key, secret_key, host)
3. **Data Sync**: Platform continuously syncs trace data and observations from Langfuse
4. **Quality Analysis**: System calculates quality scores and analyzes data patterns
5. **Quality Monitoring**: Dashboard provides real-time quality metrics and trend analysis
6. **Guardrail Configuration**: Define data quality rules and validation strategies
7. **Guardrail Activation**: SDK-based guardrails automatically filter and validate data

### SDK Integration Flow
1. **SDK Installation**: Developers integrate the datagusto SDK into their AI agent systems
2. **Guardrail Configuration**: Define data quality rules and handling strategies
3. **Runtime Monitoring**: SDK monitors data quality during tool calling and processing
4. **Automatic Remediation**: Configured guardrails automatically filter, clean, or halt processing based on data quality

### Data Models
- **User**: User account and authentication management
- **Organization**: Multi-tenant organization management with member roles
- **Project**: AI agent configuration and observability platform connections
- **Trace**: Individual AI agent execution traces with quality scores
- **Observation**: Detailed trace observations and data points
- **Guardrail**: Data quality rules and validation strategies
- **AuditLog**: System activity and change tracking

### Testing Strategy

#### Test Priorities
**High Priority (Must Test):**
- Data quality calculation logic - Core business functionality
- Langfuse API integration - External service reliability
- Authentication and authorization - Security critical
- Trace analysis algorithms - Main feature

**Medium Priority (Should Test):**
- Important API endpoints - User-facing functionality
- Database operations - Data integrity
- Input validation - Data consistency

**Low Priority (Don't Test):**
- Simple CRUD operations - Framework functionality
- Configuration loading - Library functionality
- Thin wrapper functions - Minimal business logic

#### Test Tools and Setup
```bash
# Install test dependencies
uv add --dev pytest pytest-asyncio httpx factory-boy freezegun pytest-mock coverage

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=app --cov-report=html --cov-report=term-missing

# Run specific test types
uv run pytest tests/unit/        # Unit tests only
uv run pytest tests/integration/ # Integration tests only
```

#### Test Configuration
```ini
# pytest.ini
[tool:pytest]
addopts = 
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=70
    --asyncio-mode=auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

[tool.coverage.run]
omit = 
    app/main.py
    app/core/config.py
    app/models/__init__.py
    */migrations/*
    */tests/*
```

#### Database Testing
```python
# conftest.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient

TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5433/test_datagusto"

@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(test_engine):
    async with test_engine.begin() as conn:
        async_session = sessionmaker(conn, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            yield session
            # Transaction automatically rolled back

@pytest.fixture
async def test_client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
```

#### Test Data Factories
- Use factory-boy for generating test data consistently
- Create factories for main domain models (User, Project, Trace)
- Use Faker for realistic test data generation

#### Mock Strategy
- Always mock external APIs (Langfuse, OpenAI) in tests
- Use freezegun for time-dependent function testing
- Mock repositories when testing services
- Use AsyncMock for async functions

#### Test Examples
- Write unit tests for business logic (data quality calculations)
- Create integration tests for API endpoints with proper assertions
- Test external service integrations with mocked clients

#### Coverage Goals
**Phase 1 (Current):** 50% - Focus on critical business logic
**Phase 2 (6 months):** 70% - Cover main API endpoints and services  
**Phase 3 (1 year):** 80% - Comprehensive coverage for stable operation

#### Test Organization
```
tests/
├── unit/
│   ├── services/
│   │   ├── test_data_quality_service.py
│   │   ├── test_trace_service.py
│   │   └── test_langfuse_service.py
│   ├── repositories/
│   │   └── test_trace_repository.py
│   └── utils/
│       └── test_calculations.py
├── integration/
│   ├── api/
│   │   ├── test_auth_endpoints.py
│   │   ├── test_project_endpoints.py
│   │   └── test_trace_endpoints.py
│   └── database/
│       └── test_migrations.py
├── factories.py
└── conftest.py
```

## Database Migrations

### Alembic Configuration
- Uses Alembic for database schema management
- Migration files in `backend/alembic/versions/`
- Create migration: `alembic revision --autogenerate -m "description"`
- Apply migrations: `alembic upgrade head`

## API Structure

### Current Endpoints
- `/api/v1/auth/*`: Authentication and user management endpoints
- `/api/v1/organizations/*`: Organization management and member operations
- `/api/v1/projects/*`: Project management and observability platform connections
- `/api/v1/traces/*`: Trace data synchronization and quality analysis
- `/api/v1/guardrails/*`: Guardrail configuration and management

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

## Backend Development Guidelines (FastAPI)

### Code Organization and Architecture

#### Layered Architecture
The backend strictly follows a layered architecture pattern:

```
app/
├── api/         # API Layer - HTTP endpoints, request/response handling
├── services/    # Service Layer - Business logic, orchestration
├── repositories/# Repository Layer - Data access abstraction
├── models/      # SQLAlchemy models - Database schema
├── schemas/     # Pydantic models - Request/response validation
└── core/        # Core utilities - Config, security, dependencies
```

**Rules:**
- Each layer should only depend on layers below it
- API layer calls Service layer, never Repository directly
- Service layer orchestrates business logic and calls Repository layer
- Repository layer handles all database operations

#### File Naming Conventions
- Use snake_case for all Python files and modules
- Suffix files with their layer type: `_service.py`, `_repository.py`, `_schema.py`
- Group related functionality in the same file

### API Design Standards

#### RESTful Endpoints
- Use proper HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Avoid verbs in URLs - let HTTP methods indicate actions
- Use consistent resource naming conventions

#### Async-First Approach
- All endpoints and service methods MUST be async unless there's a specific reason
- Use proper dependency injection for repositories and services
- Handle errors with appropriate HTTP status codes

### Error Handling

#### Simple HTTPException Usage
- Use FastAPI's built-in HTTPException for error handling
- Return appropriate HTTP status codes (404, 422, 401, 403)
- Provide clear error messages for debugging

### Service Layer Patterns

#### Service with Dependency Injection
- Services use dependency injection pattern consistent with repositories
- Inject repositories and external clients through constructor
- Implement clear business logic methods with proper async/await

#### Transaction Management
- Handle transactions at the service layer using async context managers
- Ensure atomic operations for related data changes
- Implement proper rollback on errors

### Repository Layer Patterns

#### Base Repository Pattern
- Use a base repository for common CRUD operations
- Implement generic typing for type safety
- Use flush() instead of commit() to get IDs without committing

#### Repository Implementation
- Extend base repository for domain-specific queries
- Implement organization-scoped queries for multi-tenancy
- Use proper ordering and filtering in queries

### Database Models and Schemas

#### Model Naming and Structure
- Use descriptive column names and proper SQLAlchemy types
- Implement relationships with appropriate cascade options
- Add database indexes for performance on frequently queried columns

#### Pydantic Schema Patterns
- Create base schemas for shared fields, separate Create/Update/Response schemas
- Use proper field validation with Pydantic Field constraints
- Configure from_attributes for SQLAlchemy model serialization

### Dependency Injection

#### Database Session Management
- Use async context managers for database sessions
- Implement proper commit/rollback handling
- Ensure sessions are closed properly

#### Repository Injection
- Create dependency functions for repository injection
- Use FastAPI Depends for clean dependency injection
- Keep repositories stateless and reusable

### Authentication and Authorization

#### JWT Token Handling
- Use jose library for JWT creation and validation
- Implement proper token expiration and refresh logic
- Use bcrypt for password hashing with passlib

#### Permission Checking
- Implement organization-scoped access control
- Verify user permissions before resource access
- Return appropriate HTTP status codes for access violations

### Logging

#### Simple Logging
- Use Python's standard logging module with clear messages
- Log important operations with relevant context
- Include exception info for error logging

### Testing Standards

#### Test Organization
```
tests/
├── unit/
│   ├── services/
│   ├── repositories/
│   └── utils/
├── integration/
│   ├── api/
│   └── database/
└── conftest.py  # Shared fixtures
```

#### Test Patterns
- Follow Arrange-Act-Assert pattern for test structure
- Use AsyncMock for async function mocking
- Assert both return values and method calls

### Performance Optimization

#### Query Optimization
- Use eager loading (selectinload) for related data to avoid N+1 queries
- Implement pagination for large datasets with offset/limit
- Add proper ordering to queries for consistent results


### Code Quality Standards

#### Type Hints
- Always use type hints for function parameters and return values
- Import proper types from typing module and domain models
- Use Optional for nullable parameters and return values

#### Docstrings
- Use clear, concise docstrings in English for all public functions
- Include Args, Returns, and Raises sections
- Explain the business purpose and behavior

#### Comments
- All comments must be in English
- Explain complex business logic and non-obvious decisions
- Avoid obvious comments that just restate the code

### Environment Variables

#### Configuration Management
- Use pydantic-settings for type-safe environment variable management
- Define required and optional settings with proper defaults
- Support .env files for local development

### Database Migrations

#### Migration Naming Convention
- Use descriptive names starting with a verb (create, add, update, remove)
- Include the table/column being modified
- Avoid vague names like "fix" or "update"

### Background Tasks

#### Using arq for Async Task Processing
- Use arq for reliable background task processing
- Implement proper task context and error handling
- Return job IDs for task tracking

### API Versioning

Simple versioning strategy:
- All endpoints use `/api/v1` prefix
- Breaking changes require new version (`/api/v2`)
- No complex versioning rules

## Important Notes

- Simple, lightweight architecture focused on data quality monitoring
- Manual deployment workflow - no automated CI/CD pipeline
- Strategic testing approach with 70% coverage target
- Uses JWT with refresh tokens for authentication (no external auth providers)
- Docker standard logging - no advanced monitoring setup
- **Primary Focus**: Data quality measurement and prevention for AI agents
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

## 📝 Additional Project-Specific Rules

### Test Environment Management
**When creating tests:**
1. Always use PostgreSQL for test database (not SQLite or in-memory DB)
2. Create separate docker-compose.test.yml for test environment
3. Use different ports for test services to avoid conflicts (e.g., 5433 for test PostgreSQL)
4. Create setup/cleanup scripts for test environment management
5. Set environment variables BEFORE importing app modules in conftest.py

**Test script structure:**
```bash
scripts/
├── test_setup.sh     # Initialize test environment
├── test_cleanup.sh   # Clean up after tests
└── run_tests.sh      # Main test runner with options
```

### Testing Workflow
1. Always verify the actual implementation before writing tests
2. Create comprehensive test plans and get them reviewed before implementation
3. Test one component at a time and verify it works before moving to the next
4. Use proper PostgreSQL test database with migrations, not mock databases

### Backend Refactoring Guidelines
**Layered Architecture Implementation:**
1. API Layer must NOT call Repository layer directly - always use Service layer
2. Create Service classes with dependency injection pattern
3. Use FastAPI Depends() for service injection in endpoints
4. Service layer handles business logic and orchestrates repository calls
5. Create dedicated dependency injection functions in app/core/dependencies.py
6. Update all API endpoints to use service layer instead of direct repository access

**Service Layer Standards:**
- Constructor-based dependency injection for repositories
- Comprehensive docstrings with Args, Returns, Raises sections
- Proper exception handling with HTTPException
- Clear separation of business logic from API concerns
- Transaction management at service layer (commit/rollback)

**Refactoring Process:**
1. Create Service class with proper dependency injection
2. Write comprehensive unit tests for the service
3. Update API endpoints to use service instead of repositories
4. Update dependency injection in app/core/dependencies.py
5. Run tests to verify refactoring didn't break functionality
6. Never skip testing step - always verify with unit tests