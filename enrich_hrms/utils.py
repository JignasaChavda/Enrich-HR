# Earned Leave Allocation       
import frappe
import datetime
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from frappe.model.workflow import defaultdict
from frappe.twofactor import time_diff_in_seconds
from frappe.utils.data import getdate, now, today
from frappe.utils import getdate, time_diff, today, add_days, date_diff
from isodate import Duration
from datetime import timedelta


def to_timedelta(work_hours):
    if isinstance(work_hours, str):
        # Handle string input in hh:mm or hh:mm:ss format
        parts = work_hours.split(":")
        if len(parts) == 2:  # hh:mm format
            hours, minutes = map(int, parts)
            return timedelta(hours=hours, minutes=minutes)
        elif len(parts) == 3:  # hh:mm:ss format
            hours, minutes, seconds = map(int, parts)
            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
        else:
            raise ValueError("Invalid work_hours format")
    elif isinstance(work_hours, float):
        # Handle float input, assuming it's in hours
        hours = int(work_hours)
        minutes = int((work_hours - hours) * 60)
        return timedelta(hours=hours, minutes=minutes)
    else:
        # If it's already a timedelta, return as-is
        return work_hours


# Custom attendance flow
@frappe.whitelist(allow_guest=True)
def mark_attendance(date, shift):
    if isinstance(date, str):
        date = datetime.strptime(date, '%Y-%m-%d').date()
    
    # Initialize statistics counters
    stats = {
        "total_employees": 0,
        "present": 0,
        "absent": 0,
        "half_day": 0,
        "skipped": 0,
        "errors": 0,
        "skipped_reasons": {
            "joining_date_after": 0,
            "holiday": 0,
            "already_marked": 0
        },
        "absent_reasons": {
            "no_checkin": 0,
            "no_checkout": 0,
            "below_threshold": 0
        },
        "shift_sources": {
            "from_assignment": 0,
            "from_default_shift": 0
        },
        "error_details": []
    }
    
    try:
        active_employees = frappe.db.get_all(
            "Employee",
            filters={
                "status": "Active",
                "employment_type": ["not in", ["Professional Contractor", "Labour Contractor", "Owner"]]
            },
            fields=["name", "default_shift"]
        )
        active_employee_names = [emp["name"] for emp in active_employees]
        
        # Get all shift assignment records
        emp_records_from_assignment = frappe.db.get_all(
            "Shift Assignment",
            filters={
                "status": "Active",
                "shift_type": shift,
                "start_date": ["<=", date],
                "employee": ["in", active_employee_names],
            },
            or_filters=[
                {"end_date": ["is", "not set"]},
                {"end_date": [">=", date]},
            ],
            fields=["employee", "start_date", "end_date"],
        )
        
        # Create a set of employees who have shift assignments
        employees_with_assignment = {emp["employee"] for emp in emp_records_from_assignment}
        
        # Build final employee records list
        emp_records = []
        
        # Add employees from shift assignment
        for emp_assignment in emp_records_from_assignment:
            emp_records.append({
                "employee": emp_assignment["employee"],
                "start_date": emp_assignment["start_date"],
                "end_date": emp_assignment["end_date"],
                "shift_source": "assignment"
            })
            stats["shift_sources"]["from_assignment"] += 1
        
        # Add employees with default shift but no assignment
        for emp in active_employees:
            if emp["name"] not in employees_with_assignment:
                # Check if employee has default shift matching current shift
                if emp.get("default_shift") == shift:
                    emp_records.append({
                        "employee": emp["name"],
                        "start_date": None,
                        "end_date": None,
                        "shift_source": "default"
                    })
                    stats["shift_sources"]["from_default_shift"] += 1
        
        stats["total_employees"] = len(emp_records)
        employee_checkins = {}
        
        # Process each employee with individual error handling
        for emp in emp_records:
            try:
                emp_name = emp["employee"]
                shift_source = emp.get("shift_source", "assignment")
                
                emp_doc = frappe.get_doc("Employee", emp_name)
                emp_joining_date = emp_doc.get("date_of_joining")
                
                # Skip if joining date is after the attendance date
                if emp_joining_date and emp_joining_date > date:
                    stats["skipped"] += 1
                    stats["skipped_reasons"]["joining_date_after"] += 1
                    continue
                
                # Get checkin records
                checkin_records = frappe.db.get_all(
                    "Employee Checkin",
                    filters={
                        "employee": emp_name,
                        "shift": shift,
                        "custom_date": date
                    },
                    fields=["employee", "name", "custom_date", "log_type"],
                    order_by="custom_date"
                )
                
                if checkin_records:
                    # Store checkins
                    for checkin in checkin_records:
                        date_key = checkin['custom_date']
                        if emp_name not in employee_checkins:
                            employee_checkins[emp_name] = {}
                        if date_key not in employee_checkins[emp_name]:
                            employee_checkins[emp_name][date_key] = []
                        employee_checkins[emp_name][date_key].append({
                            'name': checkin['name'],
                            'log_type': checkin['log_type']
                        })
                    continue
                
                # Check if date is a holiday
                holiday_list = frappe.db.get_value('Employee', emp_name, 'holiday_list')
                is_holiday = False
                if holiday_list:
                    holiday_doc = frappe.get_doc('Holiday List', holiday_list)
                    holidays = holiday_doc.get("holidays")
                    for holiday in holidays:
                        if date == holiday.holiday_date:
                            is_holiday = True
                            break
                
                if not is_holiday:
                    # Check if attendance already exists
                    exists_atte = frappe.db.get_value(
                        'Attendance',
                        {'employee': emp_name, 'attendance_date': date, 'docstatus': 1},
                        ['name']
                    )
                    
                    if not exists_atte:
                        # Mark Absent
                        attendance = frappe.new_doc("Attendance")
                        attendance.employee = emp_name
                        attendance.attendance_date = date
                        attendance.shift = shift
                        attendance.status = "Absent"
                        attendance.custom_remarks = f"No Checkin found (Shift from: {shift_source})"
                        attendance.insert(ignore_permissions=True)
                        attendance.submit()
                        frappe.db.commit()
                        
                        stats["absent"] += 1
                        stats["absent_reasons"]["no_checkin"] += 1
                    else:
                        stats["skipped"] += 1
                        stats["skipped_reasons"]["already_marked"] += 1
                else:
                    # Skipped due to holiday
                    stats["skipped"] += 1
                    stats["skipped_reasons"]["holiday"] += 1
                    
            except Exception as e:
                stats["errors"] += 1
                stats["error_details"].append({
                    "employee": emp_name,
                    "error": str(e)
                })
                frappe.log_error(f"Error processing employee {emp_name}: {str(e)}", "Mark Attendance Error")
                continue
        
        # Process employees with checkins
        for emp_name, dates in employee_checkins.items():
            for checkin_date, logs in dates.items():
                try:
                    # Reset variables for each employee and date
                    first_checkin = None
                    last_checkout = None
                    chkin_datetime = None
                    chkout_datetime = None
                    total_work_hours = 0.0
                    att_late_entry = 0
                    att_early_exit = 0
                    late_entry_hours_final = "00.00"
                    early_exit_hours_final = "00.00"
                    
                    # Find first checkin and last checkout
                    for log in logs:
                        name = log['name']
                        log_type = log['log_type']
                        
                        if log_type == "IN" and first_checkin is None:
                            first_checkin = name
                            chkin_datetime = frappe.db.get_value('Employee Checkin', first_checkin, 'time')
                        
                        if log_type == "OUT":
                            last_checkout = name
                            chkout_datetime = frappe.db.get_value('Employee Checkin', last_checkout, 'time')
                    
                    # Check for mismatched pairs
                    att_remarks = ""
                    if last_checkout:
                        next_in_check = frappe.db.exists(
                            "Employee Checkin",
                            {
                                "employee": emp_name,
                                "shift": shift,
                                "custom_date": date,
                                "log_type": "IN",
                                "name": [">", last_checkout]
                            }
                        )
                        if next_in_check:
                            att_remarks = "Last pair mismatched"
                    
                    # Get shift configuration
                    working_hours_calculation_based_on = frappe.db.get_value("Shift Type", shift, "working_hours_calculation_based_on")
                    shift_hours = frappe.db.get_value("Shift Type", shift, "custom_shift_hours")
                    half_day_hour = frappe.db.get_value('Shift Type', shift, 'working_hours_threshold_for_half_day')
                    absent_hour = frappe.db.get_value('Shift Type', shift, 'working_hours_threshold_for_absent')
                    
                    # Calculate working hours
                    if first_checkin and last_checkout:
                        first_chkin_time = frappe.utils.get_time(chkin_datetime)
                        last_chkout_time = frappe.utils.get_time(chkout_datetime)
                        
                        if working_hours_calculation_based_on == "First Check-in and Last Check-out":
                            work_hours = frappe.utils.time_diff(chkout_datetime, chkin_datetime)
                            total_work_hours = work_hours.total_seconds() / 3600
                        elif working_hours_calculation_based_on == "Every Valid Check-in and Check-out":
                            in_time = None
                            for log in logs:
                                name = log['name']
                                log_type = log['log_type']
                                
                                if log_type == "IN" and in_time is None:
                                    in_time = frappe.db.get_value('Employee Checkin', name, 'time')
                                
                                if log_type == "OUT" and in_time:
                                    out_time = frappe.db.get_value('Employee Checkin', name, 'time')
                                    work_time = frappe.utils.time_diff(out_time, in_time)
                                    total_work_hours += work_time.total_seconds() / 3600
                                    in_time = None
                        
                        # Convert to HH.MM format
                        hours = int(total_work_hours)
                        minutes = int(round((total_work_hours - hours) * 60))
                        formatted_total_work_hours = f"{hours:02d}.{minutes:02d}"
                        
                        # Calculate Overtime
                        emp_overtime_consent = frappe.db.get_value('Employee', emp_name, 'custom_overtime_consent')
                        final_OT = "00.00"
                        if emp_overtime_consent == 'Yes':
                            work_hours_timedelta = timedelta(hours=total_work_hours)
                            if work_hours_timedelta > shift_hours:
                                diff = work_hours_timedelta - shift_hours
                                total_seconds = abs(diff.total_seconds())
                                hours, remainder = divmod(total_seconds, 3600)
                                minutes, seconds = divmod(remainder, 60)
                                final_OT = f"{int(hours):02}.{int(minutes):02}"
                        
                        # Calculate late entry, early exit
                        shift_start_time = frappe.db.get_value('Shift Type', shift, 'start_time')
                        late_entry_grace_period = frappe.db.get_value('Shift Type', shift, 'late_entry_grace_period')
                        shift_start_time = frappe.utils.get_time(shift_start_time)
                        shift_start_datetime = datetime.combine(checkin_date, shift_start_time)
                        grace_late_datetime = frappe.utils.add_to_date(shift_start_datetime, minutes=late_entry_grace_period)
                        grace_late_time = grace_late_datetime.time()
                        
                        shift_end_time = frappe.db.get_value('Shift Type', shift, 'end_time')
                        early_exit_grace_period = frappe.db.get_value('Shift Type', shift, 'early_exit_grace_period')
                        shift_end_time = frappe.utils.get_time(shift_end_time)
                        shift_end_datetime = datetime.combine(checkin_date, shift_end_time)
                        grace_early_datetime = frappe.utils.add_to_date(shift_end_datetime, minutes=-early_exit_grace_period)
                        grace_early_time = grace_early_datetime.time()
                        
                        if first_chkin_time and first_chkin_time > grace_late_time:
                            late_entry_timedelta = frappe.utils.time_diff(str(first_chkin_time), str(grace_late_time))
                            total_late_entry_seconds = late_entry_timedelta.total_seconds()
                            late_entry_hour = int(total_late_entry_seconds // 3600)
                            late_entry_minute = int((total_late_entry_seconds % 3600) // 60)
                            late_entry_hours_final = f"{late_entry_hour:02d}.{late_entry_minute:02d}"
                            att_late_entry = 1
                        
                        if last_chkout_time and last_chkout_time < grace_early_time:
                            early_exit_timedelta = frappe.utils.time_diff(str(grace_early_time), str(last_chkout_time))
                            total_early_exit_seconds = early_exit_timedelta.total_seconds()
                            early_exit_hour = int(total_early_exit_seconds // 3600)
                            early_exit_minute = int((total_early_exit_seconds % 3600) // 60)
                            early_exit_hours_final = f"{early_exit_hour:02d}.{early_exit_minute:02d}"
                            att_early_exit = 1
                        
                        # Calculate threshold limit wise status
                        att_status = 'Present'
                        if float(total_work_hours) < half_day_hour:
                            att_status = 'Half Day'
                        if float(total_work_hours) < absent_hour:
                            att_status = 'Absent'
                        
                        # Check if attendance already exists
                        exists_atte = frappe.db.get_value('Attendance', {'employee': emp_name, 'attendance_date': checkin_date, 'docstatus': 1}, ['name'])
                        
                        if not exists_atte:
                            attendance = frappe.new_doc("Attendance")
                            attendance.employee = emp_name
                            attendance.attendance_date = checkin_date
                            attendance.shift = shift
                            attendance.in_time = chkin_datetime
                            attendance.out_time = chkout_datetime
                            attendance.custom_first_chckin = first_checkin
                            attendance.custom_last_checkout = last_checkout
                            attendance.custom_work_hours_ = formatted_total_work_hours
                            attendance.custom_overtime = final_OT
                            attendance.status = att_status
                            attendance.custom_late_entry_hours = late_entry_hours_final
                            attendance.custom_early_exit_hours = early_exit_hours_final
                            attendance.late_entry = att_late_entry
                            attendance.early_exit = att_early_exit
                            attendance.custom_remarks = att_remarks
                            attendance.insert(ignore_permissions=True)
                            attendance.submit()
                            frappe.db.commit()
                            
                            # Update statistics based on status
                            if att_status == 'Present':
                                stats["present"] += 1
                            elif att_status == 'Half Day':
                                stats["half_day"] += 1
                            elif att_status == 'Absent':
                                stats["absent"] += 1
                                stats["absent_reasons"]["below_threshold"] += 1
                        else:
                            stats["skipped"] += 1
                            stats["skipped_reasons"]["already_marked"] += 1
                    
                    elif first_checkin and not last_checkout:
                        # No checkout record found
                        exists_atte = frappe.db.get_value('Attendance', {'employee': emp_name, 'attendance_date': checkin_date, 'docstatus': 1}, ['name'])
                        
                        if not exists_atte:
                            attendance = frappe.new_doc("Attendance")
                            attendance.employee = emp_name
                            attendance.attendance_date = checkin_date
                            attendance.shift = shift
                            attendance.in_time = chkin_datetime
                            attendance.custom_first_chckin = first_checkin
                            attendance.custom_work_hours_ = 0
                            attendance.custom_overtime = 0
                            attendance.status = 'Absent'
                            attendance.custom_late_entry_hours = 0
                            attendance.custom_early_exit_hours = 0
                            attendance.late_entry = 0
                            attendance.early_exit = 0
                            attendance.custom_remarks = 'No Checkout record found'
                            attendance.insert(ignore_permissions=True)
                            attendance.submit()
                            frappe.db.commit()
                            
                            stats["absent"] += 1
                            stats["absent_reasons"]["no_checkout"] += 1
                        else:
                            stats["skipped"] += 1
                            stats["skipped_reasons"]["already_marked"] += 1
                
                except Exception as e:
                    stats["errors"] += 1
                    stats["error_details"].append({
                        "employee": emp_name,
                        "date": str(checkin_date),
                        "error": str(e)
                    })
                    frappe.log_error(f"Error processing attendance for {emp_name} on {checkin_date}: {str(e)}", "Mark Attendance Error")
                    continue
                    
        import json
        frappe.log_error(json.dumps(stats, indent=2), f"Attendance Marked Stats | Shift : {shift} | Date : {date}")
        
        return {
            "success": True,
            "summary": stats
        }
    
    except Exception as e:
        frappe.log_error(f"Critical error in mark_attendance: {str(e)}", "Mark Attendance Critical Error")
        frappe.throw(f"Critical error occurred: {str(e)}")       
  

@frappe.whitelist(allow_guest=True)
def oneshot_attendance_mark(attendance_date, company):
    data = {}
    if not company and not attendance_date:
        frappe.throw("Please Provide attendance date and compnay")
    shift_types = frappe.get_all("Shift Type", fields=['name'])
    if shift_types:
        for shifts in shift_types:
            shift = shifts.name
            data[shift] = mark_attendance(attendance_date, shift)
        return data
    else:
        frappe.throw("There is no Shift are avaialabe for employee")


@frappe.whitelist(allow_guest=True)
def set_attendance_date():
   
    date = today()
    shift_types = frappe.get_all("Shift Type", filters={'enable_auto_attendance':1}, fields=['name'])
    if shift_types:
        for shifts in shift_types:
            shift = shifts.name
            mark_attendance(date, shift)