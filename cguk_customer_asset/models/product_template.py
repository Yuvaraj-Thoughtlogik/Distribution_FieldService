from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    number_of_services_per_year = fields.Selection(
        selection=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4')],
        string="Number of Services Per Year",
        default='1',
    )
    fsm_task_creation_mode = fields.Selection(
        selection=[('per_asset', 'One Intervention per Customer Asset'), ('shared', 'Same Intervention for All Assets')],
        string="Intervention Creation Mode",
        default='shared',
    )
    track_cpe = fields.Boolean(string='Track CPE')

    show_number_of_services = fields.Boolean(compute="_compute_show_number_of_services", store=True)

    @api.depends('recurring_invoice')
    def _compute_show_number_of_services(self):
        for rec in self:
            rec.show_number_of_services = bool(rec.recurring_invoice)
