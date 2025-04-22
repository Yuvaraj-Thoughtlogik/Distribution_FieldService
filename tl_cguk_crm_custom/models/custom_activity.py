

from odoo import fields,models,api

class MailActivitySchedule(models.TransientModel):
    _inherit = "mail.activity.schedule"


    status = fields.Selection([("not_started","Not Started"),("started","Started"),("completed","Completed")],string="Status",default="not_started")
    priority = fields.Selection([("high","High"),("normal","Normal"),("low","Low")],string="Priority",default="normal")