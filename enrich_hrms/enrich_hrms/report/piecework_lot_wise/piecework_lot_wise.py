import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "fieldname": "lot_no",
            "label": _("Lot No"),
            "fieldtype": "Data",
            "width": 100
        },
        {
            "fieldname": "target_pieces",
            "label": _("Target Pieces"),
            "fieldtype": "Int",
            "width": 120
        },
        {
            "fieldname": "worked_pieces",
            "label": _("Worked Pieces"),
            "fieldtype": "Int",
            "width": 120
        },
        {
            "fieldname": "difference",
            "label": _("Difference"),
            "fieldtype": "Int",
            "width": 110
        }
    ]

def get_data(filters):
    conditions = get_conditions(filters)

    return frappe.db.sql("""
        SELECT
            prd.lot_no,
            SUM(prd.target_pieces) AS target_pieces,
            SUM(prd.pieces_completed) AS worked_pieces,
            SUM(prd.target_pieces) - SUM(prd.pieces_completed) AS difference
        FROM
            `tabPiecework Record` pr
        INNER JOIN
            `tabPiecework Details` prd ON prd.parent = pr.name
        WHERE
            pr.docstatus = 1
            AND prd.lot_no IS NOT NULL
            AND prd.lot_no != ''
            {conditions}
        GROUP BY
            prd.lot_no
        ORDER BY
            prd.lot_no
    """.format(conditions=conditions), filters, as_dict=1)

def get_conditions(filters):
    conditions = ""
    if filters.get("from_date"):
        conditions += " AND pr.date >= %(from_date)s"
    if filters.get("to_date"):
        conditions += " AND pr.date <= %(to_date)s"
    if filters.get("lot_no"):
        conditions += " AND prd.lot_no = %(lot_no)s"
    if filters.get("company"):
        conditions += " AND pr.company = %(company)s"
    return conditions