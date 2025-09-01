# Client Management System

## Overview

The TimeTracker application now includes a comprehensive client management system that allows administrators to:

- Create and manage client organizations
- Set default hourly rates per client
- Automatically populate project rates when creating projects
- Track client statistics and project relationships
- Maintain client contact information

## Features

### Client Management
- **Client Creation**: Create new clients with detailed information
- **Client Editing**: Update client details, rates, and contact information
- **Client Archiving**: Archive inactive clients while preserving data
- **Client Deletion**: Remove clients (only when no projects exist)

### Rate Management
- **Default Hourly Rates**: Set standard rates per client
- **Automatic Rate Population**: Rates automatically fill when creating projects
- **Project-Level Override**: Individual projects can still have custom rates

### Project Integration
- **Client Selection**: Dropdown selection instead of manual typing
- **Error Prevention**: Eliminates typos and duplicate client names
- **Relationship Tracking**: Clear view of all projects per client

## Database Schema

### Clients Table
```sql
CREATE TABLE clients (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    description TEXT,
    contact_person VARCHAR(200),
    email VARCHAR(200),
    phone VARCHAR(50),
    address TEXT,
    default_hourly_rate NUMERIC(9, 2),
    status VARCHAR(20) DEFAULT 'active',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);
```

### Updated Projects Table
```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    client_id INTEGER NOT NULL,
    description TEXT,
    billable BOOLEAN DEFAULT TRUE,
    hourly_rate NUMERIC(9, 2),
    billing_ref VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients (id)
);
```

## Migration

### From Old System
The old system stored client names as strings in the `projects.client` field. The migration script will:

1. Create the new `clients` table
2. Extract unique client names from existing projects
3. Create `Client` records for each unique client
4. Add `client_id` column to projects table
5. Update project records to reference client IDs
6. Remove the old `client` column

### Running Migration
```bash
cd migrations
python migrate_to_client_model.py
```

## Usage

### Creating a New Client
1. Navigate to **Clients** → **New Client**
2. Fill in client information:
   - **Client Name** (required)
   - **Default Hourly Rate** (optional)
   - **Description** (optional)
   - **Contact Person** (optional)
   - **Email** (optional)
   - **Phone** (optional)
   - **Address** (optional)
3. Click **Create Client**

### Creating a Project with Client
1. Navigate to **Projects** → **Create Project**
2. Select a client from the dropdown
3. The hourly rate will automatically populate if the client has a default rate
4. You can still modify the rate per project if needed

### Managing Clients
- **View Client**: See client details and associated projects
- **Edit Client**: Update client information and rates
- **Archive Client**: Mark client as inactive
- **Delete Client**: Remove client (only if no projects exist)

## API Endpoints

### Client Management
- `GET /clients` - List all clients
- `POST /clients/create` - Create new client
- `GET /clients/<id>` - View client details
- `POST /clients/<id>/edit` - Edit client
- `POST /clients/<id>/archive` - Archive client
- `POST /clients/<id>/activate` - Activate client
- `POST /clients/<id>/delete` - Delete client

### API for Dropdowns
- `GET /api/clients` - Get active clients for dropdowns (JSON)

## Benefits

### Error Prevention
- **No More Typos**: Dropdown selection eliminates manual typing errors
- **Consistent Naming**: Standardized client names across the system
- **Duplicate Prevention**: System prevents duplicate client entries

### Efficiency
- **Automatic Rate Population**: Saves time when creating projects
- **Quick Client Selection**: Faster project creation process
- **Centralized Management**: All client information in one place

### Better Organization
- **Client Overview**: See all projects and statistics per client
- **Contact Management**: Keep client contact information organized
- **Rate Tracking**: Monitor and adjust client rates easily

## Security

### Access Control
- **Admin Only**: Client creation, editing, and deletion restricted to administrators
- **View Access**: All authenticated users can view client information
- **Project Access**: Users can see client information through projects

### Data Integrity
- **Foreign Key Constraints**: Ensures data consistency
- **Cascade Protection**: Prevents client deletion when projects exist
- **Audit Trail**: Tracks creation and modification timestamps

## Future Enhancements

### Potential Features
- **Client Categories**: Group clients by industry or type
- **Rate History**: Track rate changes over time
- **Client Notes**: Add internal notes about clients
- **Bulk Operations**: Import/export client data
- **Client Dashboard**: Dedicated analytics per client

### Integration Opportunities
- **Invoice System**: Enhanced client billing
- **Reporting**: Client-specific time and cost reports
- **Communication**: Email integration for client updates

## Troubleshooting

### Common Issues

#### Migration Errors
- Ensure database backup before running migration
- Check database permissions
- Verify all required tables exist

#### Client Not Found
- Check if client is archived
- Verify client exists in database
- Ensure proper foreign key relationships

#### Rate Not Populating
- Verify client has default hourly rate set
- Check JavaScript console for errors
- Ensure client is active

### Support
For issues or questions about the client management system, please:
1. Check the application logs
2. Verify database schema
3. Test with a simple client creation
4. Contact system administrator

## Conclusion

The new client management system provides a robust foundation for managing client relationships and project billing. It eliminates common errors, improves efficiency, and provides better organization of client information. The system is designed to be scalable and can accommodate future enhancements as needed.
