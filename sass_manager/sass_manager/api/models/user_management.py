import frappe
from frappe.utils import add_days, getdate, now_datetime

class UserManagementModel:
    """Model for User Management operations"""
    
    @staticmethod
    def get_user_by_email(email, include_unverified=False):
        """Get user by email"""
        filters = {"user_email": email}
        if not include_unverified:
            try:
                filters["is_verified"] = 1
            except:
                pass
        
        users = frappe.get_all(
            "User Management",
            filters=filters,
            fields=["name", "user_email", "username", "company", "site_url", 
                   "ip_address", "verification_token", "verification_token_expiry",
                   "is_verified", "created_at", "first_name", "last_name", "phone_number"],
            limit_page_length=1
        )
        return users[0] if users else None
    
    @staticmethod
    def get_unverified_user(email):
        """Get unverified user by email"""
        filters = {"user_email": email}
        try:
            filters["is_verified"] = 0
        except:
            pass
        
        users = frappe.get_all(
            "User Management",
            filters=filters,
            fields=["name", "username", "company", "site_url"],
            limit_page_length=1
        )
        return users[0] if users else None
    
    @staticmethod
    def create_user(user_data):
        """Create a new user management record"""
        user_mgmt = frappe.get_doc({
            "doctype": "User Management",
            **user_data
        })
        user_mgmt.flags.ignore_permissions = True
        user_mgmt.insert()
        return user_mgmt
    
    @staticmethod
    def update_user(user_id, update_data):
        """Update user record"""
        frappe.db.set_value("User Management", user_id, update_data)
        return True
    
    @staticmethod
    def delete_user(user_id):
        """Delete user record"""
        frappe.delete_doc("User Management", user_id, force=True)
        return True
    
    @staticmethod
    def verify_user(user_id):
        """Mark user as verified"""
        update_data = {
            "verification_token": None,
            "is_verified": 1,
            "verified_at": now_datetime()
        }
        return UserManagementModel.update_user(user_id, update_data)
    
    @staticmethod
    def generate_verification_token():
        """Generate verification token"""
        token = frappe.generate_hash(length=32)
        expiry_date = add_days(frappe.utils.today(), 7)
        return token, expiry_date
    
    @staticmethod
    def validate_verification_token(email, token):
        """Validate verification token"""
        user = UserManagementModel.get_user_by_email(email, include_unverified=True)
        
        if not user or user.get("verification_token") != token:
            return None
        
        # Check expiry
        expiry_date = user.get("verification_token_expiry")
        if expiry_date and getdate(expiry_date) < getdate(frappe.utils.today()):
            return None
        
        return user