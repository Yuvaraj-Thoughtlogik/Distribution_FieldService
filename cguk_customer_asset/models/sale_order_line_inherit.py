from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    track_cpe = fields.Boolean(string='Track CPE')

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    customer_assets = fields.One2many(
        comodel_name="customer.asset",
        string="Customer Assets",
        inverse_name="subscription_id",
        domain="[('contact_id', '=', partner_id)]"
    )

    renewal_date = fields.Date(string="Renewal Date")

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()

        for order in self:
            # Create a subscription order (with plan_id to make it a recurring subscription)
            subscription_plan = self.env['sale.subscription.plan']
            yearly_plan = subscription_plan.search([('name', '=', 'Yearly')], limit=1)

            # Create it if not found
            if not yearly_plan:
                yearly_plan = subscription_plan.create({
                    'name': 'Yearly',
                    'recurring_rule_type': 'year',
                    'recurring_interval': 1,
                    'user_extend': True,  # or False — depends on your logic
                    'user_closable': True,  # optional fields
                    'user_quantity': True,
                })

            # Now create the subscription order
            subscription = self.env['sale.order'].create({
                'partner_id': order.partner_id.id,
                'company_id': order.company_id.id,
                'date_order': order.date_order,
                'plan_id': yearly_plan.id,
                'start_date': fields.Date.today(),
                'origin_order_id':order.id,
                'origin': order.name,
                'is_subscription': True,
            })
            order.subscription_id = subscription.id
            # Create customer assets linked to the subscription
            for line in order.order_line:
                if line.track_cpe and line.product_id:
                    self.env['customer.asset'].create({
                        'product_id': line.product_id.id,
                        'sale_date': order.date_order,
                        'company_id': order.company_id.id,
                        'contact_id': order.partner_id.id,
                        'sale_order_id': order.id,
                        'address': order.partner_shipping_id.contact_address,
                        'subscription_id': subscription.id,
                    })
        return res

    def action_view_subscription(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Subscription',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.subscription_id.id,
            'target': 'current',
        }
    def action_view_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.origin_order_id.id,
            'target': 'current',
        }