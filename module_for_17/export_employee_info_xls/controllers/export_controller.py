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

    def get_account_analytic_line(self, employee, validate):
        # Main condition, analytic line for the employee
        
        analytic_line = request.env['account.analytic.line'].search([("employee_id", "=", employee.id)])
        
        if validate == "validate":
            result = analytic_line.filtered(
                lambda line:
                    line.validated == True
            )
            return result
        elif validate == "draft":
            result = analytic_line.filtered(
                lambda line:
                    line.validated == False
            )
            return result
        else:
            return analytic_line

    
    def get_filtered_timeoff(self, employee, from_date, to_date):
        filtered_time_off = request.env["hr.leave"].search([]).filtered(
            lambda timeoff: 
                # holiday date must be on or AFTER the selected period beginning
                fields.Date.to_date(timeoff.date_from) >= from_date
            and
                # holiday date must be on or BEFORE the selected period end
                fields.Date.to_date(timeoff.date_from) <= to_date
            and
                # employee must have rcorded his own holiday
                employee in timeoff.all_employee_ids
            and
                # display only the validated time off
                timeoff.state == "validate" 
        )

        return filtered_time_off


    def check_public_holiday(self, public_holidays, step_date):
        publick_holiday = public_holidays.filtered(
            lambda rec: 
                step_date >= fields.Date.to_date(rec.date_from) 
                and 
                step_date <= fields.Date.to_date(rec.date_to)
        )

        if len(publick_holiday) > 0:
            return True
        else:
            return False


    def check_time_off(self, filtered_time_off, step_date):
        time_off = filtered_time_off.filtered(
            lambda rec:
                step_date >= fields.Date.to_date(rec.date_from) 
                and 
                step_date <= fields.Date.to_date(rec.date_to)
        )

        if len(time_off) > 0:
            time_off = time_off[:1]
            time_off_name = time_off.holiday_status_id.display_name
            
            # default value prefix for time off display name
            prefix = ""
                
            if "Sick" in time_off_name:
                prefix = "S"
            elif "Compensatory" in time_off_name or "Paid" in time_off_name or "Unpaid" in time_off_name:
                prefix = "V"
            
            return True, prefix
        else:
            return False, False


    def check_work_day(self, employee, analytic_line, step_date):
        lines = analytic_line.search([("date", "=", step_date)])
        prefix = False

        for line in lines:
            if (not line.global_leave_id) and (not line.holiday_id) and line.unit_amount > 0.0:
                
                day_num = step_date.isoweekday()
                
                if day_num == 1 and employee.work_from_home_monday:
                    prefix = "W"
                elif day_num == 2 and employee.work_from_home_tuesday:
                    prefix = "W"
                elif day_num == 3 and employee.work_from_home_wednesday:
                    prefix = "W"
                elif day_num == 4 and employee.work_from_home_thursday:
                    prefix = "W"
                elif day_num == 5 and employee.work_from_home_friday:
                    prefix = "W"
                elif day_num == 6 and employee.work_from_home_saturday:
                    prefix = "W"
                elif day_num == 7 and employee.work_from_home_sunday:
                    prefix = "W"
                else:
                    prefix = "P"
            
        
        if prefix != False:
            return True, prefix
        else:
            return False, False

    
    def append_day(self, time_off_list, step_date, letter):
        print("time_off_list 2", time_off_list)
        time_off_list.append(
            [
                {
                    "step_date": step_date,
                },

                {
                    "time_off": letter,
                }
            ]
        )

        return time_off_list



    def get_target_employees_days(self, employee, from_date, to_date, validate):

        """
            Mehtod will get three arguments [employee, from_date, to_date]
        """
        print("Time Off for employee: ", employee.name)

        # ------------------------------------------- Defaults -------------------------------------------
        # ------------------------------------------------------------------------------------------------

        # time range for which days number is added in the excel sheet
        number_of_days = (to_date - from_date).days
        step_date = from_date

        filtered_time_off = self.get_filtered_timeoff(employee, from_date, to_date)
        
        # Main condition, analytic line for the employee
        analytic_line = self.get_account_analytic_line(employee, validate)

        print("Analytic Line is:", analytic_line)
        for line in analytic_line:
            print(line.display_name)
            print(line.name)
            print(line.global_leave_id.name)
            print(line.holiday_id.name)
            print(line.unit_amount)
            print(line.validated_status)
            print(line.validated)

        # public hoidays to check within before returning time off days
        public_holidays = request.env["resource.calendar.leaves"].search([]).filtered(
            lambda leave:
                (not leave.holiday_id.id) and (not leave.resource_id.id)
        )

        # List of all employee time off days 
        time_off_list = []
        
        # ------------------------------------------------------------------------------------------------
        # ------------------------------------------------------------------------------------------------

        for i in range(number_of_days + 1):
            if step_date in analytic_line.mapped("date"):
                print("^^^^^^^^^^^^")
                print("I am recorded")
                print(analytic_line.search([("date", "=", step_date)]))
                print("^^^^^^^^^^^^")

                public_holiday_result = self.check_public_holiday(public_holidays, step_date)
                timeoff_result, timeoff_prefix = self.check_time_off(filtered_time_off, step_date)
                work_day_result, work_day_prefix = self.check_work_day(employee, analytic_line, step_date)

                if public_holiday_result:
                    time_off_list = self.append_day(time_off_list, step_date, "H")
                elif timeoff_result:
                    time_off_list = self.append_day(time_off_list, step_date, timeoff_prefix)
                elif step_date.isoweekday() in [5, 6]:
                    time_off_list = self.append_day(time_off_list, step_date, "")
                elif work_day_result:
                    time_off_list = self.append_day(time_off_list, step_date, work_day_prefix)
                else:
                    time_off_list = self.append_day(time_off_list, step_date, "")
            else:
                time_off_list = self.append_day(time_off_list, step_date, "")

            
            # append day before starting a new loop
            step_date = fields.Date.add(from_date, days=i+1)

        for item in time_off_list:
            print(item)

        return time_off_list


    

    def get_xlsx_report(self, data):
        # initializing
        from_date = datetime.date(
            data['from_date']['year'], 
            data['from_date']['month'], 
            data['from_date']['day'])
        
        to_date = datetime.date(
            data['to_date']['year'], 
            data['to_date']['month'], 
            data['to_date']['day'])
        
        validate = data['validate']
        
        number_of_days = (to_date - from_date).days + 1

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Project Info')
        
        # styleing
        heading_format = workbook.add_format({'bold': True, 'bg_color': '#714693', 'font_color': 'white' })
        v_format = workbook.add_format({'bold': True, 'bg_color': '#70AD47', 'font_color': 'white' })
        h_format = workbook.add_format({'bold': True, 'bg_color': '#FFFF00', 'font_color': 'black' })
        s_format = workbook.add_format({'bold': True, 'bg_color': 'red', 'font_color': 'white' })

        # writing data
        employees_list_of_dicts = data['hr.employee']
        worksheet.write(0, 0, "#", heading_format)
        worksheet.write(0, 1, "Name", heading_format)
        worksheet.write(0, 2, "Employee Vendor ID", heading_format)
        worksheet.write(0, 3, "Employee Email", heading_format)
        worksheet.write(0, 4, "Start Date", heading_format)
        worksheet.write(0, 5, "Gender", heading_format)
        worksheet.write(0, 6, "Section Manager Name", heading_format)
        worksheet.write(0, 7, "Director/GM", heading_format)
        worksheet.write(0, 8, "Company", heading_format)
        worksheet.write(0, 9, "Job Title", heading_format)
        worksheet.write(0, 10, "PO", heading_format)

        row = 1
        col = 1
        for emp_dict in employees_list_of_dicts:
            # 0 cell
            worksheet.write(row, col, emp_dict['name'])
            # 1 cell
            emp_obj = request.env["hr.employee"].browse([emp_dict['id']])
            # 2 cell
            if emp_obj.work_email:
                worksheet.write(row, col+1, emp_obj.work_email)
            # 3 cell
            if emp_obj.emp_email:
                worksheet.write(row, col+2, emp_obj.emp_email)
            # 4 cell
            if emp_obj.joining_date:
                worksheet.write(row, col+3, emp_obj.joining_date)
            # 5 cell
            if emp_obj.gender:
                worksheet.write(row, col+4, emp_obj.gender)
            # 6 cell
            if emp_obj.section_manager:
                worksheet.write(row, col+5, emp_obj.section_manager)
            # 7 cell
            if emp_obj.director:
                worksheet.write(row, col+6, emp_obj.director)
            # 8 cell
            if emp_obj.address_id:
                worksheet.write(row, col+7, emp_obj.address_id.name)
            # 9 cell
            if emp_obj.job_id:
                worksheet.write(row, col+8, emp_obj.job_id.name)
            # 10 cell
            if emp_obj.project_id.po:
                worksheet.write(row, col+9, emp_obj.project_id.po)

            timeoff_result = self.get_target_employees_days(emp_obj, from_date, to_date, validate)
            appended_cols = len(timeoff_result)
            
            for i in range(appended_cols):
                step_day = timeoff_result[i][0]['step_date'].strftime('%d')
                worksheet.write(0, col+9+i+1, step_day, heading_format)
                
                timeoff = timeoff_result[i][1]['time_off']
                if timeoff == "V":
                    worksheet.write(row, col+9+i+1, timeoff, v_format)
                elif timeoff == "H":
                    worksheet.write(row, col+9+i+1, timeoff, h_format)
                elif timeoff == "S":
                    worksheet.write(row, col+9+i+1, timeoff, s_format)
                else:
                    worksheet.write(row, col+9+i+1, timeoff)
            
            # before last cell
            worksheet.write(0, col+9+number_of_days+1, "Location", heading_format)
            if emp_obj.location:
                worksheet.write(row, col+9+number_of_days+1, emp_obj.location)
            # last cell
            worksheet.write(0, col+9+number_of_days+2, "Nationality", heading_format)
            if emp_obj.country_id:
                worksheet.write(row, col+9+number_of_days+2, emp_obj.country_id.name)

            row += 1

        workbook.close()
        xlsx_data = output.getvalue()
        return xlsx_data


    @http.route('/employee_xlsx_report', type='http', auth='user')
    def get_employee_xlsx_report(self, data, **kw):
        report_obj = request.env["employee.xls.report"]
        data = json.loads(data)
        filename = "employee_timesheet_report"
        xlsx_data = self.get_xlsx_report(data)
        response = request.make_response(
            xlsx_data,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition(filename + '.xlsx'))
            ],
        )

        return response

