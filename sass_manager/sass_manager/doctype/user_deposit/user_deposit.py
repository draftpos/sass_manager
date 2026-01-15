# Copyright (c) 2025, nasirucode and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document


class UserDeposit(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amount: DF.Currency
		applied_to_subscription: DF.Check
		currency: DF.Link
		deposit_date: DF.Date
		gateway_transaction_id: DF.Data | None
		naming_series: DF.Literal["UD-.YYYY.-"]
		notes: DF.TextEditor | None
		payment_gateway: DF.Data | None
		payment_method: DF.Literal["Manual", "Payment Gateway", "Bank Transfer", "Cash"]
		payment_status: DF.Literal["Pending", "Completed", "Failed", "Cancelled"]
		site_registration: DF.Link
		transaction_reference: DF.Data | None
	# end: auto-generated types

	def on_update(self):
		"""Update subscription when payment is completed"""
		if self.payment_status == "Completed" and not self.applied_to_subscription:
			# Auto-apply to subscription if needed
			self.apply_to_subscription()

	def apply_to_subscription(self):
		"""Apply deposit to subscription"""
		site = frappe.get_doc("Site Registration", self.site_registration)
		if site.subscription_package:
			# Update subscription dates based on package price
			package = frappe.get_doc("Subscription Package", site.subscription_package)
			if package.price > 0:
				from frappe.utils import add_months, today
				months = int(self.amount / package.price)
				if months > 0:
					if not site.subscription_start_date:
						site.subscription_start_date = today()
					site.subscription_end_date = add_months(site.subscription_start_date, months)
					site.subscription_status = "Active"
					site.is_active = 1
					site.save()
					self.applied_to_subscription = 1
					self.save()
					frappe.msgprint(f"Subscription extended by {months} month(s)")
