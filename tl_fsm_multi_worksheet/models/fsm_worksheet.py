from ast import literal_eval

from odoo import api, fields, models


class FsmWorksheet(models.Model):
    _name = 'project.task.worksheet'
    _description = 'FSM Worksheets'

    name = fields.Char(
        string='Name',
        store=True,
        readonly=False,
        compute='_compute_name',
    )
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

    def unlink(self):
        for record in self:
            template = record.worksheet_template_id.sudo()

            worksheet_model = self.env[template.model_id.model]

            worksheet_model.search([
                ('x_project_task_id', '=', record.project_task_id.id),
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
        ], limit=1)

        context = literal_eval(action.get('context', '{}'))

        action.update({
            'res_id': worksheet.id or False,
            'views': [(False, 'form')],
            'context': {
                **context,
                'edit': True,
                'default_x_project_task_id': self.project_task_id.id,
            },
        })

        return action

    def _compute_state(self):
        for record in self:
            template = record.worksheet_template_id.sudo()

            worksheet_model = self.env[template.model_id.model]

            worksheet = worksheet_model.search([
                ('x_project_task_id', '=', record.project_task_id.id),
            ], limit=1)

            record.state = 'completed' if worksheet else 'draft'