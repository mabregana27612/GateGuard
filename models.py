from datetime import datetime
import uuid
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Admin User Model for simple authentication
class AdminUser(UserMixin, db.Model):
    __tablename__ = 'admin_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    first_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Security Access Control Models
class SecurityUser(db.Model):
    __tablename__ = 'security_users'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Excel fields - matching exactly
    no = db.Column(db.Integer, nullable=True)  # Sequential number
    date_registered = db.Column(db.Date, default=datetime.now().date)
    last_name = db.Column(db.String, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    middle_name = db.Column(db.String, nullable=True)
    role = db.Column(db.String, nullable=True)  # Position/Role
    company = db.Column(db.String, nullable=True)
    address = db.Column(db.Text, nullable=True)
    contact_number = db.Column(db.String, nullable=True)
    complete_name = db.Column(db.String, nullable=False)  # Full name
    id_number = db.Column(db.String, nullable=True)
    barcode = db.Column(db.String, unique=True, nullable=False)  # QR Code ID
    status = db.Column(db.String, default='Active')  # Active, Inactive, etc.
    
    # Legacy fields for backward compatibility (will be auto-populated)
    full_name = db.Column(db.String, nullable=True)  # Maps to complete_name
    qr_code_id = db.Column(db.String, nullable=True)  # Maps to barcode
    
    # System fields
    picture_filename = db.Column(db.String, nullable=True)
    qr_code_filename = db.Column(db.String, nullable=True)
    biometric_template = db.Column(db.Text, nullable=True)  # For future face recognition
    is_checked_in = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    security_user_id = db.Column(db.String, db.ForeignKey('security_users.id'), nullable=True)
    qr_code_id = db.Column(db.String, nullable=False)
    user_name = db.Column(db.String, nullable=False)
    action = db.Column(db.String, nullable=False)  # check_in, check_out, access_denied
    method = db.Column(db.String, default='QR')  # QR, Face, Manual
    details = db.Column(db.String, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    
    security_user = db.relationship('SecurityUser', backref='activity_logs')
