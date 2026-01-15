# Copyright (c) 2025, nasirucode and Contributors
# License: MIT. See LICENSE

"""
Report generation utilities for SaaS Manager
"""

import frappe
from frappe import _


@frappe.whitelist()
def get_site_summary():
	"""
	Get summary of all sites
	
	Returns:
		dict: Summary statistics
	"""
	try:
		total_sites = frappe.db.count("Site Registration")
		active_sites = frappe.db.count("Site Registration", {"is_active": 1})
		expired_sites = frappe.db.count("Site Registration", {"subscription_status": "Expired"})
		pending_sites = frappe.db.count("Site Registration", {"subscription_status": "Pending"})
		
		# Get latest sync data
		latest_syncs = frappe.db.sql("""
			SELECT 
				sds.site_registration,
				sds.active_users,
				sds.total_companies,
				sds.total_sales_invoices,
				sds.total_purchase_invoices,
				sds.sync_date
			FROM `tabSite Data Sync` sds
			INNER JOIN (
				SELECT site_registration, MAX(sync_date) as max_sync_date
				FROM `tabSite Data Sync`
				GROUP BY site_registration
			) latest ON sds.site_registration = latest.site_registration 
				AND sds.sync_date = latest.max_sync_date
		""", as_dict=True)
		
		total_users = sum(sync.get("active_users", 0) for sync in latest_syncs)
		total_companies = sum(sync.get("total_companies", 0) for sync in latest_syncs)
		total_sales_invoices = sum(sync.get("total_sales_invoices", 0) for sync in latest_syncs)
		total_purchase_invoices = sum(sync.get("total_purchase_invoices", 0) for sync in latest_syncs)
		
		# Get revenue from deposits
		total_revenue = frappe.db.sql("""
			SELECT SUM(amount) as total
			FROM `tabUser Deposit`
			WHERE payment_status = 'Completed'
		""", as_dict=True)
		
		revenue = total_revenue[0].total if total_revenue and total_revenue[0].total else 0
		
		return {
			"total_sites": total_sites,
			"active_sites": active_sites,
			"expired_sites": expired_sites,
			"pending_sites": pending_sites,
			"total_users": total_users,
			"total_companies": total_companies,
			"total_sales_invoices": total_sales_invoices,
			"total_purchase_invoices": total_purchase_invoices,
			"total_revenue": revenue
		}
	except Exception as e:
		frappe.log_error(f"Error getting site summary: {str(e)}")
		return {}


@frappe.whitelist()
def get_site_details(site_registration):
	"""
	Get detailed information about a specific site
	
	Args:
		site_registration: Name of Site Registration
	
	Returns:
		dict: Site details
	"""
	try:
		site = frappe.get_doc("Site Registration", site_registration)
		
		# Get latest sync data
		latest_sync = frappe.db.sql("""
			SELECT *
			FROM `tabSite Data Sync`
			WHERE site_registration = %s
			ORDER BY sync_date DESC
			LIMIT 1
		""", site_registration, as_dict=True)
		
		# Get deposit history
		deposits = frappe.get_all(
			"User Deposit",
			filters={"site_registration": site_registration},
			fields=["*"],
			order_by="deposit_date DESC"
		)
		
		# Get sync history (last 30 days)
		from frappe.utils import add_days, today
		thirty_days_ago = add_days(today(), -30)
		
		sync_history = frappe.get_all(
			"Site Data Sync",
			filters={
				"site_registration": site_registration,
				"sync_date": [">=", thirty_days_ago]
			},
			fields=["sync_date", "active_users", "total_sales_invoices", "total_purchase_invoices"],
			order_by="sync_date DESC"
		)
		
		return {
			"site": site.as_dict(),
			"latest_sync": latest_sync[0] if latest_sync else None,
			"deposits": deposits,
			"sync_history": sync_history
		}
	except Exception as e:
		frappe.log_error(f"Error getting site details: {str(e)}")
		return {}


@frappe.whitelist()
def get_package_statistics():
	"""
	Get statistics by subscription package
	
	Returns:
		dict: Package statistics
	"""
	try:
		packages = frappe.get_all("Subscription Package", fields=["name", "package_name", "max_users", "price"])
		
		package_stats = []
		for package in packages:
			sites = frappe.get_all(
				"Site Registration",
				filters={"subscription_package": package.name},
				fields=["name", "subscription_status", "is_active"]
			)
			
			active_sites = len([s for s in sites if s.is_active])
			total_sites = len(sites)
			
			# Get total users for this package
			site_names = [s.name for s in sites]
			if site_names:
				total_users = frappe.db.sql("""
					SELECT SUM(active_users) as total
					FROM `tabSite Data Sync`
					WHERE site_registration IN %s
					AND sync_date IN (
						SELECT MAX(sync_date)
						FROM `tabSite Data Sync`
						WHERE site_registration IN %s
						GROUP BY site_registration
					)
				""", (site_names, site_names), as_dict=True)
				
				users = total_users[0].total if total_users and total_users[0].total else 0
			else:
				users = 0
			
			package_stats.append({
				"package_name": package.package_name,
				"max_users": package.max_users,
				"price": package.price,
				"total_sites": total_sites,
				"active_sites": active_sites,
				"total_users": users
			})
		
		return package_stats
	except Exception as e:
		frappe.log_error(f"Error getting package statistics: {str(e)}")
		return []
