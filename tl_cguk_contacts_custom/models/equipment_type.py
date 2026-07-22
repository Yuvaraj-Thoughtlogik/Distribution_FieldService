from odoo import models,fields


class EquipmentType(models.Model):
    _name = 'equipment.type'
    _description = 'Equipment Type'

    name = fields.Char("Name")

class SampleMaterial(models.Model):
    _name = 'sample.material'
    _description = 'Sample Material'

    name = fields.Char("Name")

class Analysis(models.Model):
    _name = 'analysis.analysis'
    _description = 'Analysis'

    name = fields.Char("Name")

class PreparationRequirements(models.Model):
    _name = 'preparation.requirements'
    _description = 'Preparation Requirements'

    name = fields.Char("Name")

