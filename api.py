
import frappe
from frappe.model.document import Document
from frappe import whitelist

@frappe.whitelist()
def get_oven_operations_specification(batch_no):
    # Find the item linked with the batch
    item = frappe.db.get_value('Batch', {'name': batch_no}, 'item')

    if not item:
        frappe.throw(f"Item not found for batch number: {batch_no}")

    # Get the first matching Oven Operations Specification
    oven_spec_name = frappe.db.get_value('Oven Operations Specification', {'product': item}, 'name')

    if not oven_spec_name:
        frappe.throw(f"Oven Operations Specification not found for item: {item}")

    # Load the complete document including child tables
    oven_spec_doc = frappe.get_doc('Oven Operations Specification', oven_spec_name)
    
    return oven_spec_doc.as_dict()