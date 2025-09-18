import frappe
import json
from frappe.utils import getdate, money_in_words, today, formatdate
from erpnext import get_company_currency
from erpnext.accounts.party import get_party_account_currency
from erpnext.accounts.report.general_ledger.general_ledger import execute as get_soa
from erpnext.accounts.report.accounts_receivable_summary.accounts_receivable_summary import (
    execute as get_ageing,
)


@frappe.whitelist()
def get_statements_of_account_from_gl(name, is_from_customer=False):
    """Generate statement of accounts from General Ledger data"""
    if not is_from_customer:
        name = frappe.form_dict.name

    psoa_doc = frappe.get_doc("Process Statement Of Accounts", name)

    # default date handling
    from_date = psoa_doc.from_date or "2000-01-01"
    to_date = psoa_doc.to_date or today()

    out_data, out_list = {}, []

    for cust in psoa_doc.customers:
        cust_dict = {}

        presentation_currency = (
            get_party_account_currency("Customer", cust.customer, psoa_doc.company)
            or psoa_doc.currency
            or get_company_currency(psoa_doc.company)
        )

        tax_id = frappe.db.get_value("Customer", cust.customer, "tax_id")

        filters = frappe._dict(
            {
                "from_date": from_date,
                "to_date": to_date,
                "company": psoa_doc.company,
                "finance_book": psoa_doc.finance_book or None,
                "account": [psoa_doc.account] if psoa_doc.account else None,
                "party_type": "Customer",
                "party": [cust.customer],
                "presentation_currency": presentation_currency,
                "group_by": psoa_doc.group_by,
                "currency": psoa_doc.currency,
                "cost_center": [cc.cost_center_name for cc in psoa_doc.cost_center],
                "project": [p.project_name for p in psoa_doc.project],
                "show_opening_entries": 0,
                "include_default_book_entries": 0,
                "tax_id": tax_id or None,
            }
        )

        # fetch general ledger results
        _, res = get_soa(filters)
        if not res:
            frappe.throw(f"No data found for customer {cust.customer}")

        # enrich data for Sales Invoices
        for row in res:
            if row.get("voucher_type") == "Sales Invoice":
                sales_invoice = frappe.db.get_value(
                    "Sales Invoice",
                    row.get("voucher_no"),
                    ["due_date", "po_no", "total"],
                    as_dict=True,
                )
                if sales_invoice:
                    row.update({k: v or row.get(k) for k, v in sales_invoice.items()})

        cust_dict["data"] = res

        # customer address
        cad_data = frappe.db.sql(
            """
            SELECT ad.name, ad.address_line1, ad.address_line2, ad.city, ad.email_id,
                   ad.phone, ad.pincode, ad.country,
                   cus.name as customer, cus.customer_name, cus.payment_terms
            FROM tabAddress ad
            LEFT JOIN `tabDynamic Link` dl ON dl.parent = ad.name
            LEFT JOIN tabCustomer cus ON dl.link_name = cus.name
            WHERE dl.link_doctype = 'Customer' AND dl.link_name = %s
            """,
            (cust.customer,),
            as_dict=True,
        )
        if cad_data:
            cust_dict["cad_data"] = cad_data[0]

        # customer primary contact
        cco_data = frappe.db.sql(
            """
            SELECT co.first_name, co.middle_name, co.last_name
            FROM tabContact co
            LEFT JOIN `tabDynamic Link` dl ON dl.parent = co.name
            WHERE dl.link_doctype = 'Customer' AND dl.link_name = %s
              AND co.is_primary_contact = 1
            """,
            (cust.customer,),
            as_dict=True,
        )
        if cco_data:
            cust_dict["cco_data"] = cco_data[0]

        # ageing data if enabled
        if psoa_doc.include_ageing:
            ageing_filters = frappe._dict(
                {
                    "company": psoa_doc.company,
                    "report_date": to_date,
                    "ageing_based_on": psoa_doc.ageing_based_on,
                    "range1": 30,
                    "range2": 60,
                    "range3": 90,
                    "range4": 120,
                    "party": [cust.customer],
                    "party_type": "Customer",
                }
            )
            _, ageing = get_ageing(ageing_filters)
            if ageing:
                ageing[0]["ageing_based_on"] = psoa_doc.ageing_based_on
                cust_dict["ageing"] = ageing[0]

        out_list.append(cust_dict)

    # company address
    cod_data = frappe.db.sql(
        """
        SELECT ad.name, ad.address_line1, ad.address_line2, ad.city, ad.email_id,
               ad.phone, ad.pincode, ad.fax, ad.country
        FROM tabAddress ad
        LEFT JOIN `tabDynamic Link` dl ON dl.parent = ad.name
        WHERE dl.link_doctype = 'Company' AND dl.link_name = %s
        """,
        (psoa_doc.company,),
        as_dict=True,
    )
    if cod_data:
        out_data["cod_data"] = cod_data[0]

    # compile response
    out_data.update(
        {
            "cust": out_list,
            "currency": psoa_doc.currency,
            "to_date": formatdate(to_date, "dd MMM YYYY"),
            "posting_date": formatdate(getdate(), "dd MMM YYYY"),
            "tax_id": frappe.db.get_value("Company", psoa_doc.company, "tax_id"),
        }
    )

    # add outstanding in words + current due for first customer
    if out_list and out_list[0].get("ageing"):
        ageing = out_list[0]["ageing"]
        ageing["outstanding_in_words"] = money_in_words(abs(ageing["outstanding"]))
        ageing["current_due"] = ageing["outstanding"] - sum(
            ageing.get(f"range{i}", 0) for i in range(1, 6)
        )

    return out_data
