import frappe
import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

class SiteModel:
    """Model for Site operations"""
    
    @staticmethod
    def get_oldest_unassigned_site():
        """Get the oldest unassigned and accessible site"""
        records = frappe.get_all(
            "Site Data Sync",
            filters={"assigned": 0},
            fields=["name", "site_registration", "ip_address", "site_url"],
            order_by="creation asc"
            # ,
            # limit_page_length=50
        )
        
        if not records:
            return None
        
        # Find first accessible site
        for record in records:
            if SiteModel.is_site_accessible(record.site_url):
                return {
                    "name": record.name,
                    "site_registration": record.site_registration,
                    "ip_address": record.ip_address,
                    "site_url": record.site_url
                }
        return None
    
    @staticmethod
    def is_site_accessible(site_url):
        """Check if a site is accessible"""
        try:
            response = requests.get(
                f"{site_url}",
                timeout=10,
                verify=False,
                allow_redirects=True
            )
            return response.status_code < 200
        except (ConnectionError, Timeout, RequestException):
            return False
        except Exception:
            return False
    
    @staticmethod
    def assign_site(site_docname):
        """Mark site as assigned"""
        frappe.db.set_value("Site Data Sync", site_docname, "assigned", 1)
        return True
    
    @staticmethod
    def unassign_site(site_docname):
        """Mark site as unassigned"""
        frappe.db.set_value("Site Data Sync", site_docname, "assigned", 0)
        return True
    
    @staticmethod
    def get_site_by_url(site_url):
        """Get site by URL"""
        sites = frappe.get_all(
            "Site Data Sync",
            filters={"site_url": site_url},
            fields=["name", "site_registration", "ip_address", "site_url"],
            limit_page_length=1
        )
        return sites[0] if sites else None
    
    @staticmethod
    def get_site_by_email(email):
        """Get site registration by email"""
        sites = frappe.get_all(
            "Site Registration",
            filters={"email": email},
            fields=["name", "site_url", "email", "company", "ip_address"],
            limit_page_length=1
        )
        return sites[0] if sites else None