# Backend Service

FastAPI-based backend service with multi-tenant architecture and organization management.

## Features

- **Multi-tenant Organization Management**: Complete organization lifecycle support
- **User Management**: User profiles, authentication, and authorization
- **Role-Based Access Control**: Owner, Admin, and Member roles
- **Organization Isolation**: Secure data isolation between organizations
- **JWT Authentication**: Token-based authentication with refresh tokens
- **Organization Switching**: Users can belong to multiple organizations
- **RESTful API**: Comprehensive API endpoints with OpenAPI documentation
- **Database Migrations**: Alembic-powered schema versioning
- **Test Coverage**: Unit, integration, and security tests

## Architecture

This application follows a layered architecture with clear separation of concerns:

### 1. **API Layer** (Controllers)
- FastAPI endpoints in `app/api/v1/endpoints/`
- HTTP request/response handling
- Input validation and serialization
- Authentication and authorization enforcement

### 2. **Service Layer**
- Business logic in `app/services/`
- Transaction management
- Cross-cutting concerns (permissions, validation)
- Orchestration of repository operations

### 3. **Repository Layer**
- Data access in `app/repositories/`
- Database query abstraction
- CRUD operations
- Relationship management

### 4. **Model Layer**
- SQLAlchemy models in `app/models/`
- Pydantic schemas in `app/schemas/`
- Database schema definitions

## Multi-Tenant Data Model

The application uses an ultra-fine-grained data model with **13 tables** for maximum flexibility:

### Core Tables
- `organizations`: Organization base data
- `users`: User identity (minimal, ID only)

### Organization Management
- `organization_active_status`: Active/inactive state
- `organization_suspensions`: Suspension history
- `organization_archives`: Soft delete records
- `organization_members`: User membership
- `organization_admins`: Admin privileges
- `organization_owners`: Ownership records

### User Management
- `user_profile`: User profile data (name, bio, avatar)
- `user_login_password`: Authentication credentials
- `user_active_status`: Active/inactive state
- `user_suspensions`: Suspension history
- `user_archives`: Soft delete records

## Technology Stack

- **FastAPI**: Modern Python web framework
- **SQLAlchemy 2.0**: Async ORM with PostgreSQL
- **Alembic**: Database migration tool
- **Pydantic**: Data validation and serialization
- **JWT**: Token-based authentication
- **pytest**: Testing framework
- **Python 3.12**: Latest Python version

## Setup

### 1. Install Dependencies

Using `uv` (recommended):
```bash
uv sync
```

Or using pip:
```bash
pip install -e .
```

### 2. Environment Variables

Create `.env` file with the following configuration:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost/datagusto

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_REFRESH_SECRET_KEY=your-refresh-secret-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Application
DEBUG=True
ENVIRONMENT=development
ENABLE_REGISTRATION=true

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

### 3. Run Database Migrations

```bash
alembic upgrade head
```

### 4. Start Development Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs (if DEBUG=True)
- ReDoc: http://localhost:8000/redoc (if DEBUG=True)

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user with organization
- `POST /api/v1/auth/token` - Login and get JWT tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/switch-organization` - Switch active organization
- `GET /api/v1/auth/me` - Get current user info

### User Management
- `GET /api/v1/users/{user_id}` - Get user details
- `PATCH /api/v1/users/{user_id}/profile` - Update user profile
- `PATCH /api/v1/users/{user_id}/password` - Change password
- `POST /api/v1/users/{user_id}/activate` - Activate user (admin)
- `POST /api/v1/users/{user_id}/deactivate` - Deactivate user (admin)
- `POST /api/v1/users/{user_id}/suspend` - Suspend user (admin)

### Organization Management
- `POST /api/v1/organizations` - Create new organization
- `GET /api/v1/organizations` - List user's organizations
- `GET /api/v1/organizations/{org_id}` - Get organization details
- `PATCH /api/v1/organizations/{org_id}` - Update organization
- `POST /api/v1/organizations/{org_id}/suspend` - Suspend organization
- `POST /api/v1/organizations/{org_id}/archive` - Archive organization

### Organization Members
- `GET /api/v1/organizations/{org_id}/members` - List members
- `POST /api/v1/organizations/{org_id}/members` - Add member (admin)
- `DELETE /api/v1/organizations/{org_id}/members/{user_id}` - Remove member (admin)

### Organization Admins
- `GET /api/v1/organizations/{org_id}/admins` - List admins
- `POST /api/v1/organizations/{org_id}/admins` - Grant admin (owner)
- `DELETE /api/v1/organizations/{org_id}/admins/{user_id}` - Revoke admin (owner)

### Organization Ownership
- `GET /api/v1/organizations/{org_id}/owner` - Get current owner
- `POST /api/v1/organizations/{org_id}/transfer-ownership` - Transfer ownership (owner)

## Testing

### Run All Tests
```bash
uv run pytest
```

### Run Specific Test Categories
```bash
# Controller tests only
uv run pytest tests/api/

