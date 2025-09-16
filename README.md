# TimeTracker - Professional Time Tracking Application

A comprehensive web-based time tracking application built with Flask, featuring complete project lifecycle management from time tracking to invoicing. Perfect for freelancers, teams, and businesses who need professional time tracking with client billing capabilities.

## 🌟 Key Features Overview

- **⏱️ Smart Time Tracking** - Automatic timers with idle detection, manual entry, and real-time updates
- **👥 Client & Project Management** - Complete client database with project organization and billing rates
- **📋 Task Management** - Break down projects into manageable tasks with progress tracking
- **🧾 Professional Invoicing** - Generate branded PDF invoices with customizable layouts
- **📊 Analytics & Reporting** - Comprehensive reports with visual analytics and data export
- **🔐 Multi-User Support** - Role-based access control with admin and user roles
- **🐳 Docker Ready** - Multiple deployment options with automatic database migration
- **📱 Mobile Optimized** - Responsive design that works perfectly on all devices

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

## 🚀 Quick Start Guide

### 🐳 Docker Deployment (Recommended)

#### Option 1: Local Development with PostgreSQL
```bash
# Clone the repository
git clone https://github.com/drytrix/TimeTracker.git
cd TimeTracker

# Copy and configure environment
cp env.example .env
# Edit .env with your settings (optional - defaults work for testing)

# Start with Docker Compose
docker-compose up -d

# Access the application
open http://localhost:8080
```

#### Option 2: Quick Testing with SQLite
```bash
# Clone the repository
git clone https://github.com/drytrix/TimeTracker.git
cd TimeTracker

# Start with SQLite (no database setup needed)
docker-compose -f docker-compose.local-test.yml up --build

# Access the application
open http://localhost:8080
```

#### Option 3: Production Deployment with Pre-built Images
```bash
# Use production-ready images from GitHub Container Registry
docker-compose -f docker-compose.remote.yml up -d

# Or development version for testing
docker-compose -f docker-compose.remote-dev.yml up -d
```

### 💻 Manual Installation

#### Prerequisites
- **Python 3.8+** (3.9+ recommended)
- **PostgreSQL 12+** (recommended) or SQLite
- **Git** for cloning the repository

#### Step-by-Step Installation
```bash
# 1. Clone the repository
git clone https://github.com/drytrix/TimeTracker.git
cd TimeTracker

# 2. Create virtual environment (recommended)
python -m venv timetracker-env
source timetracker-env/bin/activate  # Linux/macOS
# or
timetracker-env\Scripts\activate     # Windows

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp env.example .env
# Edit .env with your database and application settings

# 5. Initialize the database
python -c "from app import create_app; app = create_app(); app.app_context().push(); app.initialize_database()"

# 6. Run the application
python app.py
```

#### Database Setup

**PostgreSQL (Recommended for production):**
```bash
# Install PostgreSQL and create database
sudo apt-get install postgresql postgresql-contrib  # Ubuntu/Debian
# or
brew install postgresql                              # macOS

# Create database and user
sudo -u postgres createdb timetracker
sudo -u postgres createuser --interactive timetracker

# Set connection in .env file
DATABASE_URL=postgresql+psycopg2://timetracker:password@localhost:5432/timetracker
```

**SQLite (Good for development):**
```bash
# SQLite requires no setup - just set in .env file
DATABASE_URL=sqlite:///timetracker.db
```

### 🎯 First Time Setup

#### 1. Access the Application
- Open your browser and navigate to `http://localhost:8080`
- You'll be redirected to the login page

#### 2. Create Admin User
- Enter username: `admin` (or any username you prefer)
- The first user is automatically granted admin privileges
- Admin usernames can be configured via `ADMIN_USERNAMES` environment variable

#### 3. Configure System Settings
1. Go to **Admin → System Settings**
2. Set your company information (name, address, logo)
3. Configure currency and timezone
4. Adjust timer behavior (idle timeout, single active timer)
5. Set default invoice terms and tax rates

#### 4. Create Your First Client
1. Navigate to **Clients → Create Client**
2. Enter client name and contact information
3. Set default hourly rate for automatic project setup

#### 5. Create Your First Project
1. Go to **Projects → Create Project**
2. Select the client from dropdown
3. Set project details and billing information
4. Mark as billable if you plan to invoice

#### 6. Start Tracking Time
1. Use the dashboard timer to start tracking
2. Select project (and task if available)
3. Timer continues running even if you close the browser
4. Stop timer when finished or let idle detection handle it

