import frappe
import requests
from ..models.user_management import UserManagementModel
from ..models.site_model import SiteModel
from ..models.email_model import EmailModel

class UserService:
    """Service layer for User operations"""
    
    @staticmethod
    def validate_user_data(data, required_fields):
        """Validate user input data"""
        missing = [f for f in required_fields if not data.get(f)]
        if missing:
            return {
                "valid": False,
                "message": f"Missing required fields: {', '.join(missing)}"
            }
        return {"valid": True}
    
    @staticmethod
    def check_existing_user(email):
        """Check if user already exists"""
        existing_user = UserManagementModel.get_user_by_email(email, include_unverified=True)
        if existing_user:
            is_verified = existing_user.get("is_verified", 0)
            return {
                "exists": True,
                "is_verified": is_verified,
                "user": existing_user
            }
        return {"exists": False}
    
    @staticmethod
    def register_new_user(user_data):
        """Register a new user"""
        # Get available site
        free_site = SiteModel.get_oldest_unassigned_site()
        if not free_site:
            return {
                "status": "error",
                "message": "No sites available. Please contact administrator.",
                "code": "NO_SITES_AVAILABLE"
            }
        
        # Create admin user on client site
        create_response = UserService.create_admin_user_on_site(
            base_url=free_site["site_url"],
            username=user_data.get("username"),
            email=user_data.get("email"),
            password=user_data.get("password"),
            company=user_data.get("company"),
            country=user_data.get("country", "Zimbabwe")
        )
        
        if create_response.get("status") != "success":
            return {
                "status": "error",
                "message": f"Failed to create user on site: {create_response.get('message')}"
            }
        
        # Generate verification token
        token, expiry_date = UserManagementModel.generate_verification_token()
        
        # Create user management record
        user_mgmt_data = {
            "user_email": user_data.get("email"),
            "company": user_data.get("company"),
            "site": free_site.get("site_registration"),
            "site_url": free_site.get("site_url"),
            "ip_address": free_site.get("ip_address"),
            "username": user_data.get("username"),
            "first_name": user_data.get("first_name"),
            "last_name": user_data.get("last_name"),
            "phone_number": user_data.get("phone_number"),
            "verification_token": token,
            "verification_token_expiry": expiry_date,
            "is_verified": 0,
            "created_at": frappe.utils.now()
        }
        
        user_mgmt = UserManagementModel.create_user(user_mgmt_data)
        
        # Mark site as assigned
        SiteModel.assign_site(free_site["name"])
        
        return {
            "status": "success",
            "user": user_mgmt,
            "site": free_site,
            "verification_token": token,
            "expiry_date": expiry_date
        }
    

    @staticmethod
    def create_admin_user_on_site(base_url, username, email, password, company, country):
        """Create admin user on client site with proper error handling"""
        try:
            url = f"{base_url}/api/method/sass_client.api.user.create_admin_user"
            
            payload = {
                "username": username,
                "email": email,
                "password": password,
                "company": company,
                "country": country
            }
            
            response = requests.post(url, json=payload, timeout=15)
            
            # FIX 1: Check if response has content
            if not response.text:
                return {
                    "status": "error", 
                    "message": f"Empty response from {base_url}. Site may not be ready."
                }
            
            # FIX 2: Try to parse JSON with error handling
            try:
                res = response.json()
            except Exception as json_error:
                frappe.log_error(f"JSON Parse Error: {str(json_error)}", "Create Admin User")
                frappe.log_error(f"Response text: {response.text[:500]}", "Create Admin User")
                return {
                    "status": "error",
                    "message": f"Invalid response from site (not JSON): {response.text[:100]}"
                }
            
            # FIX 3: Extract the inner message
            payload_result = res.get("message", {})
            
            if not payload_result:
                return {
                    "status": "error",
                    "message": f"Missing 'message' in response: {res}"
                }
            
            if payload_result.get("status") != "success":
                return {
                    "status": "error",
                    "message": payload_result.get("message", "Account creation failed")
                }
            
            return payload_result
            
        except requests.exceptions.Timeout:
            return {
                "status": "error", 
                "message": f"Request timed out to {base_url}"
            }
        except requests.exceptions.ConnectionError:
            return {
                "status": "error", 
                "message": f"Connection error: {base_url} is not reachable"
            }
        except Exception as e:
            frappe.log_error(frappe.get_traceback(), "Create Admin User Error")
            return {
                "status": "error", 
                "message": str(e)
            }
            
    @staticmethod
    def send_verification_email(email_data):
        """Send verification email with rollback support"""
        verification_link = f"{frappe.utils.get_url()}/api/method/saas_manager.api.verify_user_email?token={email_data['token']}&email={email_data['email']}"
        
        try:
            EmailModel.send_verification_email(
                recipient_email=email_data["email"],
                username=email_data["username"],
                verification_link=verification_link,
                expiry_days=7,
                company=email_data["company"],
                site_url=email_data["site_url"]
            )
            return {"status": "success"}
        except Exception as e:
            # Rollback: Delete user and unassign site
            UserManagementModel.delete_user(email_data["user_id"])
            SiteModel.unassign_site(email_data["site_docname"])
            frappe.db.commit()
            raise e