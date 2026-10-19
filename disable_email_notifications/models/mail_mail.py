from odoo import models, api

class MailMail(models.Model):
    _inherit = "mail.mail"

    def send(self, auto_commit=False, raise_exception=False, post_send_callback=None):
        """Block only email notifications related to incoming emails but allow other emails."""
        filtered_mails = self.filtered(lambda mail: not (
            mail.is_notification and 
            mail.notification_ids and 
            any(notification.notification_type == 'email' and 
                notification.mail_message_id and 
                notification.mail_message_id.message_type == 'email' 
                for notification in mail.notification_ids)
        ))
        return super(MailMail, filtered_mails).send(auto_commit=auto_commit, raise_exception=raise_exception, post_send_callback=post_send_callback)
    
    @api.model
    def auto_remove_stuck_emails(self):
        """Automatically delete stuck email notifications & outgoing emails."""

        # Fix: Use 'notification_status' instead of 'state'
        notifications = self.env['mail.notification'].search([
            ('notification_type', '=', 'email'),
            ('notification_status', '=', 'ready')  # Correct field name
        ])
        if notifications:
            print(f"Deleting {len(notifications)} email notifications...")
            notifications.unlink()

        emails = self.env['mail.mail'].search([
            ('state', '=', 'outgoing')
        ])
        if emails:
            print(f"Deleting {len(emails)} stuck outgoing emails...")
            emails.unlink()