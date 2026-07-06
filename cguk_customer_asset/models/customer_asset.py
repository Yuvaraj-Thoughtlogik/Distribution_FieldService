from email.policy import default

from odoo import models, fields, api
import typing
from odoo.addons.base.models.res_country import Country, CountryState
from odoo.api import readonly

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

    product_lot_id = fields.Many2one('stock.lot',string="Lot ID")
    product_id = fields.Many2one('product.product', string='Product', required=True)
    sale_date = fields.Date(string='Sale Date')
    install_date = fields.Date(string='Install Date')
    under_warranty = fields.Boolean(string='Under Warranty?')
    warranty_expiry = fields.Date(string='Warranty Expiry Date')
    active_contract = fields.Boolean(string='Active?',compute='_compute_active_contract')
    contract_start_date = fields.Date(string='Start Date',related="subscription_id.start_date")
    contract_end_date = fields.Date(string='End Date',related="subscription_id.end_date")
    contract_renewal_date = fields.Date(string='Renewal Date',related="subscription_id.next_invoice_date")
    # company_id = fields.Many2one('res.partner', string='Company',domain="[('is_company','=',True)]",store=True)
    customer_company_id = fields.Many2one('res.partner', string='Company',domain="[('is_company','=',True)]",store=True)
    company_id = fields.Many2one(
        'res.company',
        string='Internal Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    contact_id = fields.Many2one('res.partner', string='Contact')
    partner_id = fields.Many2one('res.partner', string='Partner')
    # address = fields.Char(string='Address', compute='_compute_address', store=True)
    # compute_address = fields.Boolean("Compute Address",default=True,compute='_compute_address')
    street = fields.Char(compute='_compute_address',store=True,readonly=False)
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
    stock_picking_id = fields.Many2one('stock.picking', string='Delivery Order',domain="[('picking_type_code', '=', 'outgoing')]")
    move_line_id = fields.Many2one('stock.move.line', string='Move Line')
    repair_order_ids = fields.One2many(
        comodel_name='repair.order',
        inverse_name='customer_asset_id',
        string='Repair Order')

    delivery_address_id = fields.Many2one(
        'res.partner',
        string='Service Address',
        domain="[('id','in',delivery_ids)]",
    )
    cache_delivery_address_id = fields.Many2one(
        'res.partner',
        string='Service Address',)
    delivery_ids = fields.Many2many(comodel_name='res.partner',compute='_compute_address_ids')
    same_as_main_address= fields.Boolean(string="Same as main address?")

    delivery_street = fields.Char(compute='_compute_delivery_address',store=True,readonly=False)
    delivery_street2 = fields.Char()
    delivery_zip = fields.Char(change_default=True)
    delivery_city = fields.Char()
    delivery_state_id: CountryState = fields.Many2one("res.country.state", string='State', ondelete='restrict',
                                             domain="[('country_id', '=?', delivery_country_id)]")
    delivery_country_id: Country = fields.Many2one('res.country', string='Country', ondelete='restrict')
    delivery_country_code = fields.Char(related='delivery_country_id.code', string="Country Code")

    @api.depends('name', 'product_id.display_name')
    def _compute_display_name(self):
        """
        Customizes the display name to be 'Customer Asset No. [Product Display Name]'
        e.g., '5300 22 0029 [12-0530] VAPODEST 300, 230VAC 50-60Hz'
        """
        for record in self:
            display_parts = []

            # Use the computed 'name' (Customer Asset No.)
            if record.name and record.name != "New":
                display_parts.append(record.name)

            # Append the product's display name
            if record.product_id and record.product_id.display_name:
                display_parts.append(record.product_id.display_name)

            # If both are missing, use the default name_get fallback (ID) or just 'New Asset'
            if not display_parts:
                record.display_name = "New Asset"
            else:
                record.display_name = ' - '.join(filter(None, display_parts))

    @api.depends('subscription_id')
    def _compute_active_contract(self):
        for record in self:
            record.active_contract = bool(record.subscription_id)

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


    @api.depends('product_serial_No')
    def _compute_name_from_lot(self):
        for rec in self:
            rec.name = rec.product_serial_No if rec.product_serial_No else "New"


    @api.depends('contact_id', 'customer_company_id')
    def _compute_address(self):
        for rec in self:
            self._compute_main_address()
            # self._compute_delivery_address()

    @api.depends('delivery_address_id')
    def _compute_delivery_address(self):
        for record in self:

            delivery = record.delivery_address_id
            # Populate address fields from the delivery address
            record.delivery_street = delivery.street or ''
            record.delivery_street2 = delivery.street2 or ''
            record.delivery_zip = delivery.zip or ''
            record.delivery_city = delivery.city or ''
            record.delivery_state_id = delivery.state_id.id if delivery.state_id else False
            record.delivery_country_id = delivery.country_id.id if delivery.country_id else False

    @api.depends('contact_id', 'customer_company_id')
    def _compute_address_ids(self):
        for rec in self:
            partners = self.env['res.partner']

            if rec.contact_id:
                partners |= rec.contact_id

                partners |= rec.contact_id.child_ids.filtered(
                    lambda p: p.type in ('delivery', 'other')
                )

            if rec.customer_company_id:
                partners |= rec.customer_company_id
            # print([partner.name for partner in partners])
            rec.delivery_ids = partners

    @api.depends('contact_id','customer_company_id')
    def _compute_main_address(self):
        for rec in self:
            company = rec.customer_company_id
            contact = rec.contact_id
            if company:
                rec.street = company.street
                rec.street2 = company.street2
                rec.zip = company.zip
                rec.city = company.city
                rec.state_id = company.state_id.id
                rec.country_id = company.country_id.id

            elif contact:
                rec.street = contact.street
                rec.street2 = contact.street2
                rec.zip = contact.zip
                rec.city = contact.city
                rec.state_id = contact.state_id.id
                rec.country_id = contact.country_id.id
            else:
                rec.street = ''
                rec.street2 = ''
                rec.zip = ''
                rec.city = ''
                rec.state_id = False
                rec.country_id = False

    @api.onchange('same_as_main_address')
    def _onchange_same_as_main_address(self):
        for rec in self:
            if rec.same_as_main_address:
                rec.delivery_address_id = rec.contact_id.id if rec.contact_id else rec.customer_company_id if rec.customer_company_id else False
            else:
               rec.delivery_address_id = rec.cache_delivery_address_id.id

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
            'domain': [('customer_assets_ids', 'in', self.id)],  # or use correct relation field
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

    def action_view_repair_order(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Repairs',
            'res_model': 'repair.order',
            'view_mode': 'list,form',
            'domain': [('customer_asset_id', '=', self.id)],  # or use correct relation field
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
        domain="['|', ('contact_id', '=', partner_id), '|', ('customer_company_id', '=', partner_id), ('customer_company_id', '=', parent_company)]"
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
        domain="['|', ('contact_id', '=', partner_id), '|', ('customer_company_id', '=', partner_id), ('customer_company_id', '=', parent_company)]"

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
            if task.helpdesk_ticket_id and task.helpdesk_ticket_id.customer_assets_ids:
                # asset_id = task.helpdesk_ticket_id.customer_assets_ids.ids
                # if asset_id and asset_id not in task.customer_assets_ids.ids:
                #     task.customer_assets_ids = [(4, asset_id)]
                task.customer_assets_ids = task.helpdesk_ticket_id.customer_assets_ids
            for asset in task.customer_assets_ids:
                if asset and task.id not in asset.fsm_task_ids.ids:
                    asset.fsm_task_ids = [(4, task.id)]


