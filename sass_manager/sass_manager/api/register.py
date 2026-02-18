import frappe
from frappe.utils import now_datetime
import requests


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
def register_new_site():
    """
    API endpoint to register a new site.
    Checks if the site_url already exists and returns a message if it does.
    """
    data = frappe.form_dict
    site_name = data.get("site_name")
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
        # doc.site_url = site_url
        doc.email = email
        doc.company = company
        doc.ip_address = ip_address
        doc.client_type = client_type
        doc.subscription_package = subscription_package
        doc.subscription_start_date = subscription_start_date
        doc.subscription_end_date = subscription_end_date
        doc.new_site_name = site_name
        doc.old_url=doc.name,
        doc.username=username
        doc.name=site_url
        doc.save()
        frappe.db.commit()
        create_admin_user_guest(
        base_url=site_url,
        username=username,
        email=email,
        password=password,
        company=company
        )

        send_site_registration_email(
            gmail_user="chirovemunyaradzi@gmail.com",
            app_password="uftq mawx amqr nots",
            recipient_email=email,
            username=username,
            site_url=site_url,
            ip_address=ip_address,
            company=company
        )

    #     frappe.rename_doc(
    #     "Site Registration",
    #     doc.name,
    #     site_url_new,
    #     force=True 
    # )
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

import requests

def create_admin_user_guest(
    base_url,
    username,
    email,
    password,
    company
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
            "company": company
        }

        response = requests.post(
            url,
            json=payload,
            timeout=15
        )

        # Non-200 HTTP error
        if response.status_code != 200:
            return {
                "status": "error",
                "message": f"HTTP {response.status_code}",
                "details": response.text
            }

        try:
            return response.json()
        except ValueError:
            return {
                "status": "error",
                "message": "Invalid JSON response",
                "raw": response.text
            }

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


import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_site_registration_email(
    gmail_user,
    app_password,
    recipient_email,
    username,
    site_url,
    ip_address,
    company
):
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
