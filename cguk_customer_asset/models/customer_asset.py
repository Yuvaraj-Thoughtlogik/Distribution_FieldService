from odoo import api, fields, models


class CustomerAsset(models.Model):
    _name = 'customer.asset'
    _description = 'Customer Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string="Customer Asset No", compute='_compute_name_from_lot', store=True)
    active_asset = fields.Boolean(string="Active?", default=True)
    product_serial_No = fields.Char(
        string="Serial Number",
        related="product_lot_id.name",
        store=True,
        readonly=False,
    )

    product_lot_id = fields.Many2one('stock.lot', string="Lot ID")
    product_id = fields.Many2one('product.product', string='Product', required=True)
    sale_date = fields.Date(string='Sale Date')
    install_date = fields.Date(string='Install Date')
    under_warranty = fields.Boolean(string='Under Warranty?')
    warranty_expiry = fields.Date(string='Warranty Expiry Date')
    active_contract = fields.Boolean(string='Active Contract?', compute='_compute_active_contract')
    contract_start_date = fields.Date(string='Start Date', related="subscription_id.start_date")
    contract_end_date = fields.Date(string='End Date', related="subscription_id.end_date")
    contract_renewal_date = fields.Date(string='Renewal Date', related="subscription_id.next_invoice_date")
    customer_company_id = fields.Many2one('res.partner', string='Company', domain="[('is_company','=',True)]")
    company_id = fields.Many2one(
        'res.company',
        string='Internal Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    contact_id = fields.Many2one('res.partner', string='Contact')
    partner_id = fields.Many2one('res.partner', string='Partner')
    street = fields.Char(compute='_compute_address', store=True, readonly=False)
    street2 = fields.Char(compute='_compute_address', store=True, readonly=False)
    zip = fields.Char(change_default=True, compute='_compute_address', store=True, readonly=False)
    city = fields.Char(compute='_compute_address', store=True, readonly=False)
    state_id = fields.Many2one(
        "res.country.state",
        string='State',
        ondelete='restrict',
        domain="[('country_id', '=?', country_id)]",
        compute='_compute_address', store=True, readonly=False,
    )
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict',
                                 compute='_compute_address', store=True, readonly=False)
    country_code = fields.Char(related='country_id.code', string="Country Code")

    # Both sides of these Many2many share the same relation table, so they are
    # automatically kept in sync by the ORM.
    helpdesk_ticket_ids = fields.Many2many(
        'helpdesk.ticket', 'customer_asset_helpdesk_ticket_rel',
        'customer_asset_id', 'helpdesk_ticket_id',
        string='Help Desk Ticket',
    )
    intervention_ids = fields.Many2many(
        'planning.slot', 'customer_asset_planning_slot_rel',
        'customer_asset_id', 'planning_slot_id',
        string='Interventions',
        help="Field Service interventions (planning shifts) performed on this asset.",
    )
    intervention_count = fields.Integer(compute='_compute_intervention_count', string="Intervention Count")
    subscription_id = fields.Many2one('sale.order', string='Subscription', domain="[('is_subscription','=',True)]")
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', domain="[('is_subscription','=',False)]")
    stock_picking_id = fields.Many2one('stock.picking', string='Delivery Order', domain="[('picking_type_code', '=', 'outgoing')]")
    move_line_id = fields.Many2one('stock.move.line', string='Move Line', index='btree_not_null')
    repair_order_ids = fields.One2many(
        comodel_name='repair.order',
        inverse_name='customer_asset_id',
        string='Repair Order')

    delivery_address_id = fields.Many2one(
        'res.partner',
        string='Service Address',
        domain="[('id','in',delivery_ids)]",
    )
    cache_delivery_address_id = fields.Many2one('res.partner', string='Cached Service Address')
    delivery_ids = fields.Many2many(comodel_name='res.partner', compute='_compute_address_ids')
    same_as_main_address = fields.Boolean(string="Same as main address?")

    delivery_street = fields.Char(compute='_compute_delivery_address', store=True, readonly=False)
    delivery_street2 = fields.Char(compute='_compute_delivery_address', store=True, readonly=False)
    delivery_zip = fields.Char(change_default=True, compute='_compute_delivery_address', store=True, readonly=False)
    delivery_city = fields.Char(compute='_compute_delivery_address', store=True, readonly=False)
    delivery_state_id = fields.Many2one(
        "res.country.state", string='Delivery State', ondelete='restrict',
        domain="[('country_id', '=?', delivery_country_id)]",
        compute='_compute_delivery_address', store=True, readonly=False)
    delivery_country_id = fields.Many2one('res.country', string='Delivery Country', ondelete='restrict',
                                          compute='_compute_delivery_address', store=True, readonly=False)
    delivery_country_code = fields.Char(related='delivery_country_id.code', string="Delivery Country Code")

    @api.depends('name', 'product_id.display_name')
    def _compute_display_name(self):
        """'Customer Asset No - [Product Display Name]'"""
        for record in self:
            display_parts = []
            if record.name and record.name != "New":
                display_parts.append(record.name)
            if record.product_id and record.product_id.display_name:
                display_parts.append(record.product_id.display_name)
            record.display_name = ' - '.join(display_parts) if display_parts else self.env._("New Asset")

    @api.depends('subscription_id')
    def _compute_active_contract(self):
        for record in self:
            record.active_contract = bool(record.subscription_id)

    @api.depends('intervention_ids')
    def _compute_intervention_count(self):
        for record in self:
            record.intervention_count = len(record.intervention_ids)

    @api.depends('product_serial_No')
    def _compute_name_from_lot(self):
        for rec in self:
            rec.name = rec.product_serial_No or "New"

    @api.depends('contact_id', 'customer_company_id')
    def _compute_address(self):
        self._compute_main_address()

    @api.depends('delivery_address_id')
    def _compute_delivery_address(self):
        for record in self:
            delivery = record.delivery_address_id
            record.delivery_street = delivery.street or ''
            record.delivery_street2 = delivery.street2 or ''
            record.delivery_zip = delivery.zip or ''
            record.delivery_city = delivery.city or ''
            record.delivery_state_id = delivery.state_id
            record.delivery_country_id = delivery.country_id

    @api.depends('contact_id', 'customer_company_id')
    def _compute_address_ids(self):
        for rec in self:
            partners = self.env['res.partner']
            for partner in (rec.contact_id, rec.customer_company_id):
                if partner:
                    partners |= partner
                    partners |= partner.child_ids.filtered(lambda p: p.type in ('delivery', 'other'))
            rec.delivery_ids = partners

    def _compute_main_address(self):
        for rec in self:
            source = rec.customer_company_id or rec.contact_id
            rec.street = source.street or ''
            rec.street2 = source.street2 or ''
            rec.zip = source.zip or ''
            rec.city = source.city or ''
            rec.state_id = source.state_id
            rec.country_id = source.country_id

    @api.onchange('same_as_main_address')
    def _onchange_same_as_main_address(self):
        for rec in self:
            if rec.same_as_main_address:
                rec.delivery_address_id = rec.contact_id or rec.customer_company_id
            else:
                rec.delivery_address_id = rec.cache_delivery_address_id

    def _get_asset_partner(self):
        self.ensure_one()
        return self.delivery_address_id or self.contact_id or self.customer_company_id or self.partner_id

    def action_view_subscription(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Subscription'),
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.subscription_id.id,
            'target': 'current',
        }

    def action_view_ticket(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Helpdesk Tickets'),
            'res_model': 'helpdesk.ticket',
            'view_mode': 'list,form',
            'domain': [('customer_assets_ids', 'in', self.id)],
            'context': {'default_customer_assets_ids': [self.id], 'default_partner_id': self.contact_id.id or self.customer_company_id.id},
            'target': 'current',
        }

    def action_view_interventions(self):
        self.ensure_one()
        partner = self._get_asset_partner()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Interventions'),
            'res_model': 'planning.slot',
            'view_mode': 'list,form,calendar,gantt',
            'views': [(False, 'list'), (False, 'form'), (False, 'calendar'), (False, 'gantt')],
            'domain': [('customer_assets_ids', 'in', self.id)],
            'context': {
                'default_customer_assets_ids': [self.id],
                'default_partner_id': partner.id,
            },
            'target': 'current',
        }

    def action_plan_intervention(self):
        """Create a new (to schedule) intervention for this asset and open it."""
        self.ensure_one()
        partner = self._get_asset_partner()
        slot = self.env['planning.slot'].create({
            'name': self.env._("Service - %(asset)s", asset=self.display_name),
            'partner_id': partner.id,
            'customer_assets_ids': [fields.Command.link(self.id)],
            'start_datetime': False,
            'end_datetime': False,
            'allocated_hours': 1.0,
            'company_id': self.company_id.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'planning.slot',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_id': slot.id,
            'target': 'current',
        }

    def action_view_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Sale Order'),
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
            'target': 'current',
        }

    def action_view_delivery_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Delivery Order'),
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.stock_picking_id.id,
            'target': 'current',
        }

    def action_view_repair_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Repairs'),
            'res_model': 'repair.order',
            'view_mode': 'list,form',
            'domain': [('customer_asset_id', '=', self.id)],
            'target': 'current',
        }
