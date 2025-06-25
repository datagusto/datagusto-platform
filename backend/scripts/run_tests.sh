#!/usr/bin/env bash
set -euo pipefail

# Comprehensive test runner script
echo "🚀 DataGusto Backend Test Runner"
echo "================================"

# Check if test environment is set up
if ! docker compose -f docker-compose.test.yml ps | grep -q "postgres-test.*Up"; then
    echo "⚠️  Test environment not running. Setting up..."
    ./scripts/test_setup.sh
fi

# Export environment variables
export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5433/datagusto_test"
export DATABASE_URL="$TEST_DATABASE_URL"
export ENABLE_REGISTRATION="true"
export JWT_SECRET_KEY="test-secret-key-for-testing-only"
export JWT_REFRESH_SECRET_KEY="test-refresh-secret-key-for-testing-only"
export JWT_ACCESS_TOKEN_EXPIRE_MINUTES="30"
export JWT_REFRESH_TOKEN_EXPIRE_DAYS="7"

# Parse command line arguments
TEST_TARGET="${1:-all}"
VERBOSE="${2:-}"

cd /Users/nkmrtty/repos/datagusto-platform-backend-refactoring/backend

case "$TEST_TARGET" in
    "unit")
        echo "🧪 Running unit tests..."
        uv run pytest tests/unit/ -v --tb=short
        ;;
    "services")
        echo "🧪 Running service tests..."
        uv run pytest tests/services/ -v --tb=short
        ;;
    "api")
        echo "🧪 Running API tests..."
        uv run pytest tests/api/ -v --tb=short
        ;;
    "auth")
        echo "🧪 Running AuthService tests..."
        uv run pytest tests/services/test_auth_service.py -v --tb=short
        ;;
    "quality")
        echo "🧪 Running DataQualityService tests..."
        uv run pytest tests/services/test_data_quality_service.py -v --tb=short
        ;;
    "coverage")
        echo "📊 Running tests with coverage..."
        uv run pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
        echo "Coverage report generated at: htmlcov/index.html"
        ;;
    "all")
        echo "🧪 Running all tests..."
        if [ "$VERBOSE" = "-v" ]; then
            uv run pytest tests/ -v --tb=short
        else
            uv run pytest tests/ --tb=short
        fi
        ;;
    *)
        echo "Usage: $0 [unit|services|api|auth|quality|coverage|all] [-v]"
        echo ""
        echo "Examples:"
        echo "  $0 auth        # Run only AuthService tests"
        echo "  $0 services -v # Run all service tests with verbose output"
        echo "  $0 coverage    # Run all tests with coverage report"
        exit 1
        ;;
esac

echo ""
echo "✅ Test run completed!"