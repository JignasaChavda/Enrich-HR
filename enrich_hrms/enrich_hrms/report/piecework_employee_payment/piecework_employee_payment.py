import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    data = add_totals_row(data)
    return columns, data

def get_columns():
    return [
        {
            "fieldname": "employee",
            "label": _("Employee"),
            "fieldtype": "Link",
            "options": "Employee",
            "width": 150
        },
        {
            "fieldname": "employee_name",
            "label": _("Employee Name"),
            "fieldtype": "Data",
            "width": 140
        },
        {
            "fieldname": "department",
            "label": _("Department"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "designation",
            "label": _("Designation"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "total_pieces_worked",
            "label": _("Pieces Worked"),
            "fieldtype": "Int",
            "width": 110
        },
        {
            "fieldname": "total_amount",
            "label": _("Total Amount"),
            "fieldtype": "Currency",
            "width": 120
        }
    ]

def get_data(filters):
    # Step 1: Get all submitted Piecework Records in the date range
    pr_conditions = {"docstatus": 1}

    if filters.get("from_date"):
        pr_conditions["date"] = [">=", filters["from_date"]]
    if filters.get("from_date") and filters.get("to_date"):
        pr_conditions["date"] = ["between", [filters["from_date"], filters["to_date"]]]
    if filters.get("company"):
        pr_conditions["company"] = filters["company"]

    piecework_records = frappe.get_all(
        "Piecework Record",
        filters=pr_conditions,
        fields=["name", "date", "company"]
    )

    if not piecework_records:
        return []

    # Step 2: Loop through each Piecework Record and collect child rows
    employee_map = {}  # key: employee id

    for pr in piecework_records:
        # Get all child rows from Piecework Details for this parent
        detail_filters = {"parent": pr.name}
        if filters.get("employee"):
            detail_filters["employee"] = filters["employee"]

        details = frappe.get_all(
            "Piecework Details",
            filters=detail_filters,
            fields=[
                "employee",
                "employee_name",
                "department",
                "designation",
                "pieces_completed",
                "amount"
            ]
        )
        
        # Step 3: Aggregate per employee
        for row in details:
            print("\n\n\n\n", {row.employee}, {row.pieces_completed}, {row.amount} ,"\n\n\n")
            emp = row.employee
            if not emp:
                continue

            if emp not in employee_map:
                employee_map[emp] = {
                    "employee":           emp,
                    "employee_name":      row.employee_name or "",
                    "department":         row.department or "",
                    "designation":        row.designation or "",
                    "total_pieces_worked": 0,
                    "total_amount":       0.0
                }

            employee_map[emp]["total_pieces_worked"] += row.pieces_completed or 0
            employee_map[emp]["total_amount"]        += row.amount or 0.0

    # Step 4: Sort by employee name and return as list
    data = sorted(employee_map.values(), key=lambda x: x["employee_name"])
    return data

def add_totals_row(data):
    if not data:
        return data

    total_row = {
        "employee":            "",
        "employee_name":       "Total",
        "department":          "",
        "designation":         "",
        "total_pieces_worked": sum(r.get("total_pieces_worked") or 0 for r in data),
        "total_amount":        sum(r.get("total_amount") or 0.0 for r in data),
        "bold": 1
    }

    data.append(total_row)
    return data