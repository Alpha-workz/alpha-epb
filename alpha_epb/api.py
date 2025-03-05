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

@frappe.whitelist()
def get_running_oven_jobs():
    """
    Get all running oven job cards.
    
    Returns:
        list: List of running oven job cards
    """
    jobs = frappe.get_all('Oven Job Card', 
        filters={'status': 'Running'},
        fields=['name', 'batch_number', 'workstation', 'operator', 'start_time', 'starting_temperature']
    )
    return jobs

@frappe.whitelist()
def cancel_oven_job_card(job_card_no, reason=None):
    """
    Cancel an Oven Job Card
    
    Args:
        job_card_no (str): The job card to cancel
        reason (str, optional): Reason for cancellation
    
    Returns:
        dict: The updated job card
    """
    try:
        job_card = frappe.get_doc('Oven Job Card', job_card_no)
        job_card.status = "Cancelled"
        job_card.end_time = now()
        job_card.cancellation_reason = reason
        job_card.save()
        frappe.db.commit()
        return job_card.as_dict()
    except Exception as e:
        frappe.log_error(f"Error cancelling Oven Job Card: {str(e)}")
        frappe.throw(f"Error cancelling Oven Job Card: {str(e)}")

@frappe.whitelist()
def pause_oven_job_card(job_card_no, reason=None):
    """
    Pause a running Oven Job Card
    
    Args:
        job_card_no (str): The job card to pause
        reason (str, optional): Reason for pausing
    
    Returns:
        dict: The updated job card
    """
    try:
        job_card = frappe.get_doc('Oven Job Card', job_card_no)
        if job_card.status != "Running":
            frappe.throw("Can only pause running job cards")
            
        job_card.status = "Paused"
        job_card.pause_reason = reason
        job_card.pause_time = now()
        job_card.save()
        frappe.db.commit()
        return job_card.as_dict()
    except Exception as e:
        frappe.log_error(f"Error pausing Oven Job Card: {str(e)}")
        frappe.throw(f"Error pausing Oven Job Card: {str(e)}")

@frappe.whitelist()
def resume_oven_job_card(job_card_no):
    """
    Resume a paused Oven Job Card
    
    Args:
        job_card_no (str): The job card to resume
    
    Returns:
        dict: The updated job card
    """
    try:
        job_card = frappe.get_doc('Oven Job Card', job_card_no)
        if job_card.status != "Paused":
            frappe.throw("Can only resume paused job cards")
            
        job_card.status = "Running"
        job_card.resume_time = now()
        job_card.save()
        frappe.db.commit()
        return job_card.as_dict()
    except Exception as e:
        frappe.log_error(f"Error resuming Oven Job Card: {str(e)}")
        frappe.throw(f"Error resuming Oven Job Card: {str(e)}")

@frappe.whitelist()
def get_oven_job_card_history(batch_no):
    """
    Get history of all oven job cards for a batch
    
    Args:
        batch_no (str): Batch number to get history for
    
    Returns:
        list: List of job cards for the batch
    """
    try:
        jobs = frappe.get_all('Oven Job Card',
            filters={'batch_number': batch_no},
            fields=['name', 'status', 'start_time', 'end_time', 
                   'starting_temperature', 'closing_temperature',
                   'operator', 'workstation'],
            order_by='creation desc'
        )
        return jobs
    except Exception as e:
        frappe.log_error(f"Error fetching Oven Job Card history: {str(e)}")
        frappe.throw(f"Error fetching Oven Job Card history: {str(e)}")
