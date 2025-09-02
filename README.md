# TimeTracker - Professional Time Tracking Application

A comprehensive web-based time tracking application built with Flask, featuring project management, time tracking, invoicing, and analytics.

## 📸 Screenshots

### Core Application Views
<div align="center">
  <img src="assets/screenshots/Dashboard.png" alt="Dashboard" width="300" style="margin: 10px;">
  <img src="assets/screenshots/Projects.png" alt="Projects" width="300" style="margin: 10px;">
  <img src="assets/screenshots/Tasks.png" alt="Tasks" width="300" style="margin: 10px;">
  <img src="assets/screenshots/Clients.png" alt="Clients" width="300" style="margin: 10px;">
</div>

### Management & Analytics
<div align="center">
  <img src="assets/screenshots/Reports.png" alt="Reports" width="300" style="margin: 10px;">
  <img src="assets/screenshots/VisualAnalytics.png" alt="Visual Analytics" width="300" style="margin: 10px;">
  <img src="assets/screenshots/Task_Management.png" alt="Task Management" width="300" style="margin: 10px;">
  <img src="assets/screenshots/Admin.png" alt="Admin Panel" width="300" style="margin: 10px;">
</div>

### Data Entry & Creation
<div align="center">
  <img src="assets/screenshots/LogTime.png" alt="Log Time" width="300" style="margin: 10px;">
  <img src="assets/screenshots/New-Task.png" alt="New Task Creation" width="300" style="margin: 10px;">
  <img src="assets/screenshots/New-Client.png" alt="New Client Creation" width="300" style="margin: 10px;">
  <img src="assets/screenshots/New-Project.png" alt="New Project Creation" width="300" style="margin: 10px;">
</div>

## 🌐 Platform Support

**Web Application (Primary)**
- **Desktop**: Windows, macOS, Linux with modern web browsers
- **Mobile**: Responsive design optimized for Android and iOS devices
- **Tablets**: Full touch-friendly interface for iPad and Android tablets

**Access Methods**
- **Web Browser**: Chrome, Firefox, Safari, Edge (latest versions)
- **Mobile Web**: Progressive Web App (PWA) capabilities
- **API Access**: RESTful API for third-party integrations
- **CLI Tools**: Command-line interface for administration and automation

**Note**: This is a web-based application that runs in any modern browser. While not native mobile apps, the responsive design provides an excellent mobile experience across all devices.

## 📊 Reporting Features

### Comprehensive Analytics Dashboard
- **Real-time Statistics**: Live updates of current time tracking status
- **Time Period Analysis**: Daily, weekly, and monthly hour summaries
- **Project Performance**: Time breakdown by project with client information
- **User Productivity**: Individual and team performance metrics
- **Billable vs Non-billable**: Separate tracking for invoicing purposes

### Detailed Reports
- **Project Reports**: Time analysis by project with user breakdowns
- **User Reports**: Individual performance metrics and project allocation
- **Summary Reports**: Key performance indicators and trends
- **Custom Date Ranges**: Flexible reporting periods for analysis
- **Export Capabilities**: CSV export with customizable delimiters

### Visual Analytics
- **Progress Bars**: Visual representation of time allocation
- **Statistics Cards**: Key metrics displayed prominently
- **Trend Analysis**: Historical data visualization
- **Mobile-Optimized Charts**: Responsive charts for all screen sizes

## ⚡ Automatic Time Tracking

### Smart Timer Features
- **Idle Detection**: Automatic pause after configurable idle timeout (default: 30 minutes)
- **Single Active Timer**: Option to allow only one active timer per user
- **Auto-source Tracking**: Distinguishes between manual and automatic time entries
- **Real-time Updates**: WebSocket-powered live timer updates

### Timer Management
- **Start/Stop Controls**: Simple one-click timer management
- **Project Association**: Automatic project linking for time entries
- **Task Categorization**: Optional task-level time tracking
- **Notes and Tags**: Rich metadata for time entries
- **Duration Calculation**: Automatic time calculation and formatting

### Configuration Options
- **Idle Timeout**: Customizable idle detection (5-120 minutes)
- **Timer Behavior**: Single vs. multiple active timers
- **Rounding Rules**: Configurable time rounding (1-minute increments)
- **Timezone Support**: Full timezone awareness and conversion

## 🏢 Client Management System

### Comprehensive Client Management
- **Client Organization**: Create and manage client organizations with detailed information
- **Contact Management**: Store contact person, email, phone, and address details
- **Default Rate Setting**: Set standard hourly rates per client for automatic project population
- **Status Management**: Active/inactive client status with archiving capabilities
- **Project Relationships**: Clear view of all projects associated with each client

### Enhanced Project Creation
- **Client Selection**: Dropdown selection instead of manual typing to prevent errors
- **Automatic Rate Population**: Client default rates automatically fill project hourly rates
- **Error Prevention**: Eliminates typos and duplicate client names
- **Quick Setup**: Faster project creation with pre-filled client information

### Client Analytics
- **Project Statistics**: Total and active project counts per client
- **Time Tracking**: Total hours worked across all client projects
- **Cost Estimation**: Estimated total cost based on billable hours and rates
- **Performance Metrics**: Client-specific productivity and billing insights

