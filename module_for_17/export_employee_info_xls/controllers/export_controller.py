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
from odoo.exceptions import ValidationError
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter



class XLSXReportController(http.Controller):
    """Controller to generate and print XLS reports."""

    def get_account_analytic_line(self, employee, validate, project, from_date, to_date):
        # Main condition, analytic line for the employee
        
        analytic_line = request.env['account.analytic.line'].search(
            [
                "&", 
                    ("employee_id", "=", employee.id), 
                    "&", 
                        ("project_id", "=", project.id),
                        "&", 
                            ("date", ">=", from_date), 
                            ("date", "<=", to_date)
            ]
        )

        # print("ANALYTIC LINE:")
        # print(analytic_line)
        # print(analytic_line.mapped("project_id"))
        # print(analytic_line.mapped("task_id"))
        # print("ANALYTIC LINE...")
        
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
        
        lines = analytic_line.filtered(
            lambda line:
                line.date == step_date
        )

        prefix = False

        # print("LINES Before:", analytic_line)
        # print("LINES Before:", analytic_line.mapped("date"))
        # print("LINES Before:", analytic_line.mapped("project_id"))
        # print("LINES After:", lines)

        for line in lines:
            if (not line.global_leave_id) and (not line.holiday_id) and (line.unit_amount > 0.0) and (step_date == line.date):
                
                # print("step_date:", step_date)
                # print("line_date:", line.date)
                # print("display_name", line.display_name)
                # print("name", line.name)
                # print("unit_amount", line.unit_amount)
                # print("employee", line.employee_id)

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
                
                break
            
        # print("step_date", step_date, "prefix", prefix)

        if prefix != False:
            return True, prefix
        else:
            return False, False

    
    def append_day(self, time_off_list, step_date, letter):
        # print("time_off_list 2", time_off_list)
        time_off_list.append(
            {
                "step_date": step_date,
                "time_off": letter,
            },
        )

        return time_off_list



    def get_target_employees_days(self, employee, from_date, to_date, validate, project):

        """
            Mehtod will get three arguments [employee, from_date, to_date]
        """
        # print("Time Off for employee: ", employee.name)

        # ------------------------------------------- Defaults -------------------------------------------
        # ------------------------------------------------------------------------------------------------

        # time range for which days number is added in the excel sheet
        number_of_days = (to_date - from_date).days
        step_date = from_date

        filtered_time_off = self.get_filtered_timeoff(employee, from_date, to_date)
        
        # Main condition, analytic line for the employee
        analytic_line = self.get_account_analytic_line(employee, validate, project, from_date, to_date)

        # print("Analytic Line is:", analytic_line)
        # for line in analytic_line:
        #     print(line.date)
        #     print(line.display_name)
        #     print(line.name)
        #     print(line.project_id)
        #     print(line.task_id)
        #     print(line.global_leave_id.name)
        #     print(line.holiday_id.name)
        #     print(line.unit_amount)
        #     print(line.validated_status)
        #     print(line.validated)

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
            public_holiday_result = self.check_public_holiday(public_holidays, step_date)
            timeoff_result, timeoff_prefix = self.check_time_off(filtered_time_off, step_date)
            work_day_result, work_day_prefix = self.check_work_day(employee, analytic_line, step_date)
            
            if work_day_result:
                time_off_list = self.append_day(time_off_list, step_date, work_day_prefix)
                # print("work_day_result")
            elif public_holiday_result:
                time_off_list = self.append_day(time_off_list, step_date, "H")
                # print("public_holiday_result")
            elif timeoff_result:
                time_off_list = self.append_day(time_off_list, step_date, timeoff_prefix)
                # print("timeoff_result")
            elif step_date.isoweekday() in [5, 6]:
                time_off_list = self.append_day(time_off_list, step_date, "")
                # print("work_day_result")
            else:
                time_off_list = self.append_day(time_off_list, step_date, "")
                # print("else_1")
            

            
            # append day before starting a new loop
            step_date = fields.Date.add(from_date, days=i+1)

        # for item in time_off_list:
        #     print(item)

        return time_off_list



    def prepare_excel_list(self, data):

        from_date = datetime.date(
            data['from_date']['year'], 
            data['from_date']['month'], 
            data['from_date']['day'])
        
        to_date = datetime.date(
            data['to_date']['year'], 
            data['to_date']['month'], 
            data['to_date']['day'])
        
        validate = data['validate']
        
        employees_list = data['hr.employee']
        employees_list_2 = data['employee']
        projects_list = data['project.project']

        number_of_days = (to_date - from_date).days + 1

        projects = request.env['project.project']
        employees = request.env['hr.employee']
        
        if len(employees_list_2) > 0:
            for item in employees_list_2:
                item_employee = request.env['hr.employee'].browse([item['id']])
                employees |= item_employee
        elif len(projects_list) > 0:
            for item in projects_list:
                item_project = request.env['project.project'].browse([
                    item['id']
                ])

                item_tasks = item_project.task_ids
                item_assignees = item_tasks.mapped("user_ids")
                item_employees = request.env['hr.employee'].search([("user_id", "in", item_assignees.mapped("id"))])
                employees |= item_employees
        else:
            employees = request.env['hr.employee'].search([])

        excel_list = []

        print("==================================")
        print(employees)
        print(projects)
        print("==================================")
        
        for employee in employees:
            # print("employee record:", employee)

            if len(projects_list) == 0:
                # print("Not accessed")
                tasks = request.env['project.task'].search([]).filtered(
                    lambda task: 
                        employee.user_id in task.user_ids
                )
                # print(tasks)
                projects = tasks.mapped("project_id")
            elif len(projects_list) > 0:
                # print("accessed")
                for item in projects_list:
                    projects |= request.env['project.project'].browse([
                        item['id']
                    ])
                
                # print("Projects:", projects.mapped("display_name"))

            
            for project in projects:
                timeoff_result = self.get_target_employees_days(
                    employee, from_date, to_date, validate, project
                )

                excel_list.append(
                    {
                        'employee': employee, 
                        'project': project,
                        'timeoff_result': timeoff_result,
                    }
                )
            
        print(projects)
        # print("----------------------------------------------")
        # print("Excel List:")
        # for item in excel_list:
            # print(item)
            # print("\n")
        # print("----------------------------------------------")

        return excel_list


            

    

    def get_xlsx_report(self, data):

        if len(data) == 0:
            raise ValidationError("Did not find any matching employees")
        
        # initializing
        timeoffResult = data[0]['timeoff_result']
        appendedCols = len(timeoffResult)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Project Info')
        
        # styleing
        heading_format = workbook.add_format({'bold': True, 'bg_color': '#714693', 'font_color': 'white' })
        v_format = workbook.add_format({'bold': True, 'bg_color': '#70AD47', 'font_color': 'white' })
        h_format = workbook.add_format({'bold': True, 'bg_color': '#FFFF00', 'font_color': 'black' })
        s_format = workbook.add_format({'bold': True, 'bg_color': 'red', 'font_color': 'white' })
        w_format = workbook.add_format({'bold': True, 'bg_color': '#29344C', 'font_color': 'white' })

        # writing data
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
        for dict_row in data:
            emp_obj = dict_row['employee']
            project_obj = dict_row['project']
            timeoff_result = dict_row['timeoff_result']

            # 0 cell
            worksheet.write(row, 0, row)
            worksheet.set_column(0, 0, 3)
            # 1 cell
            if emp_obj.name:
                worksheet.write(row, col, emp_obj.name)
                worksheet.set_column(col, col, 45)
            # 2 cell
            if emp_obj.work_email:
                worksheet.write(row, col+1, emp_obj.work_email)
                worksheet.set_column(col+1, col+1, 30)
            # 3 cell
            if emp_obj.emp_email:
                worksheet.write(row, col+2, emp_obj.emp_email)
                worksheet.set_column(col+2, col+2, 30)
            # 4 cell
            if emp_obj.joining_date:
                worksheet.write(row, col+3, emp_obj.joining_date)
                worksheet.set_column(col+3, col+3, 30)
            # 5 cell
            if emp_obj.gender:
                worksheet.write(row, col+4, emp_obj.gender)
                worksheet.set_column(col+4, col+4, 10)
            # 6 cell
            if emp_obj.section_manager:
                worksheet.write(row, col+5, emp_obj.section_manager)
                worksheet.set_column(col+5, col+5, 30)
            # 7 cell
            if emp_obj.director:
                worksheet.write(row, col+6, emp_obj.director)
                worksheet.set_column(col+6, col+6, 30)
            # 8 cell
            if emp_obj.company:
                worksheet.write(row, col+7, emp_obj.company)
                worksheet.set_column(col+7, col+7, 30)
            # 9 cell
            if emp_obj.job_id:
                worksheet.write(row, col+8, emp_obj.job_id.name)
                worksheet.set_column(col+8, col+8, 30)
            # 10 cell
            if project_obj.po:
                worksheet.write(row, col+9, project_obj.po)
                worksheet.set_column(col+9, col+9, 30)
                
            appended_cols = len(timeoff_result)
            
            for i in range(appended_cols):
                step_day = timeoff_result[i]['step_date'].strftime('%d')
                worksheet.write(0, col+9+i+1, step_day, heading_format)
                worksheet.set_column(col+9+i+1, col+9+i+1, 3)
                
                timeoff = timeoff_result[i]['time_off']
                if timeoff == "V":
                    worksheet.write(row, col+9+i+1, timeoff, v_format)
                elif timeoff == "H":
                    worksheet.write(row, col+9+i+1, timeoff, h_format)
                elif timeoff == "S":
                    worksheet.write(row, col+9+i+1, timeoff, s_format)
                elif timeoff == "W":
                    worksheet.write(row, col+9+i+1, timeoff, w_format)
                else:
                    worksheet.write(row, col+9+i+1, timeoff)
            
            # before last cell
            worksheet.write(0, col+9+appended_cols+1, "Location", heading_format)
            if emp_obj.location:
                worksheet.write(row, col+9+appended_cols+1, emp_obj.location)
                worksheet.set_column(col+9+appendedCols+1, col+9+appendedCols+1, 30)
            # last cell
            worksheet.write(0, col+9+appended_cols+2, "Nationality", heading_format)
            if emp_obj.country_id:
                worksheet.write(row, col+9+appended_cols+2, emp_obj.country_id.name)
                worksheet.set_column(col+9+appendedCols+2, col+9+appendedCols+2, 30)

            row += 1

        workbook.close()
        xlsx_data = output.getvalue()
        return xlsx_data


    @http.route('/employee_xlsx_report', type='http', auth='user')
    def get_employee_xlsx_report(self, data, **kw):
        report_obj = request.env["employee.xls.report"]
        data = json.loads(data)
        
        excel_list = self.prepare_excel_list(data)
        print("============= Excel List =============")
        print(data)
        print("============= Excel List =============")
        
        filename = "employee_timesheet_report"
        xlsx_data = self.get_xlsx_report(excel_list)
        response = request.make_response(
            xlsx_data,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition(filename + '.xlsx'))
            ],
        )

        return response

