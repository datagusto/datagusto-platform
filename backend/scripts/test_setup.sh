#!/usr/bin/env bash
set -euo pipefail

# Script for setting up test environment
echo "🔧 Setting up test environment..."

# Start test PostgreSQL if not running
echo "📦 Starting test PostgreSQL container..."
docker compose -f docker-compose.test.yml up -d postgres-test

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if docker compose -f docker-compose.test.yml exec -T postgres-test pg_isready -U postgres >/dev/null 2>&1; then
        echo "✅ PostgreSQL is ready!"
        break
    fi
    echo -n "."
    sleep 1
done

# Export test environment variables
export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5433/datagusto_test"
export DATABASE_URL="$TEST_DATABASE_URL"
export ENABLE_REGISTRATION="true"
export JWT_SECRET_KEY="test-secret-key-for-testing-only"
export JWT_REFRESH_SECRET_KEY="test-refresh-secret-key-for-testing-only"
export JWT_ACCESS_TOKEN_EXPIRE_MINUTES="30"
export JWT_REFRESH_TOKEN_EXPIRE_DAYS="7"

echo "🌍 Environment variables set:"
echo "   TEST_DATABASE_URL=$TEST_DATABASE_URL"
echo "   ENABLE_REGISTRATION=$ENABLE_REGISTRATION"

# Run migrations on test database
echo "🔄 Running migrations on test database..."
cd /Users/nkmrtty/repos/datagusto-platform-backend-refactoring/backend
uv run alembic upgrade head

echo "✨ Test environment is ready!"
echo ""
echo "You can now run tests with:"
echo "   uv run pytest tests/"
echo ""
echo "To run specific test files:"
echo "   uv run pytest tests/services/test_auth_service.py -v"
echo ""
echo "To clean up after testing, run:"
echo "   ./scripts/test_cleanup.sh"