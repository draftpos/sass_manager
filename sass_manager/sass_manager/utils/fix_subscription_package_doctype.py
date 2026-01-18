#!/usr/bin/env python3
"""
Script to fix Subscription Package doctype metadata in the database.
This updates the is_child flag to 0 so Frappe doesn't query the parent column.

Usage:
    bench --site <site_name> console
    Then run: exec(open('apps/sass_manager/sass_manager/sass_manager/utils/fix_subscription_package_doctype.py').read())
    
    OR
    
    bench --site <site_name> execute sass_manager.sass_manager.utils.fix_subscription_package_doctype.fix_doctype
"""

import frappe


def fix_doctype():
	"""Update Subscription Package doctype to set is_child = 0"""
	try:
		# Get the DocType document
		doctype_doc = frappe.get_doc("DocType", "Subscription Package")
		
		# Check current value
		current_is_child = doctype_doc.get("is_child", 0)
		print(f"Current is_child value: {current_is_child}")
		
		# Update is_child to 0 if it's not already
		if current_is_child != 0:
			doctype_doc.db_set("is_child", 0, update_modified=False)
			print("✓ Updated is_child to 0 in database")
		else:
			print("✓ is_child is already 0")
		
		# Also ensure document_type is correct
		if doctype_doc.document_type != "Setup":
			doctype_doc.db_set("document_type", "Setup", update_modified=False)
			print("✓ Updated document_type to Setup")
		
		# Clear cache to ensure changes take effect
		frappe.clear_cache(doctype="Subscription Package")
		frappe.db.commit()
		
		print("✓ DocType metadata updated successfully!")
		print("✓ Cache cleared. Try loading the Subscription Package now.")
		
	except frappe.DoesNotExistError:
		print("✗ Error: Subscription Package doctype not found in database")
		print("  Run 'bench migrate' to create the doctype first.")
	except Exception as e:
		print(f"✗ Error: {str(e)}")
		import traceback
		traceback.print_exc()


if __name__ == "__main__":
	# This will only run if executed directly
	# For bench console, import and call fix_doctype()
	pass
