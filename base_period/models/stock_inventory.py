##############################################################################
#   Copyright (c) 2019 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import api, fields, models


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    @api.depends('date')
    def _compute_period(self):
        for si in self:
            if not si.date:
                continue

            period_obj = si.env['date.period']
            period_date = fields.Date.from_string(si.date)
            period = period_obj._get_period(period_date)
            si.period_id = period.id

    period_id = fields.Many2one(
        string="Period",
        comodel_name="date.period",
        compute='_compute_period',
        store=True,
    )
