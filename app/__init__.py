import os
import logging
from datetime import timedelta
from flask import Flask, request, session, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from dotenv import load_dotenv
from flask_babel import Babel, _
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth
import re
from jinja2 import ChoiceLoader, FileSystemLoader
from urllib.parse import urlparse
from werkzeug.middleware.proxy_fix import ProxyFix

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
socketio = SocketIO()
babel = Babel()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=[])
oauth = OAuth()


def create_app(config=None):
    """Application factory pattern"""
    app = Flask(__name__)

    # Make app aware of reverse proxy (scheme/host) for correct URL generation & cookies
    # Trust a single proxy by default; adjust via env if needed
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # Configuration
    # Load env-specific config class
    try:
        env_name = os.getenv("FLASK_ENV", "production")
        cfg_map = {
            "development": "app.config.DevelopmentConfig",
            "testing": "app.config.TestingConfig",
            "production": "app.config.ProductionConfig",
        }
        app.config.from_object(cfg_map.get(env_name, "app.config.Config"))
    except Exception:
        app.config.from_object("app.config.Config")
    if config:
        app.config.update(config)

    # Add top-level templates directory in addition to app/templates
    extra_templates_path = os.path.abspath(
        os.path.join(app.root_path, "..", "templates")
    )
    app.jinja_loader = ChoiceLoader(
        [app.jinja_loader, FileSystemLoader(extra_templates_path)]
    )

    # Prefer Postgres if POSTGRES_* envs are present but URL points to SQLite
    current_url = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if (
        not app.config.get("TESTING")
        and isinstance(current_url, str)
        and current_url.startswith("sqlite")
        and (
            os.getenv("POSTGRES_DB")
            or os.getenv("POSTGRES_USER")
            or os.getenv("POSTGRES_PASSWORD")
        )
    ):
        pg_user = os.getenv("POSTGRES_USER", "timetracker")
        pg_pass = os.getenv("POSTGRES_PASSWORD", "timetracker")
        pg_db = os.getenv("POSTGRES_DB", "timetracker")
        pg_host = os.getenv("POSTGRES_HOST", "db")
        app.config["SQLALCHEMY_DATABASE_URI"] = (
            f"postgresql+psycopg2://{pg_user}:{pg_pass}@{pg_host}:5432/{pg_db}"
        )

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    oauth.init_app(app)
    csrf.init_app(app)
    try:
        # Configure limiter defaults from config if provided
        default_limits = []
        raw = app.config.get("RATELIMIT_DEFAULT")
        if raw:
            # support semicolon or comma separated limits
            parts = [
                p.strip() for p in str(raw).replace(",", ";").split(";") if p.strip()
            ]
            if parts:
                default_limits = parts
        limiter._default_limits = default_limits  # set after init
        limiter.init_app(app)
    except Exception:
        limiter.init_app(app)

    # Ensure translations exist and configure absolute translation directories before Babel init
    try:
        translations_dirs = (
            app.config.get("BABEL_TRANSLATION_DIRECTORIES") or "translations"
        ).split(",")
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        abs_dirs = []
        for d in translations_dirs:
            d = d.strip()
            if not d:
                continue
            abs_dirs.append(
                d if os.path.isabs(d) else os.path.abspath(os.path.join(base_path, d))
            )
        if abs_dirs:
            app.config["BABEL_TRANSLATION_DIRECTORIES"] = os.pathsep.join(abs_dirs)
        # Best-effort compile with Babel CLI if available, else Python fallback
        try:
            import subprocess

            subprocess.run(["pybabel", "compile", "-d", abs_dirs[0]], check=False)
        except Exception:
            pass
        from app.utils.i18n import ensure_translations_compiled

        for d in abs_dirs:
            ensure_translations_compiled(d)
    except Exception:
        pass

    # Internationalization: locale selector compatible with Flask-Babel v4+
    def _select_locale():
        try:
            # 1) User preference from DB
            from flask_login import current_user

            if current_user and getattr(current_user, "is_authenticated", False):
                pref = getattr(current_user, "preferred_language", None)
                if pref:
                    return pref
            # 2) Session override (set-language route)
            if "preferred_language" in session:
                return session.get("preferred_language")
            # 3) Best match with Accept-Language
            supported = list(app.config.get("LANGUAGES", {}).keys()) or ["en"]
            return request.accept_languages.best_match(supported) or app.config.get(
                "BABEL_DEFAULT_LOCALE", "en"
            )
        except Exception:
            return app.config.get("BABEL_DEFAULT_LOCALE", "en")

    babel.init_app(
        app,
        default_locale=app.config.get("BABEL_DEFAULT_LOCALE", "en"),
        default_timezone=app.config.get("TZ", "Europe/Rome"),
        locale_selector=_select_locale,
    )

    # Ensure gettext helpers available in Jinja
    try:
        from flask_babel import gettext as _gettext, ngettext as _ngettext

        app.jinja_env.globals.update(_=_gettext, ngettext=_ngettext)
    except Exception:
        pass

    # Log effective database URL (mask password)
    db_url = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    try:
        masked_db_url = re.sub(r"//([^:]+):[^@]+@", r"//\\1:***@", db_url)
    except Exception:
        masked_db_url = db_url
    app.logger.info(f"Using database URL: {masked_db_url}")

    # Configure login manager
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    # Internationalization selector handled via babel.init_app(locale_selector=...)

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
            if request.path == "/login":
                app.logger.info(
                    "%s %s from %s UA=%s",
                    request.method,
                    request.path,
                    request.headers.get("X-Forwarded-For") or request.remote_addr,
                    request.headers.get("User-Agent"),
                )
        except Exception:
            pass

    # Log all write operations and their outcomes
    @app.after_request
    def log_write_requests(response):
        try:
            if request.method in ("POST", "PUT", "PATCH", "DELETE"):
                app.logger.info(
                    "%s %s -> %s from %s",
                    request.method,
                    request.path,
                    response.status_code,
                    request.headers.get("X-Forwarded-For") or request.remote_addr,
                )
        except Exception:
            pass
        return response

    # Configure session
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
        seconds=int(os.getenv("PERMANENT_SESSION_LIFETIME", 86400))
    )

    # Setup logging
    setup_logging(app)

    # Fail-fast on weak secret in production
    if not app.debug and app.config.get("FLASK_ENV", "production") == "production":
        if app.config.get("SECRET_KEY") == "dev-secret-key-change-in-production":
            app.logger.error(
                "Weak SECRET_KEY configured in production; refusing to start"
            )
            raise RuntimeError("Weak SECRET_KEY in production")

    # Apply security headers and a basic CSP
    @app.after_request
    def apply_security_headers(response):
        try:
            headers = app.config.get("SECURITY_HEADERS", {}) or {}
            for k, v in headers.items():
                # do not overwrite existing header if already present
                if not response.headers.get(k):
                    response.headers[k] = v
            # Minimal CSP allowing our own resources and common CDNs used in templates
            if not response.headers.get("Content-Security-Policy"):
                csp = (
                    "default-src 'self'; "
                    "img-src 'self' data: https:; "
                    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com https://cdn.datatables.net; "
                    "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com data:; "
                    "script-src 'self' 'unsafe-inline' https://code.jquery.com https://cdn.datatables.net https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
                    "connect-src 'self' ws: wss:; "
                    "frame-ancestors 'none'"
                )
                response.headers["Content-Security-Policy"] = csp
            # Additional privacy headers
            if not response.headers.get("Referrer-Policy"):
                response.headers["Referrer-Policy"] = "no-referrer"
            if not response.headers.get("Permissions-Policy"):
                response.headers["Permissions-Policy"] = (
                    "geolocation=(), microphone=(), camera=()"
                )
        except Exception:
            pass
        return response

    # CSRF error handler with HTML-friendly fallback
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        try:
            wants_json = (
                request.is_json
                or request.headers.get("X-Requested-With") == "XMLHttpRequest"
                or request.accept_mimetypes["application/json"]
                >= request.accept_mimetypes["text/html"]
            )
        except Exception:
            wants_json = False

        if wants_json:
            return jsonify(error="csrf_token_missing_or_invalid"), 400

        try:
            flash(_("Your session expired or the page was open too long. Please try again."), "warning")
        except Exception:
            flash("Your session expired or the page was open too long. Please try again.", "warning")

        # Redirect back to a safe same-origin referrer if available, else to dashboard
        dest = url_for("main.dashboard")
        try:
            ref = request.referrer
            if ref:
                ref_host = urlparse(ref).netloc
                cur_host = urlparse(request.host_url).netloc
                if ref_host and ref_host == cur_host:
                    dest = ref
        except Exception:
            pass
        return redirect(dest)

    # Expose csrf_token() in Jinja templates even without FlaskForm
    try:
        from flask_wtf.csrf import generate_csrf

        @app.context_processor
        def inject_csrf_token():
            return dict(csrf_token=lambda: generate_csrf())

    except Exception:
        pass

    # CSRF token refresh endpoint (GET)
    @app.route("/auth/csrf-token", methods=["GET"])
    def get_csrf_token():
        try:
            from flask_wtf.csrf import generate_csrf

            token = generate_csrf()
        except Exception:
            token = ""
        resp = jsonify(csrf_token=token)
        try:
            resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        except Exception:
            pass
        return resp

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
    from app.routes.comments import comments_bp
    from app.routes.kanban import kanban_bp

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
    app.register_blueprint(comments_bp)
    app.register_blueprint(kanban_bp)

    # Exempt API blueprint from CSRF protection (JSON API uses authentication, not CSRF tokens)
    csrf.exempt(api_bp)

    # Register OAuth OIDC client if enabled
    try:
        auth_method = (app.config.get("AUTH_METHOD") or "local").strip().lower()
    except Exception:
        auth_method = "local"

    if auth_method in ("oidc", "both"):
        issuer = app.config.get("OIDC_ISSUER")
        client_id = app.config.get("OIDC_CLIENT_ID")
        client_secret = app.config.get("OIDC_CLIENT_SECRET")
        scopes = app.config.get("OIDC_SCOPES", "openid profile email")
        if issuer and client_id and client_secret:
            try:
                oauth.register(
                    name="oidc",
                    client_id=client_id,
                    client_secret=client_secret,
                    server_metadata_url=f"{issuer.rstrip('/')}/.well-known/openid-configuration",
                    client_kwargs={
                        "scope": scopes,
                        "code_challenge_method": "S256",
                    },
                )
                app.logger.info("OIDC client registered with issuer %s", issuer)
            except Exception as e:
                app.logger.error("Failed to register OIDC client: %s", e)
        else:
            app.logger.warning(
                "AUTH_METHOD is %s but OIDC envs are incomplete; OIDC login will not work",
                auth_method,
            )

    # Register error handlers
    from app.utils.error_handlers import register_error_handlers

    register_error_handlers(app)

    # Register context processors
    from app.utils.context_processors import register_context_processors

    register_context_processors(app)

    # (translations compiled and directories set before Babel init)

    # Register template filters
    from app.utils.template_filters import register_template_filters

    register_template_filters(app)

    # Register CLI commands
    from app.utils.cli import register_cli_commands

    register_cli_commands(app)

    # Promote configured admin usernames automatically on each request (idempotent)
    @app.before_request
    def _promote_admin_users_on_request():
        try:
            from flask_login import current_user

            if not current_user or not getattr(current_user, "is_authenticated", False):
                return
            admin_usernames = [
                u.strip().lower() for u in app.config.get("ADMIN_USERNAMES", ["admin"])
            ]
            if (
                current_user.username
                and current_user.username.lower() in admin_usernames
                and current_user.role != "admin"
            ):
                current_user.role = "admin"
                db.session.commit()
        except Exception:
            # Non-fatal; avoid breaking requests if this fails
            try:
                db.session.rollback()
            except Exception:
                pass

    # Initialize database on first request
    def initialize_database():
        try:
            # Import models to ensure they are registered
            from app.models import (
                User,
                Project,
                TimeEntry,
                Task,
                Settings,
                TaskActivity,
                Comment,
            )

            # Create database tables
            db.create_all()

            # Check and migrate Task Management tables if needed
            migrate_task_management_tables()

            # Create default admin user if it doesn't exist
            admin_username = app.config.get("ADMIN_USERNAMES", ["admin"])[0]
            if not User.query.filter_by(username=admin_username).first():
                admin_user = User(username=admin_username, role="admin")
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
    log_level = os.getenv("LOG_LEVEL", "INFO")
    # Default to a file in the project logs directory if not provided
    default_log_path = os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "logs", "timetracker.log"
        )
    )
    log_file = os.getenv("LOG_FILE", default_log_path)

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
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )

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
        logging.getLogger("werkzeug").setLevel(logging.ERROR)


