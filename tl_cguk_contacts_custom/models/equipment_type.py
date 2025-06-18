from odoo import models,fields


class EquipmentType(models.Model):
    _name = 'equipment.type'

    name = fields.Char("Name")

class SampleMaterial(models.Model):
    _name = 'sample.material'

    name = fields.Char("Name")

class Analysis(models.Model):
    _name = 'analysis.analysis'

    name = fields.Char("Name")

class PreparationRequirements(models.Model):
    _name = 'preparation.requirements'

    name = fields.Char("Name")

