# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    remarks_for_purchase = fields.Text(
        string="Remarks for Purchase", related="purchase_id.remarks")
    is_remarks_for_purchase = fields.Boolean(
        related="company_id.remark_for_purchase_order", string="Is Remarks for Purchase")

    def write(self, vals):
        if vals.get('date_done'):
            po_pickings = self.filtered(
                lambda p: p.purchase_id and p.purchase_id.date_approve and p.company_id.backdate_for_stock_move)
            if po_pickings:
                for date_approve, pickings in po_pickings.grouped(lambda p: p.purchase_id.date_approve).items():
                    super(StockPicking, pickings).write(dict(vals, date_done=date_approve))
                others = self - po_pickings
                if others:
                    super(StockPicking, others).write(vals)
                return True
        return super().write(vals)
