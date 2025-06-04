from odoo import models, fields, api
from datetime import timedelta
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    number_of_services_per_year = fields.Selection(
        selection=[('1', '1'), ('2', '2'), ('3', '3'), ('4', '4')],
        string="Number of Services Per Year"
    )

    show_number_of_services = fields.Boolean(compute="_compute_show_number_of_services", store=True)

    @api.depends('recurring_invoice')
    def _compute_show_number_of_services(self):
        for rec in self:
            rec.show_number_of_services = bool(rec.recurring_invoice)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super().action_confirm()
        self._create_fsm_tasks_from_subscription()
        return res

    def _create_fsm_tasks_from_subscription(self):
        Task = self.env['project.task']
        for order in self:
            for line in order.order_line:
                product = line.product_id
                # Only if product is of type 'service', recurring, and has number of services
                if (
                    product.recurring_invoice
                    and product.type == 'service'
                    and product.number_of_services_per_year
                ):
                    for i in range(int(product.number_of_services_per_year)):
                        Task.create([{
                            'name': f"{product.name} - {order.name} - Task {i + 1}",
                            'sale_line_id': line.id,
                            'partner_id': order.partner_id.id,
                            'is_fsm': True,
                            # 'user_id': self.env.uid,
                            'project_id': product.project_id.id if product.project_id else None,
                            'planned_date_begin': fields.Datetime.now(),
                            'date_deadline': fields.Datetime.now()


                        }])
