# Copyright (c) 2025, nasirucode and Contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.utils import now
import requests
import json


@frappe.whitelist(allow_guest=True)
def register_site(site_url, site_name, company=None, client_type=None, ip_address=None):
	"""
	Register a new site with the main SaaS manager
	
	Args:
		site_url: URL of the client site
		site_name: Name of the site
		company: Company name
		client_type: Type of client (ERP, Mobile POS, Desktop POS, Fiscalisation)
		ip_address: IP address of the site
	
	Returns:
		dict: Registration details including API key
	"""
	try:
		# Check if site already exists
		if frappe.db.exists("Site Registration", {"site_url": site_url}):
			site = frappe.get_doc("Site Registration", {"site_url": site_url})
			return {
				"status": "success",
				"message": "Site already registered",
				"api_key": site.api_key,
				"site_name": site.name
			}
		
		# Get IP address from request if not provided
		if not ip_address:
			ip_address = frappe.get_request_header("X-Forwarded-For") or frappe.get_request_header("X-Real-IP") or frappe.local.request.remote_addr if hasattr(frappe.local, 'request') else "Unknown"
		
		# Create new site registration
		site = frappe.get_doc({
			"doctype": "Site Registration",
			"site_url": site_url,
			"site_name": site_name,
			"company": company,
			"client_type": client_type,
			"ip_address": ip_address,
			"subscription_status": "Pending",
			"is_active": 0
		})
		site.insert(ignore_permissions=True)
		
		return {
			"status": "success",
			"message": "Site registered successfully",
			"api_key": site.api_key,
			"site_name": site.name
		}
	except Exception as e:
		frappe.log_error(f"Error registering site: {str(e)}")
		return {
			"status": "error",
			"message": str(e)
		}


@frappe.whitelist(allow_guest=True)
def sync_site_data(api_key=None, data=None):
    """
    Sync site data from client site to main SaaS manager
    """
    try:
        # Handle JSON data from request
        if not api_key and frappe.request:
            request_data = frappe.request.json if hasattr(frappe.request, 'json') else {}
            api_key = request_data.get("api_key") or api_key
            data = request_data.get("data") or data

        # Validate API key
        if not api_key or not frappe.db.exists("Site Registration", {"api_key": api_key}):
            return {"status": "error", "message": "Invalid API key"}

        site_reg = frappe.get_doc("Site Registration", {"api_key": api_key})

        # Parse JSON string if needed
        if isinstance(data, str):
            data = json.loads(data)

        from frappe.utils import getdate, now
        from datetime import date, datetime

        # Convert date strings
        def parse_date(d):
            if not d:
                return None
            if isinstance(d, str):
                return getdate(d)
            elif isinstance(d, (date, datetime)):
                return d
            else:
                return getdate(str(d))

        subscription_start_date = parse_date(data.get("subscription_start_date"))
        subscription_end_date = parse_date(data.get("subscription_end_date"))

        # Check if sync record exists for this site + company
        existing = frappe.db.exists(
            "Site Data Sync",
            {"site_registration": site_reg.name, "company": data.get("company")}
        )

        if existing:
            # Update existing record
            sync_doc = frappe.get_doc("Site Data Sync", existing)
            sync_doc.update({
                "sync_date": now(),
                "total_sales_invoices": data.get("total_sales_invoices", 0),
                "total_credit_notes": data.get("total_credit_notes", 0),
                "total_purchase_invoices": data.get("total_purchase_invoices", 0),
                "total_stock_reconciliations": data.get("total_stock_reconciliations", 0),
                "active_users": data.get("active_users", 0),
                "total_companies": data.get("total_companies", 0),
                "ip_address": data.get("ip_address"),
                "site_url": data.get("site_url") or site_reg.site_url,
                "subscription_package": data.get("subscription_package"),
                "package_status": data.get("package_status", "Expired"),
                "subscription_start_date": subscription_start_date,
                "subscription_end_date": subscription_end_date,
				"days_left": data.get("days_left")
            })
            sync_doc.save(ignore_permissions=True)
            action = "updated"
        else:
            # Insert new record
            sync_doc = frappe.get_doc({
                "doctype": "Site Data Sync",
                "site_registration": site_reg.name,
                "sync_date": now(),
                "company": data.get("company"),
                "client_type": data.get("client_type"),
                "total_sales_invoices": data.get("total_sales_invoices", 0),
                "total_credit_notes": data.get("total_credit_notes", 0),
                "total_purchase_invoices": data.get("total_purchase_invoices", 0),
                "total_stock_reconciliations": data.get("total_stock_reconciliations", 0),
                "active_users": data.get("active_users", 0),
                "total_companies": data.get("total_companies", 0),
                "ip_address": data.get("ip_address"),
                "site_url": data.get("site_url") or site_reg.site_url,
                "subscription_package": data.get("subscription_package"),
                "package_status": data.get("package_status", "Expired"),
                "subscription_start_date": subscription_start_date,
                "subscription_end_date": subscription_end_date,
				"days_left": data.get("days_left")
            })
            sync_doc.insert(ignore_permissions=True)
            action = "created"

        # Update last sync on site registration
        site_reg.db_set("last_sync", now(), update_modified=False)

        return {"status": "success", "message": f"Data {action} successfully", "sync_id": sync_doc.name}

    except Exception as e:
        frappe.log_error(f"Error syncing site data: {str(e)}")
        return {"status": "error", "message": str(e)}

