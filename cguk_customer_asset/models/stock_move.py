from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    track_cpe = fields.Boolean(string='Track CPE', compute='_compute_track_cpe', store=True, readonly=False)

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        moves._create_customer_assets()
        return moves

    def write(self, vals):
        res = super().write(vals)
        self._create_customer_assets()
        return res

    def _prepare_customer_asset_values(self, move_line):
        self.ensure_one()
        sale_order = self.picking_id.sale_id
        partner = sale_order.partner_id or self.picking_id.partner_id
        delivery_address = sale_order.partner_shipping_id or self.picking_id.partner_id
        return {
            'product_id': self.product_id.id,
            'delivery_address_id': delivery_address.id,
            'cache_delivery_address_id': delivery_address.id,
            'product_lot_id': move_line.lot_id.id,
            'sale_date': sale_order.date_order and sale_order.date_order.date(),
            'customer_company_id': partner.id if partner.is_company else partner.parent_id.id,
            'contact_id': partner.id if not partner.is_company else False,
            'partner_id': partner.id,
            'sale_order_id': sale_order.id,
            'stock_picking_id': self.picking_id.id,
            'move_line_id': move_line.id,
            'company_id': self.company_id.id,
        }

    def _create_customer_assets(self):
        """Create / update one customer asset per move line of an outgoing move of a
        'Track CPE' product (one per serial number for serial tracked products).
        Assets are removed when the product is not tracked anymore."""
        CustomerAsset = self.env['customer.asset'].sudo()
        moves = self.filtered(lambda m: m.picking_id and m.picking_type_id.code == 'outgoing')
        for move in moves:
            tracked = move.track_cpe or move.product_id.product_tmpl_id.track_cpe
            for move_line in move.move_line_ids:
                existing_asset = CustomerAsset.search([('move_line_id', '=', move_line.id)], limit=1)
                if tracked:
                    values = move._prepare_customer_asset_values(move_line)
                    if not existing_asset:
                        CustomerAsset.create(values)
                    else:
                        changed = {}
                        for key, value in values.items():
                            current = existing_asset[key]
                            if existing_asset._fields[key].type == 'many2one':
                                current = current.id
                            if (current or False) != (value or False):
                                changed[key] = value
                        if changed:
                            existing_asset.write(changed)
                elif existing_asset:
                    existing_asset.unlink()

    @api.depends('product_id', 'picking_type_id')
    def _compute_track_cpe(self):
        for move in self:
            move.track_cpe = bool(move.product_id.product_tmpl_id.track_cpe and move.picking_type_id.code == 'outgoing')


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines.move_id._create_customer_assets()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if 'lot_id' in vals or 'lot_name' in vals:
            self.move_id._create_customer_assets()
        return res

    def unlink(self):
        self.env['customer.asset'].sudo().search([('move_line_id', 'in', self.ids)]).unlink()
        return super().unlink()


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    customer_assets_ids = fields.One2many(
        comodel_name="customer.asset",
        string="Customer Assets",
        inverse_name="stock_picking_id",
    )
    customer_assets_count = fields.Integer(string="Customer Assets Count", compute="_compute_customer_assets_count")

    hide_track_cpe = fields.Boolean(compute='_compute_hide_track_cpe')

    @api.depends('picking_type_id')
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
            'name': self.env._('Related Customer Assets'),
            'res_model': 'customer.asset',
            'view_mode': 'list,form',
            'domain': [('stock_picking_id', '=', self.id)],
            'target': 'current',
        }
