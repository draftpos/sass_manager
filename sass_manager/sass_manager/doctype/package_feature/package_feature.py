# Copyright (c) 2025, nasirucode and Contributors
# License: MIT. See LICENSE

import frappe
from frappe.model.document import Document


class PackageFeature(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		feature_description: DF.SmallText | None
		feature_name: DF.Data
	# end: auto-generated types

	pass
