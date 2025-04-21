from odoo import models, fields

class TypeOfVisit(models.Model):
    _name = "calendar.type.visit"
    _description ="Calendar visit Types"

    name = fields.Char(string="Name")

class Meeting(models.Model):
    _inherit = "calendar.event"

    #Meetings : many to many- "Product line"
    product_line = fields.Many2many(comodel_name="crm.lead.manufacture",string="Product Line")

    #Meetings : many to many - "Type of visit?"
    type_of_visit = fields.Many2many(comodel_name="calendar.type.visit", string="Type of Visit")

    #Notes - Key points from Visit
    key_points = fields.Text(string="Key Points form Visit ")

    #notes field : Follow up actions
    follow_up_action = fields.Text(string= "Follow up Actions")


