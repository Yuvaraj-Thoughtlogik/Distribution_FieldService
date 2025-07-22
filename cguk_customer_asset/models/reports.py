from odoo import models, fields, api
from odoo.tools.float_utils import float_round

class SaleOrderOption(models.Model):
    _inherit = 'sale.order.option'


    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='order_id.currency_id',
        store=True,
        readonly=True
    )

    total_price = fields.Monetary(
        string='Total Price',
        compute='_compute_total_price',
        store=True,
        currency_field='currency_id',
    )


    @api.depends('price_unit', 'quantity', 'discount')
    def _compute_total_price(self):
        for rec in self:
            discount_factor = (1 - (rec.discount or 0.0) / 100)
            total = rec.price_unit * rec.quantity * discount_factor
            rec.total_price = float_round(total, precision_rounding=rec.currency_id.rounding)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    order_line_total_price = fields.Monetary(
        string='Total Price',
        compute='_compute_order_line_total_price',
        store=True,
        currency_field='currency_id',
        readonly=True,
    )

    @api.depends('price_unit', 'product_uom_qty', 'discount')
    def _compute_order_line_total_price(self):
        for line in self:
            discount_factor = (1 - (line.discount or 0.0) / 100)
            total = line.price_unit * line.product_uom_qty * discount_factor
            line.order_line_total_price = float_round(total, precision_rounding=line.currency_id.rounding)
            
            
class SaleOrder(models.Model):
    _inherit = 'sale.order'
 
    individual_name = fields.Char(
        string='Individual Name',
        compute='_compute_partner_details',
        store=True
    )
 
    company_name = fields.Char(
        string='Company Name',
        compute='_compute_partner_details',
        store=True
    )
 
    contact_address = fields.Text(
        string='Contact Address',
        compute='_compute_partner_details',
        store=True
    )
    partner_street = fields.Char(related='partner_id.street', store=True)
    partner_street2 = fields.Char(related='partner_id.street2', store=True)
    partner_city = fields.Char(related='partner_id.city', store=True)
    partner_state_id = fields.Many2one(related='partner_id.state_id', store=True)
    partner_zip = fields.Char(related='partner_id.zip', store=True)
    partner_country_id = fields.Many2one(related='partner_id.country_id', store=True)
    related_address = fields.Char(string="Full Address", compute="_compute_related_address", store=True)    
 
 
 
    @api.depends('partner_id')
    def _compute_partner_details(self):
        for order in self:
            partner = order.partner_id
            order.individual_name = partner.name or ''
            order.company_name = partner.parent_id.name if partner.parent_id else ''
            # Get address without name
            address_fields = partner._display_address().split('\n')
            if len(address_fields) > 1:
                order.contact_address = '\n'.join(address_fields[1:])
            else:
                order.contact_address = ''
                
    @api.depends(
            'partner_street', 'partner_street2', 'partner_city',
            'partner_state_id', 'partner_zip', 'partner_country_id'
    )
    def _compute_related_address(self):
            for order in self:
                lines = [
                    order.partner_street or '',
                    order.partner_street2 or '',
                    order.partner_city or '',
                    order.partner_state_id.name if order.partner_state_id else '',
                    order.partner_zip or '',
                    order.partner_country_id.name if order.partner_country_id else ''
                ]
                # Filter out empty lines and join with newline
                order.related_address = '\n'.join(filter(None, lines))
                
class ResCompany(models.Model):
    _inherit = 'res.company'
 
    footer_logo = fields.Binary("Footer Logo")
