from datetime import datetime
import uuid
from app import db
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin
from flask_login import UserMixin
from sqlalchemy import UniqueConstraint

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True)
    email = db.Column(db.String, unique=True, nullable=True)
    first_name = db.Column(db.String, nullable=True)
    last_name = db.Column(db.String, nullable=True)
    profile_image_url = db.Column(db.String, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime,
                           default=datetime.now,
                           onupdate=datetime.now)

# (IMPORTANT) This table is mandatory for Replit Auth, don't drop it.
class OAuth(OAuthConsumerMixin, db.Model):
    user_id = db.Column(db.String, db.ForeignKey(User.id))
    browser_session_key = db.Column(db.String, nullable=False)
    user = db.relationship(User)

    __table_args__ = (UniqueConstraint(
        'user_id',
        'browser_session_key',
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

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
