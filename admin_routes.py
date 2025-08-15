
from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user
from app import app, db
from auth import require_super_admin, require_admin
from models import AdminUser
import logging

@app.route('/admin/manage_admins')
@require_super_admin
def manage_admins():
    """Admin management page for super admins"""
    admins = AdminUser.query.order_by(AdminUser.created_at.desc()).all()
    return render_template('manage_admins.html', user=current_user, admins=admins)

@app.route('/admin/create_admin', methods=['POST'])
@require_super_admin
def create_admin():
    """Create a new admin user"""
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    role = request.form.get('role', 'guard')
    password = request.form.get('password', '').strip()
    
    if not username or not password or not first_name or not last_name:
        flash('Username, password, first name, and last name are required', 'danger')
        return redirect(url_for('manage_admins'))
    
    # Check if username already exists
    existing_user = AdminUser.query.filter_by(username=username).first()
    if existing_user:
        flash('Username already exists', 'danger')
        return redirect(url_for('manage_admins'))
    
    # Validate role
    if role not in ['super_admin', 'admin', 'guard']:
        flash('Invalid role selected', 'danger')
        return redirect(url_for('manage_admins'))
    
    try:
        new_admin = AdminUser(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            created_by=current_user.id
        )
        new_admin.set_password(password)
        
        db.session.add(new_admin)
        db.session.commit()
        
        flash(f'{role.replace("_", " ").title()} user "{username}" created successfully', 'success')
        logging.info(f"Admin user created: {username} ({role}) by {current_user.username}")
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating user: {str(e)}', 'danger')
        logging.error(f"Error creating admin user: {str(e)}")
    
    return redirect(url_for('manage_admins'))

@app.route('/admin/update_admin/<int:admin_id>', methods=['POST'])
@require_super_admin
def update_admin(admin_id):
    """Update admin user"""
    admin_user = AdminUser.query.get_or_404(admin_id)
    
    # Prevent super admin from modifying themselves if it's the only super admin
    if admin_user.id == current_user.id:
        super_admin_count = AdminUser.query.filter_by(role='super_admin').count()
        if super_admin_count == 1:
            flash('Cannot modify the only super admin account', 'danger')
            return redirect(url_for('manage_admins'))
    
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip()
    role = request.form.get('role', admin_user.role)
    active = request.form.get('active') == 'on'
    
    if not first_name or not last_name:
        flash('First name and last name are required', 'danger')
        return redirect(url_for('manage_admins'))
    
    try:
        admin_user.first_name = first_name
        admin_user.last_name = last_name
        admin_user.email = email
        admin_user.role = role
        admin_user.active = active
        
        db.session.commit()
        flash(f'User "{admin_user.username}" updated successfully', 'success')
        logging.info(f"Admin user updated: {admin_user.username} by {current_user.username}")
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating user: {str(e)}', 'danger')
        logging.error(f"Error updating admin user: {str(e)}")
    
    return redirect(url_for('manage_admins'))

@app.route('/admin/delete_admin/<int:admin_id>')
@require_super_admin
def delete_admin(admin_id):
    """Delete admin user"""
    admin_user = AdminUser.query.get_or_404(admin_id)
    
    # Prevent deletion of the only super admin
    if admin_user.role == 'super_admin':
        super_admin_count = AdminUser.query.filter_by(role='super_admin').count()
        if super_admin_count == 1:
            flash('Cannot delete the only super admin account', 'danger')
            return redirect(url_for('manage_admins'))
    
    # Prevent self-deletion
    if admin_user.id == current_user.id:
        flash('Cannot delete your own account', 'danger')
        return redirect(url_for('manage_admins'))
    
    try:
        username = admin_user.username
        db.session.delete(admin_user)
        db.session.commit()
        flash(f'User "{username}" deleted successfully', 'success')
        logging.info(f"Admin user deleted: {username} by {current_user.username}")
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'danger')
        logging.error(f"Error deleting admin user: {str(e)}")
    
    return redirect(url_for('manage_admins'))

@app.route('/admin/reset_password/<int:admin_id>', methods=['POST'])
@require_super_admin
def reset_admin_password(admin_id):
    """Reset admin user password"""
    admin_user = AdminUser.query.get_or_404(admin_id)
    new_password = request.form.get('new_password', '').strip()
    
    if not new_password or len(new_password) < 6:
        flash('Password must be at least 6 characters long', 'danger')
        return redirect(url_for('manage_admins'))
    
    try:
        admin_user.set_password(new_password)
        db.session.commit()
        flash(f'Password reset for "{admin_user.username}"', 'success')
        logging.info(f"Password reset for admin user: {admin_user.username} by {current_user.username}")
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error resetting password: {str(e)}', 'danger')
        logging.error(f"Error resetting admin password: {str(e)}")
    
    return redirect(url_for('manage_admins'))
