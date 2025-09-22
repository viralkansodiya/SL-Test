frappe.ui.form.on('Customer', {
	refresh(frm) {
		frm.add_custom_button(__('Download SOA'), function(){
			frappe.call({
				method: "singapore_l10n.events.customer.get_statements_of_account_for_customer",
				args: {
					name: frm.doc.name
				},
                freeze: true,
			    freeze_message: __("Generating report ..."),
				callback: function (r) {
					const data = r.message[0]
					const header = r.message[1]
                    const report = r.message[2]
                    const p_html = generateStatementHTML(frm, data, header, report);
                    frappe.render_pdf(p_html, { orientation: "Portrait" });
				}
			});
		});
	}
})
// Generate the complete statement HTML
const generateStatementHTML = function(frm, data, header, report) {
    return `
        ${getStyles()}
        ${getHeader(header)}
        ${getCustomerSections(frm, data, report)}
    `;
};

// Get CSS styles for the document
const getStyles = function() {
    return `
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;700&display=swap">
    <style>
        .page-break { display: block; page-break-before: always; }
        
        .lhead {
            font-size: 9px;
            margin-top: 0px;
            margin-bottom: 0px !important;
            vertical-align: top !important;
        }
        
        * {
            font-family: 'IBM Plex Sans', sans-serif !important;
        }
        
        .print-format {
            margin-left: 4mm;
            margin-right: 4mm;
        }
        
        .new1 {
            border-top: 1px dotted !important;
        }
        
        .blhead {
            font-weight: 600 !important;
            font-size: 9px !important;
        }
        
        .print-format .letter-head {
            margin-bottom: 0px;
        }
        
        .print-format .letterhead td, 
        .print-format th {
            padding: 1px !important;
            vertical-align: top !important;
            margin: 0px !important;
        }
        
        .print-format p {
            margin: 0px 0px 2px;
        }
        
        p {
            font-size: 13px;
        }
        
        .address-sec {
            margin-top: 0px;
            margin-bottom: 0px !important;
            vertical-align: text-top;
        }
        
        .left_dotted {
            border-left: 2px dotted !important;
        }
        
        .ontop {
            border-top: 1px solid;
        }
        
        .onbottom {
            border-bottom: 1px solid;
        }
        
        .table-bordered {
            border-collapse: collapse;
            width: 100%;
        }
        
        .table-bordered td, 
        .table-bordered th {
            border: 1px solid #ddd;
            padding: 4px;
        }
        
        .text-right {
            text-align: right;
        }
        
        .text-center {
            text-align: center;
        }
    </style>`;
};

// Get document header
const getHeader = function(header) {
    return `${header}`;
};

// Generate customer sections
const getCustomerSections = function(frm, data, report) {
    let html = '';
    
    if (data.cust && data.cust.length) {
        data.cust.forEach((customer, index) => {
            html += getCustomerSection(frm, customer, data, index, report);
            
            // Add page break if not the last customer
            if (index < data.cust.length - 1) {
                html += `<div class="page-break"></div>${getHeader()}`;
            }
        });
    }
    
    return html;
};

// Generate a single customer section
const getCustomerSection = function(frm, customer, data, index, report) {
    const cad = customer.cad_data || {};
    const ageing = customer.ageing || {};
    
    return `
        ${getCustomerHeader(cad, data.currency, ageing, frm)}
        ${getTransactionsTable(customer.data || [], report)}
        ${getCustomerFooter(ageing, frm.doc.name, data.posting_date)}
    `;
};

// Get customer header information
const getCustomerHeader = function(cad, currency, ageing, frm) {
    return `
    <table width="100%" class="cust_head">
        <tbody>
            <tr>
                <td>
                    <p class="address-sec">${cad.customer_name || ''}</p>
                    <p class="address-sec">${cad.address_line1 || ''}</p>
                    <p class="address-sec">${cad.address_line2 || ''}</p>
                    <p class="address-sec">${cad.city || ''} ${cad.pincode || ''}</p>
                    <p class="address-sec">${cad.country || ''}</p>
                </td>
                <td>
                    <p class="address-sec">Currency : ${currency || ''}</p>
                    <p class="address-sec">Payment Terms : C.O.D</p>
                    <p class="address-sec">Total Due : ${format_currency(ageing.outstanding) || ''}</p>
                </td>
                <td class="left_dotted">
                    <p class="address-sec" style="padding-left: 10px;">Statement No.: ${frm.doc.name}</p>
                    <p class="address-sec" style="padding-left: 10px;">Date: ${frappe.datetime.get_today()} </p>
                </td>
            </tr>
        </tbody>
    </table>
    <hr class="new1">
    `;
};

