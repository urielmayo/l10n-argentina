##############################################################################
#   Copyright (c) 2019 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import api, fields, models


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    period_id = fields.Many2one(
        string="Period",
        comodel_name="date.period",
        compute='_compute_period',
        store=True,
    )

    @api.depends('date')
    def _compute_period(self):
        period_model = self.env['date.period']
        for si in self:
            if si.date:
                period_date = fields.Date.from_string(si.date)
                period = period_model._get_period(period_date)
                period_id = period.id
            else:
                period_id = False

            si.period_id = period_id
