from odoo import api, fields, models


class PlanningSlotWorksheet(models.Model):
    """One worksheet of an intervention (multiple worksheets mode).

    Odoo 20 worksheets are not generated ``x_*`` models anymore: a worksheet template
    holds a properties definition, and the filled values are stored in a Properties
    field of the record using the template (here: this worksheet line)."""
    _name = 'planning.slot.worksheet'
    _description = 'Intervention Worksheet'
    _order = 'sequence, id'
    _check_company_auto = True

    name = fields.Char(string='Name', compute='_compute_name', store=True, readonly=False)
    sequence = fields.Integer(default=10)
    planning_slot_id = fields.Many2one(
        'planning.slot', string='Intervention', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='planning_slot_id.company_id', store=True)
    partner_id = fields.Many2one(related='planning_slot_id.partner_id')
    worksheet_template_id = fields.Many2one(
        'worksheet.template',
        string='Worksheet Template',
        required=True,
        check_company=True,
        domain="[('res_model', '=', 'planning.slot'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    worksheet_properties = fields.Properties(
        'Worksheet', definition='worksheet_template_id.worksheet_properties_definition', copy=True)
    customer_asset_id = fields.Many2one(comodel_name='customer.asset', string='Customer Asset')
    has_asset_details = fields.Boolean(related='worksheet_template_id.has_asset_details')
    serial_number = fields.Char(
        string='Serial Number', compute='_compute_asset_details', store=True, readonly=False)
    service_contract_number = fields.Char(
        string='Service Contract Number', compute='_compute_asset_details', store=True, readonly=False)
    state = fields.Selection(
        selection=[('draft', 'Draft'), ('completed', 'Completed')],
        string='Status',
        compute='_compute_state',
        store=True,
        readonly=False,
        default='draft',
    )

    @api.depends('worksheet_template_id')
    def _compute_name(self):
        for record in self:
            if record.worksheet_template_id and (not record.name or record.name == record._origin.worksheet_template_id.name):
                record.name = record.worksheet_template_id.name

    @api.depends('customer_asset_id')
    def _compute_asset_details(self):
        for record in self:
            asset = record.customer_asset_id
            if not asset:
                continue
            if not record.serial_number:
                record.serial_number = asset.product_serial_No or asset.name
            if not record.service_contract_number:
                record.service_contract_number = (asset.subscription_id or asset.sale_order_id).name or False

    @api.depends('worksheet_properties')
    def _compute_state(self):
        for record in self:
            values = record.worksheet_properties or {}
            record.state = 'completed' if any(values.values()) else (record.state or 'draft')

    def action_mark_completed(self):
        self.state = 'completed'

    def action_reset_draft(self):
        self.state = 'draft'

    def open_fsm_worksheet(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.name,
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'views': [(self.env.ref('tl_fsm_multi_worksheet.planning_slot_worksheet_view_form').id, 'form')],
            'target': 'new',
        }

    def _get_props_formatted(self):
        """Same output format as planning.slot._get_props_formatted (used by the reports)."""
        self.ensure_one()
        formatted = []
        if self.has_asset_details:
            formatted += [
                {'type': 'separator', 'name': self.env._('Asset Details'), 'value': False},
                {'type': 'char', 'name': self.env._('Serial Number'), 'value': self.serial_number or ''},
                {'type': 'char', 'name': self.env._('Service Contract Number'), 'value': self.service_contract_number or ''},
            ]
        if self.worksheet_properties:
            properties_values = self.worksheet_properties.field.convert_to_read(
                self.worksheet_properties._values,
                self.worksheet_properties.record,
                use_display_name=False,
            )
            for prop in properties_values:
                if prop['type'] == 'monetary':
                    prop['currency_field'] = self.worksheet_template_id.currency_id
            formatted += self.worksheet_template_id.format_props(properties_values)
        return formatted
