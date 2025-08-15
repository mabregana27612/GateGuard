
#!/usr/bin/env python3
"""
Migration script to add role management columns to admin_users table
"""

import os
import sys
from sqlalchemy import text
from app import app, db

def migrate_admin_users():
    """Add role management columns to admin_users table"""
    try:
        with app.app_context():
            # Check if columns exist
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'admin_users' AND table_schema = 'public'
            """))
            
            existing_columns = [row[0] for row in result.fetchall()]
            
            # Add role column if it doesn't exist
            if 'role' not in existing_columns:
                print("Adding role column...")
                db.session.execute(text("""
                    ALTER TABLE admin_users 
                    ADD COLUMN role VARCHAR(20) DEFAULT 'guard'
                """))
                print("✓ role column added")
            
            # Add created_by column if it doesn't exist
            if 'created_by' not in existing_columns:
                print("Adding created_by column...")
                db.session.execute(text("""
                    ALTER TABLE admin_users 
                    ADD COLUMN created_by INTEGER REFERENCES admin_users(id)
                """))
                print("✓ created_by column added")
            
            # Add last_login column if it doesn't exist
            if 'last_login' not in existing_columns:
                print("Adding last_login column...")
                db.session.execute(text("""
                    ALTER TABLE admin_users 
                    ADD COLUMN last_login TIMESTAMP
                """))
                print("✓ last_login column added")
            
            # Update existing admin to super_admin role
            db.session.execute(text("""
                UPDATE admin_users 
                SET role = 'super_admin' 
                WHERE username = 'admin' AND role IS NULL
            """))
            
            db.session.commit()
            print("✓ Admin users table migration completed successfully!")
            return True
            
    except Exception as e:
        print(f"✗ Migration failed: {str(e)}")
        db.session.rollback()
        return False

if __name__ == "__main__":
    print("Starting admin_users table migration...")
    success = migrate_admin_users()
    
    if success:
        print("✓ Migration completed successfully!")
        sys.exit(0)
    else:
        print("✗ Migration failed!")
        sys.exit(1)