### 🔧 Environment Configuration Examples

#### Development Setup
```bash
# .env for development
SECRET_KEY=dev-secret-key
FLASK_ENV=development
FLASK_DEBUG=true
DATABASE_URL=sqlite:///timetracker.db
TZ=America/New_York
CURRENCY=USD
ALLOW_SELF_REGISTER=true
```

#### Production Setup
```bash
# .env for production
SECRET_KEY=your-very-secure-random-key-here
FLASK_ENV=production
FLASK_DEBUG=false
DATABASE_URL=postgresql+psycopg2://timetracker:secure-password@db:5432/timetracker
SESSION_COOKIE_SECURE=true
REMEMBER_COOKIE_SECURE=true
TZ=Europe/London
CURRENCY=GBP
ADMIN_USERNAMES=admin,manager
ALLOW_SELF_REGISTER=false
```

### 🆘 Troubleshooting Quick Start

#### Common Issues

**Port Already in Use:**
```bash
# Check what's using port 8080
lsof -i :8080

# Use different port
docker-compose up -d -e PORT=8081
```

**Database Connection Issues:**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Reset database (⚠️ destroys data)
docker-compose down -v
docker-compose up -d
```

**Permission Issues:**
```bash
# Fix Docker permissions (Linux)
sudo chown -R $USER:$USER .
```

**Migration Issues:**
```bash
# Force database recreation
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.drop_all(); app.initialize_database()"
```

#### Getting Help
- Check application logs: `docker-compose logs -f app`
- Review documentation in the `docs/` directory
- Open an issue on GitHub with error details
- Verify all prerequisites are installed and up to date

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

- **`docker-compose.local-test.yml`** - Quick local testing with SQLite
  - Uses SQLite database (no separate database container needed)
  - Development mode with debug logging enabled
  - Perfect for quick testing and development
  - See [Local Testing Documentation](docs/LOCAL_TESTING_WITH_SQLITE.md)

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

#### Quick Start with Local Testing (SQLite)
```bash
# Clone the repository
git clone https://github.com/drytrix/TimeTracker.git
cd TimeTracker

# Start with SQLite (no database setup needed)
docker-compose -f docker-compose.local-test.yml up --build

# Access the application at http://localhost:8080
# Or use the convenience script:
# Windows: scripts\start-local-test.bat
# Linux/macOS: ./scripts/start-local-test.sh
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

#### Useful Docker Commands

**Basic Operations:**
```bash
# View application logs
docker-compose logs -f app

# View database logs
docker-compose logs -f db

# View all services logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes all data)
docker-compose down -v

# Rebuild and restart
docker-compose up -d --build

# Check service status
docker-compose ps

# Restart specific service
docker-compose restart app
```

**Database Operations:**
```bash
# Access database directly
docker-compose exec db psql -U timetracker -d timetracker

# Create database backup
docker-compose exec db pg_dump -U timetracker timetracker > backup.sql

# Restore database backup
docker-compose exec -T db psql -U timetracker -d timetracker < backup.sql

# Check database connection
docker-compose exec app python -c "from app import db; print('Database connected:', db.engine.execute('SELECT 1').scalar())"
```

**Troubleshooting Commands:**
```bash
# Check container health
docker-compose exec app curl -f http://localhost:8080/_health

# View container resource usage
docker stats

# Execute shell in container
docker-compose exec app /bin/bash

# Check environment variables
docker-compose exec app env | grep -E "(DATABASE|SECRET|TZ)"

# Test database migration
docker-compose exec app python -c "from app import create_app; app = create_app(); app.app_context().push(); print('Migration test passed')"
```

### 🐳 Docker Troubleshooting Guide

#### Common Docker Issues

**1. Port Already in Use (Port 8080 Conflict)**
```bash
# Check what's using port 8080
lsof -i :8080          # macOS/Linux
netstat -ano | findstr :8080  # Windows

# Solution 1: Use different port
PORT=8081 docker-compose up -d

# Solution 2: Stop conflicting service
sudo kill -9 $(lsof -t -i:8080)  # macOS/Linux
```

**2. Database Connection Issues**
```bash
# Check database container status
docker-compose ps db

# Check database logs
docker-compose logs db

# Reset database (⚠️ destroys data)
docker-compose down -v
docker-compose up -d

# Manual database initialization
docker-compose exec app python -c "
from app import create_app, db
app = create_app()
app.app_context().push()
app.initialize_database()
print('Database initialized successfully')
"
```

