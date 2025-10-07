-- ============================================
-- Row Level Security (RLS) for Multi-Tenancy
-- ============================================
-- 
-- This script enables PostgreSQL Row Level Security to enforce
-- organization-level data isolation at the database level.
-- 
-- IMPORTANT: This provides defense-in-depth security, ensuring that
-- even if application-level checks fail, data isolation is maintained.
--
-- Usage:
--   psql -U timetracker -d timetracker -f enable_row_level_security.sql
--
-- Prerequisites:
--   - PostgreSQL 9.5+
--   - The organization_id column must exist on all tables
--   - The current_setting function is used to pass organization_id
--
-- ============================================

BEGIN;

-- ============================================
-- Helper function to get current organization from context
-- ============================================

CREATE OR REPLACE FUNCTION current_organization_id()
RETURNS INTEGER AS $$
BEGIN
    -- Try to get organization_id from current_setting
    -- This will be set by the application for each request
    RETURN NULLIF(current_setting('app.current_organization_id', TRUE), '')::INTEGER;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION current_organization_id() IS 
'Returns the current organization ID from the session variable set by the application';


-- ============================================
-- Function to check if user is a super admin
-- (Super admins can access data across organizations)
-- ============================================

CREATE OR REPLACE FUNCTION is_super_admin()
RETURNS BOOLEAN AS $$
BEGIN
    -- Check if current role has super admin flag
    RETURN COALESCE(current_setting('app.is_super_admin', TRUE)::BOOLEAN, FALSE);
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION is_super_admin() IS 
'Returns true if the current session user is a super admin';


-- ============================================
-- Create RLS policies for each tenant-scoped table
-- ============================================

-- Organizations table
-- ============================================
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see organizations they are members of
CREATE POLICY organizations_tenant_isolation ON organizations
    FOR ALL
    USING (
        is_super_admin() OR
        id = current_organization_id() OR
        id IN (
            SELECT organization_id 
            FROM memberships 
            WHERE user_id = current_user_id() 
            AND status = 'active'
        )
    );

COMMENT ON POLICY organizations_tenant_isolation ON organizations IS
'Users can only access organizations they are members of, unless they are super admins';


-- Memberships table
-- ============================================
ALTER TABLE memberships ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see memberships for their organizations
CREATE POLICY memberships_tenant_isolation ON memberships
    FOR ALL
    USING (
        is_super_admin() OR
        organization_id = current_organization_id()
    );

COMMENT ON POLICY memberships_tenant_isolation ON memberships IS
'Users can only access memberships within their current organization';


-- Projects table
-- ============================================
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY projects_tenant_isolation ON projects
    FOR ALL
    USING (
        is_super_admin() OR
        organization_id = current_organization_id()
    );

COMMENT ON POLICY projects_tenant_isolation ON projects IS
'Users can only access projects within their current organization';


-- Clients table
-- ============================================
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;

CREATE POLICY clients_tenant_isolation ON clients
    FOR ALL
    USING (
        is_super_admin() OR
        organization_id = current_organization_id()
    );

COMMENT ON POLICY clients_tenant_isolation ON clients IS
'Users can only access clients within their current organization';


-- Time Entries table
-- ============================================
ALTER TABLE time_entries ENABLE ROW LEVEL SECURITY;

CREATE POLICY time_entries_tenant_isolation ON time_entries
    FOR ALL
    USING (
        is_super_admin() OR
        organization_id = current_organization_id()
    );

COMMENT ON POLICY time_entries_tenant_isolation ON time_entries IS
'Users can only access time entries within their current organization';


-- Tasks table
-- ============================================
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY tasks_tenant_isolation ON tasks
    FOR ALL
    USING (
        is_super_admin() OR
        organization_id = current_organization_id()
    );

COMMENT ON POLICY tasks_tenant_isolation ON tasks IS
'Users can only access tasks within their current organization';


-- Invoices table
-- ============================================
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;

CREATE POLICY invoices_tenant_isolation ON invoices
    FOR ALL
    USING (
        is_super_admin() OR
        organization_id = current_organization_id()
    );

COMMENT ON POLICY invoices_tenant_isolation ON invoices IS
'Users can only access invoices within their current organization';


