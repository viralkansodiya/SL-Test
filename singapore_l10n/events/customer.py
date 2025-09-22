import frappe
from frappe.utils import today
from singapore_l10n.events.process_statement_of_accounts import get_statements_of_account_from_gl


@frappe.whitelist()
def get_statements_of_account_for_customer(name):
    psoa_name =  f"{name}-{today()}"
    if frappe.db.exists("Process Statement Of Accounts", psoa_name):
        psoa_doc = frappe.get_doc("Process Statement Of Accounts", psoa_name)
        return get_statements_of_account_from_gl(psoa_doc.name, is_from_customer=True)
    psoa_doc = frappe.new_doc("Process Statement Of Accounts")
    psoa_doc.report = "Accounts Receivable"
    psoa_doc.posting_date = today()
    psoa_doc.from_date = '2000-01-01'
    psoa_doc.to_date = today()
    psoa_doc.append("customers", {
        'customer' : name
    })
    psoa_doc.name = f"{name}-{today()}"
    psoa_doc.insert(ignore_permissions=True)
    frappe.db.commit()

    return get_statements_of_account_from_gl(psoa_doc.name, is_from_customer=True)