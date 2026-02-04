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

                const hasAnyValue = obj => Object.values(obj || {}).some(v => v > 0);

                let html = `
                <style>
                    .att-grid {
                        display: grid;
                        grid-template-columns: repeat(2, 1fr);
                        gap: 10px;
                        font-size: 11px;
                    }
                    .att-card {
                        border: 1px solid #d1d8dd;
                        border-radius: 6px;
                        padding: 8px;
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
                        margin: 6px 0 2px;
                        font-size: 11px;
                        color: #555;
                    }
                    .att-error {
                        color: #b42318;
                        font-size: 11px;
                        background: #fff3f3;
                        border-radius: 4px;
                        padding: 4px 6px;
                        margin-bottom: 4px;
                    }
                </style>
                <div class="att-grid">
                `;

                Object.keys(data).forEach(shift => {
                    const s = data[shift].summary;

                    const showSkipped = hasAnyValue(s.skipped_reasons);
                    const showAbsent = hasAnyValue(s.absent_reasons);
                    const showSources = hasAnyValue(s.shift_sources);
                    const showErrors = s.errors > 0 && s.error_details?.length;

                    html += `
                    <div class="att-card">
                        <div class="att-title">${shift}</div>

                        <table class="att-table">
                            <tr><td>Total</td><td>${s.total_employees}</td></tr>
                            <tr><td>Present</td><td>${s.present}</td></tr>
                            <tr><td>Absent</td><td>${s.absent}</td></tr>
                            <tr><td>Half Day</td><td>${s.half_day}</td></tr>
                            <tr><td>Skipped</td><td>${s.skipped}</td></tr>
                            <tr><td><b>Errors</b></td><td><b>${s.errors}</b></td></tr>
                        </table>

                        ${showSkipped ? `
                        <div class="att-subtitle">Skipped Reasons</div>
                        <table class="att-table">
                            ${s.skipped_reasons.already_marked ? `<tr><td>Already Marked</td><td>${s.skipped_reasons.already_marked}</td></tr>` : ""}
                            ${s.skipped_reasons.holiday ? `<tr><td>Holiday</td><td>${s.skipped_reasons.holiday}</td></tr>` : ""}
                            ${s.skipped_reasons.joining_date_after ? `<tr><td>Joining After</td><td>${s.skipped_reasons.joining_date_after}</td></tr>` : ""}
                        </table>
                        ` : ""}

                        ${showAbsent ? `
                        <div class="att-subtitle">Absent Reasons</div>
                        <table class="att-table">
                            ${s.absent_reasons.no_checkin ? `<tr><td>No Check-in</td><td>${s.absent_reasons.no_checkin}</td></tr>` : ""}
                            ${s.absent_reasons.no_checkout ? `<tr><td>No Check-out</td><td>${s.absent_reasons.no_checkout}</td></tr>` : ""}
                            ${s.absent_reasons.below_threshold ? `<tr><td>Below Threshold</td><td>${s.absent_reasons.below_threshold}</td></tr>` : ""}
                        </table>
                        ` : ""}

                        ${showSources ? `
                        <div class="att-subtitle">Shift Sources</div>
                        <table class="att-table">
                            ${s.shift_sources.from_assignment ? `<tr><td>From Assignment</td><td>${s.shift_sources.from_assignment}</td></tr>` : ""}
                            ${s.shift_sources.from_default_shift ? `<tr><td>From Default Shift</td><td>${s.shift_sources.from_default_shift}</td></tr>` : ""}
                        </table>
                        ` : ""}

                        ${showErrors ? `
                        <div class="att-subtitle">Error Details</div>
                        ${s.error_details.map(e => `
                            <div class="att-error">
                                <b>${e.employee}</b> — ${e.error}
                            </div>
                        `).join("")}
                        ` : ""}
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
                dialog.fields_dict.msg.$wrapper.html("<p style='color:red;'>Something went wrong.</p>");
                dialog.set_primary_action(__("Close"), async () => {
                    await frm.save();
                    dialog.hide();
                });
            }
        });
    }
});
