# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError

from datetime import datetime


class EmloyeeReport(models.TransientModel):

    _name = "employee.xls.report"
    _description = "Current Project details"
    
    from_date = fields.Date(
        string='From Date',
        required=True,
    )

    to_date = fields.Date(
        string='To Date',
        required=True,
    )

    project_ids = fields.Many2many(
        'project.project',
        string='Projects',
    )

    po = fields.Char()

    employee_ids = fields.Many2many(
        'hr.employee',
        string='Employees',
    )

    validate = fields.Selection(
        [
            ("validate", "Validated"),
            ("draft", "Drafted"),
            ("all", "Validated and Drafted"),
        ],
        required=True,
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

    
    # @api.onchange("employee_ids")
    # def onchange_employee_ids(self):
    #     for rec in self:
    #         for employee in rec.employee_ids:
    #             if employee not in rec.target_employees_ids:
    #                 raise UserError(_("No any employees fit your filter entries"))


    @api.depends("from_date", "to_date", "project_ids", "employee_ids", "po")
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
            
            # filter employees according to specific project selection
            if rec.project_ids:
                """
                call _origin attribute for each record of project_ids as their ids are of type "odoo.models.NewId"
                and they themselves are of type "odoo.api.project.project"
                """
                projects = rec.project_ids.mapped(lambda p: p._origin)
                target_ids_origin = rec.target_employees_ids.mapped(lambda rec: rec._origin)
                
                """
                Based on timesheet records
                """
                # analytic_actions_2 = self.env["account.analytic.line"].search(
                #     [("project_id", "in", projects.mapped("id"))]
                # )
                # distinct_emp_ids_2 = set(analytic_actions_2.mapped(lambda rec: rec.employee_id.id))
                # distinct_emp_recs_2 = self.env["hr.employee"].browse(distinct_emp_ids_2)
                # common = target_ids_origin & distinct_emp_recs_2

                """
                Based on project followers
                """
                followers = projects.mapped(lambda project: project.message_follower_ids)
                follower_emp_recs_2 = self.env["hr.employee"].browse(followers.mapped("id"))
                common = target_ids_origin & follower_emp_recs_2
                
                print("=========================================")
                for employee in follower_emp_recs_2:
                    print(employee, employee.name)
                    print(employee.user_id, employee.user_id.name)
                    tasks = self.env['project.task'].search([]).filtered(
                        lambda task: 
                            employee.user_id in task.user_ids
                    )
                    print(tasks)
                    print(tasks.mapped("project_id"))
                print("=========================================")

                rec.target_employees_ids = common
            
            if rec.po:
                target_ids_origin = rec.target_employees_ids.mapped(lambda rec: rec._origin)
                po_projects = self.env['project.project'].search([("po", "ilike", rec.po)])
                followers_2 = po_projects.mapped(lambda project: project.message_follower_ids)
                follower_emp_recs_3 = self.env["hr.employee"].browse(followers_2.mapped("id"))
                common = target_ids_origin & follower_emp_recs_3
                rec.target_employees_ids = common


            # filter employees according to specific selected employees
            if rec.employee_ids:
                # selected_employees = self.env['hr.employee']
                # for employee in rec.employee_ids:
                #     if employee in rec.target_employees_ids:
                #         selected_employees |= employee

                rec.target_employees_ids = rec.employee_ids
    
