from ..padron import TemplatePadron
from odoo import fields

class PadronSalta(TemplatePadron):
    _name = 'padron.salta'

    vat = fields.Char('CUIT', size=11)
    name_partner = fields.Text('Company name')
    percentage_perception = fields.Float('Percentage of perception')