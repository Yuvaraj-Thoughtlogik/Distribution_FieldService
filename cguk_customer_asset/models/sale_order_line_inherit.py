from odoo import models, fields, api

class StockMove(models.Model):
    _inherit = 'stock.move'

    track_cpe = fields.Boolean(string='Track CPE',compute='_compute_track_cpe',store=True,readonly=False)

    @api.model
    def create(self, vals):
        move = super().create(vals)
        move._create_customer_assets()
        return move

    def write(self, vals):
        res = super().write(vals)
        self._create_customer_assets()
        return res

    def _create_customer_assets(self):
        customer_asset = self.env['customer.asset']
        for move in self:
            for move_line in move.move_line_ids:
                lot_id = move_line.lot_id.id if move_line.lot_id else False
                print("lot_id-->",move_line.lot_id)
                existing_asset = customer_asset.search([
                    ('product_id', '=', move.product_id.id),
                    ('stock_picking_id', '=', move.picking_id.id),
                    ('sale_order_id', '=', move.picking_id.sale_id.id),
                    ('move_line_id', '=', move_line.id),
                ], limit=1)

                if move.track_cpe or  move.product_id.product_tmpl_id.track_cpe:
                    values = {
                        'product_id': move.product_id.id,
                        'product_lot_id': lot_id,
                        'sale_date': move.picking_id.sale_id.date_order,
                        'company_id': move.picking_id.partner_id.parent_id.id,
                        'contact_id': move.picking_id.sale_id.partner_id.id,
                        'sale_order_id': move.picking_id.sale_id.id,
                        'stock_picking_id': move.picking_id.id,
                        'move_line_id': move_line.id,
                    }

                    if not existing_asset:
                        customer_asset.create(values)
                    else:
                        existing_asset.write(values)
                else:
                    if existing_asset:
                        existing_asset.unlink()

    @api.depends('product_id')
    def _compute_track_cpe(self):
        for move in self:
            if move.product_id.product_tmpl_id.track_cpe:
                move.track_cpe = True

class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def unlink(self):
        customer_asset = self.env['customer.asset']
        for line in self:
            # Find and unlink related customer asset
            related_asset = customer_asset.search([
                ('move_line_id', '=', line.id)
            ])
            if related_asset:
                related_asset.unlink()
        return super().unlink()

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_customer_assets_ids = fields.One2many(
        comodel_name="customer.asset",
        string="Customer Assets",
        inverse_name="sale_order_id",
        domain="[('contact_id', '=', partner_id)]"
    )
    subscription_customer_assets_ids = fields.One2many(
        comodel_name="customer.asset",
        string="Customer Assets",
        inverse_name="subscription_id",
        domain="[('contact_id', '=', partner_id)]"
    )

    renewal_date = fields.Date(string="Renewal Date")

    sale_customer_assets_count = fields.Integer(string="Customer Assets", compute="_compute_sale_customer_assets_count")
    subscription_customer_assets_count = fields.Integer(string="Customer Assets", compute="_compute_subscription_customer_assets_count")

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

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    customer_assets_ids = fields.One2many(
        comodel_name="customer.asset",
        string="Customer Assets",
        inverse_name="stock_picking_id",
        domain="[('contact_id', '=', partner_id)]"
    )
    customer_assets_count = fields.Integer(string="Customer Assets",compute="_compute_customer_assets_count")

    @api.depends('customer_assets_ids')
    def _compute_customer_assets_count(self):
        for pick in self:
                pick.customer_assets_count = len(pick.customer_assets_ids)
    
    def action_view_customer_assets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Related Customer Assets',
            'res_model': 'customer.asset',  # replace with actual model
            'view_mode': 'list,form',
            'domain': [('stock_picking_id', '=', self.id)],  # or use correct relation field
            'target': 'current',
        }

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    track_cpe = fields.Boolean(string='Track CPE')