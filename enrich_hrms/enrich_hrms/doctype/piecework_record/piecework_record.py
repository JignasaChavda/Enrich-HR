# Copyright (c) 2025, jignasha@sanskartechnolab.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class PieceworkRecord(Document):
    pass

@frappe.whitelist()
def fetch_employees(company, emp_type):
    employees = frappe.get_all("Employee", 
                               filters={"company": company, "employment_type": emp_type, "status": "Active"},
                               fields=["name", "employee_name", "department", "designation"])
    return employees
