from odoo import models

class WorksheetTemplate(models.Model):
    _inherit = 'worksheet.template'

    def action_duplicate_templates(self):
        for record in self:
            record.copy()
        # Do not change the view, stay on the same list view
        return None
        
   
