from flask import render_template, request, redirect, url_for, flash, make_response, session, send_file, jsonify
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
import logging
import os
import uuid
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
import qrcode
from PIL import Image
import io
import base64

from app import app, db
from replit_auth import require_login, make_replit_blueprint
from data_store import security_store
from models import ClientUser

# Register Replit Auth blueprint
app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    """Landing page with appropriate redirects based on user type"""
    if current_user.is_authenticated:
        # Check if it's a client user (has username attribute)
        if hasattr(current_user, 'username'):
            return redirect(url_for('client_profile'))
        else:
            # Admin user - redirect to admin dashboard
            return redirect(url_for('admin_dashboard'))
    return render_template('index.html')

@app.route('/admin')
@require_login
def admin_dashboard():
    """Admin dashboard for user management"""
    users = security_store.get_all_users()
    recent_activity = security_store.get_activity_log(limit=10)
    
    # Calculate stats
    total_users = len(users)
    allowed_users = len([u for u in users if u['status'] == 'allowed'])
    banned_users = len([u for u in users if u['status'] == 'banned'])
    checked_in_users = len([u for u in users if u.get('is_checked_in', False)])
    
    stats = {
        'total_users': total_users,
        'allowed_users': allowed_users,
        'banned_users': banned_users,
        'checked_in_users': checked_in_users
    }
    
    return render_template('admin_dashboard.html', 
                          user=current_user, 
                          users=users, 
                          recent_activity=recent_activity,
                          stats=stats)

