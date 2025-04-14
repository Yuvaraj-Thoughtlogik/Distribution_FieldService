from odoo import models,fields,api


class Contacts(models.Model):
    _inherit ='res.partner'

    equipment_type = fields.Many2many('equipment.type', string="Equipment Type")
    sample_material = fields.Many2many('sample.material', string="Sample material")
    analysis_analysis = fields.Many2many('analysis.analysis', string="Analysis")
    preparation_requirements = fields.Many2many('preparation.requirements', string="Sample Preparation Requirements")
    email_opt_out = fields.Boolean( string="Email Opt Out")
    actively_employee = fields.Boolean( string="Actively employee")
    sample_material_specification = fields.Html( string="Sample Material Specification")
    analysis_further = fields.Html(string="Analysis -Further Information")
    secondary_email = fields.Char(string="Secondary Email")
    description_custom = fields.Text(string="Description")
    department = fields.Html(string="Department")
    # enquiry_source = fields.Selection([('advertisement', 'Advertisement'), ('broker', 'Broker'), ('coldcall', 'Cold Call'), ('employeereferral', 'Employee Referral'), ('externalreferral', 'External Referral'), ('onlinestore', 'OnlineStore'), ('partner', 'Partner'), ('publicrelations', 'Public Relations'), ('salesmailalias', 'Sales Mail Alias'), ('seminarpartner', 'Seminar Partner'), ('seminar-internal', 'Seminar-Internal'),
    #                                    ('tradeshow', 'Trade Show'),
    #                                    ('webcases', 'Web Cases'),
    #                                    ('webdownload', 'Web Download'),
    #                                    ('webresearch', 'Web Research'),
    #                                    ('webmail', 'Web Mail'),
    #                                    ('chat', 'Chat'),
    #                                    ('twitter', 'Twitter'),
    #                                    ('facebook', 'Facebook'),
    #                                    ('google+', 'Google+'),], "Enquiry Source")
    source_id = fields.Many2one('utm.source',string='Enquiry Source')

    first_name = fields.Char(
        'First Name',
        help='Enter the first name of the individual.',
        compute='_compute_name_parts',
        store=True,
        readonly=False,
    )
    last_name = fields.Char(
        'Last Name',
        help='Enter the last name of the individual.',
        compute='_compute_name_parts',
        store=True,
        readonly=False,
    )
    
     account_type = fields.Selection([
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('distributor', 'Distributor'),
        ('reseller', 'Reseller'),
        ('prospect', 'Prospect'),
    ], string='Account Type')

    @api.depends('name', 'is_company')
    def _compute_name_parts(self):
        """
        Compute first_name and last_name for individual contacts only,
        without affecting the display_name.
        """
        for record in self:
            try:
                if not record.is_company and record.name:
                    parts = record.name.strip().split(' ', 1)
                    record.first_name = parts[0]
                    record.last_name = parts[1] if len(parts) > 1 else ''
                else:
                    record.first_name = ''
                    record.last_name = ''
            except Exception as e:
                raise ValueError(f"Error in _compute_name_parts for record {record.id}: {e}")

    @api.onchange('first_name', 'last_name')
    def _onchange_name_parts(self):
        """
        Updates the full name ('name') based on the first and last names
        for individual contacts only, without affecting the display_name.
        """
        for record in self:
            if not record.is_company:  # Only apply for individuals
                record.name = f"{record.first_name or ''} {record.last_name or ''}".strip()
