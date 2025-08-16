import os
import logging
from datetime import timedelta
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from dotenv import load_dotenv
import re
from jinja2 import ChoiceLoader, FileSystemLoader

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()

def create_app(config=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuration
    app.config.from_object('app.config.Config')
    if config:
        app.config.update(config)
    
    # Add top-level templates directory in addition to app/templates
    extra_templates_path = os.path.abspath(
        os.path.join(app.root_path, '..', 'templates')
    )
    app.jinja_loader = ChoiceLoader([
        app.jinja_loader,
        FileSystemLoader(extra_templates_path)
    ])
    
    # Prefer Postgres if POSTGRES_* envs are present but URL points to SQLite
    current_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if (
        not app.config.get('TESTING')
        and isinstance(current_url, str)
        and current_url.startswith('sqlite')
        and (
            os.getenv('POSTGRES_DB')
            or os.getenv('POSTGRES_USER')
            or os.getenv('POSTGRES_PASSWORD')
        )
    ):
        pg_user = os.getenv('POSTGRES_USER', 'timetracker')
        pg_pass = os.getenv('POSTGRES_PASSWORD', 'timetracker')
        pg_db = os.getenv('POSTGRES_DB', 'timetracker')
        pg_host = os.getenv('POSTGRES_HOST', 'db')
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f'postgresql+psycopg2://{pg_user}:{pg_pass}@{pg_host}:5432/{pg_db}'
        )
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # Log effective database URL (mask password)
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    try:
        masked_db_url = re.sub(r"//([^:]+):[^@]+@", r"//\\1:***@", db_url)
    except Exception:
        masked_db_url = db_url
    app.logger.info(f"Using database URL: {masked_db_url}")
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Configure session
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(
        seconds=int(os.getenv('PERMANENT_SESSION_LIFETIME', 86400))
    )
    
    # Setup logging
    setup_logging(app)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.projects import projects_bp
    from app.routes.timer import timer_bp
    from app.routes.reports import reports_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(timer_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    
    # Register error handlers
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Register context processors
    from app.utils.context_processors import register_context_processors
    register_context_processors(app)
    
    # Register CLI commands
    from app.utils.cli import register_cli_commands
    register_cli_commands(app)
    
    # Initialize database on first request
    def initialize_database():
        try:
            # Import models to ensure they are registered
            from app.models import User, Project, TimeEntry, Settings
            
            # Create database tables
            db.create_all()
            
            # Create default admin user if it doesn't exist
            admin_username = app.config.get('ADMIN_USERNAMES', ['admin'])[0]
            if not User.query.filter_by(username=admin_username).first():
                admin_user = User(
                    username=admin_username,
                    role='admin'
                )
                admin_user.is_active = True
                db.session.add(admin_user)
                db.session.commit()
                print(f"Created default admin user: {admin_username}")
            
            print("Database initialized successfully")
        except Exception as e:
            print(f"Error initializing database: {e}")
            # Don't raise the exception, just log it
    
    # Store the initialization function for later use
    app.initialize_database = initialize_database
    
    return app

def setup_logging(app):
    """Setup application logging"""
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.getenv('LOG_FILE')
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )
    
    # Suppress Werkzeug logs in production
    if not app.debug:
        logging.getLogger('werkzeug').setLevel(logging.ERROR)

def init_database(app):
    """Initialize database tables and create default admin user"""
    with app.app_context():
        try:
            # Import models to ensure they are registered
            from app.models import User, Project, TimeEntry, Settings
            
            # Create database tables
            db.create_all()
            
            # Create default admin user if it doesn't exist
            admin_username = app.config.get('ADMIN_USERNAMES', ['admin'])[0]
            if not User.query.filter_by(username=admin_username).first():
                admin_user = User(
                    username=admin_username,
                    role='admin'
                )
                admin_user.is_active = True
                db.session.add(admin_user)
                db.session.commit()
                print(f"Created default admin user: {admin_username}")
            
            print("Database initialized successfully")
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise
