frappe.ui.form.on("Mark Attendance", {
    attendance_date: function(frm) {
        const selected_date = frm.doc.attendance_date;
        const today = frappe.datetime.get_today(); // YYYY-MM-DD
        if (selected_date === today) {
            frappe.msgprint(__('You cannot select today\'s date.'));
            frm.set_value('attendance_date', ''); // clear the field
        }
    },

    mark_attendance(frm) {
        const dialog = new frappe.ui.Dialog({
            title: __("Processing"),
            fields: [{ fieldtype: "HTML", fieldname: "msg" }]
        });
        dialog.show();
        dialog.fields_dict.msg.$wrapper.html("<p>Processing attendance, please wait...</p>");

        frappe.call({
            method: "enrich_hrms.utils.oneshot_attendance_mark",
            args: {
                attendance_date: frm.doc.attendance_date,
                company: frm.doc.company
            },
            callback(r) {
                const data = r.message || {};
                frm.set_value("last_log", JSON.stringify({ datetime: frappe.datetime.now_datetime(), summary: data }, null, 2));

                const hasAnyValue = obj => Object.values(obj || {}).some(v => v > 0);

                let html = `
                <style>
                    .att-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; font-size: 11px; }
                    .att-card { border: 1px solid #d1d8dd; border-radius: 6px; padding: 8px; background: #fafbfc; }
                    .att-title { font-weight: 600; margin-bottom: 6px; font-size: 13px; }
                    .att-table { width: 100%; margin-bottom: 6px; }
                    .att-table td { padding: 2px 4px; }
                    .att-subtitle { font-weight: 600; margin: 6px 0 2px; font-size: 11px; color: #555; }
                    .att-error { color: #b42318; font-size: 11px; background: #fff3f3; border-radius: 4px; padding: 4px 6px; margin-bottom: 4px; }
                </style>
                <div class="att-grid">
                `;

                Object.keys(data).forEach(shift => {
                    const s = data[shift].summary;

                    const showErrors = s.errors > 0 && s.error_details?.length;

                    // Filter only non-zero fields dynamically
                    const nonZeroFields = Object.keys(s).filter(k => {
                        return typeof s[k] === 'number' && s[k] > 0;
                    });

                    html += `<div class="att-card">
                        <div class="att-title">${shift}</div>
                        <table class="att-table">
                            ${nonZeroFields.map(f => `<tr><td>${f.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}</td><td>${s[f]}</td></tr>`).join("")}
                        </table>
                        ${showErrors ? `
                        <div class="att-subtitle">Error Details</div>
                        ${s.error_details.map(e => `<div class="att-error"><b>${e.employee}</b> — ${e.error}</div>`).join("")}
                        ` : ""}
                    </div>`;
                });

                html += `</div>`;

                dialog.set_title(__("Attendance Summary"));
                dialog.fields_dict.msg.$wrapper.html(html);
                dialog.set_primary_action(__("Close"), async () => {
                    dialog.hide();
                });
                frm.save();
            },
            error() {
                dialog.set_title(__("Error"));
                dialog.fields_dict.msg.$wrapper.html("<p style='color:red;'>Something went wrong.</p>");
                dialog.set_primary_action(__("Close"), async () => {
                    await frm.save();
                    dialog.hide();
                });
            }
        });
    }
});
