from odoo import fields, models


class WorksheetTemplate(models.Model):
    _inherit = 'worksheet.template'

    has_asset_details = fields.Boolean(
        string='Asset Details',
        default=False,
        help="If enabled, the worksheet starts with an 'Asset Details' section (Serial Number, "
             "Service Contract Number) prefilled from the customer asset of the intervention.",
    )
