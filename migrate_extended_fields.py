
#!/usr/bin/env python3
"""
Database migration script to update fields to match Excel structure
"""
import os
import sys
from sqlalchemy import text
from app import app, db

def migrate_database():
    """Update security_users table to match Excel fields"""
    with app.app_context():
        try:
            # List of new columns to add (Excel-based)
            new_columns = [
                ('no', 'INTEGER'),
                ('date_registered', 'DATE'),
                ('role', 'VARCHAR'),
                ('complete_name', 'VARCHAR'),
                ('barcode', 'VARCHAR')
            ]
            
            # Check existing columns
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='security_users'
            """))
            
            existing_columns = [row[0] for row in result.fetchall()]
            
            # Add missing columns
            columns_added = 0
            for column_name, column_type in new_columns:
                if column_name not in existing_columns:
                    print(f"Adding column: {column_name}")
                    db.session.execute(text(f"""
                        ALTER TABLE security_users
                        ADD COLUMN {column_name} {column_type}
                    """))
                    columns_added += 1
                else:
                    print(f"✓ Column {column_name} already exists")
            
            if columns_added > 0:
                db.session.commit()
                print(f"✓ Successfully added {columns_added} new columns")
                
                # Update existing records to populate new fields
                from models import SecurityUser
                
                users = SecurityUser.query.all()
                
                if users:
                    print(f"Updating {len(users)} existing users with Excel fields...")
                    for i, user in enumerate(users, 1):
                        # Set sequential number
                        user.no = i
                        
                        # Set complete_name from full_name if available
                        if user.full_name and not user.complete_name:
                            user.complete_name = user.full_name
                        elif not user.complete_name and user.first_name and user.last_name:
                            middle = f" {user.middle_name}" if user.middle_name else ""
                            user.complete_name = f"{user.first_name}{middle} {user.last_name}"
                        
                        # Set barcode from qr_code_id
                        if user.qr_code_id and not user.barcode:
                            user.barcode = user.qr_code_id
                        
                        # Set role from position if available
                        if hasattr(user, 'position') and user.position and not user.role:
                            user.role = user.position
                        
                        # Convert status to Excel format
                        if user.status == 'allowed':
                            user.status = 'Active'
                        elif user.status == 'banned':
                            user.status = 'Inactive'
                    
                    db.session.commit()
                    print("✓ Updated existing users with Excel fields")
            else:
                print("✓ All columns already exist")
            
            return True
            
        except Exception as e:
            print(f"✗ Migration failed: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("Starting Excel fields migration...")
    success = migrate_database()
    
    if success:
        print("✓ Excel fields migration completed successfully!")
        sys.exit(0)
    else:
        print("✗ Excel fields migration failed!")
        sys.exit(1)
