frappe.ui.form.on("Mark Attendance", {
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
                let html = `
                    <style>
                        .att-grid {
                            display: grid;
                            grid-template-columns: repeat(2, 1fr);
                            gap: 12px;
                            font-size: 12px;
                        }
                        .att-card {
                            border: 1px solid #d1d8dd;
                            border-radius: 6px;
                            padding: 8px 10px;
                            background: #fafbfc;
                        }
                        .att-title {
                            font-weight: 600;
                            margin-bottom: 6px;
                            font-size: 13px;
                        }
                        .att-table {
                            width: 100%;
                            margin-bottom: 6px;
                        }
                        .att-table td {
                            padding: 2px 4px;
                        }
                        .att-subtitle {
                            font-weight: 600;
                            margin: 4px 0 2px;
                            font-size: 11px;
                            color: #555;
                        }
                    </style>
                    <div class="att-grid">
                `;

                Object.keys(data).forEach(shift => {
                    const s = data[shift].summary;

                    html += `
                        <div class="att-card">
                            <div class="att-title">${shift}</div>

                            <table class="att-table">
                                <tr><td>Total</td><td>${s.total_employees}</td></tr>
                                <tr><td>Present</td><td>${s.present}</td></tr>
                                <tr><td>Absent</td><td>${s.absent}</td></tr>
                                <tr><td>Half</td><td>${s.half_day}</td></tr>
                                <tr><td>Skipped</td><td>${s.skipped}</td></tr>
                            </table>

                            <div class="att-subtitle">Skipped</div>
                            <table class="att-table">
                                <tr><td>Already</td><td>${s.skipped_reasons.already_marked}</td></tr>
                                <tr><td>Holiday</td><td>${s.skipped_reasons.holiday}</td></tr>
                            </table>

                            <div class="att-subtitle">Absent</div>
                            <table class="att-table">
                                <tr><td>No In</td><td>${s.absent_reasons.no_checkin}</td></tr>
                                <tr><td>No Out</td><td>${s.absent_reasons.no_checkout}</td></tr>
                            </table>
                        </div>
                    `;
                });

                html += `</div>`;

                dialog.set_title(__("Attendance Summary"));
                dialog.fields_dict.msg.$wrapper.html(html);
                dialog.set_primary_action(__("Close"), async () => {
                await frm.save();
                dialog.hide();
                });

            },
            error() {
                dialog.set_title(__("Error"));
                dialog.fields_dict.msg.$wrapper.html(
                    "<p style='color:red;'>Something went wrong.</p>"
                );
                dialog.set_primary_action(__("Close"), async () => {
                    await frm.save();
                    dialog.hide();
                    });

            }
        });
    }
});
