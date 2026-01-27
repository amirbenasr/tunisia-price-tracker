-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "timescaledb";

-- Create text search configuration for product names
-- This helps with full-text search on product names
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_ts_config WHERE cfgname = 'product_search') THEN
        CREATE TEXT SEARCH CONFIGURATION product_search (COPY = english);
    END IF;
END$$;
