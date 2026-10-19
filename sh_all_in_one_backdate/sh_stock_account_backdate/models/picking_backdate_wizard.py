# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import models


class PickngBackdateWizardInherit(models.TransientModel):
    _inherit = 'sh.picking.backdate.wizard'

    def assign_backdate(self):
        res = super().assign_backdate()
        if self.company_id.backdate_for_picking:
            # Odoo 20: no stock.valuation.layer anymore, journal entries are on stock.move
            self.stock_picking_ids.move_ids._sh_backdate_account_moves(self.scheduled_date)
        return res
