# Enhanced Database Startup Procedure

This document describes the improved database initialization and startup procedure for TimeTracker that ensures all tables are correctly created with proper schema and handles migrations automatically.

## Overview

The enhanced startup procedure addresses several issues found in the previous implementation:

1. **Missing Analytics Table**: The analytics functionality exists but there was no dedicated analytics table
2. **Schema Verification**: Previous scripts didn't verify that all required columns exist in existing tables
3. **Migration Handling**: Analytics setting migration wasn't integrated into the main startup process
4. **Table Recreation Logic**: Previous logic might drop and recreate tables unnecessarily

## New Components

### 1. Enhanced Database Initialization Script (`init-database-enhanced.py`)

This script provides comprehensive database setup:

- **Schema Definition**: Defines the complete expected database schema including all tables, columns, and relationships
- **Smart Table Creation**: Creates tables only if they don't exist, or adds missing columns if they do exist
- **Index Management**: Creates performance indexes for all tables
- **Trigger Setup**: Sets up automatic timestamp updates for `updated_at` columns
- **Data Initialization**: Inserts default admin user, project, and settings
- **Schema Verification**: Verifies that all required tables and columns exist after initialization

#### Tables Created

- `users` - User accounts and authentication
- `projects` - Project definitions and client information
- `time_entries` - Time tracking records
- `tasks` - Task management within projects
- `settings` - Application configuration and company branding
- `invoices` - Invoice management
- `invoice_items` - Individual invoice line items
 - `focus_sessions` - Pomodoro/focus session summaries linked to `time_entries`
 - `recurring_blocks` - Templates for recurring time blocks to auto-create entries
 - `rate_overrides` - Per-project and per-user billable rate overrides
 - `saved_filters` - User-defined saved filters payloads for reusable queries

#### Key Features

- **Non-destructive**: Never drops existing tables or data
- **Migration-friendly**: Automatically adds missing columns to existing tables
- **Comprehensive**: Handles all aspects of database setup in one script
- **Error-tolerant**: Continues operation even if some optional features fail

### 2. Enhanced Startup Script (`start-enhanced.py`)

Simplified startup process that:

- Uses the enhanced database initialization script
- Provides better error handling and logging
- Displays network information for debugging
- Ensures proper startup sequence

### 3. Database Verification Script (`verify-database.py`)

Independent verification tool that:

- Checks all tables exist with correct schema
- Verifies indexes and foreign keys
- Reports any missing or incorrect elements
- Can be run independently to diagnose issues

## Startup Sequence

1. **Container Start**: Docker container starts with the enhanced startup script
2. **Database Wait**: Waits for PostgreSQL database to be ready
3. **Enhanced Initialization**: Runs the comprehensive database setup script
4. **Schema Verification**: Verifies all tables and columns are correct
5. **Application Start**: Launches the Flask application with Gunicorn

## Database Schema

### Core Tables

#### users
```sql
id SERIAL PRIMARY KEY,
username VARCHAR(80) UNIQUE NOT NULL,
role VARCHAR(20) DEFAULT 'user' NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
last_login TIMESTAMP,
is_active BOOLEAN DEFAULT true NOT NULL,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
```

#### projects
```sql
id SERIAL PRIMARY KEY,
name VARCHAR(200) NOT NULL,
client VARCHAR(200) NOT NULL,
description TEXT,
billable BOOLEAN DEFAULT true NOT NULL,
hourly_rate NUMERIC(9, 2),
billing_ref VARCHAR(100),
status VARCHAR(20) DEFAULT 'active' NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### time_entries
```sql
id SERIAL PRIMARY KEY,
user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
task_id INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
start_time TIMESTAMP NOT NULL,
end_time TIMESTAMP,
duration_seconds INTEGER,
notes TEXT,
tags VARCHAR(500),
source VARCHAR(20) DEFAULT 'manual' NOT NULL,
billable BOOLEAN DEFAULT true NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### tasks
```sql
id SERIAL PRIMARY KEY,
project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
name VARCHAR(200) NOT NULL,
description TEXT,
status VARCHAR(20) DEFAULT 'pending' NOT NULL,
priority VARCHAR(20) DEFAULT 'medium' NOT NULL,
assigned_to INTEGER REFERENCES users(id),
created_by INTEGER REFERENCES users(id) NOT NULL,
due_date DATE,
estimated_hours NUMERIC(5,2),
actual_hours NUMERIC(5,2),
started_at TIMESTAMP,
completed_at TIMESTAMP,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
```

