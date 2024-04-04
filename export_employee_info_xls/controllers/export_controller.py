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

    def get_xlsx_report(self, data, response):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Project Info')
        worksheet.write(0, 0, 'Hello Excel')
        
        # styleing
        
        # writing data

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
        data = {}
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


