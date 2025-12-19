from odoo import models


class ResPartner(models.Model):
    _inherit = "res.company"

    def _get_tax_periodicity(self, report):
        # if report == self.env.ref('l10n_uk_reports_paye.tax_report_paye_eps'):
        #    return 'monthly'
        return super()._get_tax_periodicity(report)
