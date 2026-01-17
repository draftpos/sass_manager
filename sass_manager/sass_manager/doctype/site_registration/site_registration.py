# Copyright (c) 2025, nasirucode and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document
from frappe.utils import random_string
from datetime import datetime
import requests


class SiteRegistration(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		api_key: DF.Data | None
		client_type: DF.Literal["ERP", "Mobile POS", "Desktop POS", "Fiscalisation"]
		company: DF.Data | None
		ip_address: DF.Data | None
		is_active: DF.Check
		last_sync: DF.Datetime | None
		notes: DF.TextEditor | None
		site_name: DF.Data
		site_url: DF.Data
		subscription_end_date: DF.Date | None
		subscription_package: DF.Link | None
		subscription_start_date: DF.Date | None
		subscription_status: DF.Literal["Active", "Expired", "Pending", "Cancelled"]
	# end: auto-generated types

	def before_insert(self):
		"""Generate API key before inserting"""
		if not self.api_key:
			self.api_key = random_string(32)

	def validate(self):
		"""Validate subscription dates"""
		if self.subscription_start_date and self.subscription_end_date:
			from frappe.utils import getdate
			# Ensure dates are date objects, not strings
			start_date = getdate(self.subscription_start_date) if self.subscription_start_date else None
			end_date = getdate(self.subscription_end_date) if self.subscription_end_date else None
			
			if start_date and end_date and end_date < start_date:
				frappe.throw("Subscription End Date cannot be before Start Date")

	def on_update(self):
		"""Update subscription status based on dates and notify client site"""
		# Check if is_active has changed
		previous_is_active = frappe.db.get_value("Site Registration", self.name, "is_active")
		is_active_changed = previous_is_active != self.is_active
		
		if self.subscription_end_date:
			from frappe.utils import today, getdate
			# Ensure subscription_end_date is a date object, not a string
			subscription_end_date = getdate(self.subscription_end_date) if self.subscription_end_date else None
			
			if subscription_end_date and subscription_end_date < today():
				if self.subscription_status == "Active":
					self.subscription_status = "Expired"
					self.is_active = 0
					is_active_changed = True
			elif self.subscription_status == "Expired" and subscription_end_date and subscription_end_date >= today():
				if self.is_active:
					self.subscription_status = "Active"
					is_active_changed = True
		
		# Notify client site about maintenance mode change
		if is_active_changed:
			self._notify_client_site_maintenance_mode()
	
	def _notify_client_site_maintenance_mode(self):
		"""
		Notify client site to set maintenance mode based on is_active status
		If site is not active, enable maintenance mode; if active, disable it
		"""
		try:
			if not self.site_url or not self.api_key:
				return
			
			# Determine maintenance mode: 1 if inactive, 0 if active
			maintenance_mode = 0 if self.is_active else 1
			
			# Prepare API endpoint
			api_endpoint = f"{self.site_url}/api/method/sass_client.api.maintenance_api.set_maintenance_mode"
			
			# Make API call to client site
			response = requests.post(
				api_endpoint,
				json={
					"api_key": self.api_key,
					"maintenance_mode": maintenance_mode
				},
				timeout=10
			)
			
			if response.status_code == 200:
				result = response.json()
				if result.get("message", {}).get("status") == "success":
					frappe.logger().info(
						f"Maintenance mode {'enabled' if maintenance_mode else 'disabled'} "
						f"for site {self.site_name} ({self.site_url})"
					)
				else:
					frappe.log_error(
						f"Failed to set maintenance mode for site {self.site_name}: "
						f"{result.get('message', {}).get('message')}",
						"Site Maintenance Mode Error"
					)
			else:
				frappe.log_error(
					f"HTTP error setting maintenance mode for site {self.site_name}: "
					f"{response.status_code}",
					"Site Maintenance Mode Error"
				)
		except Exception as e:
			# Log error but don't fail the document save
			frappe.log_error(
				f"Error notifying client site about maintenance mode: {str(e)}",
				"Site Maintenance Mode Error"
			)


@frappe.whitelist()
def set_maintenance_mode(site_name, maintenance_mode):
	"""
	Manually set or remove maintenance mode for a site
	Called from the UI button
	
	Args:
		site_name: Name of the Site Registration document
		maintenance_mode: 1 to enable, 0 to disable
	
	Returns:
		dict: Status of the operation
	"""
	try:
		# Get the site registration document
		site_reg = frappe.get_doc("Site Registration", site_name)
		
		if not site_reg.site_url or not site_reg.api_key:
			return {
				"status": "error",
				"message": "Site URL or API key is missing"
			}
		
		# Convert maintenance_mode to int if it's a string
		if isinstance(maintenance_mode, str):
			maintenance_mode = int(maintenance_mode)
		
		# Prepare API endpoint
		api_endpoint = f"{site_reg.site_url}/api/method/sass_client.api.maintenance_api.set_maintenance_mode"
		
		# Make API call to client site
		response = requests.post(
			api_endpoint,
			json={
				"api_key": site_reg.api_key,
				"maintenance_mode": maintenance_mode
			},
			timeout=10
		)
		
		if response.status_code == 200:
			result = response.json()
			if result.get("message", {}).get("status") == "success":
				frappe.logger().info(
					f"Maintenance mode {'enabled' if maintenance_mode else 'disabled'} "
					f"for site {site_reg.site_name} ({site_reg.site_url}) via manual action"
				)
				return {
					"status": "success",
					"message": f"Maintenance mode {'enabled' if maintenance_mode else 'disabled'} successfully"
				}
			else:
				error_msg = result.get("message", {}).get("message", "Unknown error")
				frappe.log_error(
					f"Failed to set maintenance mode for site {site_reg.site_name}: {error_msg}",
					"Site Maintenance Mode Error"
				)
				return {
					"status": "error",
					"message": error_msg
				}
		else:
			error_msg = f"HTTP error: {response.status_code}"
			frappe.log_error(
				f"HTTP error setting maintenance mode for site {site_reg.site_name}: {response.status_code}",
				"Site Maintenance Mode Error"
			)
			return {
				"status": "error",
				"message": error_msg
			}
	except frappe.DoesNotExistError:
		return {
			"status": "error",
			"message": f"Site Registration {site_name} not found"
		}
	except Exception as e:
		frappe.log_error(
			f"Error setting maintenance mode for site {site_name}: {str(e)}",
			"Site Maintenance Mode Error"
		)
		return {
			"status": "error",
			"message": str(e)
		}