**3. Permission Issues (Linux)**
```bash
# Fix file ownership
sudo chown -R $USER:$USER .

# Fix Docker socket permissions
sudo chmod 666 /var/run/docker.sock

# Fix data directory permissions
sudo chmod -R 755 ./data
```

**4. Container Won't Start**
```bash
# Check container logs
docker-compose logs app

# Check for syntax errors in docker-compose.yml
docker-compose config

# Rebuild without cache
docker-compose build --no-cache app
docker-compose up -d
```

**5. Database Migration Failures**
```bash
# Manual migration reset
docker-compose exec app python -c "
from app import create_app, db
from flask_migrate import stamp
app = create_app()
app.app_context().push()
db.drop_all()
db.create_all()
stamp()
print('Database reset complete')
"

# Check migration status
docker-compose exec app flask db current

# Force migration
docker-compose exec app flask db upgrade
```

**6. SSL/HTTPS Issues**
```bash
# For development with self-signed certificates
export PYTHONHTTPSVERIFY=0

# Check SSL certificate
openssl s_client -connect localhost:443 -servername localhost

# Disable SSL verification (development only)
curl -k https://localhost/
```

#### Docker Performance Optimization

**Resource Allocation:**
```yaml
# docker-compose.override.yml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
  
  db:
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: '0.25'
```

**Volume Optimization:**
```bash
# Use named volumes for better performance
docker volume create timetracker_data
docker volume create timetracker_db

# Check volume usage
docker system df -v
```

#### Production Docker Deployment

**Security Hardening:**
```bash
# Use non-root user in production
USER_ID=$(id -u) GROUP_ID=$(id -g) docker-compose -f docker-compose.remote.yml up -d

# Enable Docker secrets (Swarm mode)
echo "your-secret-key" | docker secret create timetracker_secret -

# Use environment file with restricted permissions
chmod 600 .env
```

**Monitoring Setup:**
```yaml
# docker-compose.monitoring.yml
services:
  app:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/_health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
  
  db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER -d $$POSTGRES_DB"]
      interval: 10s
      timeout: 5s
      retries: 5
```

**Backup Strategy:**
```bash
# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U timetracker timetracker | gzip > "backup_${DATE}.sql.gz"

# Automated cleanup (keep last 7 days)
find . -name "backup_*.sql.gz" -mtime +7 -delete
```

#### Multi-Environment Setup

**Development Environment:**
```bash
# docker-compose.dev.yml
cp docker-compose.yml docker-compose.dev.yml
# Edit for development settings

# Use development compose
docker-compose -f docker-compose.dev.yml up -d
```

**Staging Environment:**
```bash
# docker-compose.staging.yml
cp docker-compose.remote-dev.yml docker-compose.staging.yml
# Edit for staging settings

# Deploy to staging
docker-compose -f docker-compose.staging.yml up -d
```

**Production Environment:**
```bash
# Use production compose with secrets
docker-compose -f docker-compose.remote.yml up -d

# With external database
DATABASE_URL=postgresql://user:pass@external-db:5432/timetracker \
docker-compose -f docker-compose.remote.yml up -d
```

### Version Management

A comprehensive version management system provides flexible versioning:
- **GitHub Releases** - Automatic versioning when creating releases
- **Git Tags** - Manual version tagging for releases
- **Build Numbers** - Automatic versioning for branch builds
- **Local Tools** - Command-line version management scripts

See [Version Management Documentation](docs/VERSION_MANAGEMENT.md) for detailed information.

## 🔧 Comprehensive Feature Set

### ⏱️ Smart Time Tracking
- **Automatic Timers**: Server-side persistent timers that continue running even when browser is closed
- **Idle Detection**: Configurable idle timeout (5-120 minutes) with automatic pause
- **Single Active Timer**: Optional restriction to one active timer per user
- **Manual Time Entry**: Add time entries with start/end times, notes, and tags
- **Real-time Updates**: WebSocket-powered live timer updates across all browser sessions
- **Time Rounding**: Configurable time rounding (1-minute increments)
- **Source Tracking**: Distinguishes between manual and automatic time entries
- **Duration Calculation**: Automatic time calculation with multiple display formats

