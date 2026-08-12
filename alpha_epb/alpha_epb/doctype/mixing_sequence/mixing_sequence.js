// Copyright (c) 2026, AlphaWorkz and contributors
// For license information, please see license.txt

frappe.ui.form.on("Mixing Sequence", {
	setup(frm) {
		frm.set_query("item_code", () => ({
			filters: { item_group: ["in", ["Compound", "Batch"]] },
		}));
		frm.set_query("bom", () => ({
			filters: { item: frm.doc.item_code, docstatus: 1, is_active: 1 },
		}));
	},
});
