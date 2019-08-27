##############################################################################
#   Copyright (c) 2019 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('date')
    def _compute_period(self):
        for move in self:
            if not move.date:
                continue

            period_obj = move.env['date.period']
            period_date = fields.Date.from_string(move.date)
            period = period_obj._get_period(period_date)
            move.period_id = period.id

    period_id = fields.Many2one(
        string="Period",
        comodel_name="date.period",
        compute='_compute_period',
        store=True,
    )


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    period_id = fields.Many2one(
        string="Period",
        comodel_name="date.period",
        related="move_id.period_id",
    )