### 👥 Client & Project Management
- **Complete Client Database**: Store client organizations with detailed contact information
- **Contact Management**: Contact person, email, phone, and address details
- **Default Billing Rates**: Set standard hourly rates per client for automatic project setup
- **Project Organization**: Create projects linked to clients with descriptions and billing info
- **Status Management**: Active/inactive status for both clients and projects
- **Smart Dropdowns**: Error-preventing client selection with auto-populated rates
- **Project Analytics**: Time tracking and cost estimation per project
- **Billing References**: Track PO numbers and external billing references

### 📋 Advanced Task Management
- **Task Breakdown**: Break projects into manageable tasks with full lifecycle tracking
- **Status Workflow**: Todo → In Progress → Review → Done → Cancelled
- **Priority Levels**: Low, Medium, High, Urgent priority assignment
- **Time Estimation**: Estimate hours and track actual time vs. estimates
- **Task Assignment**: Assign tasks to specific team members
- **Due Date Tracking**: Set deadlines with overdue notifications
- **Task-level Time Tracking**: Start timers and log time directly to specific tasks
- **Automatic Migration**: Database tables created automatically on first run

### 🧾 Professional Invoicing System
- **Branded PDF Generation**: Create professional invoices with company branding
- **Visual PDF Editor**: HTML/CSS editor with live preview for custom invoice layouts
- **Automatic Numbering**: Unique invoice numbers with customizable format (INV-YYYYMMDD-XXX)
- **Time Integration**: Generate invoice items directly from tracked time entries
- **Smart Grouping**: Group time entries by task or project for organized billing
- **Tax Calculations**: Configurable tax rates with automatic calculations
- **Status Tracking**: Draft, Sent, Paid, Overdue, Cancelled status management
- **Payment Tracking**: Monitor outstanding amounts and overdue invoices
- **Duplicate Prevention**: Prevent double-billing of time entries
- **Export Options**: PDF and CSV export for external accounting systems

### 📊 Analytics & Comprehensive Reporting
- **Real-time Dashboard**: Live statistics with current tracking status
- **Time Period Analysis**: Daily, weekly, monthly, and custom date range reports
- **Project Performance**: Detailed breakdowns by project with client information
- **User Productivity**: Individual and team performance metrics
- **Billable vs Non-billable**: Separate tracking for accurate billing
- **Visual Analytics**: Progress bars, charts, and trend analysis
- **Mobile-Optimized Charts**: Responsive visualizations for all screen sizes
- **CSV Export**: Customizable data export with configurable delimiters
- **Summary Reports**: Key performance indicators and business insights

### 🔐 User Management & Security
- **Username-based Authentication**: Simple login system (no passwords required)
- **Role-based Access Control**: Admin and user roles with appropriate permissions
- **Self-registration**: Configurable user self-registration
- **Session Management**: Secure session handling with configurable timeouts
- **Admin Panel**: Comprehensive system administration interface
- **User Preferences**: Theme selection (light/dark/system) and language preferences
- **Activity Tracking**: Last login and user activity monitoring

### 🌐 Platform & Integration Support
- **Responsive Design**: Perfect experience on desktop, tablet, and mobile devices
- **Progressive Web App**: PWA capabilities for app-like mobile experience
- **RESTful API**: Complete API for third-party integrations
- **WebSocket Support**: Real-time updates and notifications
- **Multi-language Support**: Internationalization with Flask-Babel
- **Timezone Awareness**: Full timezone support with automatic conversion
- **Cross-browser Compatibility**: Works with Chrome, Firefox, Safari, Edge

### 🎨 PDF Layout Editor (Admin)
- **Visual Editor**: Customize invoice PDF layout with HTML and CSS
- **Live Preview**: Real-time preview of changes before saving
- **Local Assets**: GrapesJS served locally (no CDN dependency)
- **Template Support**: Full Flask-Babel internationalization support
- **Company Branding**: Integrates with system settings for logo and company info
- **Safe Defaults**: One-click default template loading

## ⚙️ Configuration & Settings

### 🔧 Environment Variables

#### Core Application Settings
```bash
# Flask Configuration
SECRET_KEY=your-secure-secret-key-here          # Required: Flask secret key
FLASK_ENV=production                            # Environment: development/production
FLASK_DEBUG=false                              # Debug mode: true/false

# Database Configuration
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname  # Database connection string
POSTGRES_DB=timetracker                        # PostgreSQL database name
POSTGRES_USER=timetracker                      # PostgreSQL username
POSTGRES_PASSWORD=timetracker                  # PostgreSQL password
POSTGRES_HOST=db                               # PostgreSQL host

# Session & Security
SESSION_COOKIE_SECURE=false                    # Secure cookies (true for HTTPS)
SESSION_COOKIE_HTTPONLY=true                   # HTTP-only cookies
PERMANENT_SESSION_LIFETIME=86400                # Session lifetime in seconds
REMEMBER_COOKIE_SECURE=false                   # Secure remember cookies
REMEMBER_COOKIE_DAYS=365                       # Remember cookie duration
```

