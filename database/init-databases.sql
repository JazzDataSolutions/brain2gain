-- Initialize databases for Brain2Gain microservices
-- This script creates separate databases for each microservice

-- Create databases for microservices
CREATE DATABASE brain2gain_auth;
CREATE DATABASE brain2gain_products;
CREATE DATABASE brain2gain_orders;
CREATE DATABASE brain2gain_inventory;

-- Grant permissions to brain2gain_user for all databases
GRANT ALL PRIVILEGES ON DATABASE brain2gain TO brain2gain_user;
GRANT ALL PRIVILEGES ON DATABASE brain2gain_auth TO brain2gain_user;
GRANT ALL PRIVILEGES ON DATABASE brain2gain_products TO brain2gain_user;
GRANT ALL PRIVILEGES ON DATABASE brain2gain_orders TO brain2gain_user;
GRANT ALL PRIVILEGES ON DATABASE brain2gain_inventory TO brain2gain_user;

-- Connect to each database and grant schema permissions
\c brain2gain_auth;
GRANT ALL ON SCHEMA public TO brain2gain_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO brain2gain_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO brain2gain_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO brain2gain_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO brain2gain_user;

\c brain2gain_products;
GRANT ALL ON SCHEMA public TO brain2gain_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO brain2gain_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO brain2gain_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO brain2gain_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO brain2gain_user;

\c brain2gain_orders;
GRANT ALL ON SCHEMA public TO brain2gain_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO brain2gain_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO brain2gain_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO brain2gain_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO brain2gain_user;

\c brain2gain_inventory;
GRANT ALL ON SCHEMA public TO brain2gain_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO brain2gain_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO brain2gain_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO brain2gain_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO brain2gain_user;

-- Switch back to main database
\c brain2gain;
GRANT ALL ON SCHEMA public TO brain2gain_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO brain2gain_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO brain2gain_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO brain2gain_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO brain2gain_user;