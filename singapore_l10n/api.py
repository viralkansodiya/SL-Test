import frappe

@frappe.whitelist()
def get_sales_person(user):
    if emp := frappe.db.exists("Employee", {'user_id':user}):
        if sales_person := frappe.db.exists("Sales Person", {'Employee' : emp}):
            return sales_person
    return