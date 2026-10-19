# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    remarks_for_sale = fields.Text(
        string="Remarks for Sale", related="picking_id.remarks_for_sale")
    is_remarks_for_sale = fields.Boolean(
        related="company_id.remark_for_sale_order", string="Is Remarks for Sale")

    # Odoo 20: the forced move date (write override) lives in sh_stock_backdate,
    # journal entry dating in sh_stock_account_backdate (_create_account_move).
