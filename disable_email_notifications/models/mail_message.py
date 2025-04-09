from odoo import models

class MailMessage(models.Model):
    _inherit = "mail.message"

    def _notify(self, force_send=False, send_after_commit=True, **kwargs):
        """Completely block notifications for incoming email messages before they are processed."""
        if self.message_type == 'email':
            return  # Stop notifications at the source

        return super()._notify(force_send, send_after_commit, **kwargs)