// Get transactions table
const getTransactionsTable = function(transactions, report) {
    let html = `
            <table class="table-bordered" style="font-size: 13px;">
                <thead>
                    <tr>
                        <th style="width: 5%">No.</th>
                        <th style="width: 20%">Doc NO</th>
                        <th style="width: 12%">DOCDATE</th>
                        <th style="width: 10%">DUE DATE</th>
                        <th style="width: 10%" class="text-right">DEBIT</th>
                        <th style="width: 10%" class="text-right">CREDIT</th>`
        if(report == "General Ledger"){
            html += `<th style="width: 14%" class="text-right">BALANCE</th>`
        }else{
            html += `<th style="width: 14%" class="text-right">Outstading Amount</th>`
        }
        html += `
                    </tr>
                </thead>
                <tbody>`;
    
    if (transactions && transactions.length) {
        transactions.forEach((transaction, idx) => {
            if (transaction.voucher_no) {
                html += getTransactionRow(transaction, idx + 1);
                
                // Add page break every 27 rows
                if ((idx + 1) % 27 === 0) {
                    html += `
                        </tbody>
                        </table>
                        <div class="page-break"></div>
                        ${getHeader()}
                        <table class="table-bordered" style="font-size: 13px;">
                            <thead>
                                <tr>
                                    <th style="width: 5%">No.</th>
                                    <th style="width: 20%">Doc NO</th>
                                    <th style="width: 12%">Document DATE</th>
                                    <th style="width: 10%">DUE DATE</th>
                                    <th style="width: 10%" class="text-right">DEBIT</th>
                                    <th style="width: 10%" class="text-right">CREDIT</th>
                        `
                        html += `<th style="width: 14%" class="text-right">BALANCE</th>`
                   
                    html += `
                                </tr>
                            </thead>
                            <tbody>`;
                }
            }
        });
    }
    
    html += `</tbody></table>`;
    return html;
};

// Get a single transaction row
const getTransactionRow = function(transaction, index) {
    return `
    <tr>
        <td align="center">${index}</td>
        <td align="center">${transaction.voucher_no || ''}</td>
        <td align="center">${transaction.posting_date || ''}</td>
        <td align="center">${transaction.due_date || ''}</td>
        <td class="text-right">${transaction.debit ? format_currency(transaction.debit.toFixed(2)).replace('$', '') : '-'}</td>
        <td class="text-right">${transaction.credit ? format_currency((Number(Math.round((transaction.credit) + Number.EPSILON) * 100) / 100).toFixed(2)).replace('$', '') : '-'}</td>
        <td class="text-right">${transaction.balance ? format_currency(transaction.balance) : '-'}</td>
    </tr>`;
};

// Get customer footer with summary
const getCustomerFooter = function(ageing, statementNo, postingDate) {
    return `
    <div id="footer-html" class="visible-pdf letter-head-footer">
        <table width="100%" class="table">
            <tbody>
                <tr>
                    <td width="14%" class="ontop onbottom"><p><b>In Words:</b></p></td>
                    <td width="58%" class="ontop onbottom"><p>${ageing.outstanding_in_words || ''}</p></td>
                    <td width="12%" class="ontop onbottom"><p><b>Total Due:</b></p></td>
                    <td width="16%" class="ontop onbottom"><p>${format_currency(ageing.outstanding) || '-'}</p></td>
                </tr>
            </tbody>
        </table>
        <table class="table-bordered" style="font-size: 13px;">
            <thead>
                <tr>
                    <th style="width: 16%" class="text-center">Current Due</th>
                    <th style="width: 16%" class="text-center">1-30 Days</th>
                    <th style="width: 16%" class="text-center">31-60 Days</th>
                    <th style="width: 16%" class="text-center">61-90 Days</th>
                    <th style="width: 16%" class="text-center">120+ Days</th>
                    <th style="width: 16%" class="text-center">Amount Due</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td class="text-center">${format_currency(ageing.range1) || '-'}</td>
                    <td class="text-center">${format_currency(ageing.range2) || '-'}</td>
                    <td class="text-center">${format_currency(ageing.range3) || '-'}</td>
                    <td class="text-center">${format_currency(ageing.range4) || '-'}</td>
                    <td class="text-center">${format_currency(ageing.outstanding) || '-'}</td>
                </tr>
            </tbody>
        </table>
		<br>
        <center style="font-size: 8px;">THIS IS A COMPUTER GENERATED DOCUMENT. NO SIGNATURE IS REQUIRED.</center>
    </div>`;
};