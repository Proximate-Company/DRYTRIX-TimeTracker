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
 - **🎯 Focus Mode (Pomodoro)** - Start focus sessions with configurable cycles and view summaries
 - **📈 Estimates vs Actuals** - Project estimates, burn-down charts, and budget threshold alerts
 - **🔁 Recurring Time Blocks** - Create templates for common tasks and auto-generate entries
 - **🏷️ Tagging & Saved Filters** - Add tags to entries and reuse saved filters across views
 - **💰 Rate Overrides** - Billable rate overrides per project/member for precise invoicing

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

## 💬 Enhanced Comments System

### Project & Task Discussions
- **Contextual Comments**: Add comments directly to projects and tasks for better collaboration
- **Threaded Conversations**: Reply to comments with nested discussions and visual hierarchy
- **User Attribution**: Clear identification with user avatars and timestamps
- **Real-time Interactions**: Inline editing and replying without page reloads

### Comment Management
- **Inline Editing**: Click to edit comments directly in the interface
- **Permission System**: Users can edit/delete their own comments, admins manage all
- **Soft Delete**: Comments with replies are preserved to maintain conversation structure
- **Rich Formatting**: Support for line breaks and formatted text in comments

### User Experience
- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Dark Theme Support**: Seamless integration with the application's theme system
- **Loading States**: Visual feedback during comment operations
- **Accessibility**: Proper ARIA labels and semantic HTML structure

### Technical Features
- **Database Integration**: Comments stored with proper relationships and indexing
- **API Endpoints**: RESTful API for comment operations and retrieval
- **Internationalization**: Full support for multi-language applications
- **Migration Support**: Alembic migration for seamless database updates

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
│   ├── models/            # Database models (User, Project, Task, Comment, etc.)
│   ├── routes/            # Route handlers (auth, projects, tasks, comments, etc.)
│   ├── static/            # Static assets (CSS, JS, images)
│   ├── templates/         # HTML templates
│   │   ├── comments/      # Comment system templates
│   │   ├── projects/      # Project management templates
│   │   ├── tasks/         # Task management templates
│   │   └── ...            # Other feature templates
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

**Note**: The Enhanced Comments System includes migration `013_add_comments_table.py` which creates the comments table with proper relationships and indexes. This migration will be automatically applied when running `flask db upgrade`.

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

This project is licensed under the GNU General Public License v3.0 — see `LICENSE` for details.

## 🆘 Support

- **Issues**: Report bugs and feature requests on GitHub
- **Documentation**: Check the `docs/` directory
- **Troubleshooting**: See `docs/SOLUTION_GUIDE.md`

## 🔄 Recent Updates

- **Enhanced Comments System**: Added comprehensive commenting system for projects and tasks with threaded replies, inline editing, and real-time interactions
- **Project Cleanup**: Reorganized project structure for better maintainability
- **Docker Organization**: Consolidated Docker configurations and scripts
- **Documentation**: Moved all documentation to dedicated `docs/` directory
- **Script Organization**: Grouped utility scripts by purpose

---

**Note**: This project has been cleaned up and reorganized. All files have been preserved and moved to appropriate directories for better organization and maintainability.