#### Time Tracking Settings
```bash
# Time & Localization
TZ=Europe/Rome                                 # Timezone (default: Europe/Rome)
CURRENCY=EUR                                   # Currency symbol (EUR, USD, GBP, etc.)
ROUNDING_MINUTES=1                             # Time rounding in minutes (1-60)

# Timer Behavior
SINGLE_ACTIVE_TIMER=true                       # Allow only one active timer per user
IDLE_TIMEOUT_MINUTES=30                        # Auto-pause after idle time (5-120)
```

#### User Management
```bash
# Authentication & Access
ALLOW_SELF_REGISTER=true                       # Allow new user registration
ADMIN_USERNAMES=admin,manager                  # Comma-separated admin usernames
```

#### File & Upload Settings
```bash
# File Handling
MAX_CONTENT_LENGTH=16777216                    # Max upload size (16MB)
UPLOAD_FOLDER=/data/uploads                    # Upload directory path

# CSRF Protection
WTF_CSRF_ENABLED=false                         # Enable CSRF protection
WTF_CSRF_TIME_LIMIT=3600                       # CSRF token lifetime
```

#### Backup & Maintenance
```bash
# Backup Configuration
BACKUP_RETENTION_DAYS=30                       # Days to keep backups
BACKUP_TIME=02:00                             # Daily backup time (HH:MM)

# Logging
LOG_LEVEL=INFO                                # Log level (DEBUG, INFO, WARNING, ERROR)
LOG_FILE=/data/logs/timetracker.log          # Log file path
```

#### Optional Analytics & Metrics
```bash
# Metrics Server (Optional)
METRICS_SERVER_URL=https://your-metrics-server.com     # Metrics server URL
METRICS_SERVER_API_KEY=your-api-key                    # API key for metrics
METRICS_HEARTBEAT_SECONDS=300                           # Heartbeat interval
METRICS_SERVER_TIMEOUT_SECONDS=10                       # Request timeout
```

### 🏗️ System Settings (Admin Panel)

Access via **Admin → System Settings** in the web interface:

#### Company Information
- **Company Name**: Your organization name (appears on invoices)
- **Company Address**: Full address for invoicing
- **Company Logo**: Upload logo for branding (appears on invoices and interface)
- **Contact Information**: Phone, email, website

#### Application Behavior
- **Default Currency**: System-wide currency setting
- **Time Rounding**: How to round time entries (1, 5, 15, 30 minutes)
- **Idle Timeout**: Minutes before auto-pausing timers
- **Single Active Timer**: Enforce one timer per user
- **User Registration**: Allow new users to register

#### Invoice Settings
- **Default Tax Rate**: Standard tax rate for new invoices
- **Invoice Terms**: Default payment terms and conditions
- **Invoice Notes**: Standard notes that appear on all invoices
- **PDF Layout**: Custom HTML/CSS for invoice appearance

#### Privacy & Analytics
- **Analytics Enabled**: Enable/disable optional usage analytics
- **Data Retention**: How long to keep deleted data
- **Export Settings**: Default formats and delimiters for data export

### 📊 Database Configuration

#### Supported Databases
- **PostgreSQL** (Recommended for production)
  - Full feature support
  - Better performance for multiple users
  - Advanced indexing and querying
- **SQLite** (Good for development/small deployments)
  - Single file database
  - No separate database server required
  - Perfect for testing and small teams

#### Connection Examples
```bash
# PostgreSQL (Recommended)
DATABASE_URL=postgresql+psycopg2://timetracker:password@localhost:5432/timetracker

# SQLite (Development)
DATABASE_URL=sqlite:///timetracker.db

# PostgreSQL with SSL
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/db?sslmode=require
```

### 🔒 Security Configuration

#### Production Security Checklist
- [ ] Set a strong, unique `SECRET_KEY`
- [ ] Enable secure cookies (`SESSION_COOKIE_SECURE=true`) for HTTPS
- [ ] Use strong database passwords
- [ ] Enable CSRF protection (`WTF_CSRF_ENABLED=true`)
- [ ] Configure proper firewall rules
- [ ] Regular database backups
- [ ] Monitor application logs

