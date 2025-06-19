
from odoo import models, fields, api


class Manufacturer(models.Model):
    _name = 'crm.lead.manufacture'
    _description = 'Manufacturer or Product Line'

    name = fields.Char(string="Name", required=True)

class SampleMaterialOption(models.Model):
    _name = 'crm.lead.sample_material_option'
    _description = 'Sample Material Option'

    name = fields.Char(required=True)


class AnalysisOption(models.Model):
    _name = 'crm.lead.analysis_option'
    _description = 'Analysis Option'

    name = fields.Char(required=True)


class SamplePreparationOption(models.Model):
    _name = 'crm.lead.sample_preparation_option'
    _description = 'Sample Preparation Requirement'

    name = fields.Char(required=True)

class ProductLine(models.Model):
    _name = "crm.lead.product_line"

    name = fields.Char(required=True)

class Lead(models.Model):
    _inherit = 'crm.lead'

    # first_name = fields.Char(string="First Name")
    company_name = fields.Many2one(
        comodel_name="res.partner",
        string="Company name",
        domain="[('company_type', '=', 'company')]",
        compute='_compute_company_name',
        store=False  # Optional: only if you want it stored in DB
    )
    business_type = fields.Selection(
        [
            ("expansion_additional_systems","Expansion/ additional systems"),
            ("new_business","New Business"),
            ("replacement_of_existing_system","Replacement of existing system"),
            ("consumables_accessories","Consumables/ Accessories")]
        ,string="Type")
    last_name = fields.Char(string="Last Name")
    secondary_email = fields.Char(string="Secondary Email")
    created_by = fields.Char(string="Created By")
    modified_by = fields.Char(string="Modified By")
    manufacturer_ids = fields.Many2many(
        'crm.lead.manufacture',
        string="Manufacturer"
    )
    industry = fields.Selection(
        selection=[
            ('academic', 'Academic'),
            ('manufacturer', 'Manufacturer'),
            ('contract_lab', 'Contract Laboratory'),
            ('export_resale', 'Export/ Resale'),
            ('researcher', 'Researcher'),
        ],
        string="Industry",
    )
    rating = fields.Selection(
        selection=[
            ('prospective', 'Prospective Customer'),
            ('active', 'Active Customer'),
            ('inactive', 'Inactive Customer'),
            ('closed', 'Closed down'),
        ],
        string="Rating",
    )
    enquiry_status = fields.Selection(
        selection=[
            ('not_contacted', 'Not Contacted'),
            ('attempted', 'Attempted to contact'),
            ('contacted', 'Contacted'),
            ('pre_qualified', 'Pre-qualified'),
            ('junk', 'Junk'),
            ('unqualified', 'Un Qualified'),
            ('future', 'Contact in Future'),
            ('not_qualified','Not Qualified'),
        ],
        string="Enquiry Status",
        default='not_contacted'  # optional: set a default
    )
    # email_opt_out = fields.Boolean(string="Email Opt Out")
    exchange_rate = fields.Float(string="Exchange Rate")
    currency = fields.Many2one(comodel_name="res.currency",string="Currency")
    description = fields.Text(string="Description")

    #Application Information
    sample_material_ids = fields.Many2many(
        'crm.lead.sample_material_option',
        string='Sample Material'
    )
    sample_material_special = fields.Char(string="Sample material Special")

    analysis_ids = fields.Many2many(
        'crm.lead.analysis_option',
        string='Analysis'
    )
    analysis_further_information = fields.Char(string="Analysis future information")

    description_of_analysis = fields.Char(string="Description of Analysis")

    sample_preparation_ids = fields.Many2many(
        'crm.lead.sample_preparation_option',
        string='Sample Preparation Requirements'
    )
    amount = fields.Float(string="Amount")
    # closing_date = fields.Date(string="Closing Date")
    products= fields.Many2one(
        'product.product',
        string="Product"
    )

    # forecast_category = fields.Selection()
    expected_closer_date = fields.Date(string="Expected Closer Date")

    detail_of_current_state = fields.Text(string="Detail of current state")

    detail_of_next_action = fields.Text(string="Detail of Next Action")

    crm_id = fields.Char(string="Zoho CRM ID")

    manufacturer_id = fields.Many2one("crm.lead.manufacture",string="Manufacturer")

    next_contact_date = fields.Date(string="Next Contact Date")

    @api.model_create_multi
    def create(self, vals_list):
        # Loop through values before calling super()
        for vals in vals_list:
            if vals.get('manufacturer_id'):
                manufacturer = vals['manufacturer_id']
                # If manufacturer_ids not set, initialize as list
                if 'manufacturer_ids' not in vals:
                    vals['manufacturer_ids'] = [(6, 0, [manufacturer])]
        leads = super(Lead, self).create(vals_list)

        return leads

    @api.depends('partner_name')
    def _compute_company_name(self):
        for record in self:
            if record.partner_name:
                # Search for a company with matching name
                company = self.env['res.partner'].search([('name', '=', record.partner_name)], limit=1)
                record.company_name = company if company else False
            else:
                record.company_name = False

class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    manufacturer_id = fields.Many2one("crm.lead.manufacture", string="Manufacturer")