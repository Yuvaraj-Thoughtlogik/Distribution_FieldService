# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import models, fields, api
from datetime import date


class AccountPayment(models.Model):

    _inherit = 'account.payment'

    remarks = fields.Text(string="Remarks")
    is_remarks = fields.Boolean(related="company_id.remark_for_payment")
    is_remarks_mandatory = fields.Boolean(
        related="company_id.remark_mandatory_payment")
    is_boolean = fields.Boolean()

    @api.onchange('date')
    def onchange_date(self):
        if str(self.date) < str(date.today()):
            self.is_boolean = True
        else:
            self.is_boolean = False
