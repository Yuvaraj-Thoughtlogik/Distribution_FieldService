# -*- coding: utf-8 -*-
from odoo import api, fields, models


class WorksheetTemplate(models.Model):
    _inherit = 'worksheet.template'

    has_asset_details = fields.Boolean(
        string='Asset Details',
        default=False,
        help="If enabled, automatically adds the Asset Details group (Asset Number, SO Number, Serial Number, Service Contract Number) as the first group on the worksheet form.",
    )
    asset_details_view_id = fields.Many2one(
        'ir.ui.view',
        string='Asset Details View',
        ondelete='set null',
        copy=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.has_asset_details:
                record._sync_asset_details()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'has_asset_details' in vals or 'model_id' in vals:
            for record in self:
                record._sync_asset_details()
        return res

    def unlink(self):
        for record in self:
            if record.asset_details_view_id and record.asset_details_view_id.exists():
                record.asset_details_view_id.sudo().unlink()
        return super().unlink()

    def _get_base_form_view(self):
        self.ensure_one()
        if not self.model_id:
            return False
        model = self.model_id.model
        view = self.env['ir.ui.view'].sudo().search([
            ('model', '=', model),
            ('type', '=', 'form'),
            ('mode', '=', 'primary'),
        ], limit=1)
        if not view:
            view = self.env['ir.ui.view'].sudo().search([
                ('model', '=', model),
                ('type', '=', 'form'),
                ('inherit_id', '=', False),
            ], limit=1)
        return view

    def _sync_asset_details(self):
        self.ensure_one()
        if self.has_asset_details:
            self._create_asset_fields()
            self._create_or_update_asset_details_view()
        else:
            self._remove_asset_details_view()

    def _create_asset_fields(self):
        self.ensure_one()
        if not self.model_id:
            return

        fields_to_create = [
            ('x_asset_number', 'Asset Number', 'char'),
            ('x_so_number', 'SO Number', 'char'),
            ('x_serial_number', 'Serial Number', 'char'),
            ('x_service_contract_number', 'Service Contract Number', 'char'),
        ]

        ir_fields_obj = self.env['ir.model.fields'].sudo()
        for fname, fdesc, ftype in fields_to_create:
            existing_field = ir_fields_obj.search([
                ('model_id', '=', self.model_id.id),
                ('name', '=', fname),
            ], limit=1)
            if not existing_field:
                ir_fields_obj.create({
                    'name': fname,
                    'field_description': fdesc,
                    'model_id': self.model_id.id,
                    'ttype': ftype,
                    'store': True,
                })

    def _create_or_update_asset_details_view(self):
        self.ensure_one()
        if not self.model_id:
            return

        base_view = self._get_base_form_view()
        if not base_view:
            return

        view_xml = """
<group>
    <group string="Asset Details" name="asset_details">
        <field name="x_asset_number" />
        <field name="x_so_number" />
        <field name="x_serial_number"/>
        <field name="x_service_contract_number" />
    </group>
    <group></group>
</group>"""

        base_arch = base_view.arch or ''
        if '<h1' in base_arch:
            xpath_expr = "//form[1]/sheet[1]/h1[1]"
            position = "before"
        elif '<sheet' in base_arch:
            xpath_expr = "//form[1]/sheet[1]"
            position = "inside"
        elif '<group' in base_arch:
            xpath_expr = "//group[1]"
            position = "before"

        else:
            xpath_expr = "//form/*[1]"
            position = "before"

        arch = f"""<data>
    <xpath expr="{xpath_expr}" position="{position}">
        {view_xml}
    </xpath>
</data>"""

        view_obj = self.env['ir.ui.view'].sudo()
        if self.asset_details_view_id and self.asset_details_view_id.exists():
            self.asset_details_view_id.sudo().write({
                'arch': arch,
                'active': True,
                'priority': 999,
            })
        else:
            existing_inherited_view = view_obj.search([
                ('model', '=', self.model_id.model),
                ('inherit_id', '=', base_view.id),
                ('name', '=', f"{self.name or 'Worksheet'} - Asset Details"),
            ], limit=1)

            if existing_inherited_view:
                existing_inherited_view.write({
                    'arch': arch,
                    'active': True,
                    'priority': 1,
                })
                self.sudo().asset_details_view_id = existing_inherited_view.id
            else:
                inherited_view = view_obj.create({
                    'name': f"{self.name or 'Worksheet'} - Asset Details",
                    'type': 'form',
                    'model': self.model_id.model,
                    'inherit_id': base_view.id,
                    'arch': arch,
                    'active': True,
                    'priority': 999,
                })
                self.sudo().asset_details_view_id = inherited_view.id

    def _remove_asset_details_view(self):
        self.ensure_one()
        if self.asset_details_view_id and self.asset_details_view_id.exists():
            self.asset_details_view_id.sudo().unlink()
            self.sudo().asset_details_view_id = False
