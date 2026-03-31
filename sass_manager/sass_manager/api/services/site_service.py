import frappe
from ..models.site_model import SiteModel
from ..services.user_service import UserService
from ..models.email_model import EmailModel

class SiteService:
    """Service layer for Site operations"""
    
    @staticmethod
    def register_new_site(site_data):
        """Register a new site"""
        # Check if site already exists
        existing_site = SiteModel.get_site_by_email(site_data.get("email"))
        
        # Get free site
        free_site = SiteModel.get_oldest_unassigned_site()
        if not free_site:
            return {"status": "error", "message": "No free sites available"}
        
        site_url = free_site.get("site_url")
        ip_address = free_site.get("ip_address")
        
        # Create admin user
        user_response = UserService.create_admin_user_on_site(
            base_url=site_url,
            username=site_data.get("username"),
            email=site_data.get("email"),
            password=site_data.get("password"),
            company=site_data.get("company"),
            country=site_data.get("country", "Zimbabwe")
        )
        
        if user_response.get("status") != "success":
            return user_response
        
        # Send registration email
        EmailModel.send_site_registration_email(
            recipient_email=site_data.get("email"),
            username=site_data.get("username"),
            site_url=site_url,
            ip_address=ip_address,
            company=site_data.get("company")
        )
        
        return {
            "status": "success",
            "message": "Site registered successfully",
            "site_url": site_url,
            "email": site_data.get("email"),
            "company": site_data.get("company"),
            "username": site_data.get("username"),
            "ip_address": ip_address,
        }