#### settings
```sql
id SERIAL PRIMARY KEY,
timezone VARCHAR(50) DEFAULT 'Europe/Rome' NOT NULL,
currency VARCHAR(3) DEFAULT 'EUR' NOT NULL,
rounding_minutes INTEGER DEFAULT 1 NOT NULL,
single_active_timer BOOLEAN DEFAULT true NOT NULL,
allow_self_register BOOLEAN DEFAULT true NOT NULL,
idle_timeout_minutes INTEGER DEFAULT 30 NOT NULL,
backup_retention_days INTEGER DEFAULT 30 NOT NULL,
backup_time VARCHAR(5) DEFAULT '02:00' NOT NULL,
export_delimiter VARCHAR(1) DEFAULT ',' NOT NULL,
allow_analytics BOOLEAN DEFAULT true NOT NULL,
-- Company branding fields...
company_name VARCHAR(200) DEFAULT 'Your Company Name' NOT NULL,
company_address TEXT DEFAULT 'Your Company Address' NOT NULL,
company_email VARCHAR(200) DEFAULT 'info@yourcompany.com' NOT NULL,
company_phone VARCHAR(50) DEFAULT '+1 (555) 123-4567' NOT NULL,
company_website VARCHAR(200) DEFAULT 'www.yourcompany.com' NOT NULL,
company_logo_filename VARCHAR(255) DEFAULT '' NOT NULL,
company_tax_id VARCHAR(100) DEFAULT '' NOT NULL,
company_bank_info TEXT DEFAULT '' NOT NULL,
-- Invoice defaults...
invoice_prefix VARCHAR(10) DEFAULT 'INV' NOT NULL,
invoice_start_number INTEGER DEFAULT 1000 NOT NULL,
invoice_terms TEXT DEFAULT 'Payment is due within 30 days of invoice date.' NOT NULL,
invoice_notes TEXT DEFAULT 'Thank you for your business!' NOT NULL,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
```

#### invoices
```sql
id SERIAL PRIMARY KEY,
invoice_number VARCHAR(50) UNIQUE NOT NULL,
project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
client_name VARCHAR(200) NOT NULL,
client_email VARCHAR(200),
client_address TEXT,
issue_date DATE NOT NULL,
due_date DATE NOT NULL,
status VARCHAR(20) DEFAULT 'draft' NOT NULL,
subtotal NUMERIC(10, 2) NOT NULL DEFAULT 0,
tax_rate NUMERIC(5, 2) NOT NULL DEFAULT 0,
tax_amount NUMERIC(10, 2) NOT NULL DEFAULT 0,
total_amount NUMERIC(10, 2) NOT NULL DEFAULT 0,
notes TEXT,
terms TEXT,
created_by INTEGER REFERENCES users(id) ON DELETE CASCADE,
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### invoice_items
```sql
id SERIAL PRIMARY KEY,
invoice_id INTEGER REFERENCES invoices(id) ON DELETE CASCADE,
description VARCHAR(500) NOT NULL,
quantity NUMERIC(10, 2) NOT NULL DEFAULT 1,
unit_price NUMERIC(10, 2) NOT NULL,
total_amount NUMERIC(10, 2) NOT NULL,
time_entry_ids VARCHAR(500),
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

## Performance Features

### Indexes
- User authentication: `username`, `role`
- Project queries: `client`, `status`
- Time tracking: `user_id`, `project_id`, `task_id`, `start_time`, `billable`
- Task management: `project_id`, `status`, `assigned_to`, `due_date`
- Invoice management: `project_id`, `status`, `issue_date`

### Triggers
- Automatic `updated_at` timestamp updates for all tables that have this column
- Ensures data consistency without application-level code

## Migration Support

The enhanced initialization script automatically handles:

- **New Tables**: Creates any missing tables
- **New Columns**: Adds missing columns to existing tables
- **Schema Updates**: Ensures existing databases are updated to current schema
- **Data Preservation**: Never drops existing data

## Verification

### Startup Verification
- Automatic verification after initialization
- Reports any issues found
- Ensures application only starts with correct database schema

### Manual Verification
```bash
# Run verification script independently
python docker/verify-database.py

# Check specific aspects
python docker/test-schema.py
```

## Error Handling

The enhanced startup procedure includes comprehensive error handling:

- **Database Connection**: Waits for database to be ready with retry logic
- **Schema Issues**: Reports specific problems and continues where possible
- **Non-critical Failures**: Continues operation even if some optional features fail
- **Detailed Logging**: Provides clear information about what succeeded and what failed

## Troubleshooting

### Common Issues

1. **Missing Tables**: Run `verify-database.py` to identify missing tables
2. **Schema Mismatches**: The enhanced script automatically adds missing columns
3. **Permission Issues**: Ensure database user has CREATE, ALTER, and INSERT privileges
4. **Connection Problems**: Check DATABASE_URL environment variable and network connectivity

### Debug Commands

```bash
# Check database schema
python docker/verify-database.py

# Test database connection
python docker/test-db.py

# View startup logs
docker logs <container_name>
```

## Benefits

1. **Reliability**: Ensures consistent database schema across all deployments
2. **Maintainability**: Single script handles all database setup
3. **Migration Safety**: Never loses existing data during updates
4. **Performance**: Proper indexes and triggers for optimal operation
5. **Debugging**: Comprehensive verification and error reporting

## Future Enhancements

- **Version Tracking**: Database schema version tracking for future migrations
- **Rollback Support**: Ability to rollback schema changes if needed
- **Performance Monitoring**: Database performance metrics collection
- **Automated Testing**: Integration with CI/CD pipeline for schema validation
