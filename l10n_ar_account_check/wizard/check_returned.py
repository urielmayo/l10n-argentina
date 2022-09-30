
import json
from datetime import date, timedelta
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ReturnedCheck(models.Model):
    _name = 'account.returned.check'
    _description = 'Returned Check'

    @api.constrains('return_date')
    def constrains_return_date(self):
        for rec in self:
            if rec.return_date:
                if rec.return_date < fields.Date.today() - timedelta(days=1) or rec.return_date > fields.Date.today():
                    raise UserError("Date not allowed.")

    return_date = fields.Date(string='Return Date', required=True, default=fields.Date.context_today)
    reason_id = fields.Many2one(comodel_name='reason.rejected.check', string='Reason',
                                domain="[('type', '=', 'returned')]", required=True)
    note = fields.Text(string='Observations')

    def action_return(self):
        record_id = self.env.context.get('active_ids', [])
        check_obj = self.env['account.issued.check'].browse(record_id)

        check_obj.write(
            {'return_date': self.return_date,
             'reason_id': self.reason_id.id,
             'note': self.note})

        # if self.generate_journal_entry:
        self.create_returned_journal_entry(check_obj)

        # update invoice amounts
        self.update_invoice(check_obj)

        check_obj.return_check()
        return {'type': 'ir.actions.act_window_close'}

    def create_returned_journal_entry(self, check):
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        payment_order = check.payment_order_id

        ctx = {
            'date': self.return_date,
            'check_move_validity': False,
        }

        for payment_line in payment_order.move_line_ids:
            if payment_line.issued_check_id == check:
                # Create the account move record.
                original_move_data = payment_order.account_move_get()
                original_move_data['state'] = 'posted'
                move_recordset = move_obj.with_context(ctx).create(original_move_data)

                # Get the name of the account_move just created
                move_id = move_recordset.id
                partner_id = payment_line.partner_id

                # haber: cuenta a pagar establecida en la ficha del proveedor
                inverse_supplier_line = {
                    'invoice_id': check.invoice_id.id or False,
                    'name': '/',
                    'account_id': partner_id.property_account_payable_id.id,
                    'move_id': move_id,
                    'partner_id': partner_id.id,
                    'period_id': payment_line.period_id.id,
                    'date': self.return_date,
                    'credit': payment_line.credit,
                    'debit': 0,
                    'amount_currency': payment_line.amount_currency,
                    'journal_id': original_move_data['journal_id'],
                    'currency_id': payment_line.currency_id.id,
                    'analytic_account_id': payment_line.analytic_account_id.id,
                    'issued_check_id': check.id,
                    'ref': _('Cheque devuelto') + ': Cheque Propio ' + (check.number or '/'),
                }
                move_line_obj.with_context(ctx).create(inverse_supplier_line)

                # debe: cuenta del banco donde se emitió el cheque
                inverse_check_line = {
                    'invoice_id': check.invoice_id.id or False,
                    'name': _('Cheque devuelto') + ': Cheque Propio ' + (check.number or '/'),
                    'account_id': payment_line.account_id.id,
                    'move_id': move_id,
                    'partner_id': payment_line.partner_id.id,
                    'period_id': payment_line.period_id.id,
                    'date': self.return_date,
                    'credit': 0,
                    'debit': payment_line.credit,
                    'amount_currency': payment_line.amount_currency,
                    'journal_id': original_move_data['journal_id'],
                    'currency_id': payment_line.currency_id.id,
                    'analytic_account_id': payment_line.analytic_account_id.id,
                    'ref': _('Cheque devuelto') + ': Cheque Propio ' + (check.number or '/'),
                }
                move_line_obj.with_context(ctx).create(inverse_check_line)

    def update_invoice(self, check):
        ch_invoice = check.invoice_id
        if not ch_invoice:
            raise UserError('No se econtró una factura asociada.')

        # outstanding payment
        payment_dict = json.loads(ch_invoice.payments_widget)
        reverse_dict = {'content': []}
        for cont in payment_dict['content']:
            if cont['amount'] == check.amount and cont['move_id'] == check.payment_move_id.id:
                cont['rev_date'] = date.today()
                reverse_dict['content'].append(cont)
        if reverse_dict:
            ch_invoice.compute_reverse_widget(reverse_dict)
