##############################################################################
#   Copyright (c) 2019 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.depends('date_invoice')
    def _compute_period(self):
        for invoice in self:
            if not invoice.date_invoice:
                continue

            period_obj = invoice.env['date.period']
            period_date = fields.Date.from_string(invoice.date_invoice)
            period = period_obj._get_period(period_date)
            invoice.period_id = period.id

    period_id = fields.Many2one(
        string="Period",
        comodel_name="date.period",
        compute='_compute_period',
        store=True,
    )
