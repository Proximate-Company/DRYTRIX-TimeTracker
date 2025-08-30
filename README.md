# TimeTracker - Professional Time Tracking Application

A comprehensive web-based time tracking application built with Flask, featuring project management, time tracking, invoicing, and analytics.

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
