##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

import logging

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        res = super(SaleOrder, self).action_invoice_create(grouped, final)
        for invoice_id in res:
            invoice = self.env['account.invoice'].browse(invoice_id)
            fiscal_field = self.env.ref('l10n_ar_wsfe.field_account_invoice__fiscal_type_id').id
            default_fiscal_type = self.env['ir.default'].search([('company_id', '=', invoice.company_id.id),
                                                                 ('field_id', '=', fiscal_field)], limit=1)
            if default_fiscal_type:
                invoice.fiscal_type_id = int(default_fiscal_type.json_value)
            invoice._onchange_partner_id()
        return res
