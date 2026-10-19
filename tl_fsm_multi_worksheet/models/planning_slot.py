from odoo import api, fields, models


class PlanningSlot(models.Model):
    _inherit = 'planning.slot'

    multiple_worksheet = fields.Boolean(string="Multiple worksheets", default=False, copy=True)
    fsm_worksheet_ids = fields.One2many(
        'planning.slot.worksheet', 'planning_slot_id', string='Worksheets', copy=True)
    fsm_worksheet_count = fields.Integer(
        string='Worksheets Count', compute='_compute_fsm_worksheet_count', store=True)
    fsm_worksheet_completed_count = fields.Integer(
        string='Completed Worksheets', compute='_compute_fsm_worksheet_count', store=True)
    fsm_worksheet_completed = fields.Boolean(
        string='Worksheets Completed', compute='_compute_fsm_worksheet_count', store=True)

    # Asset details of the (single) intervention worksheet
    worksheet_has_asset_details = fields.Boolean(related='worksheet_template_id.has_asset_details')
    worksheet_serial_number = fields.Char(
        string='Serial Number', compute='_compute_worksheet_asset_details', store=True, readonly=False)
    worksheet_service_contract_number = fields.Char(
        string='Service Contract Number', compute='_compute_worksheet_asset_details', store=True, readonly=False)

    @api.depends('fsm_worksheet_ids', 'fsm_worksheet_ids.state')
    def _compute_fsm_worksheet_count(self):
        for slot in self:
            slot.fsm_worksheet_count = len(slot.fsm_worksheet_ids)
            slot.fsm_worksheet_completed_count = len(slot.fsm_worksheet_ids.filtered(lambda w: w.state == 'completed'))
            slot.fsm_worksheet_completed = slot.fsm_worksheet_count > 0 and slot.fsm_worksheet_count == slot.fsm_worksheet_completed_count

    @api.depends('customer_assets_ids')
    def _compute_worksheet_asset_details(self):
        for slot in self:
            asset = slot.customer_assets_ids[:1]
            if not asset:
                continue
            if not slot.worksheet_serial_number:
                slot.worksheet_serial_number = asset.product_serial_No or asset.name
            if not slot.worksheet_service_contract_number:
                slot.worksheet_service_contract_number = (asset.subscription_id or asset.sale_order_id).name or False

    def action_open_fsm_worksheets(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Worksheets'),
            'res_model': 'planning.slot.worksheet',
            'views': [
                (self.env.ref('tl_fsm_multi_worksheet.planning_slot_worksheet_view_list').id, 'list'),
                (self.env.ref('tl_fsm_multi_worksheet.planning_slot_worksheet_view_form').id, 'form'),
            ],
            'view_mode': 'list,form',
            'domain': [('planning_slot_id', '=', self.id)],
            'context': {'default_planning_slot_id': self.id},
        }

    def action_generate_asset_worksheets(self):
        """Create one worksheet per customer asset of the intervention (using the
        intervention worksheet template, or the last used template)."""
        for slot in self:
            template = slot.worksheet_template_id or slot.fsm_worksheet_ids[-1:].worksheet_template_id
            if not template:
                continue
            existing_assets = slot.fsm_worksheet_ids.customer_asset_id
            slot.fsm_worksheet_ids = [
                fields.Command.create({'worksheet_template_id': template.id, 'customer_asset_id': asset.id})
                for asset in slot.customer_assets_ids - existing_assets
            ]

    def _get_multi_worksheets_props(self):
        """[(worksheet, props_formatted)] of the completed worksheets, for reports/portal."""
        self.ensure_one()
        return [
            (worksheet, worksheet._get_props_formatted())
            for worksheet in self.fsm_worksheet_ids.filtered(lambda w: w.state == 'completed')
        ]

    def _get_props_formatted(self, readonly=False):
        formatted = super()._get_props_formatted(readonly=readonly)
        if self.worksheet_template_id.has_asset_details and (self.worksheet_serial_number or self.worksheet_service_contract_number):
            formatted = [
                {'type': 'separator', 'name': self.env._('Asset Details'), 'value': False},
                {'type': 'char', 'name': self.env._('Serial Number'), 'value': self.worksheet_serial_number or ''},
                {'type': 'char', 'name': self.env._('Service Contract Number'), 'value': self.worksheet_service_contract_number or ''},
            ] + formatted
        return formatted

    def _is_intervention_report_available(self):
        return super()._is_intervention_report_available() or (
            self.multiple_worksheet and bool(self.fsm_worksheet_completed_count)
        )

    def _get_is_intervention_report_available_domain(self):
        return super()._get_is_intervention_report_available_domain() | fields.Domain([
            ('multiple_worksheet', '=', True), ('fsm_worksheet_completed_count', '>', 0),
        ])

    @api.depends('fsm_worksheet_completed_count', 'multiple_worksheet')
    def _compute_show_customer_preview(self):
        super()._compute_show_customer_preview()

    @api.depends('fsm_worksheet_completed_count', 'multiple_worksheet')
    def _compute_show_sign_report(self):
        super()._compute_show_sign_report()