## 📁 Data Standards & Import/Export

### Export Formats
- **CSV Export**: Standard comma-separated values with configurable delimiters
- **Data Fields**: Complete time entry information including:
  - User, Project, Client, Task details
  - Start/End times in ISO format
  - Duration in hours and formatted display
  - Notes, Tags, Source, Billable status
  - Creation and modification timestamps

### Data Structure
- **Standardized Fields**: Consistent data format across all exports
- **ISO 8601 Timestamps**: Standard datetime format for compatibility
- **Configurable Delimiters**: Support for different regional CSV standards
- **UTF-8 Encoding**: Full international character support

### Import Capabilities
- **Database Schema**: PostgreSQL and SQLite support
- **Migration System**: Flask-Migrate with version tracking and rollback support
- **Backup/Restore**: Database backup and restoration tools
- **CLI Management**: Command-line database operations with migration commands

### API Integration
- **RESTful Endpoints**: Standard HTTP API for external access
- **JSON Format**: Modern data exchange format
- **Authentication**: Secure API access with user authentication
- **Real-time Updates**: WebSocket support for live data synchronization

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Docker (optional)
- PostgreSQL (recommended) or SQLite

### Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (see `env.example`)
4. Run the application: `python app.py`

## 📁 Project Structure

The project has been organized for better maintainability:

```
TimeTracker/
├── app/                    # Main Flask application
│   ├── models/            # Database models
│   ├── routes/            # Route handlers
│   ├── static/            # Static assets (CSS, JS, images)
│   ├── templates/         # HTML templates
│   └── utils/             # Utility functions
├── docs/                  # Documentation and README files
├── docker/                # Docker-related scripts and utilities
│   ├── config/            # Configuration files (Caddyfile, supervisord)
│   ├── fixes/             # Database and permission fix scripts
│   ├── startup/           # Startup and initialization scripts
│   └── tests/             # Docker environment test scripts
├── migrations/            # Database migrations with Flask-Migrate
│   ├── versions/          # Migration version files
│   ├── env.py             # Migration environment configuration
│   ├── script.py.mako     # Migration template
│   └── README.md          # Migration documentation
├── scripts/                # Deployment and utility scripts
├── tests/                  # Application test suite
├── templates/              # Additional templates
├── assets/                 # Project assets and screenshots
├── logs/                   # Application logs
├── docker-compose.yml      # Local development setup
├── docker-compose.remote.yml      # Production deployment
├── docker-compose.remote-dev.yml  # Development deployment
└── Dockerfile              # Application container definition
```

## 🐳 Docker Support

Multiple Docker configurations are available for different deployment scenarios:

### Local Development
- **`docker-compose.yml`** - Standard local development setup with all features
  - Builds from local source code
  - Includes optional Caddy reverse proxy for TLS
  - Suitable for development and testing

### Remote Deployment
- **`docker-compose.remote.yml`** - Production deployment using GitHub Container Registry
  - Uses pre-built `ghcr.io/drytrix/timetracker:latest` image
  - Secure cookie settings enabled
  - Optimized for production environments

- **`docker-compose.remote-dev.yml`** - Development deployment using GitHub Container Registry
  - Uses pre-built `ghcr.io/drytrix/timetracker:development` image
  - Secure cookie settings enabled
  - Suitable for testing pre-release versions

### Database Migration System

The application now uses **Flask-Migrate** for standardized database migrations with:

- **Version Tracking**: Complete history of all database schema changes
- **Rollback Support**: Ability to revert to previous database versions
- **Automatic Schema Detection**: Migrations generated from SQLAlchemy models
- **Cross-Database Support**: Works with both PostgreSQL and SQLite
- **CLI Commands**: Simple commands for migration management

#### Migration Commands
```bash
# Initialize migrations (first time only)
flask db init

# Create a new migration
flask db migrate -m "Description of changes"

# Apply pending migrations
flask db upgrade

# Rollback last migration
flask db downgrade

# Check migration status
flask db current

# View migration history
flask db history
```

#### Quick Migration Setup
```bash
# Use the migration management script
python migrations/manage_migrations.py

# Or manually initialize
flask db init
flask db migrate -m "Initial schema"
flask db upgrade
```

#### **Comprehensive Migration for Any Existing Database:**
```bash
# For ANY existing database (recommended)
python migrations/migrate_existing_database.py

# For legacy schema migration
python migrations/legacy_schema_migration.py
```

#### **Migration Support:**
- ✅ **Fresh Installation**: No existing database
- ✅ **Legacy Databases**: Old custom migration systems
- ✅ **Mixed Schema**: Some tables exist, some missing
- ✅ **Production Data**: Existing databases with user data
- ✅ **Cross-Version**: Databases from different TimeTracker versions

#### **🚀 Automatic Container Migration:**
- ✅ **Zero Configuration**: Container automatically detects database state
- ✅ **Smart Strategy Selection**: Chooses best migration approach
- ✅ **Automatic Startup**: Handles migration during container startup
- ✅ **Production Ready**: Safe migration with automatic fallbacks

