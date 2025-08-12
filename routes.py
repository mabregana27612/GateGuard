from flask import render_template, request, redirect, url_for, flash, make_response, session
from flask_login import current_user
from datetime import datetime
import logging

from app import app, db
from replit_auth import require_login, make_replit_blueprint
from data_store import security_store

# Register Replit Auth blueprint
app.register_blueprint(make_replit_blueprint(), url_prefix="/auth")

# Make session permanent
@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    """Landing page for logged out users, access control for logged in users"""
    if current_user.is_authenticated:
        return render_template('access_control.html', user=current_user)
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
    """Access control page - QR code scanning simulation"""
    if request.method == 'POST':
        qr_code_id = request.form.get('qr_code_id', '').strip()
        
        if not qr_code_id:
            flash('Please enter a QR Code ID', 'warning')
            return render_template('access_control.html', user=current_user)
        
        success, message = security_store.process_access_attempt(qr_code_id)
        
        if success:
            flash(message, 'success')
            logging.info(f"Access granted: {qr_code_id}")
        else:
            flash(message, 'danger')
            logging.warning(f"Access denied: {qr_code_id} - {message}")
    
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
