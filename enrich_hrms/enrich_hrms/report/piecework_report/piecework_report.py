import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "fieldname": "date",
            "label": _("Date"),
            "fieldtype": "Date",
            "width": 100
        },
        {
            "fieldname": "employee",
            "label": _("Employee"),
            "fieldtype": "Link",
            "options": "Employee",
            "width": 140
        },
        {
            "fieldname": "employee_name",
            "label": _("Employee Name"),
            "fieldtype": "Data",
            "width": 130
        },
        {
            "fieldname": "lot_no",
            "label": _("Lot No"),
            "fieldtype": "Data",
            "width": 80
        },
        {
            "fieldname": "operation",
            "label": _("Operation"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "rate_per_piece",
            "label": _("Rate Per Piece"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "pieces_completed",
            "label": _("Pieces Worked"),
            "fieldtype": "Int",
            "width": 110
        },
        {
            "fieldname": "amount",
            "label": _("Amount"),
            "fieldtype": "Currency",
            "width": 110
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)

    return frappe.db.sql("""
        SELECT
            pr.date,
            prd.employee,
            prd.employee_name,
            prd.lot_no,
            prd.operation,
            prd.rate_per_piece,
            prd.pieces_completed,
            (prd.pieces_completed * prd.rate_per_piece) AS amount
        FROM
            `tabPiecework Record` pr
        INNER JOIN
            `tabPiecework Details` prd ON prd.parent = pr.name
        WHERE
            pr.docstatus = 1
            {conditions}
        ORDER BY
            pr.date, prd.employee_name
    """.format(conditions=conditions), filters, as_dict=1)

def get_conditions(filters):
    conditions = ""
    if filters.get("from_date"):
        conditions += " AND pr.date >= %(from_date)s"
    if filters.get("to_date"):
        conditions += " AND pr.date <= %(to_date)s"
    if filters.get("employee"):
        conditions += " AND prd.employee = %(employee)s"
    if filters.get("company"):
        conditions += " AND pr.company = %(company)s"
    return conditions