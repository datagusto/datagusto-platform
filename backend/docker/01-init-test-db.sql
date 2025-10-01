-- Create test database for integration and repository tests
-- This file is automatically executed by PostgreSQL on container initialization

CREATE DATABASE datagusto_test;

-- Grant privileges to the default postgres user
GRANT ALL PRIVILEGES ON DATABASE datagusto_test TO postgres;