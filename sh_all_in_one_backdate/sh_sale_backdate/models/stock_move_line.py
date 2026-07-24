# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    remarks_for_sale = fields.Text(
        string="Remarks for sale", related="move_id.remarks_for_sale")
    is_remarks_for_sale = fields.Boolean(
        related="company_id.remark_for_sale_order", string="Is Remarks for sale")

    def _action_done(self):
        res = super()._action_done()
        if self.picking_id.sale_id:
            self.date = self.picking_id.sale_id.date_order
        return res
