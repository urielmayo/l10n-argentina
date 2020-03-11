##############################################################################
#   Copyright (c) 2019 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import api, fields, models

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    period_id = fields.Many2one(
        string="Period",
        comodel_name="date.period",
    )

    @api.model
    def create(self, vals):
        period_obj = self.env['date.period']
        if not vals.get('period_id', False):
            date = vals.get('date_invoice', False)
            if not date:
                date = fields.Date.context_today(self)
            period_date = fields.Date.from_string(date)
            period = period_obj._get_period(period_date)
            vals.update({
                'period_id': period.id
            })
        return super(AccountInvoice, self).create(vals)

