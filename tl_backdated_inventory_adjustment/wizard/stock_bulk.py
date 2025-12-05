from odoo import models, fields, api,_
from datetime import datetime
import pytz

#from odoo import fields, models, _

from odoo.osv import expression

from odoo.tools.misc import format_date, format_datetime

from datetime import timedelta,time
 

class Stock_Move(models.Model):
    _inherit = 'stock.move'

    inv_backdated = fields.Date(string="Inventory Backdate", copy=False)

    def _action_done(self, cancel_backorder=False):
        res = super(Stock_Move, self)._action_done(cancel_backorder=cancel_backorder)
        for move in self:
            if move.inv_backdated:
                move.write({'date': move.inv_backdated})
                move.move_line_ids.write({'date': move.inv_backdated,
                                          'origin': move.origin})
        return res


class stock_quant(models.Model):
    _inherit = 'stock.quant'

    inv_backdated = fields.Date(string="Inventory Backdate", copy=True)
    backdated_remark = fields.Char(string="Notes", copy=False)

    def _get_inventory_move_values(
        self, qty, location_id, location_dest_id,
        package_id=False, package_dest_id=False
        
    ):
        res = super(stock_quant, self)._get_inventory_move_values(
            qty=qty,
            location_id=location_id,
            location_dest_id=location_dest_id,
            #owner_id=owner_id,
            package_id=package_id,
            package_dest_id=package_dest_id,
            #lot_id=lot_id,
            #product_uom_id=product_uom_id,
            #out=out
        )
        if self.inv_backdated:
            res.update({
                'inv_backdated': self.inv_backdated,
                'date_deadline': self.inv_backdated,
                'origin': self.backdated_remark
            })
        return res


    def _apply_inventory(self):
        for inventory in self.filtered(lambda l: l.inv_backdated):
            inventory.accounting_date = inventory.inv_backdated

        res = super(stock_quant, self)._apply_inventory()

        #  Remove this if you want to retain backdated values
        # for inventory in self.filtered(lambda l: l.inv_backdated):
        #     inventory.write({'inv_backdated': False, 'backdated_remark': False})

        return res

    @api.model
    def _get_inventory_fields_create(self):
        res = super(stock_quant,self)._get_inventory_fields_create()
        res += ['inv_backdated','backdated_remark']
        return res

    @api.model
    def _get_inventory_fields_write(self):
        res = super(stock_quant,self)._get_inventory_fields_write()
        res += ['inv_backdated','backdated_remark']
        return res


class stock_valuation_layer(models.Model):
    _inherit = 'stock.valuation.layer'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(stock_valuation_layer, self).create(vals_list)
        if self._context.get('force_period_date'):
            for each_rec in res:
                self.env.cr.execute("update stock_valuation_layer set create_date = %s where id = %s", (self._context.get('force_period_date'), each_rec.id))
        return res

#class BulkInventoryBackdateWizard(models.TransientModel):
    #_name = 'bulk.inventory.backdate.wizard'
    #_description = 'Bulk Inventory Backdate Wizard'

    #inv_backdated = fields.Date(string="Inventory Backdate", required=True)
    #backdated_remark = fields.Char(string="Remark")
    #quant_ids = fields.Many2many('stock.quant', string="Quants to Update")

    #def action_apply_backdate(self):
        #self.ensure_one()
        #self.quant_ids.write({
            #'inv_backdated': self.inv_backdated,
            #'backdated_remark': self.backdated_remark,
        #})

 
class StockQuantityHistory(models.TransientModel):

    _inherit = 'stock.quantity.history'

    inventory_datetime = fields.Date(

        string='Inventory at Date',

        help="Choose a date to get the inventory at that date",

        default=fields.Date.context_today

    )
 
    def open_at_date(self):
 
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')
 
        active_model = self.env.context.get('active_model')
 
        # Convert DATE → UTC end-of-day

        def get_utc_end(date):

            end_user = user_tz.localize(datetime.combine(date, time.max))

            return end_user.astimezone(pytz.utc), end_user
 
        dt_end_utc, dt_end_user = get_utc_end(self.inventory_datetime)
 
        # ----------------------------------------------------------------------

        # 1) Stock Valuation Layer

        # ----------------------------------------------------------------------

        if active_model == 'stock.valuation.layer':

            action = self.env["ir.actions.actions"]._for_xml_id(

                "stock_account.stock_valuation_layer_action"

            )
 
            action['views'] = [

                (self.env.ref('stock_account.stock_valuation_layer_valuation_at_date_tree_inherited').id, 'list'),

                (self.env.ref('stock_account.stock_valuation_layer_form').id, 'form'),

                (self.env.ref('stock_account.stock_valuation_layer_pivot').id, 'pivot'),

                (self.env.ref('stock_account.stock_valuation_layer_graph').id, 'graph'),

            ]
 
            # *** NEW: all records created BEFORE or ON entered date ***

            action['domain'] = [

                ('create_date', '<=', dt_end_utc),

                ('product_id.is_storable', '=', True),

            ]
 
            # For label

            action['display_name'] = format_datetime(self.env, dt_end_user.replace(tzinfo=None))

            action['context'] = "{}"
 
            return action
 
        # ----------------------------------------------------------------------

        # 2) Product.product

        # ----------------------------------------------------------------------

        tree_view_id = self.env.ref('stock.view_stock_product_tree').id

        form_view_id = self.env.ref('stock.product_form_view_procurement_button').id
 
        domain = [('is_storable', '=', True)]
 
        product_id = self.env.context.get('product_id')

        product_tmpl_id = self.env.context.get('product_tmpl_id')
 
        if product_id:

            domain = expression.AND([domain, [('id', '=', product_id)]])

        elif product_tmpl_id:

            domain = expression.AND([domain, [('product_tmpl_id', '=', product_tmpl_id)]])
 
        action = {

            'type': 'ir.actions.act_window',

            'views': [(tree_view_id, 'list'), (form_view_id, 'form')],

            'view_mode': 'list,form',

            'name': _('Products'),

            'res_model': 'product.product',

            'domain': domain,

            'context': dict(self.env.context, to_date=dt_end_utc),

            'display_name': format_datetime(self.env, dt_end_user.replace(tzinfo=None)),

        }
 
        return action
 
