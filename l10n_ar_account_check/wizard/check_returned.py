
from odoo import _, api, fields, models


class ReturnedCheck(models.Model):
    _name = 'account.returned.check'
    _description = 'Returned Check'

    return_date = fields.Date(string='Return Date', required=True)
    reason = fields.Many2one(comodel_name='reason.rejected.check', string='Reason',
                             domain="[('type', '=', 'returned')]", required=True)
    generate_journal_entry = fields.Boolean(string='Generate Return Journal Entry', default=True)
    note = fields.Text(string='Observations')

    def action_return(self):
        record_id = self.env.context.get('active_ids', [])
        check_obj = self.env['account.issued.check'].browse(record_id)

        check_obj.write(
            {'reject_date': self.return_date,
             'note': self.note})

        if self.generate_journal_entry:
            self.create_returned_journal_entry(check_obj)

        check_obj.return_check()
        return {'type': 'ir.actions.act_window_close'}

    def create_returned_journal_entry(self, check):
        account_obj = self.env['account.account']
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        payment = check.payment_order_id
        company = self.env.user.company_id
        check_conf_obj = self.env['account.check.config']
        def_check_account = check_conf_obj.search([('company_id', '=', company.id)]).deferred_account_id.id
        ctx = {
            'date': self.return_date,
            'check_move_validity': False,
        }
        for payment_line in payment.move_line_ids:
            if payment_line.issued_check_id == check:
                # Create the account move record.
                original_move_data = payment.account_move_get()
                original_move_data['state'] = 'posted'
                move_recordset = move_obj.with_context(ctx).create(original_move_data)

                # Get the name of the account_move just created
                move_id = move_recordset.id
                counterpart_account = account_obj.search([('code', '=', payment_line.counterpart)]).id
                inverse_supplier_line = {
                    'name': '/',
                    'account_id': check.account_bank_id.account_id.id,
                    'move_id': move_id,
                    'partner_id': payment_line.partner_id.id,
                    'period_id': payment_line.period_id.id,
                    'date': self.return_date,
                    'credit': payment_line.credit,
                    'debit': 0,
                    'amount_currency': payment_line.amount_currency,
                    # 'journal_id': original_move_data['journal_id'],
                    'currency_id': payment_line.currency_id.id,
                    'analytic_account_id': payment_line.analytic_account_id.id,
                    'ref': _('Cheque devuelto') + ': ' + (payment_line.name or '/'),
                }
                move_line_obj.with_context(ctx).create(inverse_supplier_line)

                inverse_check_line = {
                    'name': _('Cheque Rechazado') + ': ' + (payment_line.name or '/'),
                    'account_id': def_check_account,
                    'move_id': move_id,
                    'partner_id': payment_line.partner_id.id,
                    'period_id': payment_line.period_id.id,
                    'date': self.return_date,
                    'credit': 0,
                    'debit': payment_line.credit,
                    'amount_currency': payment_line.amount_currency,
                    # 'journal_id': original_move_data['journal_id'],
                    'currency_id': payment_line.currency_id.id,
                    'analytic_account_id': payment_line.analytic_account_id.id,
                    'ref': _('Cheque devuelto') + ': ' + (payment_line.name or '/'),
                }
                move_line_obj.with_context(ctx).create(inverse_check_line)
