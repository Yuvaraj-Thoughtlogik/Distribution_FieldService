from ast import literal_eval
from email.policy import default

from odoo import api, fields, models
from odoo.tools import sql


class FsmWorksheet(models.Model):
    _name = 'project.task.worksheet'
    _description = 'FSM Worksheets'
    _order = 'sequence,name'


    name = fields.Char(
        string='Name',
        store=True,
        readonly=False,
        compute='_compute_name',
    )
    sequence = fields.Integer(default=10)

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('completed', 'Completed'),
        ],
        string='Status',
        default='draft',
        compute='_compute_state',
    )
    worksheet_template_id = fields.Many2one(
        'worksheet.template',
        string='Worksheet Template',
        required=True,
    )

    project_task_id = fields.Many2one(
        'project.task',
        string='Task',
        required=True,
        ondelete='cascade',
    )


    customer_asset_id = fields.Many2one(
        comodel_name='customer.asset',
        string='Customer Asset',
    )

    worksheet_model = fields.Char(
        string='Worksheet Model',
        compute='_compute_worksheet_model',
        store=True,
    )

    worksheet_id = fields.Many2oneReference(
        string='Worksheet',
        model_field='worksheet_model',
        compute='_compute_worksheet_id',
    )

    @api.depends('worksheet_template_id', 'worksheet_template_id.model_id')
    def _compute_worksheet_model(self):
        for record in self:
            record.worksheet_model = (
                record.worksheet_template_id.model_id.model
                if record.worksheet_template_id.model_id
                else False
            )

    @api.depends(
        'project_task_id',
        'worksheet_template_id',
        'worksheet_model',
    )
    def _compute_worksheet_id(self):
        for record in self:
            record.worksheet_id = False

            if not record.project_task_id or not record.worksheet_model:
                continue

            worksheet_model = self.env[record.worksheet_model]

            worksheet = worksheet_model.search([
                ('x_project_task_id', '=', record.project_task_id.id),
                ('x_project_task_worksheet_line_id', '=', record.id),
            ], limit=1)

            if worksheet:
                record.worksheet_id = worksheet.id

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for record in records:
            record._create_dynamic_worksheet_field()
            record._update_worksheet_constraint()

        return records

    def write(self, vals):
        res = super().write(vals)
        for record in self:
            record._create_dynamic_worksheet_field()
            record._update_worksheet_constraint()
            if 'customer_asset_id' in vals and record.customer_asset_id and record.worksheet_id:
                asset = record.customer_asset_id
                template = record.worksheet_template_id.sudo()
                if template.model_id:
                    worksheet_model = self.env[template.model_id.model]
                    worksheet = worksheet_model.browse(record.worksheet_id)
                    if worksheet.exists():
                        vals_to_sync = {}
                        if 'x_serial_number' in worksheet._fields and not worksheet.x_serial_number and (asset.display_name or asset.name):
                            vals_to_sync['x_serial_number'] = asset.display_name or asset.name
                        if 'x_service_contract_number' in worksheet._fields and not worksheet.x_service_contract_number and asset.sale_order_id:
                            vals_to_sync['x_service_contract_number'] = asset.sale_order_id.name
                        if vals_to_sync:
                            worksheet.sudo().write(vals_to_sync)

        return res

    def _create_dynamic_worksheet_field(self):
        self.ensure_one()

        template = self.worksheet_template_id.sudo()

        if not template.model_id:
            return

        model = template.model_id.model

        # Check whether the field already exists
        field = self.env['ir.model.fields'].sudo().search([
            ('model', '=', model),
            ('name', '=', 'x_project_task_worksheet_line_id'),
        ], limit=1)

        if field:
            return

        model_id = self.env['ir.model'].sudo().search([
            ('model', '=', model),
        ], limit=1)

        if not model_id:
            return

        self.env['ir.model.fields'].sudo().create({
            'name': 'x_project_task_worksheet_line_id',
            'field_description': 'Worksheet Line',
            'model_id': model_id.id,
            'ttype': 'many2one',
            'relation': 'project.task.worksheet',
            'required': False,
            'store': True,
        })

    def _update_worksheet_constraint(self):
        self.ensure_one()

        template = self.worksheet_template_id.sudo()

        if not template.model_id:
            return

        res_model = template.res_model.replace('.', '_')

        table = 'x_%s_worksheet_template_%d' % (
            res_model,
            template.id,
        )

        old_constraint = '%s_x_%s_id_uniq' % (
            table,
            res_model,
        )

        new_constraint = '%s_x_project_task_worksheet_line_id_uniq' % (
            table,
        )

        # Already updated
        self.env.cr.execute("""
            SELECT 1
            FROM pg_constraint
            WHERE conrelid = %s::regclass
              AND conname = %s
            LIMIT 1
        """, (table, new_constraint))

        if self.env.cr.fetchone():
            return

        # Remove original constraint if it exists
        self.env.cr.execute("""
            SELECT 1
            FROM pg_constraint
            WHERE conrelid = %s::regclass
              AND conname = %s
            LIMIT 1
        """, (table, old_constraint))

        if self.env.cr.fetchone():
            sql.drop_constraint(
                self.env.cr,
                table,
                old_constraint,
            )

        # Add new constraint
        sql.add_constraint(
            self.env.cr,
            table,
            new_constraint,
            'UNIQUE(x_%s_id, x_project_task_worksheet_line_id)' % res_model,
        )

    def unlink(self):
        for record in self:
            template = record.worksheet_template_id.sudo()

            worksheet_model = self.env[template.model_id.model]

            record._create_dynamic_worksheet_field()

            worksheet_model.search([
                ('x_project_task_id', '=', record.project_task_id.id),
                ('x_project_task_worksheet_line_id', '=', record.id),
            ]).unlink()

        return super().unlink()

    @api.depends('worksheet_template_id')
    def _compute_name(self):
        for record in self:
            record.name = record.worksheet_template_id.name

    def open_fsm_worksheet(self):
        self.ensure_one()

        template = self.worksheet_template_id.sudo()
        action = template.action_id.sudo().read()[0]

        worksheet_model = self.env[template.model_id.model]

        worksheet = worksheet_model.search([
            ('x_project_task_id', '=', self.project_task_id.id),
            ('x_project_task_worksheet_line_id', '=', self.id),
        ], limit=1)

        context = literal_eval(action.get('context', '{}'))
        default_context = {
            **context,
            'edit': True,
            'default_x_project_task_id': self.project_task_id.id,
            'default_x_project_task_worksheet_line_id': self.id,
        }

        if self.customer_asset_id:
            asset = self.customer_asset_id
            default_context.update({
                'default_x_serial_number': asset.display_name or False,
                'default_x_service_contract_number': asset.sale_order_id.name or False,
            })

            # If worksheet already exists, populate empty asset fields if any
            if worksheet:
                vals_to_update = {}
                if 'x_serial_number' in worksheet._fields and not worksheet.x_serial_number and (asset.display_name or asset.name):
                    vals_to_update['x_serial_number'] = asset.display_name or asset.name
                if 'x_service_contract_number' in worksheet._fields and not worksheet.x_service_contract_number and asset.sale_order_id:
                    vals_to_update['x_service_contract_number'] = asset.sale_order_id.name
                if vals_to_update:
                    worksheet.sudo().write(vals_to_update)

        action.update({
            'res_id': worksheet.id or False,
            'views': [(False, 'form')],
            'context': default_context,
        })

        return action

    def _compute_state(self):
        for record in self:
            record.state = 'draft'

            if not record.worksheet_template_id or not record.project_task_id:
                continue



            template = record.worksheet_template_id.sudo()

            if not template.model_id:
                continue

            worksheet_model = self.env[template.model_id.model]

            if 'x_project_task_worksheet_line_id' not in worksheet_model._fields:
                continue

            worksheet = worksheet_model.search([
                ('x_project_task_id', '=', record.project_task_id.id),
                ('x_project_task_worksheet_line_id', '=', record.id),
            ], limit=1)

            record.state = 'completed' if worksheet else 'draft'
            record.project_task_id._compute_fsm_worksheet_count()