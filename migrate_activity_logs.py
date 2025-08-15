
#!/usr/bin/env python3
"""
Migration script to add missing columns to activity_logs table
"""

import os
import sys
from sqlalchemy import text
from app import app, db

def migrate_activity_logs():
    """Add missing columns to activity_logs table"""
    try:
        with app.app_context():
            # Check if columns exist
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'activity_logs' AND table_schema = 'public'
            """))
            
            existing_columns = [row[0] for row in result.fetchall()]
            
            # Add visit_reason column if it doesn't exist
            if 'visit_reason' not in existing_columns:
                print("Adding visit_reason column...")
                db.session.execute(text("""
                    ALTER TABLE activity_logs 
                    ADD COLUMN visit_reason VARCHAR
                """))
                print("✓ visit_reason column added")
            
            # Add user_role column if it doesn't exist
            if 'user_role' not in existing_columns:
                print("Adding user_role column...")
                db.session.execute(text("""
                    ALTER TABLE activity_logs 
                    ADD COLUMN user_role VARCHAR
                """))
                print("✓ user_role column added")
            
            # Add operator_id column if it doesn't exist
            if 'operator_id' not in existing_columns:
                print("Adding operator_id column...")
                db.session.execute(text("""
                    ALTER TABLE activity_logs 
                    ADD COLUMN operator_id INTEGER REFERENCES admin_users(id)
                """))
                print("✓ operator_id column added")
            
            # Add operator_name column if it doesn't exist
            if 'operator_name' not in existing_columns:
                print("Adding operator_name column...")
                db.session.execute(text("""
                    ALTER TABLE activity_logs 
                    ADD COLUMN operator_name VARCHAR
                """))
                print("✓ operator_name column added")
            
            # Add operator_role column if it doesn't exist
            if 'operator_role' not in existing_columns:
                print("Adding operator_role column...")
                db.session.execute(text("""
                    ALTER TABLE activity_logs 
                    ADD COLUMN operator_role VARCHAR
                """))
                print("✓ operator_role column added")
            
            db.session.commit()
            print("✓ Activity logs table migration completed successfully!")
            return True
            
    except Exception as e:
        print(f"✗ Migration failed: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    print("Starting activity_logs table migration...")
    success = migrate_activity_logs()
    
    if success:
        print("✓ Migration completed successfully!")
        sys.exit(0)
    else:
        print("✗ Migration failed!")
        sys.exit(1)
