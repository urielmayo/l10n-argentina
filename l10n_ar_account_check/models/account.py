##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import fields, models


class AccountMoveLine(models.Model):
    _name = 'account.move.line'
    _inherit = 'account.move.line'

    issued_check_id = fields.Many2one(
        comodel_name='account.issued.check',
        string='Issued Check')


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    checkbox_ids = fields.One2many(string="Checkbook",
                                   comodel_name='account.checkbook',
                                   inverse_name='journal_id')
