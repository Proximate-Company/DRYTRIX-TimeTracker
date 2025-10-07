-- Manual fix for migration 018 if it partially failed
-- Run this if the migration added columns but failed on indexes/constraints

-- First, check if we're at the right migration state
-- The migration should have added organization_id to all tables

BEGIN;

-- ========================================
-- Check what exists
-- ========================================
DO $$
BEGIN
    -- Check if organizations table exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'organizations') THEN
        RAISE NOTICE '✓ Organizations table exists';
    ELSE
        RAISE EXCEPTION 'Organizations table does not exist - migration did not complete step 1';
    END IF;
    
    -- Check if memberships table exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'memberships') THEN
        RAISE NOTICE '✓ Memberships table exists';
    ELSE
        RAISE EXCEPTION 'Memberships table does not exist - migration did not complete step 2';
    END IF;
    
    -- Check if organization_id was added to projects
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_name = 'projects' AND column_name = 'organization_id') THEN
        RAISE NOTICE '✓ Projects.organization_id exists';
    ELSE
        RAISE EXCEPTION 'Projects.organization_id does not exist - migration did not complete step 5';
    END IF;
END $$;

-- ========================================
-- Create missing indexes (safe - will skip if exists)
-- ========================================

-- Helper function to safely create index
CREATE OR REPLACE FUNCTION create_index_if_not_exists(index_name TEXT, table_name TEXT, columns TEXT)
RETURNS VOID AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = index_name) THEN
        EXECUTE format('CREATE INDEX %I ON %I (%s)', index_name, table_name, columns);
        RAISE NOTICE 'Created index: %', index_name;
    ELSE
        RAISE NOTICE 'Index already exists: %', index_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Projects indexes
SELECT create_index_if_not_exists('idx_projects_org_status', 'projects', 'organization_id, status');
SELECT create_index_if_not_exists('idx_projects_org_client', 'projects', 'organization_id, client_id');

-- Clients indexes
SELECT create_index_if_not_exists('idx_clients_org_status', 'clients', 'organization_id, status');

-- Time entries indexes
SELECT create_index_if_not_exists('idx_time_entries_org_user', 'time_entries', 'organization_id, user_id');
SELECT create_index_if_not_exists('idx_time_entries_org_project', 'time_entries', 'organization_id, project_id');
SELECT create_index_if_not_exists('idx_time_entries_org_dates', 'time_entries', 'organization_id, start_time, end_time');

-- Tasks indexes
SELECT create_index_if_not_exists('idx_tasks_org_project', 'tasks', 'organization_id, project_id');
SELECT create_index_if_not_exists('idx_tasks_org_status', 'tasks', 'organization_id, status');
SELECT create_index_if_not_exists('idx_tasks_org_assigned', 'tasks', 'organization_id, assigned_to');

-- Invoices indexes
SELECT create_index_if_not_exists('idx_invoices_org_status', 'invoices', 'organization_id, status');
SELECT create_index_if_not_exists('idx_invoices_org_client', 'invoices', 'organization_id, client_id');

-- Comments indexes
SELECT create_index_if_not_exists('idx_comments_org_project', 'comments', 'organization_id, project_id');
SELECT create_index_if_not_exists('idx_comments_org_task', 'comments', 'organization_id, task_id');
SELECT create_index_if_not_exists('idx_comments_org_user', 'comments', 'organization_id, user_id');

-- Drop helper function
DROP FUNCTION create_index_if_not_exists(TEXT, TEXT, TEXT);

-- ========================================
-- Update unique constraints for clients
-- ========================================
DO $$
BEGIN
    -- Drop old unique constraint on clients.name if it exists
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'clients_name_key') THEN
        ALTER TABLE clients DROP CONSTRAINT clients_name_key;
        RAISE NOTICE 'Dropped old constraint: clients_name_key';
    ELSE
        RAISE NOTICE 'Constraint clients_name_key does not exist (already dropped or never existed)';
    END IF;
    
    -- Create new unique constraint per organization
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_clients_org_name') THEN
        ALTER TABLE clients ADD CONSTRAINT uq_clients_org_name UNIQUE (organization_id, name);
        RAISE NOTICE 'Created constraint: uq_clients_org_name';
    ELSE
        RAISE NOTICE 'Constraint uq_clients_org_name already exists';
    END IF;
END $$;

-- ========================================
-- Update unique constraints for invoices
-- ========================================
DO $$
BEGIN
    -- Drop old unique constraint on invoices.invoice_number if it exists
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'invoices_invoice_number_key') THEN
        ALTER TABLE invoices DROP CONSTRAINT invoices_invoice_number_key;
        RAISE NOTICE 'Dropped old constraint: invoices_invoice_number_key';
    ELSE
        RAISE NOTICE 'Constraint invoices_invoice_number_key does not exist (already dropped or never existed)';
    END IF;
    
    -- Create new unique constraint per organization
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uq_invoices_org_number') THEN
        ALTER TABLE invoices ADD CONSTRAINT uq_invoices_org_number UNIQUE (organization_id, invoice_number);
        RAISE NOTICE 'Created constraint: uq_invoices_org_number';
    ELSE
        RAISE NOTICE 'Constraint uq_invoices_org_number already exists';
    END IF;
END $$;

-- ========================================
-- Mark migration as complete
-- ========================================
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM alembic_version WHERE version_num = '018') THEN
        RAISE NOTICE '✓ Migration 018 already marked as complete';
    ELSE
        UPDATE alembic_version SET version_num = '018';
        RAISE NOTICE '✓ Marked migration 018 as complete';
    END IF;
END $$;

COMMIT;

-- ========================================
-- Verification
-- ========================================
SELECT 'Migration 018 fix completed successfully!' as status;

-- Show current state
SELECT 'Alembic version: ' || version_num as info FROM alembic_version;

-- Count organizations and memberships
SELECT 'Organizations: ' || COUNT(*)::TEXT as info FROM organizations;
SELECT 'Memberships: ' || COUNT(*)::TEXT as info FROM memberships;

-- Verify organization_id columns exist
SELECT 
    'Table: ' || table_name || ' has organization_id: ' || 
    CASE WHEN EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = t.table_name 
        AND column_name = 'organization_id'
    ) THEN 'YES' ELSE 'NO' END as verification
FROM (
    SELECT unnest(ARRAY['projects', 'clients', 'time_entries', 'tasks', 
                        'invoices', 'comments', 'focus_sessions', 
                        'saved_filters', 'task_activities']) as table_name
) t;

