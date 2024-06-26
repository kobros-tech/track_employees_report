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
            ("draft", "Drafted"),
            ("validate", "Validated"),
            ("all", "Drafted and Validated"),
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

            # # filter employees according to specific date range
            # if rec.from_date and rec.to_date:
            #     analytic_actions = self.env["account.analytic.line"].search(["&", ("date", ">=", rec.from_date), ("date", "<=", rec.to_date)])
            #     distinct_emp_ids = set(analytic_actions.mapped(lambda rec: rec.employee_id.id))
            #     distinct_emp_recs = self.env["hr.employee"].browse(distinct_emp_ids)
            #     target_ids_origin = rec.target_employees_ids.mapped(lambda rec: rec._origin)
            #     common = target_ids_origin & distinct_emp_recs
            #     rec.target_employees_ids = common
            
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
                tasks = projects.mapped(lambda project: project.task_ids)
                project_assignees = tasks.mapped("user_ids")
                project_employees = self.env['hr.employee'].search([("user_id", "in", project_assignees.mapped("id"))])
                common = target_ids_origin & project_employees

                # print("=========================================")
                # print("project_assignees", project_assignees)
                # print("project_employees", project_employees)
                # print("=========================================")

                rec.target_employees_ids = common
            
            if rec.po:
                target_ids_origin = rec.target_employees_ids.mapped(lambda rec: rec._origin)
                po_projects = self.env['project.project'].search([("po", "ilike", rec.po)])
                tasks = po_projects.mapped(lambda project: project.task_ids)
                project_assignees = tasks.mapped("user_ids")
                project_employees = self.env['hr.employee'].search([("user_id", "in", project_assignees.mapped("id"))])
                common = target_ids_origin & project_employees

                # print("=========================================")
                # print("project_assignees", project_assignees)
                # print("project_employees", project_employees)
                # print("=========================================")

                rec.target_employees_ids = common


            # filter employees according to specific selected employees
            if rec.employee_ids:
                # selected_employees = self.env['hr.employee']
                # for employee in rec.employee_ids:
                #     if employee in rec.target_employees_ids:
                #         selected_employees |= employee

                rec.target_employees_ids = rec.employee_ids
    
