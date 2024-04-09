# -*- coding: utf-8 -*-

from odoo import fields, models, api, _

class WorkLocation(models.Model):

    _inherit = "project.project"

    po = fields.Char()
