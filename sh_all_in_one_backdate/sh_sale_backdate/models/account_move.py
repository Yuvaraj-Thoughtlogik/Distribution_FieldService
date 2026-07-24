# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    remarks_for_sale = fields.Text(string="Remarks for Sale")
    is_remarks_for_sale = fields.Boolean(
        related="company_id.remark_for_sale_order", string="Is Remarks for Sale")
