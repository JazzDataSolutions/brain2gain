-- Initialize production and test databases
-- This script runs when the PostgreSQL container starts

-- Set up extensions that might be needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create production database and user if they don't exist
CREATE DATABASE brain2gain_prod;
CREATE USER brain2gain_prod WITH PASSWORD 'Brain2GainPostgres2025!Secure';
GRANT ALL PRIVILEGES ON DATABASE brain2gain_prod TO brain2gain_prod;

-- Create test database and user if they don't exist
CREATE DATABASE brain2gain_test;
CREATE USER brain2gain_test WITH PASSWORD 'test_password';
GRANT ALL PRIVILEGES ON DATABASE brain2gain_test TO brain2gain_test;