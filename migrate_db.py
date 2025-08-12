
#!/usr/bin/env python3
"""
Database migration script to add missing qr_code_filename column
"""
import os
import sys
from sqlalchemy import text
from app import app, db

def migrate_database():
    """Add missing qr_code_filename column to security_users table"""
    with app.app_context():
        try:
            # Check if column exists
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='security_users' 
                AND column_name='qr_code_filename'
            """))
            
            if result.fetchone():
                print("✓ Column qr_code_filename already exists")
                return True
            
            # Add the missing column
            print("Adding qr_code_filename column to security_users table...")
            db.session.execute(text("""
                ALTER TABLE security_users 
                ADD COLUMN qr_code_filename VARCHAR
            """))
            
            db.session.commit()
            print("✓ Successfully added qr_code_filename column")
            
            # Generate QR codes for existing users without them
            from security_service import security_service
            from models import SecurityUser
            
            users_without_qr = SecurityUser.query.filter(
                (SecurityUser.qr_code_filename == None) | 
                (SecurityUser.qr_code_filename == '')
            ).all()
            
            if users_without_qr:
                print(f"Generating QR codes for {len(users_without_qr)} existing users...")
                for user in users_without_qr:
                    qr_filename = security_service.generate_qr_code(user.qr_code_id, user.full_name)
                    user.qr_code_filename = qr_filename
                
                db.session.commit()
                print("✓ Generated QR codes for existing users")
            
            return True
            
        except Exception as e:
            print(f"✗ Migration failed: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("Starting database migration...")
    success = migrate_database()
    
    if success:
        print("✓ Database migration completed successfully!")
        sys.exit(0)
    else:
        print("✗ Database migration failed!")
        sys.exit(1)