#### SSL/TLS Configuration
```bash
# For HTTPS deployments
SESSION_COOKIE_SECURE=true
REMEMBER_COOKIE_SECURE=true
```

### 🌍 Internationalization

#### Supported Languages
- **English** (en) - Default
- **German** (de)
- **French** (fr) 
- **Italian** (it)
- **Dutch** (nl)
- **Finnish** (fi)

#### Adding New Languages
1. Create translation files: `pybabel extract` and `pybabel init`
2. Translate strings in `.po` files
3. Compile translations: `pybabel compile`
4. Add language to user preferences

## 🔌 API & Integration

### 🌐 RESTful API Endpoints

TimeTracker provides a comprehensive REST API for integration with external systems.

#### Authentication
All API endpoints require user authentication via session cookies or API tokens.

#### Timer Management
```bash
# Get current timer status
GET /api/timer/status

# Start a new timer
POST /api/timer/start
{
  "project_id": 1,
  "task_id": 2  # optional
}

# Stop active timer
POST /api/timer/stop

# Get timer duration while running
GET /api/timer/duration
```

#### Time Entries
```bash
# Get time entries with pagination
GET /api/entries?page=1&per_page=20&user_id=1&project_id=2

# Create manual time entry
POST /api/entries
{
  "project_id": 1,
  "task_id": 2,
  "start_time": "2024-01-15T09:00:00",
  "end_time": "2024-01-15T17:00:00",
  "notes": "Development work",
  "billable": true
}

# Update time entry
PUT /api/entries/{id}
{
  "notes": "Updated description",
  "billable": false
}

# Delete time entry
DELETE /api/entries/{id}
```

#### Projects and Clients
```bash
# Get all projects
GET /api/projects

# Get project details
GET /api/projects/{id}

# Get all clients
GET /api/clients

# Get client with projects
GET /api/clients/{id}
```

#### Reports and Analytics
```bash
# Get user summary
GET /api/reports/user/{user_id}?start_date=2024-01-01&end_date=2024-01-31

# Get project summary
GET /api/reports/project/{project_id}?start_date=2024-01-01&end_date=2024-01-31

# Export time entries as CSV
GET /api/export/csv?start_date=2024-01-01&end_date=2024-01-31&format=csv
```

### ⚡ WebSocket Events

Real-time updates via WebSocket connection at `/socket.io/`.

#### Timer Events
```javascript
// Listen for timer updates
socket.on('timer_started', function(data) {
  console.log('Timer started:', data.timer_id, data.project_name);
});

socket.on('timer_stopped', function(data) {
  console.log('Timer stopped:', data.timer_id, data.duration);
});

socket.on('timer_updated', function(data) {
  console.log('Timer duration:', data.current_duration);
});
```

#### User Activity Events
```javascript
// Listen for user activity
socket.on('user_activity', function(data) {
  console.log('User activity:', data.user_id, data.action);
});
```

### 🔗 Third-Party Integrations

#### Webhook Support
Configure webhooks in Admin → System Settings to receive notifications for:
- Timer start/stop events
- Time entry creation/updates
- Invoice status changes
- Project milestone completion

#### CSV/Excel Export
- Customizable CSV export with configurable delimiters
- Excel-compatible formatting
- Filtered exports by date range, user, or project
- Automated scheduled exports (coming soon)

#### External Calendar Integration
- iCal export for time entries
- Calendar import for planned work (coming soon)
- Google Calendar sync (planned feature)

### 📱 Mobile App Integration

#### Progressive Web App (PWA)
- Install as native app on mobile devices
- Offline capability for basic timer functions
- Push notifications for timer reminders
- Home screen shortcuts

#### Mobile API Considerations
- Optimized endpoints for mobile bandwidth
- Compressed JSON responses
- Efficient pagination for large datasets
- Battery-optimized WebSocket connections

### 🛠️ Developer Tools

#### Database Schema Access
```python
# Access models programmatically
from app.models import User, Project, TimeEntry, Client, Task, Invoice

# Query examples
active_timers = TimeEntry.query.filter_by(end_time=None).all()
billable_hours = TimeEntry.query.filter_by(billable=True).all()
```

#### Custom Extensions
```python
# Create custom Flask blueprints
from flask import Blueprint
from app import db

custom_bp = Blueprint('custom', __name__)

@custom_bp.route('/api/custom/endpoint')
def custom_endpoint():
    # Your custom logic here
    return jsonify({'status': 'success'})
```

