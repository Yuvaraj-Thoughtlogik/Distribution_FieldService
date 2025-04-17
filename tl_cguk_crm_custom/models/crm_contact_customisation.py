from odoo import models, fields


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

class Crm_customisation(models.Model):
    _inherit = 'crm.lead'
    _description = 'Crm_customisation Model'

    # first_name = fields.Char(string="First Name")

    company_name = fields.Many2one(comodel_name="res.partner",string="Company name",domain="[('company_type', '=', 'company')]")
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
            ('not_qualified', 'Not Qualified'),
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
    closing_date = fields.Date(string="Closing Date")
    prodcuts = fields.Many2one(
        'crm.lead.manufacture',
        string="Manufacturer or Product Line"
    )
    # forecast_category = fields.Selection()
    expected_closer_date = fields.Date(string="Expected Closer Date")

    detail_of_current_state = fields.Text(string="Detail of current state")

    detail_of_next_action = fields.Text(string="Detail of Next Action")
