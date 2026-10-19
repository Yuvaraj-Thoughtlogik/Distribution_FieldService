# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import models


class ScrapBackdateWizardInherit(models.TransientModel):
    _inherit = 'sh.scrap.backdate.wizard'

    def assign_backdate(self):
        res = super().assign_backdate()
        if self.company_id.backdate_for_scrap:
            # Odoo 20: scraps are stock.move records (is_scrap); no valuation layers anymore
            self.scrap_ids._sh_backdate_account_moves(self.date_done)
        return res
