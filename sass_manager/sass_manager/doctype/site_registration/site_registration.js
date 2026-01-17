// Copyright (c) 2025, nasirucode and Contributors
// License: MIT. See LICENSE

frappe.ui.form.on('Site Registration', {
	refresh: function(frm) {
		// Only show buttons if site_url and api_key are present
		if (!frm.doc.site_url || !frm.doc.api_key) {
			return;
		}
		
		// Add button to set maintenance mode for inactive sites
		if (frm.doc.is_active === 0) {
			frm.add_custom_button(__('Set Maintenance Mode'), function() {
				frappe.call({
					method: 'sass_manager.sass_manager.doctype.site_registration.site_registration.set_maintenance_mode',
					args: {
						site_name: frm.doc.name,
						maintenance_mode: 1
					},
					callback: function(r) {
						if (r.message && r.message.status === 'success') {
							frappe.show_alert({
								message: __('Maintenance mode enabled successfully'),
								indicator: 'green'
							});
							frm.reload_doc();
						} else {
							frappe.show_alert({
								message: __('Failed to set maintenance mode: ') + (r.message?.message || 'Unknown error'),
								indicator: 'red'
							});
						}
					},
					freeze: true,
					freeze_message: __('Setting maintenance mode...')
				});
			}, __('Actions'));
		}
		
		// Add button to remove maintenance mode for active sites
		if (frm.doc.is_active === 1) {
			frm.add_custom_button(__('Remove Maintenance Mode'), function() {
				frappe.call({
					method: 'sass_manager.sass_manager.doctype.site_registration.site_registration.set_maintenance_mode',
					args: {
						site_name: frm.doc.name,
						maintenance_mode: 0
					},
					callback: function(r) {
						if (r.message && r.message.status === 'success') {
							frappe.show_alert({
								message: __('Maintenance mode disabled successfully'),
								indicator: 'green'
							});
							frm.reload_doc();
						} else {
							frappe.show_alert({
								message: __('Failed to remove maintenance mode: ') + (r.message?.message || 'Unknown error'),
								indicator: 'red'
							});
						}
					},
					freeze: true,
					freeze_message: __('Removing maintenance mode...')
				});
			}, __('Actions'));
		}
	}
});
