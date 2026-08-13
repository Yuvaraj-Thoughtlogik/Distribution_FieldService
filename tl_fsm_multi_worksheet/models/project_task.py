from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = 'project.task'

    multiple_worksheet = fields.Boolean(
        string="Multiple worksheets",
        default=False,
    )

    fsm_worksheet_ids = fields.One2many(
        'project.task.worksheet',
        'project_task_id',
        string='Worksheets',
    )



    fsm_worksheet_count = fields.Integer(
        string='Worksheets',
        compute='_compute_fsm_worksheet_count',
    )

    def _compute_fsm_worksheet_count(self):
        for task in self:
            task.fsm_worksheet_count = len(task.fsm_worksheet_ids)

    def action_open_fsm_worksheets(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Worksheets',
            'res_model': 'project.task.worksheet',
            'view_id': self.env.ref('tl_fsm_multi_worksheet.project_task_worksheet_view_list').id,
            'view_mode': 'list',
            'domain': [
                ('project_task_id', '=', self.id),
            ],
            'context': {
                'default_project_task_id': self.id,
            },
        }