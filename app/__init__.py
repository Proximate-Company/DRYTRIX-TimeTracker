import os
import logging
from datetime import timedelta
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from dotenv import load_dotenv
import re
from jinja2 import ChoiceLoader, FileSystemLoader
from werkzeug.middleware.proxy_fix import ProxyFix

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
    
    # Make app aware of reverse proxy (scheme/host) for correct URL generation & cookies
    # Trust a single proxy by default; adjust via env if needed
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    
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
    
    # Register user loader
    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login"""
        from app.models import User
        return User.query.get(int(user_id))

    # Request logging for /login to trace POSTs reaching the app
    @app.before_request
    def log_login_requests():
        try:
            if request.path == '/login':
                app.logger.info("%s %s from %s UA=%s", request.method, request.path, request.headers.get('X-Forwarded-For') or request.remote_addr, request.headers.get('User-Agent'))
        except Exception:
            pass

    # Log all write operations and their outcomes
    @app.after_request
    def log_write_requests(response):
        try:
            if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
                app.logger.info(
                    "%s %s -> %s from %s",
                    request.method,
                    request.path,
                    response.status_code,
                    request.headers.get('X-Forwarded-For') or request.remote_addr,
                )
        except Exception:
            pass
        return response
    
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
    from app.routes.analytics import analytics_bp
    from app.routes.tasks import tasks_bp
    from app.routes.invoices import invoices_bp
    from app.routes.clients import clients_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(timer_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(clients_bp)
    
    # Initialize phone home function if enabled
    if app.config.get('LICENSE_SERVER_ENABLED', True):
        try:
            from app.utils.license_server import init_license_client, start_license_client, get_license_client
            
            # Check if client is already running
            existing_client = get_license_client()
            if existing_client and existing_client.running:
                app.logger.info("Phone home function already running, skipping initialization")
            else:
                license_client = init_license_client(
                    app_identifier=app.config.get('LICENSE_SERVER_APP_ID', 'timetracker'),
                    app_version=app.config.get('LICENSE_SERVER_APP_VERSION', '1.0.0')
                )
                if start_license_client():
                    app.logger.info("Phone home function started successfully")
                else:
                    app.logger.warning("Failed to start phone home function")
        except Exception as e:
            app.logger.warning(f"Could not initialize phone home function: {e}")
    
    # Register cleanup function for graceful shutdown
    @app.teardown_appcontext
    def cleanup_license_client(exception=None):
        """Cleanup phone home function on app context teardown"""
        try:
            from app.utils.license_server import get_license_client, stop_license_client
            client = get_license_client()
            if client and client.running:
                app.logger.info("Stopping phone home function during app teardown")
                stop_license_client()
        except Exception as e:
            app.logger.warning(f"Error during license client cleanup: {e}")
    
    # Register error handlers
    from app.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Register context processors
    from app.utils.context_processors import register_context_processors
    register_context_processors(app)
    
    # Register template filters
    from app.utils.template_filters import register_template_filters
    register_template_filters(app)
    
    # Register CLI commands
    from app.utils.cli import register_cli_commands
    register_cli_commands(app)
    
    # Initialize database on first request
    def initialize_database():
        try:
            # Import models to ensure they are registered
            from app.models import User, Project, TimeEntry, Task, Settings, TaskActivity
            
            # Create database tables
            db.create_all()
            
            # Check and migrate Task Management tables if needed
            migrate_task_management_tables()
            
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
    # Default to a file in the project logs directory if not provided
    default_log_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'timetracker.log'))
    log_file = os.getenv('LOG_FILE', default_log_path)
    
    # Prepare handlers
    handlers = [logging.StreamHandler()]
    
    # Add file handler (default or specified)
    try:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # Create file handler
        file_handler = logging.FileHandler(log_file)
        handlers.append(file_handler)
    except (PermissionError, OSError) as e:
        print(f"Warning: Could not create log file '{log_file}': {e}")
        print("Logging to console only")
        # Don't add file handler, just use console logging
    
    # Configure Flask app logger directly (works well under gunicorn)
    for handler in handlers:
        handler.setLevel(getattr(logging, log_level.upper()))
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))

    # Clear existing handlers to avoid duplicate logs
    app.logger.handlers.clear()
    app.logger.propagate = False
    app.logger.setLevel(getattr(logging, log_level.upper()))
    for handler in handlers:
        app.logger.addHandler(handler)

    # Also configure root logger so modules using logging.getLogger() are captured
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    # Avoid duplicating handlers if already attached
    root_logger.handlers = []
    for handler in handlers:
        root_logger.addHandler(handler)

    # Suppress noisy logs in production
    if not app.debug:
        logging.getLogger('werkzeug').setLevel(logging.ERROR)

def migrate_task_management_tables():
    """Check and migrate Task Management tables if they don't exist"""
    try:
        from sqlalchemy import inspect, text
        
        # Check if tasks table exists
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        if 'tasks' not in existing_tables:
            print("Task Management: Creating tasks table...")
            # Create the tasks table
            db.create_all()
            print("✓ Tasks table created successfully")
        else:
            print("Task Management: Tasks table already exists")
        
        # Check if task_id column exists in time_entries table
        if 'time_entries' in existing_tables:
            time_entries_columns = [col['name'] for col in inspector.get_columns('time_entries')]
            if 'task_id' not in time_entries_columns:
                print("Task Management: Adding task_id column to time_entries table...")
                try:
                    # Add task_id column to time_entries table
                    db.engine.execute(text("ALTER TABLE time_entries ADD COLUMN task_id INTEGER REFERENCES tasks(id)"))
                    print("✓ task_id column added to time_entries table")
                except Exception as e:
                    print(f"⚠ Warning: Could not add task_id column: {e}")
                    print("  You may need to manually add this column or recreate the database")
            else:
                print("Task Management: task_id column already exists in time_entries table")
        
        print("Task Management migration check completed")
        
    except Exception as e:
        print(f"⚠ Warning: Task Management migration check failed: {e}")
        print("  The application will continue, but Task Management features may not work properly")

def init_database(app):
    """Initialize database tables and create default admin user"""
    with app.app_context():
        try:
            # Import models to ensure they are registered
            from app.models import User, Project, TimeEntry, Task, Settings, TaskActivity
            
            # Create database tables
            db.create_all()
            
            # Check and migrate Task Management tables if needed
            migrate_task_management_tables()
            
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
