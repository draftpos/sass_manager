# Add these imports at the top of your file (if not already there)
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import frappe
from frappe.utils import now_datetime
import requests
from frappe.utils import add_days, getdate
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
TEST_MODE = True 
# ==================== USER REGISTRATION ENDPOINTS ====================

@frappe.whitelist(allow_guest=True)
def register_user_with_site():
    """
    Complete user registration with auto-site assignment
    Works with your existing User Management doctype
    """
    try:
        # Get data from request
        data = frappe.local.form_dict
        
        # If data is empty, try getting from JSON body
        if not data:
            data = json.loads(frappe.request.data or "{}")
        
        # Extract user data
        email = data.get("email")
        username = data.get("username")
        password = data.get("password")
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        company = data.get("company")
        phone_number = data.get("phone_number")
        country = data.get("country", "Zimbabwe") 
        
        # ========== VALIDATION ==========
        required_fields = ["email", "username", "password", "first_name", "company"]
        missing = [f for f in required_fields if not data.get(f)]
        
        if missing:
            frappe.local.response["http_status_code"] = 400
            return {
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing)}"
            }
        
        # Check if user already exists in User Management
        existing_user = frappe.get_all(
            "User Management",
            filters={"user_email": email},
            fields=["name", "is_verified", "site_url"]
        )
        
        if existing_user:
            user = existing_user[0]
            # Check if is_verified field exists (might not be in your doctype yet)
            is_verified = user.get("is_verified", 0)
            if is_verified:
                frappe.local.response["http_status_code"] = 409
                return {
                    "status": "error",
                    "message": "User already registered and verified",
                    "data": {
                        "site_url": user.get("site_url"),
                        "login_url": f"{user.get('site_url')}/api/method/login"
                    }
                }
            else:
                # User exists but not verified, resend verification
                return resend_verification_link()
        
        # ========== GET AVAILABLE SITE ==========
        free_site = get_oldest_unassigned_site()
        
        if free_site.get("status") == "empty":
            frappe.local.response["http_status_code"] = 503
            return {
                "status": "error",
                "message": "No sites available. Please contact administrator.",
                "code": "NO_SITES_AVAILABLE"
            }
       
        site_docname = free_site.get("name") 
        site_url = free_site.get("site_url")
        ip_address = free_site.get("ip_address")
        site_registration = free_site.get("site_registration")
        
        # ========== CREATE ADMIN USER ON CLIENT SITE ==========
        create_user_response = create_admin_user_guest(
            base_url=site_url,
            username=username,
            email=email,
            password=password,
            company=company,
            country=country
        )
        
        if create_user_response.get("status") != "success":
            return {
                "status": "error",
                "message": f"Failed to create user on site: {create_user_response.get('message')}"
            }
        
        # ========== GENERATE VERIFICATION TOKEN ==========
        verification_token = frappe.generate_hash(length=32)
        expiry_days = 7
        expiry_date = add_days(frappe.utils.today(), expiry_days)
        
        # ========== CREATE USER MANAGEMENT RECORD ==========
        # Note: If fields don't exist yet, they'll be ignored
        user_mgmt_data = {
            "doctype": "User Management",
            "user_email": email,
            "company": company,
            "site": site_registration,
            "site_url": site_url,
            "ip_address": ip_address
        }
        
        # Add optional fields if they exist in your doctype
        try:
            if username:
                user_mgmt_data["username"] = username
            if first_name:
                user_mgmt_data["first_name"] = first_name
            if last_name:
                user_mgmt_data["last_name"] = last_name
            if phone_number:
                user_mgmt_data["phone_number"] = phone_number
            if verification_token:
                user_mgmt_data["verification_token"] = verification_token
            if expiry_date:
                user_mgmt_data["verification_token_expiry"] = expiry_date
            user_mgmt_data["is_verified"] = 0
            user_mgmt_data["created_at"] = frappe.utils.now()
        except:
            # If fields don't exist, continue without them
            pass
        
        user_mgmt = frappe.get_doc(user_mgmt_data)
        user_mgmt.flags.ignore_permissions = True
        user_mgmt.insert()
        
        # ========== MARK SITE AS ASSIGNED ==========
        # Update the Site Data Sync record to mark as assigned
        frappe.db.set_value("Site Data Sync", site_docname, "assigned", 1)
        frappe.db.commit()
        
        # ========== SEND VERIFICATION EMAIL ==========
        verification_link = f"{frappe.utils.get_url()}/api/method/saas_manager.api.verify_user_email?token={verification_token}&email={email}"
        
        send_user_verification_email(
            recipient_email=email,
            username=username,
            verification_link=verification_link,
            expiry_days=expiry_days,
            company=company,
            site_url=site_url
        )
        
        frappe.db.commit()
        
        # ========== SUCCESS RESPONSE ==========
        frappe.local.response["http_status_code"] = 200
        return {
            "status": "success",
            "message": "User registered successfully! Please verify your email.",
            "data": {
                "user": {
                    "email": email,
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                    "company": company,
                    "phone_number": phone_number
                },
                "site": {
                    "url": site_url,
                    "ip_address": ip_address,
                    "registration_id": site_registration
                },
                "verification": {
                    "sent_to": email,
                    "expires_in_days": expiry_days,
                    "expiry_date": str(expiry_date)
                }
            },
            "next_steps": [
                f"Check your email at {email} for verification link",
                "Click the verification link to activate your account",
                f"After verification, log in at: {site_url}",
                "Use your username and password to access the system"
            ]
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "User Registration Error")
        frappe.local.response["http_status_code"] = 500
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist(allow_guest=True)
def verify_user_email():
    """
    Verify user's email address using token
    """
    try:
        token = frappe.form_dict.get("token")
        email = frappe.form_dict.get("email")
        
        if not token or not email:
            frappe.local.response["http_status_code"] = 400
            return {
                "status": "error",
                "message": "Token and email are required"
            }
        
        # Find user with matching token
        filters = {
            "user_email": email,
            "verification_token": token
        }
        
        # Add is_verified filter if field exists
        try:
            filters["is_verified"] = 0
        except:
            pass
        
        user = frappe.get_all(
            "User Management",
            filters=filters,
            fields=["name", "verification_token_expiry", "site_url", "username", "company"],
            limit_page_length=1
        )
        
        if not user:
            frappe.local.response["http_status_code"] = 404
            return {
                "status": "error",
                "message": "Invalid or already used verification link"
            }
        
        user_doc = user[0]
        
        # Check if token is expired
        expiry_date = user_doc.get("verification_token_expiry")
        if expiry_date and getdate(expiry_date) < getdate(frappe.utils.today()):
            frappe.local.response["http_status_code"] = 410
            return {
                "status": "error",
                "message": "Verification link has expired. Please request a new one.",
                "action": "resend",
                "resend_endpoint": "/api/method/saas_manager.api.resend_verification_link"
            }
        
        # Mark user as verified
        update_data = {
            "verification_token": None
        }
        
        # Try to set is_verified if field exists
        try:
            update_data["is_verified"] = 1
            update_data["verified_at"] = frappe.utils.now()
        except:
            pass
        
        frappe.db.set_value("User Management", user_doc["name"], update_data)
        frappe.db.commit()
        
        frappe.local.response["http_status_code"] = 200
        return {
            "status": "success",
            "message": "Email verified successfully! Your account is now active.",
            "data": {
                "email": email,
                "username": user_doc.get("username"),
                "site_url": user_doc.get("site_url"),
                "company": user_doc.get("company"),
                "verified": True
            },
            "next_steps": [
                f"Log in at: {user_doc.get('site_url')}",
                "Use your username and password",
                "Start managing your business"
            ]
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Email Verification Error")
        frappe.local.response["http_status_code"] = 500
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist(allow_guest=True)
def resend_verification_link():
    """
    Resend verification link to user
    """
    try:
        email = frappe.form_dict.get("email")
        
        if not email:
            frappe.local.response["http_status_code"] = 400
            return {
                "status": "error",
                "message": "Email is required"
            }
        
        # Find unverified user
        filters = {"user_email": email}
        
        # Add is_verified filter if field exists
        try:
            filters["is_verified"] = 0
        except:
            pass
        
        user = frappe.get_all(
            "User Management",
            filters=filters,
            fields=["name", "username", "company", "site_url"],
            limit_page_length=1
        )
        
        if not user:
            frappe.local.response["http_status_code"] = 404
            return {
                "status": "error",
                "message": "User not found or already verified"
            }
        
        user_doc = user[0]
        
        # Generate new token
        verification_token = frappe.generate_hash(length=32)
        expiry_days = 7
        expiry_date = add_days(frappe.utils.today(), expiry_days)
        
        # Update user record
        update_data = {
            "verification_token": verification_token,
            "verification_token_expiry": expiry_date
        }
        
        frappe.db.set_value("User Management", user_doc["name"], update_data)
        
        # Send new verification email
        verification_link = f"{frappe.utils.get_url()}/api/method/sass_manager.sass_manager.api.register.verify_user_email?token={verification_token}&email={email}"
        
        send_user_verification_email(
            recipient_email=email,
            username=user_doc.get("username"),
            verification_link=verification_link,
            expiry_days=expiry_days,
            company=user_doc.get("company"),
            site_url=user_doc.get("site_url")
        )
        
        frappe.db.commit()
        
        frappe.local.response["http_status_code"] = 200
        return {
            "status": "success",
            "message": f"Verification link sent to {email}",
            "data": {
                "email": email,
                "expires_in_days": expiry_days,
                "expiry_date": str(expiry_date)
            }
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Resend Verification Error")
        frappe.local.response["http_status_code"] = 500
        return {
            "status": "error",
            "message": str(e)
        }

# def send_user_verification_email(recipient_email, username, verification_link, expiry_days, company, site_url):
#     """
#     Send verification email using the verify_email template
#     """
#     try:
#         frappe.sendmail(
#             recipients=[recipient_email],
#             subject="Verify Your Account - " + company,
#             template="verify_email",  # This matches the name you set
#             args={
#                 "username": username,
#                 "company": company,
#                 "verification_link": verification_link,
#                 "expiry_days": expiry_days,
#                 "site_url": site_url
#             },
#             now=True
#         )
#         print(f"✓ Verification email sent to {recipient_email}")
        
#     except Exception as e:
#         frappe.log_error(f"Failed to send email: {str(e)}", "Verification Email")
#         print(f"✗ Email failed: {e}")
#         print(f"Verification link: {verification_link}")


def send_user_verification_email(recipient_email, username, verification_link, expiry_days, company, site_url):
    """
    Send verification email using Frappe's email system
    """
    try:
        subject = f"Verify Your Account - {company}"
        
        message = f"""
Hello {username},

Thank you for registering with {company}!

Please verify your email address by clicking the link below:

{verification_link}

This link will expire in {expiry_days} days.

Once verified, you can log in to your site:
Site URL: {site_url}
Username: {username}

If you did not request this account, please ignore this email.

Regards,
Your Team
"""
        
        # Send using Frappe's email system
        frappe.sendmail(
            recipients=[recipient_email],
            subject=subject,
            message=message,
            now=True  # Send immediately, don't queue
        )
        
        frappe.log_error(f"Verification email sent to {recipient_email}", "Email Status")
        print(f"✓ Verification email sent to {recipient_email}")
        
    except Exception as e:
        frappe.log_error(f"Failed to send verification email: {str(e)}", "Verification Email Error")
        print(f"✗ Email failed: {e}")
        # Print the verification link so you can manually verify
        print(f"\nMANUAL VERIFICATION LINK: {verification_link}\n")
        
# def send_user_verification_email(recipient_email, username, verification_link, expiry_days, company, site_url):
#     """
#     Send verification email to user
#     """
#     try:
#         gmail_user = frappe.conf.gmail_user
#         app_password = frappe.conf.app_password
        
#         if not gmail_user or not app_password:
#             frappe.log_error("Email credentials not configured", "Verification Email Error")
#             return
        
#         subject = f"Verify Your Account - {company}"
        
#         body = f"""
# Hello {username},

# Thank you for registering with {company}!

# Please verify your email address by clicking the link below:

# {verification_link}

# This link will expire in {expiry_days} days.

# Once verified, you can log in to your site:
# Site URL: {site_url}
# Username: {username}

# If you did not request this account, please ignore this email.

# Regards,
# Havano ERP Team
# """
        
#         msg = MIMEMultipart()
#         msg["From"] = gmail_user
#         msg["To"] = recipient_email
#         msg["Subject"] = subject
#         msg.attach(MIMEText(body, "plain"))
        
#         with smtplib.SMTP("smtp.gmail.com", 587) as server:
#             server.starttls()
#             server.login(gmail_user, app_password)
#             server.send_message(msg)
            
#     except Exception as e:
#         frappe.log_error(f"Failed to send verification email: {str(e)}", "Verification Email Error")


@frappe.whitelist(allow_guest=True)
def get_user_account_status():
    """
    Check if user has an account and get status
    """
    try:
        email = frappe.form_dict.get("email")
        
        if not email:
            frappe.local.response["http_status_code"] = 400
            return {
                "status": "error",
                "message": "Email is required"
            }
        
        # Try to get all fields, but only those that exist
        fields = ["user_email", "company", "site_url"]
        
        # Try to add optional fields
        try:
            fields.extend(["username", "first_name", "last_name", "is_verified", "created_at"])
        except:
            pass
        
        user = frappe.get_all(
            "User Management",
            filters={"user_email": email},
            fields=fields,
            limit_page_length=1
        )
        
        if not user:
            frappe.local.response["http_status_code"] = 404
            return {
                "status": "not_found",
                "message": "No account found for this email",
                "can_register": True
            }
        
        user = user[0]
        is_verified = user.get("is_verified", 0)
        
        frappe.local.response["http_status_code"] = 200
        return {
            "status": "success",
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
            },
            "actions": {
                "login": f"{user.get('site_url')}/api/method/login" if is_verified else None,
                "resend_verification": "/api/method/saas_manager.api.resend_verification_link" if not is_verified else None
            }
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get User Account Status Error")
        frappe.local.response["http_status_code"] = 500
        return {
            "status": "error",
            "message": str(e)
        }


@frappe.whitelist(allow_guest=True)
def get_oldest_unassigned_site():
	"""
	Get the oldest unassigned Site Data Sync record
	"""
	# Fetch oldest unassigned record
	records = frappe.get_all(
		"Site Data Sync",
		filters={"assigned": 0},
		fields=["name", "site_registration", "ip_address", "site_url"],
		order_by="creation asc",
		limit_page_length=1
	)

	if not records:
		return {
			"status": "empty",
			"message": "No unassigned site records found"
		}

	record = records[0]

	return {
		"status": "success",
		"site_registration": record.site_registration,
		"ip_address": record.ip_address,
        "name": record.name,
		"site_url": record.site_url
	}

@frappe.whitelist(allow_guest=True)
def email_login(email=None):
	"""
	Get User Management record by email
	"""
	if not email:
		frappe.local.response["http_status_code"] = 400
		return {
			"status": "error",
			"message": "Email is required"
		}
	user = frappe.get_all(
		"User Management",
		filters={"user_email": email},
		fields=[
			"user_email",
			"site",
			"company",
			"site_url",
			"ip_address"
		],
		limit_page_length=1
	)

	if not user:
		frappe.local.response["http_status_code"] = 404
		return {
			"status": "not_found",
			"message": "User not found, please register"
		}

	record = user[0]

	return {
		"status": "success",
		"user_email": record.user_email,
		"site": record.site,
		"company": record.company,
		"site_url": record.site_url,
		"ip_address": record.ip_address
	}

@frappe.whitelist(allow_guest=True)
def register_new_site(**kwargs): # Add **kwargs here
    """
    API endpoint to register a new site.
    Accepts data from frappe.form_dict (HTTP) or kwargs (Python call).
    """
    # Merge form_dict and kwargs so it works in both scenarios
    data = frappe._dict(frappe.form_dict)
    data.update(kwargs)

    site_name = data.get("site_name")
    email = data.get("email")
    # ... rest of your code using 'data.get' ...
    email = data.get("email")
    username = data.get("username")
    password = data.get("password")
    company = data.get("company")
    client_type = data.get("client_type") or "ERP"
    subscription_package = data.get("subscription_package")
    subscription_start_date = data.get("subscription_start_date")
    subscription_end_date = data.get("subscription_end_date")
    site_url_new = data.get("site_url")

    free_site = get_oldest_unassigned_site()
    print(f"Free site: {free_site}")
    if free_site.get("status") == "empty":
        frappe.local.response["http_status_code"] = 400
        return {"status": "error", "message": "No free sites available"}
    
    else:
        site_url = free_site.get("site_url")
        ip_address = free_site.get("ip_address")

    # Check required fields
    if not email or not company or not username or not password:
        frappe.local.response["http_status_code"] = 400
        return {"status": "error", "message": "Missing required fields: email, company, username, password"}

    # Check if site already exists
    existing_site = frappe.get_all(
        "Site Registration",
        filters={"email": email},
        fields=["name"],
        limit_page_length=1
    )

    if existing_site:
        frappe.local.response["http_status_code"] = 409
        return {
            "status": "error",
            "message": "Site already registered. Please contact admin if you want updates.",
            "site_url": site_url
        }

    # Create new site registration
    existing_site = frappe.get_all(
        "Site Registration",
        filters={"site_url": site_url},
        fields=["name"],
        limit_page_length=1
    )
    print(site_url)

    if existing_site:
        # Update existing site
        doc = frappe.get_doc("Site Registration", existing_site[0].name)
        create_admin_user_guest(
            base_url=site_url,
            username=username,
            email=email,
            password=password,
            company=company,
        )

        # doc.site_url = site_url
        doc.email = email
        doc.company = company
        doc.ip_address = ip_address
        doc.client_type = client_type
        doc.subscription_package = subscription_package
        doc.subscription_start_date = subscription_start_date
        doc.subscription_end_date = subscription_end_date
        doc.new_site_name = site_name
        doc.old_url=doc.name
        doc.username=username
        # doc.name=site_url
        doc.save()
        frappe.db.commit()

        send_site_registration_email(
            recipient_email=email,
            username=username,
            site_url=site_url,
            ip_address=ip_address,
            company=company
        )

        return {
            "status": "success",
            "message": "Site registered successfully",
            "site_url": site_url,
            "email": email,
            "company": company,
            "username": username,
            "ip_address": ip_address,
        }


    return {
        "status": "success",
        "message": "Site registered successfully",
        "site_url": site_url,
        "email": email,
        "company": company,
        "username": username,
        "ip_address": ip_address,
    }

def create_admin_user_guest(
    base_url,
    username,
    email,
    password,
    company,
    country
):
    """
    Guest call to create admin user + company in Frappe
    """

    try:
        if not all([base_url, username, email, password, company]):
            return {
                "status": "error",
                "message": "All fields are required"
            }

        url = f"{base_url}/api/method/sass_client.api.user.create_admin_user"

        payload = {
            "username": username,
            "email": email,
            "password": password,
            "company": company,
            "country":country
        }

        response = requests.post(
            url,
            json=payload,
            timeout=15
        )

        # Non-200 HTTP error
        res = response.json()
        payload = res.get("message", {})

        if payload.get("status") != "success":
            frappe.throw(payload.get("message", "Account creation failed"))
        return payload

    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "message": "Request timed out"
        }

    except requests.exceptions.ConnectionError:
        return {
            "status": "error",
            "message": "Connection error (server unreachable)"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@frappe.whitelist(allow_guest=True)
def send_site_registration_email(
    recipient_email,
    username,
    site_url,
    ip_address,
    company
):
    gmail_user = frappe.conf.gmail_user
    app_password = frappe.conf.app_password

    print(gmail_user, app_password, recipient_email, username, site_url, ip_address, company)
    """
    Send site registration email
    """

    try:
        # Validate required fields
        if not all([gmail_user, app_password, recipient_email, username, site_url, ip_address,company]):
            return {
                "status": "error",
                "message": "Missing required parameters"
            }

        subject = "Your Site Has Been Registered Successfully"

        body = f"""
Hello {username},

Your site has been successfully registered.

Site URL: {site_url}
IP Address: {ip_address}
Company: {company}

You can now proceed to access your system.

If this was not you, please contact support immediately.

Regards,
Havano ERP Team
"""

        msg = MIMEMultipart()
        msg["From"] = gmail_user
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
            server.starttls()
            server.login(gmail_user, app_password)
            server.send_message(msg)

        return {
            "status": "success",
            "message": f"Email sent successfully to {recipient_email}"
        }

    except smtplib.SMTPAuthenticationError:
        return {
            "status": "error",
            "message": "SMTP authentication failed (check app password)"
        }

    except smtplib.SMTPConnectError:
        return {
            "status": "error",
            "message": "Failed to connect to SMTP server"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
