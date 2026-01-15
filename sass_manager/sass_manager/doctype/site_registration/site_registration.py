# Copyright (c) 2025, nasirucode and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document
from frappe.utils import random_string
from datetime import datetime


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
			if self.subscription_end_date < self.subscription_start_date:
				frappe.throw("Subscription End Date cannot be before Start Date")

	def on_update(self):
		"""Update subscription status based on dates"""
		if self.subscription_end_date:
			from frappe.utils import today
			if self.subscription_end_date < today():
				if self.subscription_status == "Active":
					self.subscription_status = "Expired"
					self.is_active = 0
			elif self.subscription_status == "Expired" and self.subscription_end_date >= today():
				if self.is_active:
					self.subscription_status = "Active"
