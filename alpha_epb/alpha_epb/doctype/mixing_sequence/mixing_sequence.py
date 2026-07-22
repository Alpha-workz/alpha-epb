# Copyright (c) 2026, AlphaWorkz and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class MixingSequence(Document):
	"""Mixing sequence standard for a product: header (item, mixing center, batch weight),
	the ordered sequence of input items, and the process parameters table."""
	pass
