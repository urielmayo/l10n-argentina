##############################################################################
#   Copyright (c) 2021 Eynes (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

class AccountPaymentOrderConceptLine(models.Model):
    _inherit = "account.payment.order.concept.line"
    _description = "Account Payment Order Concept Line"

    product_id = fields.Many2one(
        comodel_name='product.product', string='Product', required=True)
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')

    @api.onchange('product_id')
    def change_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            self.account_id = self.product_id.property_account_expense_id.id
