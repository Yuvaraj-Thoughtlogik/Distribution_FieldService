from odoo import models, api

# class MailNotification(models.Model):
#     _inherit = "mail.notification"

#     @api.model
#     def auto_remove_email_notifications(self):
#         """Automatically remove all notification emails triggered by incoming emails."""
#         notifications = self.env['mail.notification'].search([
#             ('notification_type', '=', 'email'),
#             ('mail_message_id.message_type', '=', 'email')
#         ])
#         if notifications:
#             print(f"Deleting {len(notifications)} email notifications...")
#             notifications.unlink()