#### CLI Commands
```bash
# Custom management commands
flask db upgrade                    # Run database migrations
flask user create admin            # Create admin user
flask export-data --format=json    # Export all data
flask import-data data.json         # Import data
```

### 🔐 API Security

#### Rate Limiting
- 100 requests per minute per user
- 1000 requests per hour per IP
- Configurable limits in system settings

#### CORS Configuration
```python
# Configure CORS for external access
CORS_ORIGINS = ['https://yourdomain.com', 'https://app.yourdomain.com']
CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE']
CORS_HEADERS = ['Content-Type', 'Authorization']
```

#### API Token Authentication
```bash
# Generate API token (Admin only)
POST /admin/api/tokens
{
  "name": "Integration Token",
  "permissions": ["read", "write"]
}

# Use token in requests
curl -H "Authorization: Bearer your-api-token" \
     -H "Content-Type: application/json" \
     https://your-timetracker.com/api/entries
```

## 👥 User Management & Authentication

### 🔐 Authentication System

TimeTracker uses a simplified username-based authentication system designed for team environments where security is managed at the network/infrastructure level.

#### How Authentication Works
- **No Passwords Required**: Users log in with just a username
- **Automatic User Creation**: New usernames create user accounts automatically (if enabled)
- **Session-based**: Secure session cookies maintain login state
- **Remember Me**: Optional persistent login across browser sessions

#### First User Setup
1. **Admin Bootstrap**: The first user to log in automatically becomes an admin
2. **Configurable Admins**: Set admin usernames via `ADMIN_USERNAMES` environment variable
3. **Admin Override**: Existing admins can promote/demote other users

### 👤 User Roles & Permissions

#### User Role (Default)
**Time Tracking:**
- Start/stop personal timers
- Create and edit own time entries
- View own time tracking history
- Export personal time data

**Project Access:**
- View assigned projects and tasks
- Track time on accessible projects
- View project details and time summaries

**Personal Settings:**
- Update profile information (name, preferences)
- Set theme preference (light/dark/system)
- Choose interface language
- Configure personal notification settings

#### Admin Role
**All User Permissions Plus:**

**User Management:**
- View all users and their activity
- Promote/demote user roles
- Deactivate/reactivate user accounts
- View user login history and statistics

**System Administration:**
- Access admin panel and system settings
- Configure application-wide settings
- Manage company information and branding
- Set system defaults (currency, timezone, etc.)

**Data Management:**
- View all time entries across all users
- Edit or delete any time entry
- Access comprehensive reports and analytics
- Export system-wide data

**Project & Client Management:**
- Create, edit, and archive projects
- Manage client information and billing rates
- Set project permissions and access
- Configure billing and invoice settings

**Invoice Management:**
- Create and manage all invoices
- Access invoice analytics and reports
- Configure invoice templates and branding
- Export invoice data for accounting

### ⚙️ User Configuration

#### Self-Registration Settings
```bash
# Environment variable
ALLOW_SELF_REGISTER=true    # Allow new users to register
ALLOW_SELF_REGISTER=false   # Require admin to create users
```

**When Enabled (`true`):**
- Any username can create a new account
- Suitable for open team environments
- New users get 'user' role by default

**When Disabled (`false`):**
- Only existing users can log in
- Admins must pre-create user accounts
- Better for controlled access environments

#### Admin User Configuration
```bash
# Set admin usernames (comma-separated)
ADMIN_USERNAMES=admin,manager,supervisor

# Multiple admins example
ADMIN_USERNAMES=john.doe,jane.smith,admin
```

### 🛠️ User Management Interface

#### Admin User Management (`/admin/users`)
- **User List**: View all users with status and last login
- **User Details**: Click any user to view detailed information
- **Role Management**: Change user roles with one click
- **Activity Monitoring**: View user activity and time tracking statistics
- **Bulk Operations**: Activate/deactivate multiple users

#### User Profile Management
**Personal Profile (`/profile`):**
- Update full name and display preferences
- Set theme (light/dark/system auto)
- Choose interface language
- View personal statistics and achievements

**Admin User Editing (`/admin/users/{id}`):**
- Edit any user's profile information
- Change user roles and permissions
- View detailed activity logs
- Reset user sessions and preferences

### 🔒 Security Features

