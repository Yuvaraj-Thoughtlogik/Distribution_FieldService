

from odoo import fields,models,api

class MailActivitySchedule(models.TransientModel):
    _inherit = "mail.activity.schedule"


    status = fields.Selection([("not_started","Not Started"),("started","Started"),("completed","Completed")],string="Status",default="not_started")
    priority = fields.Selection([("high","High"),("normal","Normal"),("low","Low")],string="Priority",default="normal")


    def _action_schedule_activities(self):
        return self._get_applied_on_records().activity_schedule(
            activity_type_id=self.activity_type_id.id,
            automated=False,
            summary=self.summary,
            note=self.note,
            user_id=self.activity_user_id.id,
            date_deadline=self.date_deadline,
            status = self.status,
            priority = self.priority
        )
    

class MailActivity(models.Model):
    _inherit = "mail.activity"

    status = fields.Selection(
        [
            ("not_started", "Not Started"),
            ("started", "Started"),
            ("completed", "Completed")
        ],string="Status", default="not_started")
    priority = fields.Selection(
        [
            ("high","High"),
            ("normal","Normal"),
            ("low","Low")
        ],string="Priority",default="normal")