@frappe.whitelist(allow_guest=True)
def get_subscription_status(api_key):
	"""
	Get subscription status for a site
	
	Args:
		api_key: API key for authentication
	
	Returns:
		dict: Subscription status and details
	"""
	try:
		if not frappe.db.exists("Site Registration", {"api_key": api_key}):
			return {
				"status": "error",
				"message": "Invalid API key"
			}
		
		site_reg = frappe.get_doc("Site Registration", {"api_key": api_key})
		
		package_details = {}
		if site_reg.subscription_package:
			package = frappe.get_doc("Subscription Package", site_reg.subscription_package)
			package_details = {
				"package_name": package.package_name,
				"package_code": package.package_code,
				"max_users": package.max_users,
				"price": package.price
			}
		
		return {
			"status": "success",
			"subscription_status": site_reg.subscription_status,
			"is_active": site_reg.is_active,
			"subscription_start_date": str(site_reg.subscription_start_date) if site_reg.subscription_start_date else None,
			"subscription_end_date": str(site_reg.subscription_end_date) if site_reg.subscription_end_date else None,
			"subscription_package": site_reg.subscription_package,
			"package_details": package_details
		}
	except Exception as e:
		frappe.log_error(f"Error getting subscription status: {str(e)}")
		return {
			"status": "error",
			"message": str(e)
		}


@frappe.whitelist(allow_guest=True)
def update_subscription(api_key, subscription_package=None, subscription_status=None, 
						subscription_start_date=None, subscription_end_date=None, is_active=None):
	"""
	Update subscription details (usually called manually by admin)
	
	Args:
		api_key: API key for authentication
		subscription_package: Package name
		subscription_status: Status (Active, Expired, Pending, Cancelled)
		subscription_start_date: Start date
		subscription_end_date: End date
		is_active: Active flag
	
	Returns:
		dict: Update status
	"""
	try:
		if not frappe.db.exists("Site Registration", {"api_key": api_key}):
			return {
				"status": "error",
				"message": "Invalid API key"
			}
		
		site_reg = frappe.get_doc("Site Registration", {"api_key": api_key})
		
		if subscription_package:
			site_reg.subscription_package = subscription_package
		if subscription_status:
			site_reg.subscription_status = subscription_status
		if subscription_start_date:
			site_reg.subscription_start_date = subscription_start_date
		if subscription_end_date:
			site_reg.subscription_end_date = subscription_end_date
		if is_active is not None:
			site_reg.is_active = is_active
		
		site_reg.save(ignore_permissions=True)
		
		return {
			"status": "success",
			"message": "Subscription updated successfully"
		}
	except Exception as e:
		frappe.log_error(f"Error updating subscription: {str(e)}")
		return {
			"status": "error",
			"message": str(e)
		}
