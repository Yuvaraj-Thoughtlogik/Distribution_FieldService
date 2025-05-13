from odoo import models, fields, api
import typing
from odoo.addons.base.models.res_country import Country, CountryState
if typing.TYPE_CHECKING:
    from odoo.addons.base.models.res_users import UsersView as ResUsers
    from odoo.addons.base.models.res_bank import ResPartnerBank
    from odoo.addons.base.models.res_country import Country, CountryState
    from odoo.addons.base.models.res_company import Company as ResCompany

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
        readonly=True
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

    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', string='Help Desk Ticket')
    subscription_id = fields.Many2one('sale.order', string='Subscription',domain="[('is_subscription','=',True)]")
    fsm_task_id = fields.Many2one('project.task', string='FSM Task')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order',domain="[('is_subscription','=',False)]")
    stock_picking_id = fields.Many2one('stock.picking', string='Stock Picking')
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
            'name': 'Helpdesk Ticket',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'form',
            'res_id': self.helpdesk_ticket_id.id,
            'target': 'current',
        }
    def action_view_fsm(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'FSM Task',
            'res_model': 'project.task',
            'view_mode': 'form',
            'res_id': self.fsm_task_id.id,
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

    customer_assets_id = fields.Many2one(
        comodel_name="customer.asset",
        string="Customer Assets",
        domain="[('contact_id', '=', partner_id)]"
    )

    @api.model
    def create(self, vals):
        ticket = super().create(vals)
        if vals.get('customer_assets_id'):
            asset = self.env['customer.asset'].browse(vals['customer_assets_id'])
            asset.helpdesk_ticket_id = ticket.id
        return ticket

    def write(self, vals):
        for rec in self:
            old_asset = rec.customer_assets_id
            res = super(HelpdeskTicket, rec).write(vals)

            if 'customer_assets_id' in vals:
                # Clear the old asset if it's different
                if old_asset and old_asset.id != vals['customer_assets_id']:
                    old_asset.helpdesk_ticket_id = False

                # Set the new asset
                new_asset = rec.customer_assets_id
                if new_asset:
                    new_asset.helpdesk_ticket_id = rec.id
        return True

    def action_view_customer_assets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Related Customer Assets',
            'res_model': 'customer.asset',  # replace with actual model
            'view_mode': 'form',
            'res_id': self.customer_assets_id.id,
            'target': 'current',
        }


class FSM(models.Model):
    _inherit = "project.task"

    customer_assets_id = fields.Many2one(
        comodel_name="customer.asset",
        string="Customer Assets",
        domain="[('contact_id', '=', partner_id)]"
    )

    @api.model
    def create(self, vals):
        task = super().create(vals)
        if vals.get('customer_assets_id'):
            asset = self.env['customer.asset'].browse(vals['customer_assets_id'])
            asset.fsm_task_id = task.id
        return task

    def write(self, vals):
        for rec in self:
            old_asset = rec.customer_assets_id
            res = super(FSM, rec).write(vals)

            if 'customer_assets_id' in vals:
                # Clear old asset link
                if old_asset and old_asset.id != vals['customer_assets_id']:
                    old_asset.fsm_task_id = False

                # Set new asset link
                new_asset = rec.customer_assets_id
                if new_asset:
                    new_asset.fsm_task_id = rec.id
        return True

    def action_view_customer_assets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Related Customer Assets',
            'res_model': 'customer.asset',  # replace with actual model
            'view_mode': 'form',
            'res_id': self.customer_assets_id.id,
            'target': 'current',
        }
