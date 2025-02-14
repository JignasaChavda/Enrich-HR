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



# # Process auto-checkout record
# @frappe.whitelist()
# def process_employee_checkouts():
#     current_date = datetime.now().date()

#     # Fetch all check-in records for the current date
#     checkin_records = frappe.db.get_all(
#         "Employee Checkin",
#         filters={
#             "custom_date": current_date,
#         },
#         fields=["employee", "time", "log_type"]
#     )

#     # Organize records by employee
#     employee_logs = {}
#     for record in checkin_records:
#         employee = record["employee"]
#         if employee not in employee_logs:
#             employee_logs[employee] = []
#         employee_logs[employee].append(record["log_type"])

#     # Identify employees with only IN or with unpaired IN records
#     employees_without_out = [
#         employee for employee, logs in employee_logs.items()
#         if logs.count("IN") > logs.count("OUT")
#     ]

#     emp_shift = frappe.db.get_value(
#         "Shift Assignment",
#         filters={
#             "status": "Active",
#             "employee": employee,
#             "start_date": ("<=", current_date),
#             "end_date": (">=", current_date),
#         },
#         fieldname="shift_type",  # Correct parameter name for single field
#     )

#     # Create OUT record for employees without a matching OUT
#     for employee in employees_without_out:
#         new_checkout = frappe.get_doc({
#             "doctype": "Employee Checkin",
#             "employee": employee,
#             "time": now(),  
#             "shift": emp_shift,
#             "log_type": "OUT",
#             "custom_remarks": "Auto-Checkout",
#             "latitude": "0",
#             "longitude": "0"
#         })

#         new_checkout.insert()
    