-- Comments table
-- ============================================
ALTER TABLE comments ENABLE ROW LEVEL SECURITY;

CREATE POLICY comments_tenant_isolation ON comments
    FOR ALL
    USING (
        is_super_admin() OR
        organization_id = current_organization_id()
    );

COMMENT ON POLICY comments_tenant_isolation ON comments IS
'Users can only access comments within their current organization';


-- Focus Sessions table
-- ============================================
ALTER TABLE focus_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY focus_sessions_tenant_isolation ON focus_sessions
    FOR ALL
    USING (
        is_super_admin() OR
        organization_id = current_organization_id()
    );

COMMENT ON POLICY focus_sessions_tenant_isolation ON focus_sessions IS
'Users can only access focus sessions within their current organization';


-- Saved Filters table
-- ============================================
ALTER TABLE saved_filters ENABLE ROW LEVEL SECURITY;

CREATE POLICY saved_filters_tenant_isolation ON saved_filters
    FOR ALL
    USING (
        is_super_admin() OR
        organization_id = current_organization_id()
    );

COMMENT ON POLICY saved_filters_tenant_isolation ON saved_filters IS
'Users can only access saved filters within their current organization';


-- Task Activities table
-- ============================================
ALTER TABLE task_activities ENABLE ROW LEVEL SECURITY;

CREATE POLICY task_activities_tenant_isolation ON task_activities
    FOR ALL
    USING (
        is_super_admin() OR
        organization_id = current_organization_id()
    );

COMMENT ON POLICY task_activities_tenant_isolation ON task_activities IS
'Users can only access task activities within their current organization';


-- ============================================
-- Create helper function for application to set organization context
-- ============================================

CREATE OR REPLACE FUNCTION set_organization_context(org_id INTEGER, is_admin BOOLEAN DEFAULT FALSE)
RETURNS VOID AS $$
BEGIN
    -- Set the organization ID for the current transaction
    PERFORM set_config('app.current_organization_id', org_id::TEXT, FALSE);
    
    -- Set super admin flag
    PERFORM set_config('app.is_super_admin', is_admin::TEXT, FALSE);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION set_organization_context(INTEGER, BOOLEAN) IS
'Sets the organization context for the current transaction. Call this at the start of each request.';


-- ============================================
-- Create helper function to clear organization context
-- ============================================

CREATE OR REPLACE FUNCTION clear_organization_context()
RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_organization_id', '', FALSE);
    PERFORM set_config('app.is_super_admin', 'false', FALSE);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION clear_organization_context() IS
'Clears the organization context. Call this at the end of each request.';


-- ============================================
-- Verification Query
-- ============================================

-- To verify RLS is working, run these queries:
-- 
-- -- Set context for organization 1
-- SELECT set_organization_context(1);
-- SELECT * FROM projects;  -- Should only show org 1 projects
-- 
-- -- Set context for organization 2
-- SELECT set_organization_context(2);
-- SELECT * FROM projects;  -- Should only show org 2 projects
-- 
-- -- Clear context
-- SELECT clear_organization_context();
-- SELECT * FROM projects;  -- Should show no projects (unless super admin)


COMMIT;

-- ============================================
-- IMPORTANT NOTES
-- ============================================
-- 
-- 1. Application Integration:
--    The application must call set_organization_context() at the start
--    of each request to set the proper organization context.
--
-- 2. Connection Pooling:
--    If using connection pooling, ensure context is set for each
--    request and cleared afterwards, or use transaction-level settings.
--
-- 3. Superuser Access:
--    Database superusers bypass RLS. Use dedicated application users
--    with limited privileges for normal operations.
--
-- 4. Performance:
--    RLS policies are applied to every query. Ensure proper indexes
--    exist on organization_id columns (already created in migration).
--
-- 5. Testing:
--    Always test RLS policies thoroughly before deploying to production.
--    Verify that users cannot access data from other organizations.
--
-- ============================================

\echo '✅ Row Level Security policies created successfully!'
\echo ''
\echo 'Next steps:'
\echo '1. Update application code to call set_organization_context() at request start'
\echo '2. Test RLS policies with different organization contexts'
\echo '3. Monitor query performance with RLS enabled'
\echo '4. Consider creating application-specific database users (not superusers)'

