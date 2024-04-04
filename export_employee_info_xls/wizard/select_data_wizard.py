# -*- coding: utf-8 -*-

from odoo import fields, models


class EmloyeeReport(models.TransientModel):

    _name = "employee.xls.report"
    _description = "Current Project details"

    project_ids = fields.Many2many(
        'project.project',
        string='Projects',
        required=True
    )

    user_ids = fields.Many2many(
        'res.users',
        string='Employee',
    )

    def test_export(self):
        print("will do preview for the data")

    