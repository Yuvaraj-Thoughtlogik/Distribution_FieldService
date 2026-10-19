from odoo import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _find_mail_template(self):
        """Send quotations with the Northbrook template (portal button); confirmations and pro-forma
        invoices keep Odoo's standard templates."""
        if self.env.context.get("proforma") or self.state == "sale":
            return super()._find_mail_template()
        return self.env.ref("tl_dfs_demo_data.mail_template_quotation", raise_if_not_found=False) \
            or super()._find_mail_template()
