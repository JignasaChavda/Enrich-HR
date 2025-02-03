// Copyright (c) 2025, jignasha@sanskartechnolab.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('Piecework Record', {
    get_employees: function(frm) {
        let date = frm.doc.date;  
        let company = frm.doc.company;  
        let emp_type = frm.doc.employment_type;

        if (!date || !company || !emp_type) {
            frappe.msgprint(__('Please fill all the fields before proceeding'), __('Validation Error'));
        } else {
            frappe.call({
                method: "enrich_hrms.enrich_hrms.doctype.piecework_record.piecework_record.fetch_employees",
                args: {
                    "company": company,
                    "emp_type": emp_type
                },
                freeze: true,
                freeze_message: "Fetching employees, please wait...",
                callback: function(r) {
                    if (r.message) {
                        let employees = r.message;
                        frm.clear_table("piecework_details");  
                        
                        employees.forEach(emp => {
                            let row = frm.add_child("piecework_details");
                            row.employee = emp.name;
                            row.employee_name = emp.employee_name;
                            row.department = emp.department;
                            row.designation = emp.designation
                        });

                        frm.refresh_field("piecework_details");
                       
                    }
                }
            });
        }
    },
});

frappe.ui.form.on('Piecework Details', {
    pieces_completed: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];

        var pieces = row.pieces_completed;
        var rate_per_piece = row.rate_per_piece;
        if(pieces && rate_per_piece){
            var amount = pieces*rate_per_piece;
            console.log(amount)

            frappe.model.set_value(cdt, cdn, 'amount', amount);
        }
    
    },
    rate_per_piece: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];

        var pieces = row.pieces_completed;
        var rate_per_piece = row.rate_per_piece;
        if(pieces && rate_per_piece){
            var amount = pieces*rate_per_piece;
            console.log(amount)

            frappe.model.set_value(cdt, cdn, 'amount', amount);
        }
    
    },
});




