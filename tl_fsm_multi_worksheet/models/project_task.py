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
    fsm_worksheet_completed = fields.Boolean(
        string='Worksheets Completed',
        compute='_compute_fsm_worksheet_count',
        store=True,
    )

    @api.depends('fsm_worksheet_ids','fsm_worksheet_ids.state')
    def _compute_fsm_worksheet_count(self):
        for task in self:
            task.fsm_worksheet_count = len(task.fsm_worksheet_ids)
            task.fsm_worksheet_completed_count = len(task.fsm_worksheet_ids.filtered(lambda w: w.state == 'completed'))
            task.fsm_worksheet_completed = task.fsm_worksheet_count ==  task.fsm_worksheet_completed_count and task.fsm_worksheet_count > 0

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

    def action_fsm_worksheet(self):
        action = super().action_fsm_worksheet()
        if isinstance(action, dict) and 'context' in action:
            context = dict(action['context'])
            asset = self.customer_assets_ids[:1] if hasattr(self, 'customer_assets_ids') and self.customer_assets_ids else False
            if asset:
                context.update({
                    'default_x_asset_number': asset.name or False,
                    'default_x_so_number': asset.sale_order_id.name or False,
                    'default_x_serial_number': asset.product_serial_No or False,
                    'default_x_service_contract_number': asset.subscription_id.name or False,
                })
                action['context'] = context
        return action

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS | {
            'multiple_worksheet',
            'fsm_worksheet_ids',
            'fsm_worksheet_count',
            'fsm_worksheet_completed_count',
            'fsm_worksheet_completed',
        }

    @api.depends(
        'worksheet_count',
        'allow_worksheets',
        'fsm_worksheet_completed_count',
        'multiple_worksheet',
        'fsm_worksheet_ids',
    )
    def _compute_display_conditions_count(self):
        super()._compute_display_conditions_count()

        for task in self:
            enabled = task.display_enabled_conditions_count
            satisfied = task.display_satisfied_conditions_count

            if task.multiple_worksheet:
                enabled += 1
                satisfied = bool(task.fsm_worksheet_completed_count)
            else:
                enabled += task.allow_worksheets
                satisfied += task.allow_worksheets and task.worksheet_count
            task.display_enabled_conditions_count = enabled
            task.display_satisfied_conditions_count = satisfied

    @api.depends(
        'allow_worksheets', 'multiple_worksheet', 'timer_start', 'worksheet_signature',
        'display_satisfied_conditions_count', 'display_enabled_conditions_count',
    )
    def _compute_display_sign_report_buttons(self):
        super()._compute_display_sign_report_buttons()
        for task in self:
            if not task.multiple_worksheet:
                continue
            sign_p, sign_s = True, True
            if (
                task.timer_start
                or task.worksheet_signature
                or not task.display_satisfied_conditions_count
            ):
                sign_p, sign_s = False, False
            else:
                if task.display_enabled_conditions_count == task.display_satisfied_conditions_count:
                    sign_s = False
                else:
                    sign_p = False
            task.update({
                'display_sign_report_primary': sign_p,
                'display_sign_report_secondary': sign_s,
            })

    @api.depends(
        'allow_worksheets', 'multiple_worksheet', 'timer_start', 'display_satisfied_conditions_count',
        'display_enabled_conditions_count', 'fsm_is_sent',
    )
    def _compute_display_send_report_buttons(self):
        super()._compute_display_send_report_buttons()
        for task in self:
            if not task.multiple_worksheet:
                continue
            send_p, send_s = True, True
            if (
                task.timer_start
                or not task.display_satisfied_conditions_count
                or task.fsm_is_sent
            ):
                send_p, send_s = False, False
            else:
                if task.display_enabled_conditions_count == task.display_satisfied_conditions_count:
                    send_s = False
                else:
                    send_p = False
            task.update({
                'display_send_report_primary': send_p,
                'display_send_report_secondary': send_s,
            })

    def _is_fsm_report_available(self):
        self.ensure_one()
        if self.multiple_worksheet:
            return super()._is_fsm_report_available() or bool(self.fsm_worksheet_completed_count)
        return super()._is_fsm_report_available()