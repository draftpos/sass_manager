import frappe
from frappe import _

class EmailModel:
    """Model for Email operations using Frappe's built-in email system"""
    
    @staticmethod
    def send_verification_email(recipient_email, username, verification_link, 
                                expiry_days, company, site_url):
        """
        Send verification email using Frappe's email system
        This automatically uses the configured Email Account in Frappe
        """
        try:
            subject = f"Verify Your Account - {company}"
            
            # Build the email message
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

            frappe.sendmail(
                recipients=[recipient_email],
                subject=subject,
                message=message,
                now=True, 
                retry=3   
            )
            
            frappe.log_error(
                f"Verification email queued for {recipient_email}", 
                "Email Status"
            )
            return {"status": "success", "message": "Email queued for delivery"}
            
        except Exception as e:
            frappe.log_error(
                f"Failed to queue verification email: {str(e)}", 
                "Verification Email Error"
            )
            # Log the verification link for manual verification (helpful for debugging)
            print(f"\nMANUAL VERIFICATION LINK: {verification_link}\n")
            raise e
    
    @staticmethod
    def send_site_registration_email(recipient_email, username, site_url, ip_address, company):
        """Send site registration email using Frappe's email system"""
        try:
            subject = "Your Site Has Been Registered Successfully"
            
            message = f"""
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
            
            frappe.sendmail(
                recipients=[recipient_email],
                subject=subject,
                message=message,
                now=True,
                retry=3
            )
            
            return {"status": "success", "message": f"Email queued for {recipient_email}"}
            
        except Exception as e:
            frappe.log_error(f"Failed to queue registration email: {str(e)}", "Email Error")
            return {"status": "error", "message": str(e)}