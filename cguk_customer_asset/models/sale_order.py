from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _timesheet_create_project_prepare_values(self):

        res = super()._timesheet_create_project_prepare_values()
        res['name'] = '%s - %s' % (self.order_id.client_order_ref, self.order_id.name) if self.order_id.client_order_ref else self.order_id.name
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    parent_company = fields.Many2one(string='Parent Company', related='partner_id.parent_id')
    sale_customer_assets_ids = fields.One2many(
        comodel_name="customer.asset",
        string="Sold Customer Assets",
        inverse_name="sale_order_id",
    )
    subscription_customer_assets_ids = fields.Many2many(
        comodel_name="customer.asset",
        string="Customer Assets",
        domain="[('id','in',available_assets_ids)]"
    )

    available_assets_ids = fields.Many2many(
        comodel_name="customer.asset",
        string="Available Assets",
        compute="_compute_available_assets"
    )

    @api.depends("partner_id", "partner_shipping_id")
    def _compute_available_assets(self):
        for record in self:
            record.available_assets_ids = self.env['customer.asset'].search([
               
                # Conditions 2-4: Partner match + optional shipping address match
                '&',
                '|',
                ('contact_id', '=', record.partner_id.id),
                ('customer_company_id', '=', record.partner_id.id),
                '|',
                ('delivery_address_id', '=', False),
                ('delivery_address_id', '=', record.partner_shipping_id.id)
            ])

    @api.depends('partner_id')
    def _compute_user_id(self):
        # Always use the logged-in user as salesperson instead of the customer's salesperson
        is_salesman = self.env.user.has_group('sales_team.group_sale_salesman')
        for order in self:
            if order.partner_id and not (order._origin.id and order.user_id):
                if is_salesman:
                    order.user_id = self.env.user
                else:
                    super(SaleOrder, order)._compute_user_id()

    renewal_date = fields.Date(string="Renewal Date")

    sale_customer_assets_count = fields.Integer(string="Customer Assets Count", compute="_compute_sale_customer_assets_count")
    subscription_customer_assets_count = fields.Integer(string="Subscription Customer Assets Count", compute="_compute_subscription_customer_assets_count")

    @api.depends('sale_customer_assets_ids')
    def _compute_sale_customer_assets_count(self):
        for record in self:
            record.sale_customer_assets_count = len(record.sale_customer_assets_ids)

    @api.depends('subscription_customer_assets_ids')
    def _compute_subscription_customer_assets_count(self):
        for record in self:
            record.subscription_customer_assets_count = len(record.subscription_customer_assets_ids)

    def action_view_subscription_customer_assets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Related Customer Assets',
            'res_model': 'customer.asset',  # replace with actual model
            'view_mode': 'list,form',
            'domain': [('subscription_id', '=', self.id)],  # or use correct relation field
            'target': 'current',
        }
    def action_view_sale_customer_assets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Related Customer Assets',
            'res_model': 'customer.asset',  # replace with actual model
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.id)],  # or use correct relation field
            'target': 'current',
        }


