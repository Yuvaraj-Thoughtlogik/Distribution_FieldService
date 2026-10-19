# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    remarks_for_sale = fields.Text(
        string="Remarks for sale", related="move_id.remarks_for_sale")
    is_remarks_for_sale = fields.Boolean(
        related="company_id.remark_for_sale_order", string="Is Remarks for sale")

    # Odoo 20: stock.move.line.date is related to stock.move.date, the move
    # date is forced to the sale date through the picking scheduled date.
