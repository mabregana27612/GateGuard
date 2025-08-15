import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
from sqlalchemy import text
from app import db
from models import SecurityUser, ActivityLog

import qrcode
from io import BytesIO
import base64

class SecurityService:
    def __init__(self):
        self.upload_folder = 'static/uploads'
        self.qr_folder = 'static/qr_codes'
        self.allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        os.makedirs(self.upload_folder, exist_ok=True)
        os.makedirs(self.qr_folder, exist_ok=True)
    
    def allowed_file(self, filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def save_picture(self, picture_file):
        """Save and resize user picture"""
        if not picture_file or not self.allowed_file(picture_file.filename):
            return None
        
        # Generate unique filename
        filename = secure_filename(picture_file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        filepath = os.path.join(self.upload_folder, unique_filename)
        
        # Resize and save image
        image = Image.open(picture_file)
        image = image.convert('RGB')
        # Resize to 300x300 while maintaining aspect ratio
        image.thumbnail((300, 300), Image.Resampling.LANCZOS)
        image.save(filepath, 'JPEG', quality=85)
        
        return unique_filename
    
    def generate_qr_code(self, qr_code_id, user_name):
        """Generate QR code for user"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        qr.add_data(qr_code_id)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to file
        filename = f"qr_{qr_code_id}.png"
        filepath = os.path.join(self.qr_folder, filename)
        img.save(filepath)
        
        return filename
    
    def analyze_csv(self, csv_file):
        """Analyze CSV file and return statistics"""
        import csv
        from io import StringIO
        import chardet
        
        # Read CSV content with encoding detection
        raw_content = csv_file.read()
        
        # Detect encoding
        encoding_result = chardet.detect(raw_content)
        encoding = encoding_result['encoding'] if encoding_result['encoding'] else 'utf-8'
        
        # Fallback encodings to try
        encodings_to_try = [encoding, 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        csv_content = None
        for enc in encodings_to_try:
            try:
                csv_content = raw_content.decode(enc)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        
        if csv_content is None:
            return {
                'success': False,
                'message': 'Unable to decode CSV file. Please ensure it is saved in UTF-8 format.'
            }
        
        csv_file.seek(0)  # Reset file pointer
        
        # Parse CSV
        csv_reader = csv.DictReader(StringIO(csv_content))
        
        # Validate headers - more flexible approach
        headers = csv_reader.fieldnames
        if not headers:
            return {
                'success': False,
                'message': 'CSV file appears to be empty or invalid'
            }
        
        # Check for Excel-based required fields
        required_fields = ['first_name', 'last_name']
        has_required_names = all(field in headers for field in required_fields)
        has_barcode = 'barcode' in headers or 'id_number' in headers or 'qr_code_id' in headers
        
        if not has_required_names or not has_barcode:
            return {
                'success': False,
                'message': 'CSV must contain "first_name", "last_name", and either "barcode", "id_number", or "qr_code_id"'
            }
        
        # Get existing QR codes
        existing_qr_codes = set(user.qr_code_id for user in SecurityUser.query.all())
        
        # Analyze records
        total_records = 0
        new_records = 0
        duplicate_records = 0
        error_records = 0
        errors = []
        preview_data = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start from 2 (after header)
            total_records += 1
            
            # Extract name fields (Excel format)
            first_name = row.get('first_name', '').strip()
            last_name = row.get('last_name', '').strip()
            middle_name = row.get('middle_name', '').strip()
            
            if not first_name or not last_name:
                error_records += 1
                errors.append(f"Row {row_num}: Missing first_name or last_name")
                continue
            
            # Build complete name
            complete_name = row.get('complete_name', '').strip()
            if not complete_name:
                middle_part = f" {middle_name}" if middle_name else ""
                complete_name = f"{first_name}{middle_part} {last_name}"
            
            # Extract barcode/QR code ID from various possible columns
            barcode = (row.get('barcode', '') or 
                      row.get('qr_code_id', '') or 
                      row.get('id_number', '')).strip()
            
            if not barcode:
                error_records += 1
                errors.append(f"Row {row_num}: Missing barcode/QR Code ID")
                continue
            
            # Extract other fields (Excel format)
            status = row.get('status', 'Active').strip()
            if status.lower() in ['active', 'allowed']:
                status = 'Active'
            elif status.lower() in ['inactive', 'banned']:
                status = 'Inactive'
            else:
                status = 'Active'  # Default to Active
            
            # Check for duplicates using barcode
            import_status = 'New'
            if barcode in existing_qr_codes:
                duplicate_records += 1
                import_status = 'Duplicate'
            else:
                new_records += 1
            
            # Add to preview (first 10 new records only)
            if len(preview_data) < 10 and import_status == 'New':
                preview_data.append({
                    'complete_name': complete_name,
                    'barcode': barcode,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': row.get('role', ''),
                    'company': row.get('company', ''),
                    'status': status,
                    'import_status': import_status
                })
        
        return {
            'success': True,
            'total_records': total_records,
            'new_records': new_records,
            'duplicate_records': duplicate_records,
            'error_records': error_records,
            'errors': errors,
            'preview': preview_data
        }
    
    def import_csv(self, csv_file):
        """Import users from CSV file"""
        import csv
        from io import StringIO
        import chardet
        
        # Read CSV content with encoding detection
        raw_content = csv_file.read()
        
        # Detect encoding
        encoding_result = chardet.detect(raw_content)
        encoding = encoding_result['encoding'] if encoding_result['encoding'] else 'utf-8'
        
        # Fallback encodings to try
        encodings_to_try = [encoding, 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        csv_content = None
        for enc in encodings_to_try:
            try:
                csv_content = raw_content.decode(enc)
                break
            except (UnicodeDecodeError, LookupError):
                continue
        
        if csv_content is None:
            return {
                'success': False,
                'message': 'Unable to decode CSV file. Please ensure it is saved in UTF-8 format.'
            }
        
        csv_reader = csv.DictReader(StringIO(csv_content))
        
        # Get existing barcodes
        existing_qr_codes = set(user.barcode or user.qr_code_id for user in SecurityUser.query.all() if user.barcode or user.qr_code_id)
        
        imported_count = 0
        errors = []
        
        # Get next sequential number
        max_no = db.session.execute(text("SELECT COALESCE(MAX(no), 0) FROM security_users")).scalar() or 0
        next_no = max_no + 1
        
        try:
            for row_num, row in enumerate(csv_reader, start=2):
                # Extract name fields (Excel format)
                first_name = row.get('first_name', '').strip()
                last_name = row.get('last_name', '').strip()
                middle_name = row.get('middle_name', '').strip()
                
                if not first_name or not last_name:
                    continue
                
                # Build complete name
                complete_name = row.get('complete_name', '').strip()
                if not complete_name:
                    middle_part = f" {middle_name}" if middle_name else ""
                    complete_name = f"{first_name}{middle_part} {last_name}"
                
                # Extract barcode
                barcode = (row.get('barcode', '') or 
                          row.get('qr_code_id', '') or 
                          row.get('id_number', '')).strip()
                
                # Skip invalid or duplicate records
                if not barcode:
                    continue
                
                if barcode in existing_qr_codes:
                    continue
                
                # Validate status
                status = row.get('status', 'Active').strip()
                if status.lower() in ['active', 'allowed']:
                    status = 'Active'
                elif status.lower() in ['inactive', 'banned']:
                    status = 'Inactive'
                else:
                    status = 'Active'
                
                # Parse date registered
                date_registered = None
                date_str = row.get('date_registered', '').strip()
                if date_str:
                    try:
                        from datetime import datetime
                        date_registered = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            date_registered = datetime.strptime(date_str, '%m/%d/%Y').date()
                        except ValueError:
                            pass
                
                # Create new user with Excel fields
                new_user = SecurityUser(
                    no=next_no,
                    date_registered=date_registered or datetime.now().date(),
                    first_name=first_name,
                    middle_name=middle_name or None,
                    last_name=last_name,
                    complete_name=complete_name,
                    barcode=barcode,
                    role=row.get('role', '').strip() or None,
                    company=row.get('company', '').strip() or None,
                    address=row.get('address', '').strip() or None,
                    contact_number=row.get('contact_number', '').strip() or None,
                    id_number=row.get('id_number', '').strip() or None,
                    status=status,
                    # Legacy compatibility
                    full_name=complete_name,
                    qr_code_id=barcode
                )
                
                # Generate QR code
                qr_filename = self.generate_qr_code(barcode, complete_name)
                new_user.qr_code_filename = qr_filename
                
                db.session.add(new_user)
                imported_count += 1
                next_no += 1
                
                # Add to existing set to prevent duplicates within the same file
                existing_qr_codes.add(barcode)
            
            db.session.commit()
            
            # Log the bulk import
            activity = ActivityLog(
                qr_code_id='BULK_IMPORT',
                user_name=f'Admin Import ({imported_count} users)',
                action='bulk_import',
                method='CSV',
                details=f'Imported {imported_count} users via CSV upload'
            )
            db.session.add(activity)
            db.session.commit()
            
            return {
                'success': True,
                'imported_count': imported_count,
                'message': f'Successfully imported {imported_count} users'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Import failed: {str(e)}'
            }
        qr.add_data(qr_code_id)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Save QR code
        qr_filename = f"qr_{qr_code_id}.png"
        qr_path = os.path.join(self.qr_folder, qr_filename)
        qr_img.save(qr_path)
        
        return qr_filename
    
    def add_user(self, full_name, qr_code_id, status="allowed", picture_file=None):
        """Add a new security user"""
        # Check if QR code already exists
        existing_user = SecurityUser.query.filter_by(qr_code_id=qr_code_id).first()
        if existing_user:
            return False, "QR Code ID already exists"
        
        # Save picture if provided
        picture_filename = None
        if picture_file:
            picture_filename = self.save_picture(picture_file)
        
        # Generate QR code
        qr_filename = self.generate_qr_code(qr_code_id.upper(), full_name)
        
        # Create new user
        user = SecurityUser(
            full_name=full_name,
            qr_code_id=qr_code_id.upper(),
            status=status,
            picture_filename=picture_filename,
            qr_code_filename=qr_filename
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            return True, "User added successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Database error: {str(e)}"
    
    def get_user_by_qr(self, qr_code_id):
        """Get user by QR code ID"""
        return SecurityUser.query.filter_by(qr_code_id=qr_code_id.upper()).first()
    
    def get_all_users(self):
        """Get all security users"""
        return SecurityUser.query.order_by(SecurityUser.created_at.desc()).all()
    
    def update_user(self, qr_code_id, full_name=None, status=None, picture_file=None):
        """Update user information"""
        user = self.get_user_by_qr(qr_code_id)
        if not user:
            return False, "User not found"
        
        try:
            if full_name:
                user.full_name = full_name
            if status:
                user.status = status
            if picture_file:
                # Delete old picture if exists
                if user.picture_filename:
                    old_path = os.path.join(self.upload_folder, user.picture_filename)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                user.picture_filename = self.save_picture(picture_file)
            
            user.updated_at = datetime.now()
            db.session.commit()
            return True, "User updated successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Database error: {str(e)}"
    
    def delete_user(self, qr_code_id):
        """Delete a user"""
        user = self.get_user_by_qr(qr_code_id)
        if not user:
            return False, "User not found"
        
        try:
            # Delete picture file if exists
            if user.picture_filename:
                picture_path = os.path.join(self.upload_folder, user.picture_filename)
                if os.path.exists(picture_path):
                    os.remove(picture_path)
            
            db.session.delete(user)
            db.session.commit()
            return True, "User deleted successfully"
        except Exception as e:
            db.session.rollback()
            return False, f"Database error: {str(e)}"
    
    def change_user_status(self, qr_code_id, status):
        """Change user status"""
        return self.update_user(qr_code_id, status=status)
    
    def process_access_attempt(self, qr_code_id, method="QR", visit_reason=None):
        """Process access attempt and log activity"""
        qr_code_id = qr_code_id.upper()
        user = self.get_user_by_qr(qr_code_id)
        
        if not user:
            self._log_activity(None, qr_code_id, "Unknown", "access_denied", method, "User not found", visit_reason=visit_reason)
            return False, "Access Denied: Invalid QR Code", None
        
        if user.status != 'allowed':
            self._log_activity(user.id, qr_code_id, user.full_name, "access_denied", method, f"User status: {user.status}", visit_reason=visit_reason, user_role=user.role)
            return False, f"Access Denied: User is {user.status}", user
        
        # Determine action based on current check-in status
        action = "check_out" if user.is_checked_in else "check_in"
        
        # Update check-in status
        user.is_checked_in = not user.is_checked_in
        
        try:
            db.session.commit()
            # Log the activity
            self._log_activity(user.id, qr_code_id, user.full_name, action, method, "Success", visit_reason=visit_reason, user_role=user.role)
            
            action_text = action.replace('_', ' ').title()
            return True, f"Access Granted: {action_text} successful for {user.full_name}", user
        except Exception as e:
            db.session.rollback()
            return False, f"Database error: {str(e)}", user
    
    def _log_activity(self, user_id, qr_code_id, user_name, action, method, details, visit_reason=None, user_role=None):
        """Log activity to the database"""
        activity = ActivityLog(
            security_user_id=user_id,
            qr_code_id=qr_code_id,
            user_name=user_name,
            action=action,
            method=method,
            details=details,
            visit_reason=visit_reason,
            user_role=user_role
        )
        
        try:
            db.session.add(activity)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Failed to log activity: {str(e)}")
    
    def get_activity_log(self, limit=None):
        """Get activity log sorted by timestamp (most recent first)"""
        query = ActivityLog.query.order_by(ActivityLog.timestamp.desc())
        if limit:
            return query.limit(limit).all()
        return query.all()
    
    def search_users(self, query):
        """Search users by name or QR code ID"""
        if not query:
            return self.get_all_users()
        
        search_term = f"%{query.lower()}%"
        return SecurityUser.query.filter(
            db.or_(
                SecurityUser.full_name.ilike(search_term),
                SecurityUser.qr_code_id.ilike(search_term)
            )
        ).all()
    
    def search_activity(self, query=None, start_date=None, end_date=None):
        """Search activity log with filters"""
        query_obj = ActivityLog.query
        
        if query:
            search_term = f"%{query.lower()}%"
            query_obj = query_obj.filter(
                db.or_(
                    ActivityLog.user_name.ilike(search_term),
                    ActivityLog.qr_code_id.ilike(search_term)
                )
            )
        
        if start_date:
            query_obj = query_obj.filter(ActivityLog.timestamp >= start_date)
        
        if end_date:
            # Add one day to include the end date
            end_date_plus_one = datetime.combine(end_date, datetime.max.time())
            query_obj = query_obj.filter(ActivityLog.timestamp <= end_date_plus_one)
        
        return query_obj.order_by(ActivityLog.timestamp.desc()).all()
    
    def get_statistics(self):
        """Get system statistics"""
        total_users = SecurityUser.query.count()
        allowed_users = SecurityUser.query.filter_by(status='allowed').count()
        banned_users = SecurityUser.query.filter_by(status='banned').count()
        checked_in_users = SecurityUser.query.filter_by(is_checked_in=True).count()
        
        return {
            'total_users': total_users,
            'allowed_users': allowed_users,
            'banned_users': banned_users,
            'checked_in_users': checked_in_users
        }

# Global service instance
security_service = SecurityService()