from odoo import models, fields, api

class StockMove(models.Model):
    _inherit = 'stock.move'

    track_cpe = fields.Boolean(string='Track CPE')

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

                if move.track_cpe:
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

    # @api.model
    # def create(self, vals):
    #     picking = super().create(vals)
    #     picking._create_customer_assets()
    #     return picking
    #
    # def write(self, vals):
    #     res = super().write(vals)
    #     self._create_customer_assets()
    #     return res

    # def _create_customer_assets(self):
    #     customer_asset = self.env['customer.asset']
    #     for picking in self:
    #         for move in picking.move_ids_without_package:
    #             existing_asset = customer_asset.search([
    #                 ('product_id', '=', move.product_id.id),
    #                 ('stock_picking_id', '=', picking.id),
    #                 ('sale_order_id', '=', picking.sale_id.id),
    #                 ('product_serial_No','=',move.lot_ids.name),
    #             ], limit=1)
    #
    #             if not existing_asset and move.track_cpe:
    #                 customer_asset.create({
    #                     'product_id': move.product_id.id,
    #                     'product_serial_No':move.lot_ids.name,
    #                     'sale_date': picking.sale_id.date_order,
    #                     'company_id': picking.partner_id.parent_id.id,
    #                     'contact_id': picking.sale_id.partner_id.id,
    #                     'sale_order_id': picking.sale_id.id,
    #                     'stock_picking_id': picking.id,
    #                 })
    #
    #             elif existing_asset and not move.track_cpe:
    #                 existing_asset.unlink()

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