# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from datetime import date
from odoo import fields, models, api
from odoo.fields import Command


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
        if str(self.date_order.date()) < str(date.today()):
            self.is_boolean = True
        else:
            self.is_boolean = False



    def _prepare_confirmation_values(self):
        values = super()._prepare_confirmation_values()

        if self.company_id.backdate_for_sale_order:
            if 'date_order' in values:
                values.pop('date_order', None)
        else:
            values['date_order'] = fields.Datetime.now()

        return values



    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()

        return {
            'ref': self.client_order_ref or '',
            'move_type': 'out_invoice',
            'narration': self.note,
            'currency_id': self.currency_id.id,
            'campaign_id': self.campaign_id.id,
            'medium_id': self.medium_id.id,
            'source_id': self.source_id.id,
            'team_id': self.team_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id._get_fiscal_position(self.partner_invoice_id)).id,
            'invoice_origin': self.name,
            'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_user_id': self.user_id.id,
            'payment_reference': self.reference,
            'transaction_ids': [Command.set(self.transaction_ids.ids)],
            'company_id': self.company_id.id,
            'invoice_line_ids': [],
            'invoice_date': self.date_order.date() if self.company_id.backdate_for_invoice else date.today(),
            'remarks_for_sale': self.remarks if self.remarks else False
        }
