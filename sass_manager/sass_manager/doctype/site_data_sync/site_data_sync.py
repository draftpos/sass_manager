# Copyright (c) 2025, nasirucode and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document


class SiteDataSync(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		active_users: DF.Int
		client_type: DF.Literal["ERP", "Mobile POS", "Desktop POS", "Fiscalisation"]
		company: DF.Data | None
		ip_address: DF.Data | None
		package_status: DF.Literal["Active", "Expired"]
		site_registration: DF.Link
		site_url: DF.Data | None
		subscription_end_date: DF.Date | None
		subscription_package: DF.Link | None
		subscription_start_date: DF.Date | None
		sync_date: DF.Datetime
		total_companies: DF.Int
		total_credit_notes: DF.Int
		total_purchase_invoices: DF.Int
		total_sales_invoices: DF.Int
		total_stock_reconciliations: DF.Int
	# end: auto-generated types

	pass
