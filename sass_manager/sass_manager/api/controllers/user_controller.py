import frappe
import json
from ..services.user_service import UserService
from ..models.user_management import UserManagementModel
from ..models.email_model import EmailModel

@frappe.whitelist(allow_guest=True)
def register_user_with_site():
    """Complete user registration with auto-site assignment"""
    site_docname = None
    
    try:
        # Get data from request
        data = frappe.local.form_dict
        if not data:
            data = json.loads(frappe.request.data or "{}")
        
        # Validate required fields
        required_fields = ["email", "username", "password", "first_name", "company"]
        validation = UserService.validate_user_data(data, required_fields)
        if not validation["valid"]:
            return create_error_response(400, validation["message"])
        
        # Check existing user
        existing = UserService.check_existing_user(data.get("email"))
        if existing["exists"]:
            if existing["is_verified"]:
                return create_error_response(409, "User already registered and verified", {
                    "site_url": existing["user"].get("site_url")
                })
            else:
                return resend_verification_link()
        
        # Register new user
        registration_result = UserService.register_new_user(data)
        if registration_result["status"] == "error":
            return create_error_response(503, registration_result["message"])
        
        # Send verification email
        email_data = {
            "email": data.get("email"),
            "username": data.get("username"),
            "token": registration_result["verification_token"],
            "company": data.get("company"),
            "site_url": registration_result["site"]["site_url"],
            "user_id": registration_result["user"].name,
            "site_docname": registration_result["site"]["name"]
        }
        
        email_result = UserService.send_verification_email(email_data)
        
        frappe.db.commit()
        
        return create_success_response("User registered successfully! Please verify your email.", {
            "user": {
                "email": data.get("email"),
                "username": data.get("username"),
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name"),
                "company": data.get("company"),
                "phone_number": data.get("phone_number")
            },
            "site": {
                "url": registration_result["site"]["site_url"],
                "ip_address": registration_result["site"]["ip_address"],
                "registration_id": registration_result["site"]["site_registration"]
            },
            "verification": {
                "sent_to": data.get("email"),
                "expires_in_days": 7,
                "expiry_date": str(registration_result["expiry_date"])
            }
        })
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "User Registration Error")
        return create_error_response(500, str(e))


@frappe.whitelist(allow_guest=True)
def verify_user_email():
    """Verify user's email address using token"""
    try:
        token = frappe.form_dict.get("token")
        email = frappe.form_dict.get("email")
        
        if not token or not email:
            return create_error_response(400, "Token and email are required")
        
        # Validate token
        user = UserManagementModel.validate_verification_token(email, token)
        if not user:
            return create_error_response(404, "Invalid or expired verification link")
        
        # Mark user as verified
        UserManagementModel.verify_user(user["name"])
        frappe.db.commit()
        
        return create_success_response("Email verified successfully! Your account is now active.", {
            "email": email,
            "username": user.get("username"),
            "site_url": user.get("site_url"),
            "company": user.get("company"),
            "verified": True
        })
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Email Verification Error")
        return create_error_response(500, str(e))


@frappe.whitelist(allow_guest=True)
def resend_verification_link():
    """Resend verification link to user"""
    try:
        email = frappe.form_dict.get("email")
        
        if not email:
            return create_error_response(400, "Email is required")
        
        # Get unverified user
        user = UserManagementModel.get_unverified_user(email)
        if not user:
            return create_error_response(404, "User not found or already verified")
        
        # Generate new token
        token, expiry_date = UserManagementModel.generate_verification_token()
        
        # Update user record
        UserManagementModel.update_user(user["name"], {
            "verification_token": token,
            "verification_token_expiry": expiry_date
        })
        
        # Send new verification email
        verification_link = f"{frappe.utils.get_url()}/api/method/sass_manager.api.verify_user_email?token={token}&email={email}"
        
        EmailModel.send_verification_email(
            recipient_email=email,
            username=user.get("username"),
            verification_link=verification_link,
            expiry_days=7,
            company=user.get("company"),
            site_url=user.get("site_url")
        )
        
        frappe.db.commit()
        
        return create_success_response(f"Verification link sent to {email}", {
            "email": email,
            "expires_in_days": 7,
            "expiry_date": str(expiry_date)
        })
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Resend Verification Error")
        return create_error_response(500, str(e))


@frappe.whitelist(allow_guest=True)
def get_user_account_status():
    """Check if user has an account and get status"""
    try:
        email = frappe.form_dict.get("email")
        
        if not email:
            return create_error_response(400, "Email is required")
        
        user = UserManagementModel.get_user_by_email(email, include_unverified=True)
        
        if not user:
            return create_success_response("No account found", {
                "has_account": False,
                "can_register": True
            })
        
        is_verified = user.get("is_verified", 0)
        
        return create_success_response("User found", {
            "has_account": True,
            "is_verified": is_verified,
            "data": {
                "email": user.get("user_email"),
                "username": user.get("username"),
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
                "company": user.get("company"),
                "site_url": user.get("site_url"),
                "created_at": user.get("created_at")
            }
        })
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get User Account Status Error")
        return create_error_response(500, str(e))


@frappe.whitelist(allow_guest=True)
def email_login(email=None):
    """Get User Management record by email"""
    if not email:
        return create_error_response(400, "Email is required")
    
    user = UserManagementModel.get_user_by_email(email)
    
    if not user:
        return create_error_response(404, "User not found, please register")
    
    return {
        "status": "success",
        "user_email": user.get("user_email"),
        "site": user.get("site"),
        "company": user.get("company"),
        "site_url": user.get("site_url"),
        "ip_address": user.get("ip_address")
    }


# Helper functions
def create_error_response(status_code, message, data=None):
    """Create standardized error response"""
    frappe.local.response["http_status_code"] = status_code
    response = {"status": "error", "message": message}
    if data:
        response["data"] = data
    return response


def create_success_response(message, data=None):
    """Create standardized success response"""
    response = {"status": "success", "message": message}
    if data:
        response["data"] = data
    return response