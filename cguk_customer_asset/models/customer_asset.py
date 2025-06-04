from odoo import models, fields, api
import typing
from odoo.addons.base.models.res_country import Country, CountryState
if typing.TYPE_CHECKING:
    from odoo.addons.base.models.res_country import Country, CountryState

class CustomerAsset(models.Model):
    _name = 'customer.asset'
    _description = 'Customer Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string="Customer Asset No", compute='_compute_name_from_lot', store=True)
    product_serial_No = fields.Char(
        string="Serial Number",
        related="product_lot_id.name",
        store=True,
        readonly=False
    )

    # product_serial_No = fields.Char(string="Equipment Serial No",compute="_compute_serial_no", store=True)
    product_lot_id = fields.Many2one('stock.lot',string="Lot ID")
    product_id = fields.Many2one('product.product', string='Product', required=True)
    sale_date = fields.Date(string='Sale Date')
    install_date = fields.Date(string='Install Date')
    under_warranty = fields.Boolean(string='Under Warranty?')
    warranty_expiry = fields.Date(string='Warranty Expiry Date')
    active_contract = fields.Boolean(string='Active?')
    contract_start_date = fields.Date(string='Start Date')
    contract_end_date = fields.Date(string='End Date')
    contract_renewal_date = fields.Date(string='Renewal Date')
    company_id = fields.Many2one('res.partner',compute="_compute_address_company", string='Company',domain="[('is_company','=',True)]",store=True)
    contact_id = fields.Many2one('res.partner', string='Contact',domain="[('is_company','!=','True')]",readonly=False,store=True)
    # address = fields.Char(string='Address', compute='_compute_address', store=True)
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id: CountryState = fields.Many2one(
        "res.country.state",
        string='State',
        ondelete='restrict',
        domain="[('country_id', '=?', country_id)]"
    )
    country_id: Country = fields.Many2one(
        'res.country',
        string='Country',
        ondelete='restrict'
    )
    country_code = fields.Char(
        related='country_id.code',
        string="Country Code"
    )

    helpdesk_ticket_ids = fields.Many2many('helpdesk.ticket', string='Help Desk Ticket',compute="_compute_helpdesk_tickets",store=True,readonly=False)
    fsm_task_ids = fields.Many2many('project.task', string='FSM Task',compute="_compute_fsm_tasks",store=True,readonly=False)
    subscription_id = fields.Many2one('sale.order', string='Subscription',domain="[('is_subscription','=',True)]")
    sale_order_id = fields.Many2one('sale.order', string='Sale Order',domain="[('is_subscription','=',False)]")
    stock_picking_id = fields.Many2one('stock.picking', string='Delivery Order')
    move_line_id = fields.Many2one('stock.move.line', string='Move Line')
    delivery_address_id = fields.Many2one(
        'res.partner',
        string='Service Address',
        compute='_compute_delivery_address',
        store=True,
        readonly=False
    )
    same_as_main_address= fields.Boolean(string="Same as main address?")

    delivery_street = fields.Char()
    delivery_street2 = fields.Char()
    delivery_zip = fields.Char(change_default=True)
    delivery_city = fields.Char()
    delivery_state_id: CountryState = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                                             domain="[('country_id', '=?', delivery_country_id)]")
    delivery_country_id: Country = fields.Many2one('res.country', string='Country', ondelete='restrict')
    delivery_country_code = fields.Char(related='delivery_country_id.code', string="Country Code")

    @api.depends('fsm_task_ids')
    def _compute_fsm_tasks(self):
        for asset in self:
            for task in asset.fsm_task_ids:
                if asset.id not in task.customer_assets_ids.ids:
                    task.customer_assets_ids = [(4, asset.id)]
    @api.depends('helpdesk_ticket_ids')
    def _compute_helpdesk_tickets(self):
        for asset in self:
            for ticket in asset.helpdesk_ticket_ids:
                if asset.id not in ticket.customer_assets_ids.ids:
                    ticket.customer_assets_ids = [(4, asset.id)]

    @api.depends('product_lot_id')
    def _compute_name_from_lot(self):
        for rec in self:
            rec.name = rec.product_lot_id.name if rec.product_lot_id else "New"

    @api.depends('contact_id')
    def _compute_address_company(self):
        for rec in self:
            rec.company_id = rec.contact_id.parent_id if rec.contact_id else ''
        self._compute_main_address()
        self._compute_delivery_address()

    @api.depends('contact_id','company_id')
    def _compute_delivery_address(self):
        for record in self:
            delivery = self.env['res.partner'].search([
                ('parent_id', '=', record.company_id.id),
                ('type', '=', 'delivery')
            ], limit=1)
            record.delivery_address_id = delivery or False
            # Populate address fields from the delivery address
            record.delivery_street = delivery.street or ''
            record.delivery_street2 = delivery.street2 or ''
            record.delivery_zip = delivery.zip or ''
            record.delivery_city = delivery.city or ''
            record.delivery_state_id = delivery.state_id.id if delivery.state_id else False
            record.delivery_country_id = delivery.country_id.id if delivery.country_id else False

    @api.depends('contact_id','company_id')
    def _compute_main_address(self):
        for rec in self:
            company = rec.company_id
            if company:
                rec.street = company.street
                rec.street2 = company.street2
                rec.zip = company.zip
                rec.city = company.city
                rec.state_id = company.state_id.id
                rec.country_id = company.country_id.id
            else:
                rec.street = ''
                rec.street2 = ''
                rec.zip = ''
                rec.city = ''
                rec.state_id = False
                rec.country_id = False

    @api.onchange('same_as_main_address')
    def _onchange_same_as_main_address(self):
        if self.same_as_main_address:
            # Copy main address to delivery
            self.delivery_street = self.street
            self.delivery_street2 = self.street2
            self.delivery_zip = self.zip
            self.delivery_city = self.city
            self.delivery_state_id = self.state_id
            self.delivery_country_id = self.country_id
        else:
           self._compute_delivery_address()

    @api.depends('product_lot_id')
    def _compute_serial_no(self):
        for rec in self:
            if rec.product_lot_id:
                rec.product_serial_No = rec.product_lot_id.name

    @api.depends('contact_id')
    def _compute_company(self):
        for rec in self:
            rec.company_id = rec.contact_id.parent_id if rec.contact_id else ''

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
    def action_view_ticket(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Helpdesk Tickets',
            'res_model': 'helpdesk.ticket',  # replace with actual model
            'view_mode': 'list,form',
            'domain': [('customer_assets_id', '=', self.id)],  # or use correct relation field
            'target': 'current',
        }
    def action_view_fsm(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'FSM Task',
            'res_model': 'project.task',
            'view_mode': 'list,form',
            'domain': [('customer_assets_ids', 'in', self.id)],  # or use correct relation field
            'target': 'current',
        }

    def action_view_sale_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
            'target': 'current',
        }
    def action_view_delivery_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Delivery Order',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.stock_picking_id.id,  # or use another field if needed
            'target': 'current',
        }


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    parent_company = fields.Many2one(string='Parent Company', related='partner_id.parent_id')
    customer_assets_ids = fields.Many2many(
        comodel_name="customer.asset",
        string="Customer Assets",
        compute="_compute_customer_assets_id",
        store=True,
        readonly=False,
        domain="['|', ('contact_id', '=', partner_id), '|', ('company_id', '=', partner_id), ('company_id', '=', parent_company)]"
    )

    customer_assets_count = fields.Integer(string="Customer Assets", compute="_compute_customer_assets_count")

    @api.depends('customer_assets_ids')
    def _compute_customer_assets_count(self):
        for record in self:
            record.customer_assets_count = len(record.customer_assets_ids)

    def action_view_customer_assets(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Related Customer Assets',
            'res_model': 'customer.asset',
            'view_mode': 'list,form',
            'domain': [('helpdesk_ticket_ids', 'in', self.id)],  # or use correct relation field
            'target': 'current',
        }
    @api.depends('customer_assets_ids')
    def _compute_customer_assets_id(self):
        for ticket in self:
            for asset in ticket.customer_assets_ids:
                if asset and ticket.id not in asset.helpdesk_ticket_ids.ids:
                    asset.helpdesk_ticket_ids = [(4, ticket.id)]

