from flask import render_template, request, redirect, url_for, flash, make_response, session, jsonify
from flask_login import current_user
from datetime import datetime
import logging
import csv
import io

from app import app, db
from replit_auth import require_login, make_replit_blueprint
from security_service import security_service

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
    users = security_service.get_all_users()
    recent_activity = security_service.get_activity_log(limit=10)
    stats = security_service.get_statistics()
    
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
    picture_file = request.files.get('picture')
    
    if not full_name or not qr_code_id:
        flash('Full name and QR Code ID are required', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    success, message = security_service.add_user(full_name, qr_code_id, status, picture_file)
    
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
    picture_file = request.files.get('picture')
    
    if not full_name:
        flash('Full name is required', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    success, message = security_service.update_user(qr_code_id, full_name=full_name, status=status, picture_file=picture_file)
    
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
    success, message = security_service.delete_user(qr_code_id)
    
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
    
    success, message = security_service.change_user_status(qr_code_id, status)
    
    if success:
        flash(f'User status changed to {status}', 'success')
        logging.info(f"User status changed: {qr_code_id} -> {status} by admin {current_user.email}")
    else:
        flash(message, 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/access', methods=['GET', 'POST'])
def access_control():
    """Access control page - QR code scanning"""
    if request.method == 'POST':
        qr_code_id = request.form.get('qr_code_id', '').strip()
        
        if not qr_code_id:
            flash('Please enter a QR Code ID', 'warning')
            return render_template('access_control.html', user=current_user)
        
        success, message, user_data = security_service.process_access_attempt(qr_code_id)
        
        if success:
            flash(message, 'success')
            logging.info(f"Access granted: {qr_code_id}")
        else:
            flash(message, 'danger')
            logging.warning(f"Access denied: {qr_code_id} - {message}")
        
        # Return user data for display
        return render_template('access_control.html', user=current_user, scanned_user=user_data)
    
    return render_template('access_control.html', user=current_user)

@app.route('/api/process_qr', methods=['POST'])
def api_process_qr():
    """API endpoint for QR code processing"""
    data = request.get_json()
    qr_code_id = data.get('qr_code_id', '').strip()
    
    if not qr_code_id:
        return jsonify({'success': False, 'message': 'QR Code ID is required'}), 400
    
    success, message, user_data = security_service.process_access_attempt(qr_code_id, method="Camera")
    
    response_data = {
        'success': success,
        'message': message,
        'user': None
    }
    
    if user_data:
        response_data['user'] = {
            'full_name': user_data.full_name,
            'qr_code_id': user_data.qr_code_id,
            'status': user_data.status,
            'is_checked_in': user_data.is_checked_in,
            'picture_url': f"/static/uploads/{user_data.picture_filename}" if user_data.picture_filename else None,
            'qr_code_url': f"/static/qr_codes/{user_data.qr_code_filename}" if user_data.qr_code_filename else None
        }
    
    return jsonify(response_data)

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
    
    activities = security_service.search_activity(query, start_date, end_date)
    
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
    
    activities = security_service.search_activity(query, start_date, end_date)
    
    # Generate CSV data
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Timestamp', 'User Name', 'QR Code ID', 'Action', 'Method', 'Details'])
    
    for activity in activities:
        writer.writerow([
            activity.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            activity.user_name,
            activity.qr_code_id,
            activity.action.replace('_', ' ').title(),
            activity.method,
            activity.details
        ])
    
    csv_data = output.getvalue()
    
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
    users = security_service.search_users(query)
    recent_activity = security_service.get_activity_log(limit=10)
    stats = security_service.get_statistics()
    return render_template('admin_dashboard.html', 
                          user=current_user, 
                          users=users, 
                          recent_activity=recent_activity,
                          stats=stats,
                          search_query=query)

@app.route('/admin/download_csv_template')
@require_login
def download_csv_template():
    """Download CSV template for bulk user import"""
    template_data = "no,date_registered,last_name,first_name,middle_name,role,company,address,contact_number,complete_name,id_number,barcode,status\n"
    template_data += "1,2024-01-15,Doe,John,A,Manager,ABC Corp,123 Main St,555-0001,John A Doe,ID123456,USER001,Active\n"
    template_data += "2,2024-01-16,Smith,Jane,B,Developer,ABC Corp,456 Oak St,555-0003,Jane B Smith,ID234567,USER002,Active\n"
    template_data += "3,2024-01-17,Johnson,Bob,,Security,ABC Corp,789 Pine St,555-0005,Bob Johnson,ID345678,USER003,Inactive\n"
    
    response = make_response(template_data)
    response.headers['Content-Disposition'] = 'attachment; filename=user_import_template.csv'
    response.headers['Content-Type'] = 'text/csv'
    
    logging.info(f"CSV template downloaded by admin {current_user.email}")
    return response

@app.route('/admin/analyze_csv', methods=['POST'])
@require_login
def analyze_csv():
    """Analyze CSV file before import"""
    csv_file = request.files.get('csv_file')
    
    if not csv_file or not csv_file.filename.endswith('.csv'):
        return jsonify({'success': False, 'message': 'Please upload a valid CSV file'}), 400
    
    try:
        result = security_service.analyze_csv(csv_file)
        return jsonify(result)
    except Exception as e:
        logging.error(f"CSV analysis error: {str(e)}")
        return jsonify({'success': False, 'message': 'Error analyzing CSV file'}), 500

@app.route('/admin/import_csv', methods=['POST'])
@require_login
def import_csv():
    """Import users from CSV file"""
    csv_file = request.files.get('csv_file')
    
    if not csv_file or not csv_file.filename.endswith('.csv'):
        return jsonify({'success': False, 'message': 'Please upload a valid CSV file'}), 400
    
    try:
        result = security_service.import_csv(csv_file)
        
        if result['success']:
            logging.info(f"CSV import: {result['imported_count']} users imported by admin {current_user.email}")
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"CSV import error: {str(e)}")
        return jsonify({'success': False, 'message': 'Error importing CSV file'}), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('403.html', error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    logging.error(f"Internal server error: {error}")
    return render_template('403.html', error_message="Internal server error"), 500
