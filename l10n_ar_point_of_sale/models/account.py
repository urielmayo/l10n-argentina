##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.account.models.account_move import AccountMove as AccountMoveOriginal


class AccountTax(models.Model):

    _inherit = "account.tax"
    _description = "Tax"

    other_group = fields.Char(string='Other Group', size=64)
    is_exempt = fields.Boolean(
        string='Exempt',
        default=False,
        help="Check this if this Tax represent Tax Exempts",
    )
    tax_group = fields.Selection(
        [
            ('vat', 'VAT'),
            ('perception', 'Perception'),
            ('retention', 'Retention'),
            ('internal', 'Internal Tax'),
            ('other', 'Other'),
        ],
        string='Tax Group',
        default='vat',
        required=True,
        help="This is tax categorization.",
    )


@api.multi
def post(self, invoice=False):
    if self._context.get('invoice'):
        invoice = self._context.get('invoice', False)
    self._post_validate()
    for move in self:
        move.line_ids.create_analytic_lines()
        if move.name == '/':
            if invoice:
                new_name = invoice.internal_number
            else:
                journal = move.journal_id
                if journal.sequence_id:
                    sequence = journal.sequence_id
                    new_name = sequence.with_context(
                        ir_sequence_date=move.date).next_by_id()
                else:
                    err = _('Please define a sequence on the journal.')
                    raise UserError(err)
            if new_name:
                move.name = new_name
    return self.write({'state': 'posted'})


class AccountMove(models.Model):

    _inherit = "account.move"

    @api.model_cr
    def _register_hook(self):
        res = super()._register_hook()
        # Heredamos para que no ponga el nombre del internal_number
        # al asiento contable, sino que siempre siga la secuencia
        AccountMoveOriginal._patch_method('post', post)
        return res
