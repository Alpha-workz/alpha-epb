
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
    """
    Update the status and closing temperature of an Oven Job Card.

    This function updates the specified Oven Job Card with the provided closing temperature,
    sets its status to "Completed", records the end time, and submits the changes to the database.

    Args:
        job_card_no (str): The unique identifier of the Oven Job Card to be updated.
        closing_temperature (int, optional): The closing temperature to be recorded. Defaults to 0.

    Returns:
        dict: A dictionary representation of the updated Oven Job Card.

    Raises:
        frappe.DoesNotExistError: If the specified Oven Job Card does not exist.
        frappe.ValidationError: If there is an issue with the data validation.
        frappe.PermissionError: If the user does not have permission to update the Oven Job Card.

    Example:
        >>> update_oven_job_card("JOB12345", 200)
        {
            'name': 'JOB12345',
            'closing_temperature': 200,
            'status': 'Completed',
            'end_time': '2023-10-05 14:30:00',
            ...
        }
    """
    job_card = frappe.get_doc('Oven Job Card', job_card_no)
    job_card.closing_temperature = closing_temperature
    job_card.status = "Completed"
    job_card.end_time = now()
    job_card.submit()
    frappe.db.commit()
    return job_card.as_dict()
