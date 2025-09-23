import frappe

def execute():
    if not frappe.db.exists("Letter Head", "PSOA Letter Head"):
        frappe.get_doc({
            "name": "PSOA Letter Head",
            "letter_head_name": "PSOA Letter Head",
            "source": "HTML",
            "footer_source": "HTML",
            "disabled": 0,
            "is_default": 1,
            "image_height": 0,
            "image_width": 0,
            "align": "Left",
            "content": "    <style>\n        .letterhead-container {\n            max-width: 800px;\n            margin: 20px auto;\n            background: white;\n            padding: 40px;\n            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.05);\n        }\n        .letterhead {\n            text-align: center;\n            padding-bottom: 25px;\n            margin-bottom: 30px;\n            border-bottom: 1px solid #eaeaea;\n        }\n        .company-name {\n            font-size: 24px;\n            font-weight: 600;\n            color: #2c3e50;\n            margin-bottom: 5px;\n            letter-spacing: 0.5px;\n        }\n        .document-title {\n            font-size: 32px;\n            font-weight: 300;\n            color: #2c3e50;\n            letter-spacing: 2px;\n            margin-top: 20px;\n            text-transform: uppercase;\n        }\n    </style>\n\n    <div class=\"letterhead-container\">\n        <div class=\"letterhead\">\n            <div class=\"company-name\">{{ doc.company }}</div>\n            <div class=\"document-title\">Statement of Account</div>\n        </div>\n    </div>\n\n",
            "footer": "",
            "footer_image_height": 0,
            "footer_image_width": 0,
            "footer_align": "Left",
            "doctype": "Letter Head"
        }).insert()