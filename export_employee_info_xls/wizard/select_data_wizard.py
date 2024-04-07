# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError

from datetime import datetime


class EmloyeeReport(models.TransientModel):

    _name = "employee.xls.report"
    _description = "Current Project details"
    
    from_date = fields.Date(
        string='From Date',
    )

    to_date = fields.Date(
        string='To Date',
    )

    project_ids = fields.Many2many(
        'project.project',
        string='Projects',
    )

    employee_ids = fields.Many2many(
        'hr.employee',
        string='Employees',
    )

    target_employees_ids = fields.Many2many(
        'hr.employee',
        string='Target Employees',
        compute="_compute_employees_records",
        default=lambda self: self.env['hr.employee'].search([])
    )


    @api.onchange("to_date")
    def onchange_to_date(self):
        for rec in self:
            if rec.to_date and rec.from_date:
                if rec.to_date < rec.from_date:
                    raise UserError(_("To Date must be greater than From Date"))


    @api.depends("from_date", "to_date", "project_ids", "employee_ids")
    def _compute_employees_records(self):
        self.ensure_one()

        for rec in self:

            if not rec.target_employees_ids:
                rec.target_employees_ids = rec.env['hr.employee'].search([])

            # filter employees according to specific date range
            if rec.from_date and rec.to_date:
                analytic_actions = self.env["account.analytic.line"].search(["&", ("date", ">=", rec.from_date), ("date", "<=", rec.to_date)])
                distinct_emp_ids = set(analytic_actions.mapped(lambda rec: rec.employee_id.id))
                distinct_emp_recs = self.env["hr.employee"].browse(distinct_emp_ids)
                target_ids_origin = rec.target_employees_ids.mapped(lambda rec: rec._origin)
                common = target_ids_origin & distinct_emp_recs
                rec.target_employees_ids = common
            
            if rec.project_ids:
                """
                call _origin attribute for each record of project_ids as their ids are of type "odoo.models.NewId"
                and they themselves are of type "odoo.api.project.project"
                """
                projects = rec.project_ids.mapped(lambda p: p._origin)

                analytic_actions_2 = self.env["account.analytic.line"].search([("project_id", "in", projects.mapped("id"))])
                distinct_emp_ids_2 = set(analytic_actions_2.mapped(lambda rec: rec.employee_id.id))
                distinct_emp_recs_2 = self.env["hr.employee"].browse(distinct_emp_ids_2)
                
                target_ids_origin = rec.target_employees_ids.mapped(lambda rec: rec._origin)
                common = target_ids_origin & distinct_emp_recs_2
                rec.target_employees_ids = common

            if rec.employee_ids:
                
                for employee in rec.employee_ids:
                    if employee not in rec.target_employees_ids:
                        raise UserError(_("No any employees fit your filter entries"))
                    else:
                        pass                        

                rec.target_employees_ids = rec.employee_ids

    
    def get_target_employees_days(self):
        self.ensure_one()
        employee = self.env["hr.employee"].browse([1])
        from_date = self.from_date
        to_date = self.to_date

        
        # mehtod will get three arguments [employee, from_date, to_date]
        print("Time Off for employee: ", employee.name)

        time_off_recs_all = self.env["hr.leave"].search([]).filtered(lambda timeoff: 
            employee in timeoff.all_employee_ids
        )
        
        print(employee)
        print(time_off_recs_all)
        print("Time Off Number:", len(time_off_recs_all))

        # List of all employee time off days 
        time_off_list = []

        # public hoidays to check within before returning time off days
        publick_holidays = self.env["resource.calendar.leaves"].search([("name", "ilike", "Public Time Off")])

        # do search if there is any time off records
        if len(time_off_recs_all) > 0:

            # set default starting date and end date
            if (not from_date) or (not to_date):

                all_from_dates = time_off_recs_all.mapped(lambda timeoff: fields.Date.to_date(timeoff.date_from))
                from_date = sorted(all_from_dates)[0]
                all_to_dates = time_off_recs_all.mapped(lambda timeoff: fields.Date.to_date(timeoff.date_to))
                to_date = sorted(all_to_dates)[-1]

                print(from_date.strftime('%d-%m-%Y'))
                print(to_date.strftime('%d-%m-%Y'))


            number_of_days = (to_date - from_date).days
            step_date = from_date

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
                print("Public Holidays:", publick_holidays)

                publick_holiday = publick_holidays.filtered(
                    lambda rec: 
                        fields.Date.to_date(rec.date_from) == step_date
                )
                
                for day in publick_holidays:
                    print("=================================")
                    print("Public Holiday:", day.name)
                    print("Public Holiday From:", day.date_from)
                    print("Public Holiday To:", day.date_to)
                    print("=================================")
                
                print(publick_holiday)

                # Check if each step day is a public holiday or another holiday
                if len(publick_holiday) > 0:
                    holiday = publick_holiday[:1]
                    time_off_list.append(
                        {
                            "time_off": "H",
                            "from": holiday.date_from,
                            "to": holiday.date_to,
                            "project": holiday.holiday_id.holiday_status_id.timesheet_project_id,
                            "state": holiday.holiday_id.state,
                        }
                    )
                    print("Time Off: ==>", "H")
                else:
                    for time_off in filtered_time_off:
                        time_off_date_from = fields.Date.to_date(time_off.date_from)
                        time_off_date_to = fields.Date.to_date(time_off.date_to)
                        time_off_name = time_off.holiday_status_id.display_name
                        time_off_project = time_off.holiday_status_id.timesheet_project_id
                        
                        # default value prefix for time off display name
                        prefix = ""
                        
                        # check if the step day is a working day or a time off
                        if time_off_date_from == step_date or time_off_date_to == step_date:
                            
                            if "Sick" in time_off_name:
                                prefix = "S"
                            elif "Compensatory" in time_off_name or "Paid" in time_off_name or "Unpaid" in time_off_name:
                                prefix = "V"

                            time_off_list.append(
                                {
                                    "time_off": prefix,
                                    "from": time_off_date_from,
                                    "to": time_off_date_to,
                                    "project": time_off_project,
                                    "state": time_off.state,
                                }
                            )

                            print("______________ time off result ______________")
                            print("Time Off: ==>", prefix)
                            print("From: ==>", time_off_date_from)
                            print("To: ==>", time_off_date_to)
                            print("Project: ==>", time_off_project.name)
                            print("Status: ==>", time_off.state)
                            print("_____________________________________________")
                        else:
                            prefix = "P"
                            time_off_list.append(
                                {
                                    "time_off": prefix,
                                }
                            )

                            print("______________ time off result ______________")
                            print("Working Day!")
                            print("_____________________________________________")
                        
                        # end of timeoff loop
                
                # end of looping over the specified number of days
                step_date = fields.Date.add(from_date, days=i+1)
        
        print(time_off_list)
                
    