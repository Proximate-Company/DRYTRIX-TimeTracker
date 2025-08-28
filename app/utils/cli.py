import click
from flask.cli import with_appcontext
from app import db
from app.models import User, Project, TimeEntry, Settings
from datetime import datetime, timedelta
import os
import shutil

def register_cli_commands(app):
    """Register CLI commands for the application"""
    
    @app.cli.command()
    @with_appcontext
    def init_db():
        """Initialize the database with tables and default data"""
        # Create all tables
        db.create_all()
        
        # Initialize settings if they don't exist
        if not Settings.query.first():
            settings = Settings()
            db.session.add(settings)
            db.session.commit()
            click.echo("Database initialized with default settings")
        
        # Create admin user if it doesn't exist
        admin_username = os.getenv('ADMIN_USERNAMES', 'admin').split(',')[0]
        if not User.query.filter_by(username=admin_username).first():
            admin_user = User(username=admin_username, role='admin')
            db.session.add(admin_user)
            db.session.commit()
            click.echo(f"Created admin user: {admin_username}")
        
        click.echo("Database initialization complete!")
    
    @app.cli.command()
    @with_appcontext
    def create_admin():
        """Create an admin user"""
        username = click.prompt("Enter admin username")
        if not username:
            click.echo("Username cannot be empty")
            return
        
        if User.query.filter_by(username=username).first():
            click.echo(f"User {username} already exists")
            return
        
        user = User(username=username, role='admin')
        db.session.add(user)
        db.session.commit()
        click.echo(f"Created admin user: {username}")
    
    @app.cli.command()
    @with_appcontext
    def backup_db():
        """Create a backup of the database"""
        from app.config import Config
        
        url = Config.SQLALCHEMY_DATABASE_URI
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if url.startswith('sqlite:///'):
            # SQLite file copy
            db_path = url.replace('sqlite:///', '')
            if not os.path.exists(db_path):
                click.echo(f"Database file not found: {db_path}")
                return
            backup_dir = os.path.join(os.path.dirname(db_path), 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            backup_filename = f"timetracker_backup_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_filename)
            shutil.copy2(db_path, backup_path)
            click.echo(f"Database backed up to: {backup_path}")
        else:
            click.echo("For PostgreSQL, please use pg_dump, e.g.: pg_dump --format=custom --dbname=\"$DATABASE_URL\" --file=backup.dump")
        
        # Clean up old backups
        cleanup_old_backups(backup_dir)
    
    @app.cli.command()
    @with_appcontext
    def cleanup_old_entries():
        """Clean up old time entries (older than specified days)"""
        days = click.prompt("Delete entries older than (days)", type=int, default=365)
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        old_entries = TimeEntry.query.filter(
            TimeEntry.end_time < cutoff_date
        ).all()
        
        if not old_entries:
            click.echo("No old entries found")
            return
        
        count = len(old_entries)
        if click.confirm(f"Delete {count} old entries?"):
            for entry in old_entries:
                db.session.delete(entry)
            db.session.commit()
            click.echo(f"Deleted {count} old entries")
        else:
            click.echo("Operation cancelled")
    
    @app.cli.command()
    @with_appcontext
    def stats():
        """Show database statistics"""
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        total_projects = Project.query.count()
        active_projects = Project.query.filter_by(status='active').count()
        total_entries = TimeEntry.query.count()
        completed_entries = TimeEntry.query.filter(TimeEntry.end_time.isnot(None)).count()
        active_timers = TimeEntry.query.filter_by(end_time=None).count()
        
        click.echo("Database Statistics:")
        click.echo(f"  Users: {total_users} (active: {active_users})")
        click.echo(f"  Projects: {total_projects} (active: {active_projects})")
        click.echo(f"  Time Entries: {total_entries} (completed: {completed_entries}, active: {active_timers})")
        
        # Calculate total hours
        total_hours = db.session.query(
            db.func.sum(TimeEntry.duration_seconds)
        ).filter(
            TimeEntry.end_time.isnot(None)
        ).scalar() or 0
        
        total_hours = round(total_hours / 3600, 2)
        click.echo(f"  Total Hours: {total_hours}")

def cleanup_old_backups(backup_dir, retention_days=30):
    """Clean up old backup files"""
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    
    for filename in os.listdir(backup_dir):
        file_path = os.path.join(backup_dir, filename)
        if os.path.isfile(file_path):
            file_time = datetime.fromtimestamp(os.path.getctime(file_path))
            if file_time < cutoff_date:
                os.remove(file_path)
                click.echo(f"Removed old backup: {filename}")