#### Session Management
```bash
# Session configuration
PERMANENT_SESSION_LIFETIME=86400        # 24 hours (in seconds)
SESSION_COOKIE_SECURE=true             # Require HTTPS (production)
SESSION_COOKIE_HTTPONLY=true           # Prevent XSS access
REMEMBER_COOKIE_DAYS=365               # Remember me duration
```

#### Security Best Practices
- **Network Security**: Designed for internal networks or VPN access
- **Session Timeouts**: Configurable session expiration
- **Secure Cookies**: HTTPS-only cookies in production
- **Activity Logging**: Track user login and activity patterns
- **IP Restrictions**: Configure firewall rules for additional security

#### Data Privacy
- **User Data Isolation**: Users can only see their own data (unless admin)
- **Admin Audit Trail**: All admin actions are logged
- **Data Export**: Users can export their own data
- **Account Deactivation**: Preserve data when deactivating users

### 📊 User Analytics & Monitoring

#### Admin Dashboard User Metrics
- **Active Users**: Currently logged in users
- **User Activity**: Login frequency and time tracking patterns
- **Productivity Stats**: Hours tracked per user over time periods
- **Project Participation**: Which users work on which projects

#### Individual User Statistics
- **Personal Dashboard**: Total hours, project breakdown, recent activity
- **Time Trends**: Daily, weekly, monthly time tracking patterns
- **Project Contributions**: Time spent per project and client
- **Efficiency Metrics**: Billable vs non-billable time ratios

### 🔧 User Management API

#### Admin User Management Endpoints
```bash
# Get all users (admin only)
GET /api/admin/users

# Get user details
GET /api/admin/users/{id}

# Update user role
PUT /api/admin/users/{id}/role
{
  "role": "admin"  # or "user"
}

# Deactivate user
PUT /api/admin/users/{id}/status
{
  "active": false
}

# Get user activity log
GET /api/admin/users/{id}/activity
```

#### User Profile Endpoints
```bash
# Get current user profile
GET /api/profile

# Update profile
PUT /api/profile
{
  "full_name": "John Doe",
  "theme_preference": "dark",
  "preferred_language": "en"
}

# Get user statistics
GET /api/profile/stats
```

### 🚨 Troubleshooting User Management

#### Common User Issues

**Cannot Log In:**
1. Check if self-registration is enabled
2. Verify username spelling (case-sensitive)
3. Check if user account is active
4. Review session cookie settings

**Missing Admin Access:**
1. Verify username is in `ADMIN_USERNAMES` environment variable
2. Restart application after changing admin settings
3. Check if user role was manually changed

**Session Expires Too Quickly:**
```bash
# Increase session lifetime
PERMANENT_SESSION_LIFETIME=172800  # 48 hours
```

**Users Can't Register:**
```bash
# Enable self-registration
ALLOW_SELF_REGISTER=true
```

#### Admin Troubleshooting Tools
- **User Activity Logs**: View detailed user action history
- **Session Management**: Force logout specific users
- **Database Direct Access**: Query user table for debugging
- **Application Logs**: Review authentication-related log entries

## 📚 Documentation

Detailed documentation is available in the `docs/` directory:

- **API Documentation**: API endpoints and usage
- **Feature Guides**: Detailed feature explanations
- **Troubleshooting**: Common issues and solutions
- **Deployment**: Setup and deployment instructions

### Metrics Server and Privacy

This application can optionally communicate with a metrics server to help improve reliability and features. No license is required and the app works without it.

- What is sent:
  - App identifier and version
  - Anonymous instance ID (UUID)
  - Basic system info: OS, version, architecture, hostname, local IP, Python version
  - Aggregate usage events (e.g., feature used). No time entry data or personal content
- Controls:
  - Toggle analytics in Admin → System Settings → Privacy & Analytics
  - View status in Admin → Metrics Status
- Configuration (env vars are optional and have sensible defaults):
  - `METRICS_SERVER_URL` (or legacy `LICENSE_SERVER_BASE_URL`)
  - `METRICS_SERVER_API_KEY` (or legacy `LICENSE_SERVER_API_KEY`)
  - `METRICS_HEARTBEAT_SECONDS` (or legacy `LICENSE_HEARTBEAT_SECONDS`)
  - `METRICS_SERVER_TIMEOUT_SECONDS` (or legacy `LICENSE_SERVER_TIMEOUT_SECONDS`)

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

This project is licensed under the GNU General Public License v3.0 — see `LICENSE` for details.

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