@app.route('/admin/add_user', methods=['POST'])
@require_login
def add_user():
    """Add a new user"""
    full_name = request.form.get('full_name', '').strip()
    qr_code_id = request.form.get('qr_code_id', '').strip()
    status = request.form.get('status', 'allowed')
    
    if not full_name or not qr_code_id:
        flash('Full name and QR Code ID are required', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    success, message = security_store.add_user(full_name, qr_code_id, status)
    
    if success:
        flash(message, 'success')
        logging.info(f"User added: {full_name} ({qr_code_id}) by admin {current_user.email}")
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/update_user/<qr_code_id>', methods=['POST'])
@require_login
def update_user(qr_code_id):
    """Update user information"""
    full_name = request.form.get('full_name', '').strip()
    status = request.form.get('status', 'allowed')
    
    if not full_name:
        flash('Full name is required', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    success, message = security_store.update_user(qr_code_id, full_name=full_name, status=status)
    
    if success:
        flash(message, 'success')
        logging.info(f"User updated: {qr_code_id} by admin {current_user.email}")
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_user/<qr_code_id>')
@require_login
def delete_user(qr_code_id):
    """Delete a user"""
    success, message = security_store.delete_user(qr_code_id)
    
    if success:
        flash(message, 'success')
        logging.info(f"User deleted: {qr_code_id} by admin {current_user.email}")
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/change_status/<qr_code_id>/<status>')
@require_login
def change_user_status(qr_code_id, status):
    """Change user status"""
    if status not in ['allowed', 'banned']:
        flash('Invalid status', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    success, message = security_store.change_user_status(qr_code_id, status)
    
    if success:
        flash(f'User status changed to {status}', 'success')
        logging.info(f"User status changed: {qr_code_id} -> {status} by admin {current_user.email}")
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/access', methods=['GET', 'POST'])
def access_control():
    """Access control page - QR code scanning for both admin and client users"""
    if request.method == 'POST':
        qr_code_id = request.form.get('qr_code_id', '').strip().upper()
        
        if not qr_code_id:
            flash('Please enter a QR Code ID', 'warning')
            return render_template('access_control.html', user=current_user)
        
        # First check in security store (existing system)
        success, message = security_store.process_access_attempt(qr_code_id)
        
        if success:
            flash(message, 'success')
            logging.info(f"Access granted: {qr_code_id}")
            return render_template('access_control.html', user=current_user)
        
        # If not found in security store, check client users
        client_user = ClientUser.query.filter_by(qr_code_id=qr_code_id).first()
        
        if client_user:
            if client_user.status != 'allowed':
                flash(f'Access Denied: User is {client_user.status}', 'danger')
                logging.warning(f"Access denied: {qr_code_id} - User status: {client_user.status}")
                return render_template('access_control.html', user=current_user)
            
            # Toggle check-in status
            action = "check_out" if client_user.is_checked_in else "check_in"
            client_user.is_checked_in = not client_user.is_checked_in
            
            try:
                db.session.commit()
                flash(f'Access Granted: {action.replace("_", " ").title()} successful for {client_user.full_name}', 'success')
                logging.info(f"Access granted: {qr_code_id} - {action} for {client_user.full_name}")
            except Exception as e:
                db.session.rollback()
                logging.error(f"Database error during access control: {e}")
                flash('System error during access verification', 'danger')
        else:
            flash('Access Denied: Invalid QR Code', 'danger')
            logging.warning(f"Access denied: {qr_code_id} - Invalid QR Code")
    
    return render_template('access_control.html', user=current_user)

@app.route('/reports')
@require_login
def reports():
    """Reports page for admin"""
    query = request.args.get('query', '').strip()
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid start date format', 'warning')
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid end date format', 'warning')
    
    activities = security_store.search_activity(query, start_date, end_date)
    
    return render_template('reports.html', 
                          user=current_user, 
                          activities=activities,
                          query=query,
                          start_date=start_date_str,
                          end_date=end_date_str)

@app.route('/reports/export')
@require_login
def export_reports():
    """Export activity reports to CSV"""
    query = request.args.get('query', '').strip()
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    activities = security_store.search_activity(query, start_date, end_date)
    csv_data = security_store.export_activity_to_csv(activities)
    
    response = make_response(csv_data)
    response.headers['Content-Disposition'] = f'attachment; filename=activity_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response.headers['Content-Type'] = 'text/csv'
    
    logging.info(f"Activity report exported by admin {current_user.email}")
    return response

@app.route('/search_users')
@require_login
def search_users():
    """Search users API endpoint"""
    query = request.args.get('q', '').strip()
    users = security_store.search_users(query)
    return render_template('admin_dashboard.html', 
                          user=current_user, 
                          users=users, 
                          search_query=query)

@app.errorhandler(404)
def not_found(error):
    return render_template('403.html', error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"Internal server error: {error}")
    return render_template('403.html', error_message="Internal server error"), 500

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Client User Registration and Authentication Routes

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        
        # Validation
        if not all([username, email, password, confirm_password, full_name]):
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'danger')
            return render_template('register.html')
        
        # Check if username or email already exists
        if ClientUser.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return render_template('register.html')
        
        if ClientUser.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return render_template('register.html')
        
        # Create new user
        new_user = ClientUser(
            username=username,
            email=email,
            full_name=full_name
        )
        new_user.set_password(password)
        new_user.generate_qr_code_id()
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login to continue.', 'success')
            return redirect(url_for('client_login'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Registration error: {e}")
            flash('Registration failed. Please try again.', 'danger')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def client_login():
    """Client user login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username and password are required', 'danger')
            return render_template('client_login.html')
        
        # Find user by username or email
        user = ClientUser.query.filter(
            (ClientUser.username == username) | (ClientUser.email == username)
        ).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated', 'danger')
                return render_template('client_login.html')
            
            login_user(user)
            flash(f'Welcome back, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('client_profile'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('client_login.html')

@app.route('/client_logout')
@login_required
def client_logout():
    """Client user logout"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def client_profile():
    """Client user profile page"""
    if hasattr(current_user, 'username'):  # Check if it's a ClientUser
        return render_template('client_profile.html', user=current_user)
    else:
        # Redirect admin users to admin dashboard
        return redirect(url_for('admin_dashboard'))

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit client user profile"""
    if not hasattr(current_user, 'username'):
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        
        if not full_name or not email:
            flash('Full name and email are required', 'danger')
            return render_template('edit_profile.html', user=current_user)
        
        # Check if email is already taken by another user
        existing_user = ClientUser.query.filter(
            ClientUser.email == email,
            ClientUser.id != current_user.id
        ).first()
        
        if existing_user:
            flash('Email already in use by another account', 'danger')
            return render_template('edit_profile.html', user=current_user)
        
        # Handle file upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Make filename unique
                filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}_{filename}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                current_user.profile_picture = f"uploads/{filename}"
        
        # Update user info
        current_user.full_name = full_name
        current_user.email = email
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('client_profile'))
        except Exception as e:
            db.session.rollback()
            logging.error(f"Profile update error: {e}")
            flash('Failed to update profile', 'danger')
    
    return render_template('edit_profile.html', user=current_user)

@app.route('/my_qr_code')
@login_required
def my_qr_code():
    """Generate and display user's QR code"""
    if not hasattr(current_user, 'username'):
        return redirect(url_for('admin_dashboard'))
    
    return render_template('my_qr_code.html', user=current_user)

@app.route('/qr_code_image')
@login_required
def qr_code_image():
    """Generate QR code image"""
    if not hasattr(current_user, 'username'):
        return redirect(url_for('admin_dashboard'))
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(current_user.qr_code_id)
    qr.make(fit=True)
    
    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # If user has profile picture, try to add it to center
    if current_user.profile_picture:
        try:
            profile_path = os.path.join('static', current_user.profile_picture)
            if os.path.exists(profile_path):
                # Open and resize profile image
                profile_img = Image.open(profile_path)
                
                # Calculate size for center logo (about 1/5 of QR code)
                qr_width, qr_height = qr_img.size
                logo_size = qr_width // 5
                
                # Resize profile image
                profile_img = profile_img.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                
                # Create a white background circle for the profile image
                mask = Image.new('RGBA', (logo_size, logo_size), (255, 255, 255, 255))
                
                # Paste profile image in center of QR code
                pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
                qr_img.paste(mask, pos)
                qr_img.paste(profile_img, pos)
        except Exception as e:
            logging.error(f"Error adding profile image to QR code: {e}")
    
    # Save to bytes
    img_buffer = io.BytesIO()
    qr_img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    return send_file(img_buffer, mimetype='image/png', as_attachment=False)


