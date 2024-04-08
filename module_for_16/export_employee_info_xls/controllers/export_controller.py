# -*- coding: utf-8 -*-

import json

from odoo import http, fields
from odoo.http import content_disposition, request, \
    serialize_exception as _serialize_exception
from odoo.tools import html_escape

from odoo.tools import date_utils
import io
import json
from datetime import datetime
import datetime
import pytz
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter



class XLSXReportController(http.Controller):
    """Controller to generate and print XLS reports."""

    def default_starting_and_end_dates(self, time_off_recs_all):
        all_from_dates = time_off_recs_all.mapped(lambda timeoff: fields.Date.to_date(timeoff.date_from))
        from_date = sorted(all_from_dates)[0]
        all_to_dates = time_off_recs_all.mapped(lambda timeoff: fields.Date.to_date(timeoff.date_to))
        to_date = sorted(all_to_dates)[-1]

        return from_date, to_date


    def get_target_employees_days(self, employee, from_date=None, to_date=None):

        """
            Mehtod will get three arguments [employee, from_date, to_date]
        """
        print("Time Off for employee: ", employee.name)

        # ------------------------------------------- Defaults -------------------------------------------
        time_off_recs_all = request.env["hr.leave"].search([]).filtered(lambda timeoff: 
            employee in timeoff.all_employee_ids
        )
        

        # List of all employee time off days 
        time_off_list = []

        # public hoidays to check within before returning time off days
        publick_holidays = request.env["resource.calendar.leaves"].search([("name", "ilike", "Public Time Off")])
        # ------------------------------------------------------------------------------------------------

        # do search if there is any time off records
        if len(time_off_recs_all) > 0:

            # set default starting date and end date
            if (not from_date) or (not to_date):
                from_date, to_date = self.default_starting_and_end_dates(time_off_recs_all)

                print(from_date.strftime('%d-%m-%Y'))
                print(to_date.strftime('%d-%m-%Y'))


            number_of_days = (to_date - from_date).days
            step_date = from_date

            # loop through all step days
            for i in range(number_of_days + 1):

                filtered_time_off = time_off_recs_all.filtered(
                    lambda timeoff: 
                        # holiday date must be on or AFTER the selected period beginning
                        fields.Date.to_date(timeoff.date_from) >= from_date
                    and
                        # holiday date must be on or BEFORE the selected period end
                        fields.Date.to_date(timeoff.date_from) <= to_date
                    and
                        # employee must have rcorded his own holiday
                        timeoff.all_employee_ids in employee
                    and
                        # display only the validated time off
                        timeoff.state == "validate" 
                )

                print("Step Day:", step_date)
                print("Day of the Week:", step_date.isoweekday())
                

                publick_holiday = publick_holidays.filtered(
                    lambda rec: 
                        fields.Date.to_date(rec.date_from) == step_date
                )

                time_off = filtered_time_off.filtered(
                    lambda rec:
                        step_date >= fields.Date.to_date(rec.date_from) and step_date <= fields.Date.to_date(rec.date_to)
                )
                
                # =============================================================
                print("First Condition: =====>", len(publick_holiday), publick_holiday)
                print("Second Condition : ======>", len(time_off), time_off)
                # =============================================================

                # Check if each step day is a public holiday or another holiday or a working day or a weekend
                if len(publick_holiday) > 0:
                    holiday = publick_holiday[:1]
                    time_off_list.append(
                        [
                            {
                                "step_date": step_date
                            },

                            {
                                "time_off": "H",
                                "from": holiday.date_from,
                                "to": holiday.date_to,
                                "project": holiday.holiday_id.holiday_status_id.timesheet_project_id,
                                "state": holiday.holiday_id.state,
                            }
                        ]
                    )
                # check if the step day is within the time off
                elif len(time_off) > 0:
                    time_off_date_from = fields.Date.to_date(time_off.date_from)
                    time_off_date_to = fields.Date.to_date(time_off.date_to)
                    time_off_name = time_off.holiday_status_id.display_name
                    time_off_project = time_off.holiday_status_id.timesheet_project_id
                    
                    # default value prefix for time off display name
                    prefix = ""
                        
                    if "Sick" in time_off_name:
                        prefix = "S"
                    elif "Compensatory" in time_off_name or "Paid" in time_off_name or "Unpaid" in time_off_name:
                        prefix = "V"

                    time_off_list.append(
                        [
                            {
                                "step_date": step_date
                            },

                            {
                                "time_off": prefix,
                                "from": time_off_date_from,
                                "to": time_off_date_to,
                                "project": time_off_project,
                                "state": time_off.state,
                            }
                        ]
                    )   
                # step day could be a weekend [friday or saturday]
                elif step_date.isoweekday() in [5, 6]:
                    print("Weekend!")
                    time_off_list.append(
                        [
                            {
                                "step_date": step_date
                            },

                            {
                                "time_off": "",
                            }
                        ]
                    )
                # step day should be a working day
                else:
                    print("Working Day!")
                    time_off_list.append(
                        [
                            {
                                "step_date": step_date
                            },

                            {
                                "time_off": "P",
                            }
                        ]
                    )
                
                # end of looping over the specified number of days
                step_date = fields.Date.add(from_date, days=i+1)
            
            # end of step days loop

        for item in time_off_list:
            print(item)
        
        return time_off_list


    

    def get_xlsx_report(self, data, response):
        # initializing
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Project Info')
        
        # styleing


        # writing data
        employees_list_of_dicts = data['hr.employee']
        worksheet.write(0, 0, "Name")
        worksheet.write(0, 1, "Employee Vendor ID")
        worksheet.write(0, 2, "Employee Email")
        worksheet.write(0, 3, "Start Date")
        worksheet.write(0, 4, "Gender")
        worksheet.write(0, 5, "Section Manager Name")
        worksheet.write(0, 6, "Director/GM")
        worksheet.write(0, 7, "Company")
        worksheet.write(0, 8, "Job Title")
        worksheet.write(0, 9, "PO")

        row = 1
        col = 0
        for emp_dict in employees_list_of_dicts:
            # 0 cell
            worksheet.write(row, col, emp_dict['name'])
            # 1 cell
            emp_obj = request.env["hr.employee"].browse([emp_dict['id']])
            # 2 cell
            worksheet.write(row, col+1, "Employee Vendor ID")
            # 3 cell
            if emp_obj.work_email:
                worksheet.write(row, col+2, emp_obj.work_email)
            # 4 cell
            worksheet.write(row, col+3, "Start Date")
            # 5 cell
            if emp_obj.gender:
                worksheet.write(row, col+4, emp_obj.gender)
            # 6 cell
            worksheet.write(row, col+5, "Section Manager")
            # 7 cell
            worksheet.write(row, col+6, "Director/GM")
            # 8 cell
            if emp_obj.address_id:
                worksheet.write(row, col+7, emp_obj.address_id.name)
            # 9 cell
            if emp_obj.job_id:
                worksheet.write(row, col+8, emp_obj.job_id.name)
            # 10 cell
            worksheet.write(row, col+9, "PO")
            
            # start looping over all available days
            timeoff_result = self.get_target_employees_days(emp_obj)
            for i in range(len(timeoff_result)):
                step_day = timeoff_result[i][0]['step_date'].strftime('%d')
                timeoff = timeoff_result[i][1]['time_off']
                worksheet.write(0, col+9+i+1, step_day)
                worksheet.write(row, col+9+i+1, timeoff)

            row += 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()


    @http.route('/xlsx_reports_2', type='http', auth='user', methods=['POST'])
    def get_report_xlsx_2(self, data):
        print("===========================================")
        report_obj = request.env["employee.xls.report"]

        data = json.loads(data)
        print(data)
        print(type(data))
        print("===========================================")
        
        try:
            if 1 == 1:
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition',
                         content_disposition("emplutee_report" + '.xlsx'))
                    ]
                )
                self.get_xlsx_report(data, response)
            # response.set_cookie('fileToken', token)
            return response
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))


