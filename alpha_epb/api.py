
import frappe
from frappe.model.document import Document
from frappe import whitelist
from frappe.utils.data import now

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

# ... existing code ...

@frappe.whitelist()
def create_oven_job_card(batch_number, qty, workstation, operator=None, starting_temperature=0, closing_temperature=0):
    """
    Create a new Oven Job Card for a given batch
    Args:
        batch_number: Batch Number reference
        qty: Quantity to process
        workstation: Workstation where the operation will be performed
        operator: Optional operator assignment
    """
    try:
        # Create new Oven Job Card
        job_card = frappe.get_doc({
            "doctype": "Oven Job Card",
            "batch_number": batch_number,
            "qty": qty,
            "workstation": workstation,
            "operator": operator,
            "status": "Running",
            "start_time": now(),
            "end_time": None,
            "starting_temperature": starting_temperature,  # Initial temperature
            "closing_temperature": 0,   # Initial temperature
        })
        
        job_card.insert()
        frappe.db.commit()
        
        return {
            "status": "success",
            "message": "Oven Job Card created successfully",
            "job_card": job_card
        }
        
    except Exception as e:
        frappe.log_error(f"Error creating Oven Job Card: {str(e)}")
        frappe.throw(f"Error creating Oven Job Card: {str(e)}")

def get_oven_job_card(batch_no,job_card_no):
    job_card = frappe.get_doc('Oven Job Card', job_card_no)
    return job_card.as_dict()

@frappe.whitelist()
def update_oven_job_card(job_card_no, closing_temperature=0):
    job_card = frappe.get_doc('Oven Job Card', job_card_no)
    job_card.closing_temperature = closing_temperature
    job_card.status = "Completed"
    job_card.end_time = now()
    job_card.submit()
    frappe.db.commit()
    return job_card.as_dict()
