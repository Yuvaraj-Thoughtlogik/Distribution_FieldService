# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from datetime import date
from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    remarks = fields.Text(string="Remarks")
    is_remarks = fields.Boolean(
        related="company_id.remark_for_purchase_order", string="Is Remarks")
    is_remarks_mandatory = fields.Boolean(
        related="company_id.remark_mandatory_for_purchase_order", string="Is remarks mandatory")
    is_boolean = fields.Boolean()

    @api.onchange('date_order')
    def onchange_date_order(self):
        if self.date_order:
            if str(self.date_order.date()) < str(date.today()):
                self.is_boolean = True
            else:
                self.is_boolean = False

    def button_confirm(self):
        res = super().button_confirm()
        for order in self:
            if order.company_id.backdate_for_purchase_order and order.date_approve:
                order.date_approve = order.date_order
        return res

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        invoice_vals.update({
            'invoice_date': self.date_approve if self.company_id.backdate_for_bill else date.today(),
            'remarks_for_purchase': self.remarks or False,
        })
        return invoice_vals


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        res = super()._prepare_stock_move_vals(
            picking, price_unit, product_uom_qty, product_uom)
        if self.company_id.backdate_for_stock_move:
            res.update({
                'date': self.order_id.date_order,
                'date_deadline': self.order_id.date_order,
            })
        return res
