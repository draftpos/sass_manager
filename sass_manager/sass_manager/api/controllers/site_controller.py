import frappe
from ..services.site_service import SiteService
from ..models.site_model import SiteModel

@frappe.whitelist(allow_guest=True)
def register_new_site(**kwargs):
    """API endpoint to register a new site"""
    # Merge form_dict and kwargs
    data = frappe._dict(frappe.form_dict)
    data.update(kwargs)
    
    # Validate required fields
    required_fields = ["email", "company", "username", "password"]
    missing = [f for f in required_fields if not data.get(f)]
    
    if missing:
        frappe.local.response["http_status_code"] = 400
        return {
            "status": "error",
            "message": f"Missing required fields: {', '.join(missing)}"
        }
    
    # Prepare site data
    site_data = {
        "site_name": data.get("site_name"),
        "email": data.get("email"),
        "username": data.get("username"),
        "password": data.get("password"),
        "company": data.get("company"),
        "client_type": data.get("client_type") or "ERP",
        "subscription_package": data.get("subscription_package"),
        "subscription_start_date": data.get("subscription_start_date"),
        "subscription_end_date": data.get("subscription_end_date"),
        "site_url_new": data.get("site_url"),
        "country": data.get("country", "Zimbabwe")
    }
    
    return SiteService.register_new_site(site_data)


@frappe.whitelist(allow_guest=True)
def get_oldest_unassigned_site():
    """Get the oldest unassigned and accessible site"""
    site = SiteModel.get_oldest_unassigned_site()
    
    if not site:
        return {
            "status": "empty",
            "message": "No unassigned site records found"
        }
    
    return {
        "status": "success",
        **site
    }