from odoo import models, fields, api,_
from datetime import timedelta
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    number_of_services_per_year = fields.Selection(
        selection=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4')],
        string="Number of Services Per Year",
        default='1'
    )
    track_cpe = fields.Boolean(string='Track CPE')


    show_number_of_services = fields.Boolean(compute="_compute_show_number_of_services", store=True)

    @api.depends('recurring_invoice')
    def _compute_show_number_of_services(self):
        for rec in self:
            rec.show_number_of_services = bool(rec.recurring_invoice)




