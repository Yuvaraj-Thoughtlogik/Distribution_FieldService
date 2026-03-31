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
                existing_asset = customer_asset.search([
                    ('product_id', '=', move.product_id.id),
                    ('stock_picking_id', '=', move.picking_id.id),
                    ('sale_order_id', '=', move.picking_id.sale_id.id),
                    ('move_line_id', '=', move_line.id),
                ], limit=1)

                if (move.track_cpe or move.product_id.product_tmpl_id.track_cpe) and move.picking_type_id.code == 'outgoing':
                    partner = move.picking_id.sale_id.partner_id
                    delivery_address = move.picking_id.sale_id.partner_shipping_id
                    values = {
                        'product_id': move.product_id.id,
                        'delivery_address_id':delivery_address.id if delivery_address else False,
                        'cache_delivery_address_id':delivery_address.id if delivery_address else False,
                        'product_lot_id': lot_id,
                        'sale_date': move.picking_id.sale_id.date_order,
                        'customer_company_id': partner.id if partner.is_company else partner.parent_id.id if partner.parent_id else False,
                        'contact_id': partner.id if not partner.is_company else False,
                        'partner_id': partner.id,
                        # 'compute_address':True,
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
            if move.product_id.product_tmpl_id.track_cpe and move.picking_type_id.code == 'outgoing':
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


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    customer_assets_ids = fields.One2many(
        comodel_name="customer.asset",
        string="Customer Assets",
        inverse_name="stock_picking_id",
        domain="[('contact_id', '=', partner_id)]"
    )
    customer_assets_count = fields.Integer(string="Customer Assets", compute="_compute_customer_assets_count")

    hide_track_cpe = fields.Boolean(
        compute='_compute_hide_track_cpe',
        store=False
    )

    def _compute_hide_track_cpe(self):
        for rec in self:
            rec.hide_track_cpe = rec.picking_type_id.code != 'outgoing'

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

