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
							let errorMsg = r.message?.message || 'Unknown error';
							// Show instructions for 503 errors when setting maintenance mode
							if (errorMsg.includes('503') || errorMsg.includes('cannot be reached')) {
								let instructions = __('Site cannot be reached. ') +
									__('If the site is already in maintenance mode, you may need to remove it manually: ') +
									__('Edit site_config.json and set "maintenance_mode": 0, or run: bench --site [site_name] set-maintenance-mode off');
								
								frappe.show_alert({
									message: instructions,
									indicator: 'orange'
								});
							} else {
								frappe.show_alert({
									message: __('Failed to set maintenance mode: ') + errorMsg,
									indicator: 'red'
								});
							}
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
							}, 5);
							frm.reload_doc();
						} else {
							let errorMsg = r.message?.message || 'Unknown error';
							// Show a more helpful message for 503 errors with instructions
							if (errorMsg.includes('503') || errorMsg.includes('maintenance mode') || errorMsg.includes('cannot be reached')) {
								let instructions = __('Site is in maintenance mode and cannot be reached via API. ') +
									__('To remove maintenance mode manually: ') +
									__('1. Edit site_config.json on the client site and set "maintenance_mode": 0, OR ') +
									__('2. Run: bench --site [site_name] set-maintenance-mode off');
								
								frappe.show_alert({
									message: instructions,
									indicator: 'orange'
								}, 10);
							} else {
								frappe.show_alert({
									message: __('Failed to remove maintenance mode: ') + errorMsg,
									indicator: 'red'
								});
							}
						}
					},
					freeze: true,
					freeze_message: __('Removing maintenance mode...')
				});
			}, __('Actions'));
		}
	}
});
