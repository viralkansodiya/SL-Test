# Copyright (c) 2024, earthians and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import formatdate

class PaymentVoucher(Document):
	pass



@frappe.whitelist()
def get_supplier_payments(company, supplier, from_date, to_date):
	result = {}
	condition = f""
	condition += f" and pe.company = '{company}'"
	condition += f" and pe.party = '{supplier}'"
	condition += f" and pe.posting_date >= '{from_date}'"
	condition += f" and pe.posting_date <= '{to_date}'"

	data = frappe.db.sql(f"""
			Select pe.name, pe.party_type, pe.party, ref.reference_doctype, 
			ref.reference_name, ref.total_amount, ref.outstanding_amount, 
			ref.allocated_amount, pe.posting_date,
			pe.paid_from_account_currency
			From `tabPayment Entry` as pe
			Left join `tabPayment Entry Reference` as ref ON pe.name = ref.parent
			where pe.docstatus = 1  {condition}
	""",as_dict = 1)
	
	for row in data:
		row.update({'posting_date': formatdate(row.posting_date , "dd MMM YYYY")})

	address = frappe.db.sql(f"""
	Select ad.name as title, ad.address_line1, ad.address_line2, ad.city, ad.country, ad.pincode, dl.link_name as party
	From `tabAddress` as ad
	Left join `tabDynamic Link` as  dl ON dl.parent = ad.name
	Where ad.address_type = "Billing" and dl.link_name = '{supplier}'
	""",as_dict =1)
	
	result['data'] = data
	result['address'] = address[0]
	result['currency'] = data[0].paid_from_account_currency
	result['payment_terms'] = 'C.O.D'
	
	
	return  result