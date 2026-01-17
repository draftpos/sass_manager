# Copyright (c) 2025, nasirucode and Contributors
# License: MIT. See LICENSE

"""
Scheduled tasks for SaaS Manager
"""

import frappe
import requests


def hourly():
	"""
	Hourly tasks - sync site data from registered sites and check maintenance mode
	"""
	try:
		# Get all active site registrations
		# Note: Actual sync happens from client side
		# This is just a placeholder for any server-side hourly tasks
		
		# Set maintenance mode for inactive/expired sites (runs hourly for faster response)
		set_maintenance_mode_for_inactive_sites()
	except Exception as e:
		frappe.log_error(f"Error in hourly task: {str(e)}", "SaaS Manager Hourly Task")


def daily():
	"""
	Daily tasks - check subscription expiry and update status
	"""
	try:
		from frappe.utils import today
		
		# Get all sites with active subscriptions that have expired
		sites = frappe.get_all(
			"Site Registration",
			filters={
				"subscription_status": "Active",
				"subscription_end_date": ["<", today()]
			},
			fields=["name"]
		)
		
		for site in sites:
			doc = frappe.get_doc("Site Registration", site.name)
			doc.subscription_status = "Expired"
			doc.is_active = 0
			doc.save(ignore_permissions=True)
			frappe.logger().info("Site %s subscription expired", site.name)
		
		# Set maintenance mode for inactive/expired sites
		set_maintenance_mode_for_inactive_sites()
		
	except Exception as e:
		frappe.log_error(f"Error in daily task: {str(e)}", "SaaS Manager Daily Task")


def weekly():
	"""
	Weekly tasks - generate reports, cleanup old sync data
	"""
	try:
		# Cleanup sync data older than 90 days (optional)
		# This is commented out by default - you may want to keep all sync data
		# from frappe.utils import add_days, today
		# cutoff_date = add_days(today(), -90)
		# old_syncs = frappe.get_all(
		# 	"Site Data Sync",
		# 	filters={"sync_date": ["<", cutoff_date]},
		# 	fields=["name"]
		# )
		# for sync in old_syncs:
		# 	frappe.delete_doc("Site Data Sync", sync.name, ignore_permissions=True)
		pass
	except Exception as e:
		frappe.log_error(f"Error in weekly task: {str(e)}", "SaaS Manager Weekly Task")


def set_maintenance_mode_for_inactive_sites():
	"""
	Set maintenance mode for all inactive/expired sites
	This ensures that sites with expired subscriptions are put into maintenance mode
	"""
	try:
		# Get all inactive sites (is_active = 0 or subscription_status = Expired)
		inactive_sites = frappe.get_all(
			"Site Registration",
			filters={
				"is_active": 0
			},
			fields=["name", "site_url", "api_key", "site_name", "subscription_status"]
		)
		
		for site in inactive_sites:
			if not site.site_url or not site.api_key:
				continue
			
			try:
				# Determine maintenance mode: 1 for inactive sites
				maintenance_mode = 1
				
				# Prepare API endpoint
				api_endpoint = f"{site.site_url}/api/method/sass_client.api.maintenance_api.set_maintenance_mode"
				
				# Make API call to client site
				response = requests.post(
					api_endpoint,
					json={
						"api_key": site.api_key,
						"maintenance_mode": maintenance_mode
					},
					timeout=10
				)
				
				if response.status_code == 200:
					result = response.json()
					if result.get("message", {}).get("status") == "success":
						frappe.logger().info(
							f"Maintenance mode enabled for inactive site {site.site_name} ({site.site_url})"
						)
					else:
						frappe.log_error(
							f"Failed to set maintenance mode for site {site.site_name}: "
							f"{result.get('message', {}).get('message')}",
							"Site Maintenance Mode Scheduler Error"
						)
				else:
					frappe.log_error(
						f"HTTP error setting maintenance mode for site {site.site_name}: "
						f"{response.status_code}",
						"Site Maintenance Mode Scheduler Error"
					)
			except Exception as e:
				frappe.log_error(
					f"Error setting maintenance mode for site {site.site_name}: {str(e)}",
					"Site Maintenance Mode Scheduler Error"
				)
		
		frappe.logger().info(f"Maintenance mode check completed for {len(inactive_sites)} inactive sites")
		
	except Exception as e:
		frappe.log_error(f"Error in set_maintenance_mode_for_inactive_sites: {str(e)}", "Site Maintenance Mode Scheduler Error")