# Integration tests
uv run pytest tests/integration/ -m integration

# Security tests
uv run pytest tests/security/ -m security
```

### Test Coverage
```bash
uv run pytest --cov=app --cov-report=html
```

## Project Structure

```
backend/
├── alembic/                    # Database migrations
│   └── versions/              # Migration files
├── app/
│   ├── api/                   # API layer
│   │   └── v1/
│   │       ├── endpoints/    # API endpoints
│   │       └── router.py     # Route registration
│   ├── core/                 # Core functionality
│   │   ├── auth.py          # Authentication dependencies
│   │   ├── config.py        # Configuration
│   │   ├── database.py      # Database setup
│   │   ├── multi_tenant.py  # Multi-tenant utilities
│   │   └── security.py      # JWT and password handling
│   ├── models/              # SQLAlchemy models
│   │   ├── base.py         # Base model class
│   │   ├── organization.py # Organization models
│   │   └── user.py         # User models
│   ├── repositories/        # Data access layer
│   │   ├── base_repository.py
│   │   ├── organization_*.py
│   │   └── user_*.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── organization.py
│   │   └── user.py
│   ├── services/            # Business logic layer
│   │   ├── auth_service.py
│   │   ├── organization_*.py
│   │   ├── permission_service.py
│   │   └── user_service.py
│   └── main.py             # Application entry point
├── tests/                   # Test suite
│   ├── api/                # API/controller tests
│   ├── integration/        # Integration tests
│   ├── security/           # Security tests
│   └── conftest.py         # Shared fixtures
├── .env                    # Environment variables (gitignored)
├── .env.sample            # Environment template
├── alembic.ini            # Alembic configuration
├── pyproject.toml         # Project dependencies
└── README.md              # This file
```

## Development Guidelines

### Code Style
- Follow PEP 8 style guide
- Use `ruff` for linting and formatting
- Add type hints to all functions
- Write comprehensive docstrings

### Testing
- Write tests for all new features
- Maintain test coverage above 70%
- Use pytest fixtures for common setup
- Mock external dependencies

### Database Changes
- Create Alembic migrations for all schema changes
- Test both upgrade and downgrade paths
- Never modify existing migrations
- Add descriptive comments to migrations

### Security
- Never commit secrets or credentials
- Use environment variables for configuration
- Validate all user inputs
- Test authorization on all endpoints
- Follow principle of least privilege

## Deployment

### Production Checklist
- [ ] Set `DEBUG=False` in environment
- [ ] Use strong JWT secret keys
- [ ] Configure production database URL
- [ ] Set up proper CORS origins
- [ ] Enable HTTPS
- [ ] Set up database backups
- [ ] Configure monitoring and logging
- [ ] Run security audit
- [ ] Review and update dependencies

### Environment Variables for Production
```env
DEBUG=False
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://user:password@prod-db/datagusto
JWT_SECRET_KEY=<strong-random-secret>
JWT_REFRESH_SECRET_KEY=<strong-random-secret>
CORS_ORIGINS=["https://yourdomain.com"]
```

## License

[Your License Here]

## Support

For issues and questions, please open an issue on GitHub.