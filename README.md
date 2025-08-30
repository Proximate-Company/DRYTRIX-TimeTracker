# TimeTracker - Professional Time Tracking Application

A comprehensive web-based time tracking application built with Flask, featuring project management, time tracking, invoicing, and analytics.

## 📸 Screenshots

<div align="center">
  <img src="assets/screenshots/Dashboard.png" alt="Dashboard" width="300" style="margin: 10px;">
  <img src="assets/screenshots/Projects.png" alt="Projects" width="300" style="margin: 10px;">
  <img src="assets/screenshots/Tasks.png" alt="Tasks" width="300" style="margin: 10px;">
  <img src="assets/screenshots/Reports.png" alt="Reports" width="300" style="margin: 10px;">
  <img src="assets/screenshots/Task_Management.png" alt="Task Management" width="300" style="margin: 10px;">
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
- **Migration Scripts**: Automated database schema updates
- **Backup/Restore**: Database backup and restoration tools
- **CLI Management**: Command-line database operations

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
├── docker-configs/        # Docker configurations and Dockerfiles
├── docker/                # Docker-related scripts and utilities
│   ├── config/            # Configuration files (Caddyfile, supervisord)
│   ├── fixes/             # Database and permission fix scripts
│   ├── migrations/        # Database migration scripts
│   ├── startup/           # Startup and initialization scripts
│   └── tests/             # Docker environment test scripts
├── scripts/                # Deployment and utility scripts
├── tests/                  # Application test suite
├── templates/              # Additional templates
├── assets/                 # Project assets and screenshots
└── logs/                   # Application logs
```

## 🐳 Docker Support

Multiple Docker configurations are available in `docker-configs/`:

- **Standard**: `docker-compose.yml` - Full application with all features
- **Simple**: `docker-compose.simple.yml` - Minimal setup
- **Python**: `docker-compose.python.yml` - Python-only environment
- **WeasyPrint**: `docker-compose.weasyprint.yml` - With PDF generation
- **Fixed**: `docker-compose.fixed.yml` - Resolved permission issues

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
# Use the appropriate docker-compose file
docker-compose -f docker-configs/docker-compose.yml up -d
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