#     frappe.db.commit()

   



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

    success_message_printed = False
    
    active_employees = frappe.db.get_all(
        "Employee",
        filters={
            "status": "Active",
            "employment_type": ["not in", ["Professional Contractor", "Labour Contractor", "Owner"]]
            },
        fields=["name"]
    )
    active_employee_names = [emp["name"] for emp in active_employees]

    # Get all shift assignment records
    emp_records = frappe.db.get_all(
        "Shift Assignment",
        filters={
            "status": "Active",
            "shift_type": shift,
            "start_date": ["<=", date],
            "end_date": ["is", "not set"],
            "employee": ["in", active_employee_names]  # Filter by active employees
        },
        fields=["employee", "start_date", "end_date"],
    )


    
    emp_records_with_end_date = frappe.db.get_all(
        "Shift Assignment",
        filters={
            "status": "Active",
            "shift_type": shift,
            "start_date": ["<=", date],
            "end_date": [">=", date],
            "employee": ["in", active_employee_names]  # Filter by active employees
        },
        fields=["employee", "start_date", "end_date"],
    )

    emp_records.extend(emp_records_with_end_date)


    
    employee_checkins = {}

    for emp in emp_records:
        emp_name = emp.employee
        emp_doc = frappe.get_doc("Employee", emp_name)
        emp_joining_date = emp_doc.get("date_of_joining")

        # Skip if employee's joining date is after the attendance date
        if emp_joining_date and emp_joining_date > date:
            continue

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

        # If no checkin found for particular shift and there is no holiday on date then mark absent     
        else:
            holiday_list = frappe.db.get_value('Employee', emp_name, 'holiday_list')
            is_holiday = False
            
            if holiday_list:
                holiday_doc = frappe.get_doc('Holiday List', holiday_list)
                holidays = holiday_doc.get("holidays")
                
                for holiday in holidays:
                    holiday_dt = holiday.holiday_date
                    if date == holiday_dt:
                        is_holiday = True
                        break
            
            if not is_holiday:
                exists_atte = frappe.db.get_value('Attendance', {'employee': emp_name, 'attendance_date': date, 'docstatus': 1}, ['name'])
                if not exists_atte:
                    attendance = frappe.new_doc("Attendance")
                    attendance.employee = emp_name
                    attendance.attendance_date = date
                    attendance.shift = shift
                    attendance.status = "Absent"
                    attendance.custom_remarks = "No Checkin found"
                    attendance.insert(ignore_permissions=True)
                    attendance.submit()
                    frappe.db.commit()

    # Calculate working hours
    first_chkin_time = None
    last_chkout_time = None
    first_checkin = None
    last_checkout = None
    chkin_datetime = None
    chkout_datetime = None
    total_work_hours = 0.0
    work_hours = 0.0  
    final_OT = 0.0
    att_status = 'Present'
    att_remarks = None
    att_late_entry = 0
    att_early_exit = 0
    late_entry_hours_final = 0
    early_exit_hours_final = 0

    for emp_name, dates in employee_checkins.items():
        for checkin_date, logs in dates.items():
            # Reset variables for each employee and date
            first_checkin = None  
            last_checkout = None  
            chkin_datetime = None
            chkout_datetime = None
            total_work_hours = 0.0
            att_late_entry = 0
            att_early_exit = 0
            late_entry_hours_final = "00.00"
            early_exit_hours_final = "00.00"  # Ensure it's a float to prevent conversion issues

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
                else:
                    att_remarks = ""

            working_hours_calculation_based_on = frappe.db.get_value("Shift Type", shift, "working_hours_calculation_based_on")
            shift_hours = frappe.db.get_value("Shift Type", shift, "custom_shift_hours")

            if first_checkin and last_checkout:
                first_chkin_time = frappe.utils.get_time(chkin_datetime)
                last_chkout_time = frappe.utils.get_time(chkout_datetime)

                if working_hours_calculation_based_on == "First Check-in and Last Check-out": 
                    work_hours = frappe.utils.time_diff(chkout_datetime, chkin_datetime)
                    total_work_hours += work_hours.total_seconds() / 3600  

                    # Convert to HH.MM format correctly
                    hours = int(total_work_hours)  
                    minutes = int(round((total_work_hours - hours) * 60))  
                    formatted_total_work_hours = f"{hours:02d}.{minutes:02d}"  

                    

                elif working_hours_calculation_based_on == "Every Valid Check-in and Check-out":
                    in_time = None
                    total_seconds = 0  

                    for log in logs:
                        name = log['name']
                        log_type = log['log_type']

                        if log_type == "IN" and in_time is None:
                            in_time = frappe.db.get_value('Employee Checkin', name, 'time')

                        if log_type == "OUT" and in_time:
                            out_time = frappe.db.get_value('Employee Checkin', name, 'time')

                            work_time = frappe.utils.time_diff(out_time, in_time)
                            total_work_hours += work_time.total_seconds() / 3600  
                            total_seconds += work_time.total_seconds()  
                            in_time = None  

                    # Convert to HH.MM format correctly
                    hours = int(total_work_hours)  
                    minutes = int(round((total_work_hours - hours) * 60))  
                    formatted_total_work_hours = f"{hours:02d}.{minutes:02d}" 

                  

                # Ensure total_work_hours is converted properly before using
                total_work_hours = float(total_work_hours)

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
                half_day_hour = frappe.db.get_value('Shift Type', shift, 'working_hours_threshold_for_half_day')
                absent_hour = frappe.db.get_value('Shift Type', shift, 'working_hours_threshold_for_absent')

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

                    frappe.msgprint("Attendance is Marked Successfully")
                else:
                    formatted_date = checkin_date.strftime("%d-%m-%Y")
                    attendance_link = frappe.utils.get_link_to_form("Attendance", exists_atte)
                    frappe.msgprint(f"Attendance already marked for Employee:{emp_name} for date {formatted_date}: {attendance_link}")
            
            elif first_checkin and not last_checkout:
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

                    frappe.msgprint("Attendance is Marked Successfully")
                else:
                    formatted_date = checkin_date.strftime("%d-%m-%Y")
                    attendance_link = frappe.utils.get_link_to_form("Attendance", exists_atte)
                    frappe.msgprint(f"Attendance already marked for Employee:{emp_name} for date {formatted_date}: {attendance_link}")

           
  

@frappe.whitelist(allow_guest=True)
def set_attendance_date():
   
    date = today()
    shift_types = frappe.get_all("Shift Type", filters={'enable_auto_attendance':1},fields=['name'])
    if shift_types:
        for shifts in shift_types:
            shift = shifts.name
            mark_attendance(date, shift)