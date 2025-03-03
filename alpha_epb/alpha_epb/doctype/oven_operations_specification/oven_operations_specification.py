# Copyright (c) 2025, AlphaWorkz and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe import whitelist

class OvenOperationsSpecification(Document):
    pass

@frappe.whitelist()
def get_oven_operations_specification_by_batch(batch_no):
    # Find the item linked with the batch
    item = frappe.db.get_value('Batch', {'name': batch_no}, 'item')

    if not item:
        frappe.throw(f"Item not found for batch number: {batch_no}")

    # Retrieve the OvenOperationsSpecification document by the item
    oven_operations_specification = frappe.get_all('Oven Operations Specification', filters={'product': item},fields=['*'])

    if not oven_operations_specification:
        frappe.throw(f"Oven Operations Specification not found for item: {item}")

    return oven_operations_specification
