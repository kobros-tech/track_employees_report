# -*- coding: utf-8 -*-

import json

from odoo import http
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

    def get_timeoff_days(self, employee, to_date, from_date):
        # mehtod will get three arguments [employee, from_date, to_date]
        print("Time Off for employee: ", employee.name)

        if (not from_date) or (not to_date):
            time_off_recs_all = self.env["hr.leave"].search([])
            all_from_dates = time_off_recs_all.mapped(lambda timeoff: fields.Date.to_date(timeoff.date_from))
            from_date = sorted(all_from_dates)[0]
            all_to_dates = time_off_recs_all.mapped(lambda timeoff: fields.Date.to_date(timeoff.date_to))
            to_date = sorted(all_to_dates)[-1]

            print(from_date.strftime('%d-%m-%Y'))
            print(to_date.strftime('%d-%m-%Y'))


        number_of_days = (to_date - from_date).days
        step_date = from_date
        for i in range(number_of_days + 1):

            time_off_recs_all = self.env["hr.leave"].search([])

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
            )

            
            # print("time_off_days", 
            #     time_off_recs_all.mapped(lambda timeoff: fields.Date.to_string(timeoff.date_from)), 
            #     filtered_time_off.mapped(lambda timeoff: fields.Date.to_string(timeoff.date_from)))


            for time_off in filtered_time_off:
                time_off_date = fields.Date.to_date(time_off.date_from)
                
                # check if the step day is a working day or a time off
                if time_off_date == step_date:
                    print("______________ time off result ______________")
                    print("Time Off: ==>", time_off.holiday_status_id.display_name)
                    print("From: ==>", fields.Date.to_date(time_off.date_from))
                    print("To: ==>", fields.Date.to_date(time_off.date_to))
                    print("Project: ==>", time_off.holiday_status_id.timesheet_project_id.name)
                    print("Status: ==>", time_off.state)
                    print("_____________________________________________")
                else:
                    print("______________ time off result ______________")
                    print("Working Day!")
                    print("_____________________________________________")
        
            step_date = fields.Date.add(from_date, days=i+1)
    

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
            worksheet.write(row, col+9, "PO")
            
            # start looping over all available days

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


