#!/usr/bin/env bash
set -euo pipefail

# Script for cleaning up test environment
echo "🧹 Cleaning up test environment..."

# Stop and remove test containers
echo "🛑 Stopping test PostgreSQL container..."
docker compose -f docker-compose.test.yml down -v

# Remove test database volume
echo "🗑️  Removing test database volume..."
docker volume rm backend_postgres_test_data 2>/dev/null || true

echo "✨ Test environment cleaned up!"