def migrate_task_management_tables():
    """Check and migrate Task Management tables if they don't exist"""
    try:
        from sqlalchemy import inspect, text

        # Check if tasks table exists
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()

        if "tasks" not in existing_tables:
            print("Task Management: Creating tasks table...")
            # Create the tasks table
            db.create_all()
            print("✓ Tasks table created successfully")
        else:
            print("Task Management: Tasks table already exists")

        # Check if task_id column exists in time_entries table
        if "time_entries" in existing_tables:
            time_entries_columns = [
                col["name"] for col in inspector.get_columns("time_entries")
            ]
            if "task_id" not in time_entries_columns:
                print("Task Management: Adding task_id column to time_entries table...")
                try:
                    # Add task_id column to time_entries table
                    db.engine.execute(
                        text(
                            "ALTER TABLE time_entries ADD COLUMN task_id INTEGER REFERENCES tasks(id)"
                        )
                    )
                    print("✓ task_id column added to time_entries table")
                except Exception as e:
                    print(f"⚠ Warning: Could not add task_id column: {e}")
                    print(
                        "  You may need to manually add this column or recreate the database"
                    )
            else:
                print(
                    "Task Management: task_id column already exists in time_entries table"
                )

        print("Task Management migration check completed")

    except Exception as e:
        print(f"⚠ Warning: Task Management migration check failed: {e}")
        print(
            "  The application will continue, but Task Management features may not work properly"
        )


def init_database(app):
    """Initialize database tables and create default admin user"""
    with app.app_context():
        try:
            # Import models to ensure they are registered
            from app.models import (
                User,
                Project,
                TimeEntry,
                Task,
                Settings,
                TaskActivity,
                Comment,
            )

            # Create database tables
            db.create_all()

            # Check and migrate Task Management tables if needed
            migrate_task_management_tables()

            # Create default admin user if it doesn't exist
            admin_username = app.config.get("ADMIN_USERNAMES", ["admin"])[0]
            if not User.query.filter_by(username=admin_username).first():
                admin_user = User(username=admin_username, role="admin")
                admin_user.is_active = True
                db.session.add(admin_user)
                db.session.commit()
                print(f"Created default admin user: {admin_username}")

            print("Database initialized successfully")
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise
