# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class EmloyeeReport(models.TransientModel):

    _name = "employee.xls.report"
    _description = "Current Project details"

    analytic_from = fields.Many2one(
        'account.analytic.line',
        string='From',
    )

    analytic_to = fields.Many2one(
        'account.analytic.line',
        string='To',
    )
    
    from_date = fields.Date(
        related="analytic_from.date",
        string='From Date',
    )

    to_date = fields.Date(
        related="analytic_to.date",
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

    target_users_ids = fields.Many2many(
        'hr.employee',
        string='Target Employees',
        compute="_compute_employees_records",
        default=lambda self: self.env['hr.employee'].search([])
    )


    @api.onchange("to_date")
    def onchange_to_date(self):
        for rec in self:
            if rec.to_date < rec.from_date:
                raise UserError(_("To Date must be greater than From Date"))


    @api.depends("analytic_from", "analytic_to", "project_ids", "employee_ids")
    def _compute_employees_records(self):
        self.ensure_one()

        for rec in self:

            # filter employees according to specific date range
            if rec.analytic_from and rec.analytic_to:
                analytic_actions = self.env["account.analytic.line"].search(["&", ("date", ">=", rec.from_date), ("date", "<=", rec.to_date)])
                distinct_emp_ids = set(analytic_actions.mapped(lambda rec: rec.employee_id.id))
                distinct_emp_recs = self.env["hr.employee"].browse(distinct_emp_ids)
                rec.target_users_ids |= distinct_emp_recs
                
                # print("===========================================")
                # print(analytic_actions)
                # print(set(analytic_actions.mapped(lambda rec: fields.Date.to_string(rec.date))))
                # print(analytic_actions.mapped(lambda rec: rec.employee_id.id))
                # print(distinct_emp_ids)
                # print(distinct_emp_recs)
                # print(rec.target_users_ids)
                # print("===========================================")

            if rec.project_ids:
                """
                call _origin attribute for each record of project_ids as their ids are of type "odoo.models.NewId"
                and they themselves are of type "odoo.api.project.project"
                """
                projects = rec.project_ids.mapped(lambda p: p._origin)

                analytic_actions_2 = self.env["account.analytic.line"].search([("project_id", "in", projects.mapped("id"))])
                distinct_emp_ids_2 = set(analytic_actions_2.mapped(lambda rec: rec.employee_id.id))
                distinct_emp_recs_2 = self.env["hr.employee"].browse(distinct_emp_ids_2)
                
                # print("first", distinct_emp_recs)
                # print("second", distinct_emp_recs_2)
                # print("target", rec.target_users_ids)

                # make common records with the original
                target_ids_origin = rec.target_users_ids.mapped(lambda rec: rec._origin)
                common = target_ids_origin & distinct_emp_recs_2
                rec.target_users_ids = common

            if rec.employee_ids:
                
                print(rec.employee_ids)
                print(rec.employee_ids.mapped(lambda rec: rec._origin))
                
                for employee in rec.employee_ids:
                    if employee not in rec.target_users_ids:
                        raise UserError(_("No any employees fit your filter entries"))
                    else:
                        pass                        

                rec.target_users_ids = rec.employee_ids          

            print(rec.target_users_ids.mapped(lambda u: u._origin))
            


    