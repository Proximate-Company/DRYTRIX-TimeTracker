# TimeTracker ⏱️

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)
[![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi-red.svg)](https://www.raspberrypi.org/)

A robust, self-hosted time tracking application designed for teams and freelancers who need reliable time management without cloud dependencies. Built with Flask and optimized for Raspberry Pi deployment, TimeTracker provides persistent timers, comprehensive reporting, and a modern web interface.

## 🎯 What Problem Does It Solve?

**TimeTracker addresses the common pain points of time tracking:**

- **Lost Time Data**: Traditional timers lose data when browsers close or computers restart
- **Cloud Dependency**: No need for external services or internet connectivity
- **Complex Setup**: Simple Docker deployment on Raspberry Pi or any Linux system
- **Limited Reporting**: Built-in comprehensive reports and CSV exports
- **Team Management**: User roles, project organization, and billing support

**Perfect for:**
- Freelancers tracking billable hours
- Small teams managing project time
- Consultants needing client billing reports
- Anyone wanting self-hosted time tracking

## ✨ Features

### 🕐 Time Tracking
- **Persistent Timers**: Server-side timers that survive browser restarts
- **Manual Entry**: Log time with start/end dates and project selection
- **Idle Detection**: Automatic timeout for inactive sessions
- **Multiple Projects**: Track time across different clients and projects
- **Timezone Support**: Full timezone awareness with configurable local time display

### 👥 User Management
- **Role-Based Access**: Admin and regular user roles
- **Simple Authentication**: Username-based login (no passwords required)
- **User Profiles**: Personal settings and time preferences
- **Self-Registration**: Optional user account creation

### 📊 Reporting & Analytics
- **Project Reports**: Time breakdown by project and client
- **User Reports**: Individual time tracking and productivity
- **CSV Export**: Data backup and external analysis
- **Real-time Updates**: Live timer status and progress

### 🏗️ Project Management
- **Client Projects**: Organize work by client and project
- **Billing Support**: Hourly rates and billable time tracking
- **Project Status**: Active, completed, and archived projects
- **Time Rounding**: Configurable time rounding for billing

### ✅ Task Management
- **Project Breakdown**: Break projects into manageable tasks
- **Status Tracking**: Monitor task progress (To Do, In Progress, Review, Done)
- **Priority Management**: Set and track task priorities (Low, Medium, High, Urgent)
- **Time Estimation**: Estimate and track actual time for tasks
- **Task Assignment**: Assign tasks to team members
- **Due Date Tracking**: Set deadlines with overdue notifications
- **Automatic Migration**: Database tables are automatically created on first startup

### 🚀 Technical Features
- **Responsive Design**: Works on desktop, tablet, and mobile
- **HTMX Integration**: Dynamic interactions without JavaScript complexity
- **PostgreSQL Database**: Robust database with automatic initialization
- **Docker Ready**: Easy deployment and scaling
- **RESTful API**: Programmatic access to time data
- **Timezone Management**: Comprehensive timezone support with 100+ options

## 🖼️ Screenshots

### Dashboard View
![Dashboard](assets/screenshots/Dashboard.png)
- Clean, intuitive interface showing active timers and recent activity
- Quick access to start/stop timers and manual time entry
- Real-time timer status and project selection

### Project Management
![Projects](assets/screenshots/Projects.png)
- Client and project organization with billing information
- Time tracking across multiple projects simultaneously
- Project status management and billing configuration

### Reports & Analytics
![Reports](assets/screenshots/Reports.png)
- Comprehensive time reports with export capabilities
- Visual breakdowns of time allocation and productivity
- Detailed time tracking data and export options

## 🐳 Docker Images

### GitHub Container Registry (GHCR)

TimeTracker provides pre-built Docker images available on **GitHub Container Registry (GHCR)**:

[![Docker Image](https://img.shields.io/badge/Docker%20Image-ghcr.io/drytrix/timetracker-blue.svg)](https://github.com/DRYTRIX/TimeTracker/pkgs/container/timetracker)

**Pull the latest image:**
```bash
docker pull ghcr.io/drytrix/timetracker:latest
```

**Available Tags:**
- `latest` - Latest stable build from main branch
- `main` - Latest build from main branch
- `v1.0.2` - Specific version releases
- `main-abc123` - Build from specific commit

**Supported Architectures:**
- `linux/amd64` - Intel/AMD 64-bit

### Container Types

#### 1. Simple Container (Recommended for Production)

The **simple container** is an all-in-one solution that includes both the TimeTracker application and PostgreSQL database in a single container. This is perfect for production deployments where you want simplicity and don't need separate database management.

**Features:**
- ✅ **All-in-one**: Flask app + PostgreSQL in single container
- ✅ **Auto-initialization**: Database automatically created and configured
- ✅ **Automatic migration**: Task Management tables created automatically
- ✅ **Persistent storage**: Data survives container restarts
- ✅ **Production ready**: Optimized for deployment
- ✅ **Timezone support**: Full timezone management with 100+ options

**Run with docker-compose:**
```bash
# Clone the repository
git clone https://github.com/DRYTRIX/TimeTracker.git
cd TimeTracker

# Start the simple container
docker-compose -f docker-compose.simple.yml up -d
```

**Run directly:**
```bash
docker run -d \
  --name timetracker \
  -p 8080:8080 \
  -v timetracker_data:/var/lib/postgresql/data \
  -v timetracker_logs:/app/logs \
  -e FORCE_REINIT=false \
  ghcr.io/drytrix/timetracker:latest
```

**Environment Variables:**
- `FORCE_REINIT`: Set to `true` to reinitialize database schema (default: `false`)
- `TZ`: Timezone (default: `Europe/Rome`)

**Note:** Task Management tables are automatically created on first startup if they don't exist.

#### 2. Public Container (Development/Testing)

The **public container** is designed for development and testing scenarios where you want to use external databases or have more control over the setup.

**Features:**
- 🔧 **Development focused**: External database configuration
- 🔧 **Flexible setup**: Use your own PostgreSQL/MySQL
- 🔧 **Custom configuration**: Full control over database settings

**Run with docker-compose:**
```bash
# Use the public docker-compose file
docker-compose -f docker-compose.public.yml up -d
```

**Run directly:**
```bash
docker run -d \
  --name timetracker \
  -p 8080:8080 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e SECRET_KEY=your-secret-key \
  ghcr.io/drytrix/timetracker:latest
```

### Building Your Own Image

For custom modifications or development:

```bash
# Build locally (simple container with PostgreSQL)
docker build -f Dockerfile.simple -t timetracker:local .

# Run with docker-compose
docker-compose -f docker-compose.simple.yml up -d
```

## 🚀 Quick Start

### Prerequisites

- **Docker** and **Docker Compose** installed
- **Network access** to the host system
- **Git** for cloning the repository

### Installation Options

#### Option 1: Simple Container (Recommended for Production)

**All-in-one solution with built-in PostgreSQL database:**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DRYTRIX/TimeTracker.git
   cd TimeTracker
   ```

2. **Start the application:**
   ```bash
   docker-compose -f docker-compose.simple.yml up -d
   ```

3. **Access the application:**
   ```
   http://localhost:8080
   ```

**Benefits:**
- ✅ **No external database required** - PostgreSQL included
- ✅ **Automatic initialization** - Database created automatically
- ✅ **Production ready** - Optimized for deployment
- ✅ **Persistent storage** - Data survives restarts
- ✅ **Simple setup** - One command deployment
- ✅ **Timezone support** - 100+ timezone options with automatic DST handling

**Default credentials:**
- **Username**: `admin`
- **Password**: None required (username-based authentication)

**Database Initialization:**
The container automatically:
1. Creates a PostgreSQL database named `timetracker`
2. Creates a user `timetracker` with full permissions
3. Initializes all tables with proper schema
4. Inserts default admin user and project
5. Sets up triggers for automatic timestamp updates

**Note:** Set `FORCE_REINIT=true` environment variable to reinitialize the database schema if you need to update the structure.

#### Option 2: Public Container (Development/Testing)

**For development or when you want external database control:**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/DRYTRIX/TimeTracker.git
   cd TimeTracker
   ```

2. **Configure environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your database settings
   ```

3. **Start the application:**
   ```bash
   docker-compose -f docker-compose.public.yml up -d
   ```

4. **Access the application:**
   ```
   http://localhost:8080
   ```

**Benefits:**
- 🔧 **Flexible database** - Use your own PostgreSQL/MySQL
- 🔧 **Development focused** - Full control over configuration
- 🔧 **Custom setup** - Configure as needed for your environment

#### Option 3: Using Pre-built Image

**Fastest deployment with GitHub Container Registry:**

1. **Pull the image:**
   ```bash
   docker pull ghcr.io/drytrix/timetracker:latest
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name timetracker \
     -p 8080:8080 \
     -v timetracker_data:/var/lib/postgresql/data \
     -v timetracker_logs:/app/logs \
     ghcr.io/drytrix/timetracker:latest
   ```

3. **Access the application:**
   ```
   http://localhost:8080
   ```

### Configuration

#### Simple Container Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FORCE_REINIT` | Reinitialize database schema | `false` |
| `TZ` | Timezone | `Europe/Rome` |

#### Public Container Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | - |
| `SECRET_KEY` | Flask secret key | - |
| `TZ` | Timezone | `Europe/Rome` |
| `CURRENCY` | Currency for billing | `EUR` |
| `ROUNDING_MINUTES` | Time rounding in minutes | `1` |
| `SINGLE_ACTIVE_TIMER` | Allow only one active timer per user | `true` |
| `ALLOW_SELF_REGISTER` | Allow users to create accounts | `true` |
| `ADMIN_USERNAMES` | Comma-separated list of admin usernames | - |

## 📖 Example Usage

### Starting a Timer

1. **Navigate to the dashboard**
2. **Select a project** from the dropdown
3. **Click "Start Timer"** to begin tracking
4. **Add notes** to describe what you're working on
5. **Timer runs continuously** even if you close the browser

### Manual Time Entry

1. **Go to "Manual Entry"** in the main menu
2. **Select project** and **date range**
3. **Enter start and end times**
4. **Add description** and **tags**
5. **Save** to log the time entry

### Generating Reports

1. **Access "Reports"** section
2. **Choose report type**: Project, User, or Summary
3. **Select date range** and **filters**
4. **View results** or **export to CSV**

### Managing Projects

1. **Admin users** can create new projects
2. **Set client information** and **billing rates**
3. **Assign users** to projects
4. **Track project status** and **completion**

### Timezone Configuration

1. **Access Admin Settings** (admin users only)
2. **Select your timezone** from 100+ available options
3. **View real-time preview** of current time in selected timezone
4. **Save settings** to apply timezone changes application-wide

## 🏗️ Architecture

### Technology Stack

- **Backend**: Flask with SQLAlchemy ORM
- **Database**: PostgreSQL with automatic initialization
- **Frontend**: Server-rendered templates with HTMX
- **Real-time**: WebSocket for live timer updates
- **Containerization**: Docker with docker-compose
- **Timezone**: Full timezone support with pytz

### Project Structure

```
TimeTracker/
├── app/                    # Flask application
│   ├── models/            # Database models
│   ├── routes/            # Route handlers
│   ├── templates/         # Jinja2 templates
│   ├── utils/             # Utility functions
│   └── config.py          # Configuration settings
├── docker/                # Docker configuration
├── tests/                 # Test suite
├── docker-compose.simple.yml     # Simple container setup
├── docker-compose.public.yml     # Public container setup
├── Dockerfile.simple      # Simple container Dockerfile
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

### Data Model

#### Core Entities

- **Users**: Username-based authentication with role-based access
- **Projects**: Client projects with billing information and client management
- **Time Entries**: Manual and automatic time tracking with notes, tags, and billing support
- **Settings**: System configuration including timezone preferences

#### Database Schema

The simple container automatically creates and initializes a PostgreSQL database with the following structure:

**Users Table:**
- `id`, `username`, `role`, `created_at`, `last_login`, `is_active`, `updated_at`

**Projects Table:**
- `id`, `name`, `client`, `description`, `billable`, `hourly_rate`, `billing_ref`, `status`, `created_at`, `updated_at`

**Time Entries Table:**
- `id`, `user_id`, `project_id`, `start_utc`, `end_utc`, `duration_seconds`, `notes`, `tags`, `source`, `billable`, `created_at`, `updated_at`

**Settings Table:**
- `id`, `timezone`, `currency`, `rounding_minutes`, `single_active_timer`, `allow_self_register`, `idle_timeout_minutes`, `backup_retention_days`, `backup_time`, `export_delimiter`, `created_at`, `updated_at`

#### Key Features

- **Timer Persistence**: Active timers survive server restarts
- **Billing Support**: Hourly rates, billable flags, and cost calculations
- **Export Capabilities**: CSV export for reports and data backup
- **Responsive Design**: Works on desktop and mobile devices
- **Timezone Support**: Full timezone awareness with automatic DST handling

## 🛠️ Development

### Local Development Setup

1. **Install Python 3.11+:**
   ```bash
   python --version  # Should be 3.11 or higher
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment:**
   ```bash
   cp env.example .env
   # Edit .env with development settings
   ```

4. **Initialize database:**
   ```bash
   flask db upgrade
   ```

5. **Run development server:**
   ```bash
   flask run
   ```

### Testing

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app

# Run specific test file
python -m pytest tests/test_timer.py
```

### Code Quality

- **Style**: PEP 8 compliance with Black formatter
- **Type Hints**: Python type annotations where appropriate
- **Documentation**: Docstrings for all public functions
- **Testing**: Comprehensive test coverage

## 🔒 Security Considerations

- **LAN-only deployment**: Designed for internal network use
- **Username-only auth**: Simple authentication suitable for trusted environments
- **CSRF protection**: Disabled for simplified development and API usage
- **Session management**: Secure cookie-based sessions

## 💾 Backup and Maintenance

- **Automatic backups**: Nightly PostgreSQL database backups
- **Manual exports**: On-demand CSV exports and full data dumps
- **Health monitoring**: Built-in health check endpoints
- **Database migrations**: Version-controlled schema changes

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- How to submit bug reports and feature requests
- Development setup and coding standards
- Pull request process and guidelines
- Code of conduct and community guidelines

### Quick Contribution Steps

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes
4. **Test** thoroughly
5. **Submit** a pull request

## 📄 License

This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](LICENSE) file for details.

The GPL v3 license ensures that:
- ✅ **Derivatives remain open source**
- ✅ **Source code is always available**
- ✅ **Users have freedom to modify and distribute**
- ✅ **Commercial use is permitted**

## 🆘 Support

### Getting Help

- **Documentation**: Check this README and code comments
- **Issues**: Report bugs and request features on GitHub
- **Discussions**: Ask questions and share ideas
- **Wiki**: Community-maintained documentation (coming soon)

### Common Issues

- **Timer not starting**: Check if another timer is already active
- **Database errors**: Ensure proper permissions and disk space
- **Docker issues**: Verify Docker and Docker Compose installation
- **Network access**: Check firewall settings and port configuration
- **Timezone issues**: Verify timezone settings in admin panel

## 🚀 Roadmap

### Planned Features

- [ ] **Mobile App**: Native iOS and Android applications
- [ ] **API Enhancements**: RESTful API for third-party integrations
- [ ] **Advanced Reporting**: Charts, graphs, and analytics dashboard
- [ ] **Team Collaboration**: Shared projects and time approval workflows
- [ ] **Integration**: Zapier, Slack, and other platform connections
- [ ] **Multi-language**: Internationalization support

### Recent Updates

- **v1.0.0**: Initial release with core time tracking features
- **v1.1.0**: Added comprehensive reporting and export capabilities
- **v1.2.0**: Enhanced project management and billing support
- **v1.3.0**: Added comprehensive timezone support with 100+ options

## 🙏 Acknowledgments

- **Flask Community**: For the excellent web framework
- **SQLAlchemy Team**: For robust database ORM
- **Docker Community**: For containerization tools
- **Contributors**: Everyone who has helped improve TimeTracker

---

**Made with ❤️ for the open source community**

*TimeTracker - Track your time, not your patience*
