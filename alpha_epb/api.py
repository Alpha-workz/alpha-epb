import frappe
from frappe.model.document import Document
from frappe import whitelist
from frappe.utils.data import now

@frappe.whitelist()
# find the batch number using the spp ref number ex 2501dbbm
# directly from stock entry find the batch number and item details where item group is Products
def get_oven_operations_specification(spp_ref_number):
    """
    Find batch number and oven operations specification using SPP reference number
    
    Args:
        spp_ref_number: SPP reference number (e.g., "25F07X05")
        
    Returns:
        dict: Complete oven operations specification with batch and item details
    """
    
    # Step 1: Find Stock Entry Detail with matching spp_batch_number and item group "Products"
    stock_entry_query = """
        SELECT SED.batch_no, SED.item_code, SED.qty, SED.parent as stock_entry_name, SED.t_warehouse
        FROM `tabStock Entry Detail` SED 
        INNER JOIN `tabStock Entry` SE ON SED.parent = SE.name
        INNER JOIN `tabItem` I ON SED.item_code = I.name
        WHERE SED.spp_batch_number = %s 
        AND I.item_group = 'Products'
        AND SE.docstatus = 1
        AND SED.is_finished_item = 1
        ORDER BY SE.creation DESC
        LIMIT 1
    """
    
    stock_entry_result = frappe.db.sql(stock_entry_query, (spp_ref_number,), as_dict=1)
    
    if not stock_entry_result:
        frappe.throw(f"No Stock Entry found for SPP ref number: {spp_ref_number} with item group 'Products'")
    
    stock_entry_data = stock_entry_result[0]
    batch_no = stock_entry_data.get('batch_no')
    item_code = stock_entry_data.get('item_code')
    qty = stock_entry_data.get('qty')
    stock_entry_name = stock_entry_data.get('stock_entry_name')
    warehouse = stock_entry_data.get('t_warehouse')
    
    # Step 2: Verify the batch exists
    batch_exists = frappe.db.exists('Batch', batch_no)
    if not batch_exists:
        frappe.throw(f"Batch {batch_no} not found in system")
    
    # Step 3: Get the Oven Operations Specification for the item
    oven_spec_name = frappe.db.get_value('Oven Operations Specification', {'product': item_code}, 'name')
    
    if not oven_spec_name:
        frappe.throw(f"Oven Operations Specification not found for item: {item_code}")
    
    # Step 4: Load the complete document including child tables
    oven_spec_doc = frappe.get_doc('Oven Operations Specification', oven_spec_name)
    
    # Step 5: Add batch and item details to the response
    response = oven_spec_doc.as_dict()
    response.update({
        'batch_details': {
            'batch_no': batch_no,
            'item_code': item_code,
            'qty': qty,
            'spp_ref_number': spp_ref_number,
            'stock_entry_reference': stock_entry_name,
            'warehouse': warehouse
        }
    })
    
    return response

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

@frappe.whitelist()
def get_oven_operations_specification_by_batch(batch_no):
    """
    Get oven operations specification using batch number directly
    
    Args:
        batch_no: Batch number (e.g., "T25F07X05")
        
    Returns:
        dict: Complete oven operations specification with batch details
    """
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
    
    # Add batch details to the response
    response = oven_spec_doc.as_dict()
    response.update({
        'batch_details': {
            'batch_no': batch_no,
            'item_code': item
        }
    })

    return response


# ---------------------------------------------------------------------------
# Mixing Sequence endpoints
# ---------------------------------------------------------------------------

@frappe.whitelist()
def create_mixing_sequence(mixing_sequence_id, item_code, mixing_center=None,
                           batch_weight=0, sequence_items=None, parameters=None,
                           submit=False):
    """
    Create a new Mixing Sequence.

    Args:
        mixing_sequence_id: The name/ID for the record (e.g. "C_6122-002"). Naming is manual.
        item_code: Item this mixing sequence is for.
        mixing_center: Workstation (mixing center) where mixing happens.
        batch_weight: Batch weight for the sequence.
        sequence_items: List of dicts for the Sequence table
                        (sl_no, sequence, duration, input_item, wt, mixing_seq_ref_list).
        parameters: List of dicts for the Parameters table
                    (parameters_group, parameter, min_value, max_value, uom,
                     pre_post_during, sequence, remarks).
        submit: When truthy, submit the document after inserting.

    Returns:
        dict: status, message and the created document.
    """
    if isinstance(sequence_items, str):
        sequence_items = frappe.parse_json(sequence_items)
    if isinstance(parameters, str):
        parameters = frappe.parse_json(parameters)

    try:
        doc = frappe.get_doc({
            "doctype": "Mixing Sequence",
            "__newname": mixing_sequence_id,
            "item_code": item_code,
            "mixing_center": mixing_center,
            "batch_weight": batch_weight,
            "sequence_items": sequence_items or [],
            "parameters": parameters or [],
        })

        doc.insert()
        if submit and str(submit).lower() not in ("0", "false"):
            doc.submit()
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Mixing Sequence created successfully",
            "mixing_sequence": doc.as_dict(),
        }

    except Exception as e:
        frappe.log_error(f"Error creating Mixing Sequence: {str(e)}")
        frappe.throw(f"Error creating Mixing Sequence: {str(e)}")


@frappe.whitelist()
def get_mixing_sequence(name):
    """Load a complete Mixing Sequence (including its child tables) by name."""
    if not frappe.db.exists('Mixing Sequence', name):
        frappe.throw(f"Mixing Sequence not found: {name}")
    return frappe.get_doc('Mixing Sequence', name).as_dict()


@frappe.whitelist()
def get_mixing_sequences_by_item(item_code):
    """Return all Mixing Sequences defined for a given item, newest first."""
    names = frappe.get_all(
        'Mixing Sequence',
        filters={'item_code': item_code},
        order_by='creation desc',
        pluck='name',
    )
    return [frappe.get_doc('Mixing Sequence', n).as_dict() for n in names]

