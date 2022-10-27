from odoo import models, fields



class Cm05(models.Model):
    _name = "cm05"

    res_partner = fields.Many2one("res.partner")
    province_id = fields.Many2one("res.country.state", string="Provincia")
    inscrito = fields.Boolean("inscrito")

class res_partner(models.Model):
    _inherit = 'res.partner'

    cm05 = fields.One2many("cm05", "res_partner")


