from odoo import models, fields, api
from bs4 import BeautifulSoup

class TypeOfVisit(models.Model):
    _name = "calendar.type.visit"
    _description ="Calendar visit Types"

    name = fields.Char(string="Name")


def strip_html_keep_text(html_string):
    soup = BeautifulSoup(html_string, "html.parser")
    return soup.get_text()


class Meeting(models.Model):
    _inherit = "calendar.event"

    product_line = fields.Many2many(comodel_name="crm.lead.manufacture",string="Product Line")

    type_of_visit = fields.Many2many(comodel_name="calendar.type.visit", string="Type of Visit")

    key_points = fields.Text(string="Key Points form Visit ")

    follow_up_action = fields.Text(string= "Follow up Actions")

    description = fields.Text(string='Description',readonly="not user_can_edit")

    @api.model
    def create(self, vals):
        if 'description' in vals and vals['description']:
            vals['description'] = self.strip_html_keep_text(vals['description'])
        return super().create(vals)

    def write(self, vals):
        res = super().write(vals)
        for record in self:
            if record.description:
                clean_text = strip_html_keep_text(record.description)
                if record.description != clean_text:
                    record.sudo().write({'description': clean_text})
        return res


