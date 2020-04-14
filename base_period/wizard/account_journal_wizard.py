##############################################################################
#   Copyright (c) 2019 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import api, fields, models


class CloseAccountJournalWizard(models.TransientModel):
    _name = 'close.account.journal.wizard'
    _description = "Wizard to close journals related to a period"\
        " (from Account Journal form view)"

    period_id = fields.Many2one(
        comodel_name="date.period",
        string='Period',
        required=True,
    )
    closed = fields.Boolean(compute='_compute_closed', string="Closed")

    def _get_active_journal(self):
        active_ids = self.env.context.get('active_ids')
        account_journal_id = self.env['account.journal'].browse(active_ids)
        return account_journal_id

    def _build_period_data(self, command=3):
        account_journal_id = self._get_active_journal()
        return {
            'journal_ids': [(command, account_journal_id.id, 0)],
        }

    @api.multi
    def button_open(self):
        period_data = self._build_period_data()
        self.period_id.write(period_data)

    @api.multi
    def button_close(self):
        period_data = self._build_period_data(4)
        self.period_id.write(period_data)

    @api.depends('period_id', 'period_id.journal_ids')
    def _compute_closed(self):
        account_journal_id = self._get_active_journal()
        if account_journal_id in self.period_id.journal_ids:
            self.closed = True
        else:
            self.closed = False
