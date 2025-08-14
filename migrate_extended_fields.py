
#!/usr/bin/env python3
"""
Database migration script to add extended user fields
"""
import os
import sys
from sqlalchemy import text
from app import app, db

def migrate_database():
    """Add extended user fields to security_users table"""
    with app.app_context():
        try:
            # List of new columns to add
            new_columns = [
                ('employee_number', 'VARCHAR'),
                ('first_name', 'VARCHAR'),
                ('middle_name', 'VARCHAR'),
                ('last_name', 'VARCHAR'),
                ('position', 'VARCHAR'),
                ('department', 'VARCHAR'),
                ('company', 'VARCHAR'),
                ('employee_type', 'VARCHAR'),
                ('address', 'TEXT'),
                ('contact_number', 'VARCHAR'),
                ('emergency_contact_name', 'VARCHAR'),
                ('emergency_contact_number', 'VARCHAR'),
                ('id_number', 'VARCHAR'),
                ('drivers_license', 'VARCHAR')
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
                
                # Update existing records to populate first_name and last_name from full_name
                from models import SecurityUser
                
                users = SecurityUser.query.filter(
                    (SecurityUser.first_name == None) | 
                    (SecurityUser.last_name == None)
                ).all()
                
                if users:
                    print(f"Updating {len(users)} existing users with name fields...")
                    for user in users:
                        if user.full_name and not user.first_name:
                            name_parts = user.full_name.split()
                            user.first_name = name_parts[0] if name_parts else ''
                            user.last_name = name_parts[-1] if len(name_parts) > 1 else ''
                            if len(name_parts) > 2:
                                user.middle_name = ' '.join(name_parts[1:-1])
                    
                    db.session.commit()
                    print("✓ Updated existing users with name fields")
            else:
                print("✓ All columns already exist")
            
            return True
            
        except Exception as e:
            print(f"✗ Migration failed: {str(e)}")
            db.session.rollback()
            return False

if __name__ == "__main__":
    print("Starting extended fields migration...")
    success = migrate_database()
    
    if success:
        print("✓ Extended fields migration completed successfully!")
        sys.exit(0)
    else:
        print("✗ Extended fields migration failed!")
        sys.exit(1)
