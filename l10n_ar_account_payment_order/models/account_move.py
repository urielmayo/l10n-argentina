##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from datetime import datetime

from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import float_compare
import logging

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    payment_order_id = fields.Many2one('account.payment.order')



    @api.model
    def _compute_amount_fields(self, amount, src_currency, company_currency):

        res = super()._compute_amount_fields(amount, src_currency, company_currency)
        debit, credit, amount_currency, currency_id = res

        parent = self.payment_order_id

        if self.currency_id.id != parent.company_currency.id:
            amount_computed = self.amount / parent.payment_rate
        else:
            amount_computed = self.amount

        amount_currency = amount_computed

        return debit, credit, amount_currency, currency_id

