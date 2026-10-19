# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    remarks_for_purchase = fields.Text(
        string="Remarks for Purchase", related="picking_id.remarks_for_purchase")
    is_remarks_for_purchase = fields.Boolean(
        related="company_id.remark_for_purchase_order", string="Is Remarks for Purchase")

    # Odoo 20: the forced move date (write override) lives in sh_stock_backdate,
    # journal entry dating in sh_stock_account_backdate (_create_account_move).
