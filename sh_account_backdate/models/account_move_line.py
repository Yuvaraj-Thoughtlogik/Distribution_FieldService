# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import models, fields


class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    remarks = fields.Text(string="Remarks", related="move_id.remarks")
