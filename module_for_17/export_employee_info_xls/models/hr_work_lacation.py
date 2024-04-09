# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class WorkLocation(models.Model):

    _inherit = "hr.work.location"

    work_from_home = fields.Boolean()