class FSM(models.Model):
    _inherit = "project.task"

    parent_company = fields.Many2one(string='Parent Company',related='partner_id.parent_id')
    customer_assets_ids = fields.Many2many(
        comodel_name="customer.asset",
        string="Customer Assets",
        compute="_compute_customer_assets_id",
        store=True,
        readonly=False,
        domain="['|', ('contact_id', '=', partner_id), '|', ('company_id', '=', partner_id), ('company_id', '=', parent_company)]"

    )

    customer_assets_count = fields.Integer(string="Customer Assets", compute="_compute_customer_assets_count")

    @api.depends('customer_assets_ids')
    def _compute_customer_assets_count(self):
        for record in self:
            record.customer_assets_count = len(record.customer_assets_ids)
    def action_view_customer_assets(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Related Customer Assets',
            'res_model': 'customer.asset',
            'view_mode': 'list,form',
            'domain': [('fsm_task_ids', 'in', self.id)],  # or use correct relation field
            'target': 'current',
        }

    @api.depends('helpdesk_ticket_id','customer_assets_ids')
    def _compute_customer_assets_id(self):
        for task in self:
            if task.helpdesk_ticket_id and task.helpdesk_ticket_id.customer_assets_id:
                asset_id = task.helpdesk_ticket_id.customer_assets_id.id
                if asset_id and asset_id not in task.customer_assets_ids.ids:
                    task.customer_assets_ids = [(4, asset_id)]
            for asset in task.customer_assets_ids:
                if asset and task.id not in asset.fsm_task_ids.ids:
                    asset.fsm_task_ids = [(4, task.id)]
