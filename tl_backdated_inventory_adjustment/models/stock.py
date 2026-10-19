from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    inv_backdated = fields.Date(string="Inventory Backdate", copy=False)

    def _action_done(self, cancel_backorder=False):
        res = super()._action_done(cancel_backorder=cancel_backorder)
        for move in self.filtered('inv_backdated'):
            # Odoo 20: writing the date of a valued move replays its valuation;
            # move lines `date` is related to the move date. The journal entry is
            # already dated through stock.quant.accounting_date (force_period_date).
            move.with_context(skip_backdate_validation=True).write({'date': move.inv_backdated})
        return res

    def _tl_backdate_account_moves(self, new_date):
        """Re-date the stock journal entries (stock.move.account_move_id)."""
        accounting_date = fields.Date.context_today(self, fields.Datetime.to_datetime(new_date))
        for account_move in self.sudo().account_move_id.filtered(
                lambda m: m.state != 'cancel' and m.date != accounting_date):
            was_posted = account_move.state == 'posted'
            if was_posted:
                account_move.button_draft()
            if account_move.name and account_move.name != '/':
                account_move.name = False  # new number matching the new period
            account_move.date = accounting_date
            if was_posted:
                account_move.action_post()


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    inv_backdated = fields.Date(string="Inventory Backdate", copy=True)
    backdated_remark = fields.Char(string="Notes", copy=False)

    def _get_inventory_move_values(self, qty, location_id, location_dest_id, package_id=False, package_dest_id=False):
        res = super()._get_inventory_move_values(
            qty, location_id, location_dest_id, package_id=package_id, package_dest_id=package_dest_id)
        if self.inv_backdated:
            res.update({
                'inv_backdated': self.inv_backdated,
                'date_deadline': self.inv_backdated,
                'origin': self.backdated_remark,
            })
        return res

    def _apply_inventory(self, date=None):
        # stock_account dates the valuation journal entries with `accounting_date`
        for inventory in self.filtered('inv_backdated'):
            inventory.accounting_date = inventory.inv_backdated
        return super()._apply_inventory(date=date)

    @api.model
    def _get_inventory_fields_create(self):
        return super()._get_inventory_fields_create() + ['inv_backdated', 'backdated_remark']

    @api.model
    def _get_inventory_fields_write(self):
        return super()._get_inventory_fields_write() + ['inv_backdated', 'backdated_remark']


class BulkInventoryBackdateWizard(models.TransientModel):
    _name = 'bulk.inventory.backdate.wizard'
    _description = 'Bulk Inventory Backdate Wizard'

    inv_backdated = fields.Date(string="Inventory Backdate", required=True)
    backdated_remark = fields.Char(string="Remark")
    quant_ids = fields.Many2many('stock.quant', string="Quants to Update")

    def action_apply_backdate(self):
        self.ensure_one()
        self.quant_ids.write({
            'inv_backdated': self.inv_backdated,
            'backdated_remark': self.backdated_remark,
        })


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super().button_validate()
        if 'sale.order' not in self.env:
            return res
        for picking in self:
            if picking.picking_type_code != 'outgoing' or picking.state != 'done':
                continue
            sale_order = self.env['sale.order'].search([('name', '=', picking.origin)], limit=1)
            if not sale_order or not sale_order.commitment_date:
                continue
            commitment_date = sale_order.commitment_date
            picking = picking.with_context(skip_backdate_validation=True)
            # Odoo 20: on a done picking, writing date_done also sets the moves date
            # (which replays the valuation); move lines date is related to the move.
            picking.write({'date_done': commitment_date})
            picking.move_ids.write({'date': commitment_date})
            # replaces the former stock.valuation.layer create_date SQL update
            picking.move_ids._tl_backdate_account_moves(commitment_date)
        return res
