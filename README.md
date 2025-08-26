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

### 🚀 Technical Features
- **Responsive Design**: Works on desktop, tablet, and mobile
- **HTMX Integration**: Dynamic interactions without JavaScript complexity
- **SQLite Database**: Lightweight, file-based storage
- **Docker Ready**: Easy deployment and scaling
- **RESTful API**: Programmatic access to time data

## 🖼️ Screenshots

> *Note: Screenshots will be added here once the application is running*

### Dashboard View
- Clean, intuitive interface showing active timers and recent activity
- Quick access to start/stop timers and manual time entry

### Project Management
- Client and project organization with billing information
- Time tracking across multiple projects simultaneously

### Reports & Analytics
- Comprehensive time reports with export capabilities
- Visual breakdowns of time allocation and productivity

## 🐳 Docker Images

### Public Docker Image

TimeTracker provides pre-built Docker images available on **GitHub Container Registry (GHCR)**:

```bash
# Pull the latest image
docker pull ghcr.io/yourusername/timetracker:latest

# Run with docker-compose
docker-compose -f docker-compose.public.yml up -d

# Or run directly
docker run -d \
  --name timetracker \
  -p 8080:8080 \
  -e SECRET_KEY=your-secret-key \
  -e ADMIN_USERNAMES=admin \
  ghcr.io/yourusername/timetracker:latest
```

**Available Tags:**
- `latest` - Latest stable build from main branch
- `v1.0.0` - Specific version releases
- `main-abc123` - Build from specific commit

**Supported Architectures:**
- `linux/amd64` - Intel/AMD 64-bit
- `linux/arm64` - ARM 64-bit (Apple Silicon, ARM servers)
- `linux/arm/v7` - ARM 32-bit (Raspberry Pi 3/4)

### Building Your Own Image

For custom modifications or development:

```bash
# Build locally
docker build -t timetracker .

# Run with docker-compose
docker-compose up -d
```

## 🚀 Quick Start

### Prerequisites

- **Raspberry Pi 4** (2GB+ RAM recommended) or any Linux system
- **Docker** and **Docker Compose** installed
- **Network access** to the host system

### Installation

#### Option 1: Using Public Docker Image (Recommended)

**Fastest deployment with pre-built images:**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/TimeTracker.git
   cd TimeTracker
   ```

2. **Run the deployment script:**
   ```bash
   # Linux/macOS
   ./deploy-public.sh
   
   # Windows
   deploy-public.bat
   ```

3. **Access the application:**
   ```
   http://your-pi-ip:8080
   ```

**Benefits:**
- ✅ No build time required
- ✅ Consistent builds across environments
- ✅ Automatic updates when you push to main
- ✅ Multi-architecture support (AMD64, ARM64, ARMv7)

#### Option 2: Build from Source

**For development or custom modifications:**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/TimeTracker.git
   cd TimeTracker
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your preferences
   ```

3. **Start the application:**
   ```bash
   docker-compose up -d
   ```

4. **Access the application:**
   ```
   http://your-pi-ip:8080
   ```

### Configuration

Key environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `TZ` | Timezone | `Europe/Brussels` |
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

## 🏗️ Architecture

### Technology Stack

- **Backend**: Flask with SQLAlchemy ORM
- **Database**: SQLite (with upgrade path to PostgreSQL)
- **Frontend**: Server-rendered templates with HTMX
- **Real-time**: WebSocket for live timer updates
- **Containerization**: Docker with docker-compose

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
├── docker-compose.yml     # Docker Compose configuration
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

### Data Model

#### Core Entities

- **Users**: Username-based authentication with role-based access
- **Projects**: Client projects with billing information
- **Time Entries**: Manual and automatic time tracking with notes and tags
- **Settings**: System configuration and preferences

#### Key Features

- **Timer Persistence**: Active timers survive server restarts
- **Billing Support**: Hourly rates, billable flags, and cost calculations
- **Export Capabilities**: CSV export for reports and data backup
- **Responsive Design**: Works on desktop and mobile devices

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
   cp .env.example .env
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

- **Automatic backups**: Nightly SQLite database backups
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

## 🙏 Acknowledgments

- **Flask Community**: For the excellent web framework
- **SQLAlchemy Team**: For robust database ORM
- **Docker Community**: For containerization tools
- **Contributors**: Everyone who has helped improve TimeTracker

---

**Made with ❤️ for the open source community**

*TimeTracker - Track your time, not your patience*
