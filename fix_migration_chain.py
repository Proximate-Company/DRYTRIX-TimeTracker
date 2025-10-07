"""
Fix migration chain by stamping migration 018 if it hasn't been applied.

This script checks if the organizations table exists (created by migration 018)
and if so, stamps the database to register migration 018 in alembic_version.
"""
import sys
from sqlalchemy import create_engine, inspect, text
from app import create_app, db
from app.config import Config

def fix_migration_chain():
    """Fix the migration chain by stamping migration 018 if needed."""
    
    # Create app to get database connection
    app = create_app()
    
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print("Checking database state...")
        print(f"Found {len(tables)} tables in database")
        
        # Check if organizations table exists (created by migration 018)
        if 'organizations' in tables:
            print("✓ Organizations table exists (migration 018 was applied)")
            
            # Check if migration 018 is in alembic_version
            try:
                result = db.session.execute(
                    text("SELECT version_num FROM alembic_version")
                ).fetchone()
                
                if result:
                    current_version = result[0]
                    print(f"Current migration version: {current_version}")
                    
                    if current_version == '017':
                        print("\n⚠ Migration 018 tables exist but not stamped!")
                        print("Stamping database with migration 018...")
                        
                        # Update alembic_version to 018
                        db.session.execute(
                            text("UPDATE alembic_version SET version_num = '018'")
                        )
                        db.session.commit()
                        
                        print("✓ Database stamped with migration 018")
                        print("\nNow you can run: flask db upgrade")
                        print("This will apply migration 019 (auth features)")
                        return True
                    
                    elif current_version == '018':
                        print("✓ Migration 018 is already stamped")
                        print("\nYou can now run: flask db upgrade")
                        print("This will apply migration 019 (auth features)")
                        return True
                    
                    elif current_version == '019_add_auth_features' or current_version == '019':
                        print("✓ All migrations are up to date!")
                        return True
                    
                    else:
                        print(f"⚠ Unexpected migration version: {current_version}")
                        print("Please check your migration status manually")
                        return False
                        
                else:
                    print("⚠ No migration version found in alembic_version table")
                    print("Initializing with migration 018...")
                    
                    db.session.execute(
                        text("INSERT INTO alembic_version (version_num) VALUES ('018')")
                    )
                    db.session.commit()
                    
                    print("✓ Database initialized with migration 018")
                    print("\nNow you can run: flask db upgrade")
                    return True
                    
            except Exception as e:
                print(f"Error checking alembic_version: {e}")
                
                # Try to create alembic_version table if it doesn't exist
                print("Creating alembic_version table...")
                db.session.execute(
                    text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))")
                )
                db.session.execute(
                    text("INSERT INTO alembic_version (version_num) VALUES ('018')")
                )
                db.session.commit()
                
                print("✓ Created alembic_version table and stamped with migration 018")
                print("\nNow you can run: flask db upgrade")
                return True
        
        else:
            print("⚠ Organizations table doesn't exist")
            print("You need to run migrations from scratch")
            print("\nRun: flask db upgrade")
            return False

if __name__ == '__main__':
    try:
        success = fix_migration_chain()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

