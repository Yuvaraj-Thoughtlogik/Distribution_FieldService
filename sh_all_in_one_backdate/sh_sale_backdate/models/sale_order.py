# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from datetime import date
from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    remarks = fields.Text(string="Remarks")
    is_remarks = fields.Boolean(
        related="company_id.remark_for_sale_order", string="Is Remarks")
    is_remarks_mandatory = fields.Boolean(
        related="company_id.remark_mandatory_for_sale_order", string="Is remarks mandatory")
    is_boolean = fields.Boolean()

    @api.onchange('date_order')
    def onchange_date_order(self):
        if self.date_order and str(self.date_order.date()) < str(date.today()):
            self.is_boolean = True
        else:
            self.is_boolean = False

    def _prepare_confirmation_values(self):
        values = super()._prepare_confirmation_values()
        if self.company_id.backdate_for_sale_order:
            # keep the (back)date entered by the user
            values.pop('date_order', None)
        else:
            values['date_order'] = fields.Datetime.now()
        return values

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals.update({
            'invoice_date': self.date_order.date() if self.company_id.backdate_for_invoice else date.today(),
            'remarks_for_sale': self.remarks or False,
        })
        return invoice_vals
