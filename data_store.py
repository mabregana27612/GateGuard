from datetime import datetime
import uuid
import csv
import io

# In-memory storage for MVP instead of PostgreSQL
class SecurityDataStore:
    def __init__(self):
        self.users = {}  # qr_code_id -> user_data
        self.activity_log = []  # list of activity entries
        self._initialize_sample_users()
    
    def _initialize_sample_users(self):
        """Initialize with empty data store - no sample data"""
        pass
    
    def add_user(self, full_name, qr_code_id, status="allowed", picture_url=None):
        """Add a new user to the system"""
        if qr_code_id in self.users:
            return False, "QR Code ID already exists"
        
        user_data = {
            'id': str(uuid.uuid4()),
            'full_name': full_name,
            'qr_code_id': qr_code_id,
            'status': status,
            'picture_url': picture_url,
            'created_at': datetime.now(),
            'is_checked_in': False
        }
        
        self.users[qr_code_id] = user_data
        return True, "User added successfully"
    
    def get_user_by_qr(self, qr_code_id):
        """Get user by QR code ID"""
        return self.users.get(qr_code_id)
    
    def get_all_users(self):
        """Get all users"""
        return list(self.users.values())
    
    def update_user(self, qr_code_id, **kwargs):
        """Update user information"""
        if qr_code_id not in self.users:
            return False, "User not found"
        
        user = self.users[qr_code_id]
        for key, value in kwargs.items():
            if key in user:
                user[key] = value
        
        return True, "User updated successfully"
    
    def delete_user(self, qr_code_id):
        """Delete a user"""
        if qr_code_id not in self.users:
            return False, "User not found"
        
        del self.users[qr_code_id]
        return True, "User deleted successfully"
    
    def change_user_status(self, qr_code_id, status):
        """Change user status (allowed/banned)"""
        return self.update_user(qr_code_id, status=status)
    
    def process_access_attempt(self, qr_code_id, method="QR"):
        """Process access attempt and log activity"""
        user = self.get_user_by_qr(qr_code_id)
        
        if not user:
            self._log_activity(None, qr_code_id, "access_denied", method, "User not found")
            return False, "Access Denied: Invalid QR Code"
        
        if user['status'] != 'allowed':
            self._log_activity(user['id'], qr_code_id, "access_denied", method, f"User status: {user['status']}")
            return False, f"Access Denied: User is {user['status']}"
        
        # Determine action based on current check-in status
        action = "check_out" if user['is_checked_in'] else "check_in"
        
        # Update check-in status
        user['is_checked_in'] = not user['is_checked_in']
        
        # Log the activity
        self._log_activity(user['id'], qr_code_id, action, method, "Success")
        
        return True, f"Access Granted: {action.replace('_', ' ').title()} successful for {user['full_name']}"
    
    def _log_activity(self, user_id, qr_code_id, action, method, details):
        """Log activity to the activity log"""
        activity = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'qr_code_id': qr_code_id,
            'user_name': self.users.get(qr_code_id, {}).get('full_name', 'Unknown'),
            'action': action,
            'method': method,
            'details': details,
            'timestamp': datetime.now()
        }
        self.activity_log.append(activity)
    
    def get_activity_log(self, limit=None):
        """Get activity log sorted by timestamp (most recent first)"""
        sorted_log = sorted(self.activity_log, key=lambda x: x['timestamp'], reverse=True)
        if limit:
            return sorted_log[:limit]
        return sorted_log
    
    def search_users(self, query):
        """Search users by name or QR code ID"""
        if not query:
            return self.get_all_users()
        
        query = query.lower()
        results = []
        
        for user in self.users.values():
            if (query in user['full_name'].lower() or 
                query in user['qr_code_id'].lower()):
                results.append(user)
        
        return results
    
    def search_activity(self, query=None, start_date=None, end_date=None):
        """Search activity log with filters"""
        activities = self.get_activity_log()
        
        if query:
            query = query.lower()
            activities = [a for a in activities 
                         if query in a['user_name'].lower() or 
                         query in a['qr_code_id'].lower()]
        
        if start_date:
            activities = [a for a in activities if a['timestamp'].date() >= start_date]
        
        if end_date:
            activities = [a for a in activities if a['timestamp'].date() <= end_date]
        
        return activities
    
    def export_activity_to_csv(self, activities=None):
        """Export activity log to CSV format"""
        if activities is None:
            activities = self.get_activity_log()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Timestamp', 'User Name', 'QR Code ID', 'Action', 'Method', 'Details'])
        
        # Write data
        for activity in activities:
            writer.writerow([
                activity['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                activity['user_name'],
                activity['qr_code_id'],
                activity['action'].replace('_', ' ').title(),
                activity['method'],
                activity['details']
            ])
        
        return output.getvalue()

# Global data store instance
security_store = SecurityDataStore()
