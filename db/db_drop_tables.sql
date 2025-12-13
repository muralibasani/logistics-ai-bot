-- 1. Drop all FOREIGN KEY constraints
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT tc.table_schema, tc.table_name, tc.constraint_name
        FROM information_schema.table_constraints tc
        WHERE tc.constraint_type = 'FOREIGN KEY'
    LOOP
        EXECUTE 'ALTER TABLE '
            || quote_ident(r.table_schema) || '.' || quote_ident(r.table_name)
            || ' DROP CONSTRAINT ' || quote_ident(r.constraint_name) || ' CASCADE';
    END LOOP;
END$$;

-- 2. Drop all TABLES in all non-system schemas
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_type = 'BASE TABLE'
          AND table_schema NOT IN ('pg_catalog', 'information_schema')
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS '
            || quote_ident(r.table_schema) || '.' || quote_ident(r.table_name)
            || ' CASCADE';
    END LOOP;
END$$;
