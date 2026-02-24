import frappe
from frappe.model.document import Document
import re

class register(Document):
    def validate(self):
        self.validate_required_fields()
        self.validate_email()
        self.validate_passwords()

    def validate_required_fields(self):
        required_fields = ["email", "username", "password", "company", "domain"]
        for field in required_fields:
            if not self.get(field):
                frappe.throw(f"{field.replace('_', ' ').title()} is required")

    def validate_email(self):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", self.email):
            frappe.throw("Invalid email format")

    def validate_passwords(self):
        # Note: If confirm_password isn't a field in your DocType, 
        # ensure it's passed in the local __dict__ or as a virtual field.
        if hasattr(self, "confirm_password") and self.password != self.confirm_password:
            frappe.throw("Passwords do not match")

    def on_update(self):
        """
        Usually, triggering external logic is better in on_update or on_submit 
        rather than validate, to ensure the local record is valid first.
        """
        self.call_registration_api()

    def call_registration_api(self):
        # Fetching the function via path
        try:
            register_fn = frappe.get_attr("sass_manager.sass_manager.api.register.register_new_site")
            
            data = {
                "email": self.email,
                "username": self.username,
                "password": self.password,
                "company": self.company,
                "site_url": self.domain
            }

            # Call the function directly
            result = register_fn(**data)
            
            frappe.msgprint(f"Site Registration Initiated: {result}")
            
        except Exception as e:
            frappe.log_error(message=frappe.get_traceback(), title="SaaS Registration Failed")
            frappe.throw(f"Failed to call registration API: {str(e)}")