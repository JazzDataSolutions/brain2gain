-- Initialize test databases
-- This script runs when the PostgreSQL container starts

-- Set up extensions that might be needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE brain2gain_test TO brain2gain_test;