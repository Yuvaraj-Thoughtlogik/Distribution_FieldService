# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import models, fields, api
from datetime import date


class AccountMove(models.Model):

    _inherit = 'account.move'

    remarks = fields.Text(string="Remarks")
    is_remarks = fields.Boolean(related="company_id.remark_for_move")
    is_remarks_mandatory = fields.Boolean(
        related="company_id.remark_mandatory_move")
    is_boolean = fields.Boolean()

    @api.onchange('invoice_date')
    def onchange_invoice_date(self):
        if str(self.invoice_date) < str(date.today()):
            self.is_boolean = True
        else:
            self.is_boolean = False
