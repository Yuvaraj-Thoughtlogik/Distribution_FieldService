from odoo import models, fields, api

class CustomerAsset(models.Model):
    _name = 'customer.asset'
    _description = 'Customer Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'


    name = fields.Char(string="Customer Asset No", required=True,default="New")
    product_serial_No = fields.Char(string="Equipment Serial No",compute="_compute_serial_no", store=True)
    product_lot_id = fields.Many2one('stock.lot',string="Lot ID")
    display_name = fields.Char(compute="_compute_display_name", store=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    sale_date = fields.Date(string='Sale Date')
    install_date = fields.Date(string='Install Date')
    under_warranty = fields.Boolean(string='Under Warranty?')
    warranty_expiry = fields.Date(string='Warranty Expiry Date')
    active_contract = fields.Boolean(string='Active?')
    contract_start_date = fields.Date(string='Start Date')
    contract_end_date = fields.Date(string='End Date')
    contract_renewal_date = fields.Date(string='Renewal Date')
    company_id = fields.Many2one('res.partner',compute="_compute_company", string='Company',domain="[('is_company','=',True)]",store=True)
    contact_id = fields.Many2one('res.partner', string='Contact',domain="[('is_company','!=','True')]")
    address = fields.Char(string='Address', compute='_compute_address', store=True)
    helpdesk_ticket_id = fields.Many2one('helpdesk.ticket', string='Help Desk Ticket')
    subscription_id = fields.Many2one('sale.order', string='Subscription',domain="[('is_subscription','=',True)]")
    fsm_task_id = fields.Many2one('project.task', string='FSM Task')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order',domain="[('is_subscription','=',False)]")
    stock_picking_id = fields.Many2one('stock.picking', string='Stock Picking')
    move_line_id = fields.Many2one('stock.move.line', string='Move Line')

    @api.depends('product_lot_id')
    def _compute_serial_no(self):
        for rec in self:
            if rec.product_lot_id:
                rec.product_serial_No = rec.product_lot_id.name

    @api.depends('name', 'product_serial_No')
    def _compute_display_name(self):
        for rec in self:
            if rec.product_lot_id:
                rec.display_name = f"{rec.name} - {rec.product_serial_No}"
            else:
                rec.display_name = rec.name

    @api.depends('company_id')
    def _compute_address(self):
        for rec in self:
            rec.address = rec.company_id.contact_address if rec.company_id else ''

    @api.depends('contact_id')
    def _compute_company(self):
        for rec in self:
            rec.company_id = rec.contact_id.parent_id if rec.contact_id else ''

    @api.model_create_multi
    def create(self, vals):
        for val in vals:
            if not val.get("name") or val['name'] == "New":
                val['name'] = self.env['ir.sequence'].next_by_code("customer.asset")
        return super().create(vals)

    def _compute_serial_number(self):
        pass

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
