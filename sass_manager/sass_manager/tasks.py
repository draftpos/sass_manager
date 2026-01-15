# Copyright (c) 2025, nasirucode and Contributors
# License: MIT. See LICENSE

"""
Scheduled tasks for SaaS Manager
"""

import frappe


def hourly():
	"""
	Hourly tasks - sync site data from registered sites
	"""
	try:
		# Get all active site registrations
		# Note: Actual sync happens from client side
		# This is just a placeholder for any server-side hourly tasks
		pass
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
