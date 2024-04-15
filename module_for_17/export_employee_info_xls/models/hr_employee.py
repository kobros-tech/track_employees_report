# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class WorkLocation(models.Model):

    _inherit = "hr.employee"

    joining_date = fields.Date()
    section_manager = fields.Char()
    director = fields.Char()
    emp_email = fields.Char()
    location = fields.Char()
    project_id = fields.Many2one("project.project")

    work_from_home_monday = fields.Boolean(
        "hr.work.location",
        related="monday_location_id.work_from_home",
    )
    work_from_home_tuesday = fields.Boolean(
        "hr.work.location",
        related="tuesday_location_id.work_from_home",
    )
    work_from_home_wednesday = fields.Boolean(
        "hr.work.location",
        related="wednesday_location_id.work_from_home",
    )
    work_from_home_thursday = fields.Boolean(
        "hr.work.location",
        related="thursday_location_id.work_from_home",
    )
    work_from_home_friday = fields.Boolean(
        "hr.work.location",
        related="friday_location_id.work_from_home",
    )
    work_from_home_saturday = fields.Boolean(
        "hr.work.location",
        related="saturday_location_id.work_from_home",
    )
    work_from_home_sunday = fields.Boolean(
        "hr.work.location",
        related="sunday_location_id.work_from_home",
    )
