
from odoo import models, fields, api


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

class Manufacturer(models.Model):
    _name = 'crm.lead.manufacture'
    _description = 'Manufacturer or Product Line'

    name = fields.Char(string="Name", required=True)

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
    sample_material1_ids = fields.Many2many(
        'sample.material',
        string='Sample Material'
    )

    analysis1_ids = fields.Many2many(
        'analysis.analysis',
        string='Analysis'
    )


    sample_preparation1_ids = fields.Many2many(
        'preparation.requirements',
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

    def _update_partner_fields(self):
        for lead in self:
            partner = lead.partner_id
            parent_partner = partner.parent_id

            def append_many2many_field(partner_obj, field_name, records):
                for rec in records:
                    partner_obj.write({field_name: [(4, rec.id)]})

            if partner:
                append_many2many_field(partner, 'sample_material', lead.sample_material1_ids)
                append_many2many_field(partner, 'analysis_analysis', lead.analysis1_ids)
                append_many2many_field(partner, 'preparation_requirements', lead.sample_preparation1_ids)

                partner.write({
                    'sample_material_specification': lead.sample_material_special or '',
                    'analysis_further': lead.analysis_further_information or '',
                    'description_custom': lead.description_of_analysis or '',
                })

            if parent_partner:
                append_many2many_field(parent_partner, 'sample_material', lead.sample_material1_ids)
                append_many2many_field(parent_partner, 'analysis_analysis', lead.analysis1_ids)
                append_many2many_field(parent_partner, 'preparation_requirements', lead.sample_preparation1_ids)

                parent_partner.write({
                    'sample_material_specification': lead.sample_material_special or '',
                    'analysis_further': lead.analysis_further_information or '',
                    'description_custom': lead.description_of_analysis or '',
                })

    @api.model
    def create(self, vals):
        record = super(Lead, self).create(vals)
        record._update_partner_fields()
        return record

    def write(self, vals):
        res = super(Lead, self).write(vals)
        self._update_partner_fields()
        return res

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
