from odoo import fields, models, api


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
        store=True,
    )
    fsm_worksheet_completed_count = fields.Integer(
        string='Worksheets',
        compute='_compute_fsm_worksheet_count',
        store=True,
    )

    @api.depends('fsm_worksheet_ids','fsm_worksheet_ids.state')
    def _compute_fsm_worksheet_count(self):
        for task in self:
            task.fsm_worksheet_count = len(task.fsm_worksheet_ids)
            task.fsm_worksheet_completed_count = len(task.fsm_worksheet_ids.filtered(lambda w: w.state == 'completed'))

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

    @api.depends(
        'worksheet_count',
        'allow_worksheets',
        'fsm_worksheet_completed_count',
        'multiple_worksheet',
    )
    def _compute_display_conditions_count(self):
        super()._compute_display_conditions_count()

        for task in self:
            enabled = task.display_enabled_conditions_count
            satisfied = task.display_satisfied_conditions_count

            if task.multiple_worksheet:
                enabled += 1
                satisfied += bool(task.fsm_worksheet_completed_count)
            else:
                enabled += task.allow_worksheets
                satisfied += task.allow_worksheets and task.worksheet_count

            task.display_enabled_conditions_count = enabled
            task.display_satisfied_conditions_count = satisfied