See [Migration Documentation](migrations/README.md), [Complete Migration Guide](migrations/MIGRATION_GUIDE.md), and [Container Startup Configuration](docker/STARTUP_MIGRATION_CONFIG.md) for comprehensive details.

### Enhanced Database Startup

The application now includes an enhanced database startup procedure that automatically:
- Creates all required tables with proper schema
- Handles migrations and schema updates
- Verifies database integrity before starting
- Provides comprehensive error reporting

See [Enhanced Database Startup Documentation](docs/ENHANCED_DATABASE_STARTUP.md) for detailed information.

### Docker Compose Usage

#### Quick Start with Local Development
```bash
# Clone the repository
git clone https://github.com/drytrix/TimeTracker.git
cd TimeTracker

# Copy environment file and configure
cp env.example .env
# Edit .env with your settings

# Start the application
docker-compose up -d

# Access the application at http://localhost:8080
```

#### Production Deployment with Remote Images
```bash
# Use production-ready images from GitHub Container Registry
docker-compose -f docker-compose.remote.yml up -d

# Or use development version for testing
docker-compose -f docker-compose.remote-dev.yml up -d
```

#### Development with TLS Support
```bash
# Start with Caddy reverse proxy for HTTPS
docker-compose --profile tls up -d

# Access via HTTPS at https://localhost
```

#### Environment Configuration
All docker-compose files support the following environment variables (set in `.env` file):

- **`TZ`** - Timezone (default: Europe/Brussels)
- **`CURRENCY`** - Currency symbol (default: EUR)
- **`ROUNDING_MINUTES`** - Time rounding in minutes (default: 1)
- **`SINGLE_ACTIVE_TIMER`** - Allow only one active timer per user (default: true)
- **`ALLOW_SELF_REGISTER`** - Allow user self-registration (default: true)
- **`IDLE_TIMEOUT_MINUTES`** - Auto-pause timer after idle time (default: 30)
- **`ADMIN_USERNAMES`** - Comma-separated list of admin usernames (default: admin)
- **`SECRET_KEY`** - Flask secret key (change this in production!)
- **`SESSION_COOKIE_SECURE`** - Secure session cookies (default: false for local, true for remote)
- **`REMEMBER_COOKIE_SECURE`** - Secure remember cookies (default: false for local, true for remote)

#### Database Configuration
- **`POSTGRES_DB`** - Database name (default: timetracker)
- **`POSTGRES_USER`** - Database user (default: timetracker)
- **`POSTGRES_PASSWORD`** - Database password (default: timetracker)

#### Useful Commands
```bash
# View logs
docker-compose logs -f app

# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes all data)
docker-compose down -v

# Rebuild and restart
docker-compose up -d --build

# Check service status
docker-compose ps

# Access database directly
docker-compose exec db psql -U timetracker -d timetracker
```

### Version Management

A comprehensive version management system provides flexible versioning:
- **GitHub Releases** - Automatic versioning when creating releases
- **Git Tags** - Manual version tagging for releases
- **Build Numbers** - Automatic versioning for branch builds
- **Local Tools** - Command-line version management scripts

See [Version Management Documentation](docs/VERSION_MANAGEMENT.md) for detailed information.

## 🔧 Features

- **Time Tracking**: Start/stop timer with project and task association
- **Project Management**: Create and manage projects with client information
- **Task Management**: Organize work into tasks and categories
- **Invoicing**: Generate professional invoices from time entries
- **Analytics**: Comprehensive reporting and time analysis
- **User Management**: Multi-user support with role-based access
- **Mobile Responsive**: Works on all devices
- **CLI Tools**: Command-line interface for administration
- **API Access**: RESTful API for integrations
- **Real-time Updates**: WebSocket-powered live updates

## 📚 Documentation

Detailed documentation is available in the `docs/` directory:

- **API Documentation**: API endpoints and usage
- **Feature Guides**: Detailed feature explanations
- **Troubleshooting**: Common issues and solutions
- **Deployment**: Setup and deployment instructions

## 🚀 Deployment

### Docker Deployment
```bash
# Local development
docker-compose up -d

# Production with remote images
docker-compose -f docker-compose.remote.yml up -d

# Development with remote images
docker-compose -f docker-compose.remote-dev.yml up -d
```

### Manual Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp env.example .env
# Edit .env with your configuration

# Run the application
python app.py
```

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

See `docs/CONTRIBUTING.md` for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the `docs/LICENSE` file for details.

## 🆘 Support

- **Issues**: Report bugs and feature requests on GitHub
- **Documentation**: Check the `docs/` directory
- **Troubleshooting**: See `docs/SOLUTION_GUIDE.md`

## 🔄 Recent Updates

- **Project Cleanup**: Reorganized project structure for better maintainability
- **Docker Organization**: Consolidated Docker configurations and scripts
- **Documentation**: Moved all documentation to dedicated `docs/` directory
- **Script Organization**: Grouped utility scripts by purpose

---

**Note**: This project has been cleaned up and reorganized. All files have been preserved and moved to appropriate directories for better organization and maintainability.
