from odoo import models, fields, api

class SelectLotWizard(models.TransientModel):
    _name = 'select.lot.wizard'
    _description = 'Select Lot for Product'

    product_id = fields.Many2one('product.product', string="Product", required=True)
    asset_id = fields.Many2one('customer.asset', string="Asset")
    lot_id = fields.Many2one('stock.lot', string="Select Lot", required=True, domain="[('product_id', '=', product_id),('product_qty', '>', 0)]")

    def confirm(self):
        self.asset_id.write({
            'product_lot_id': self.lot_id.id
        })
        return {'type': 'ir.actions.act_window_close'}