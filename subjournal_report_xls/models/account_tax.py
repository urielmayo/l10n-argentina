from odoo import models, fields


class AccountTax(models.Model):
    _inherit = 'account.tax'

    retention_perception_type =  fields.Selection([
        ('vat', 'Vat'),
        ('gross_income', 'Gross Income'),
        ('income_tax', 'Income Tax')],
        string='Perception / Retention type')