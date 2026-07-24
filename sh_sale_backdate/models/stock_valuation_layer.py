# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import models, api


class StockValuationLayer(models.Model):
    """Stock Valuation Layer"""

    _inherit = 'stock.valuation.layer'

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for rec in res:
            if rec.stock_move_id:
                self._cr.execute(f"""
                    UPDATE stock_valuation_layer 
                    SET create_date='{rec.stock_move_id.date}'
                    WHERE id={rec.id} """)
        return res
