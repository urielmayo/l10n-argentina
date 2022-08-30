
import json
from datetime import date
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ReturnedCheck(models.Model):
    _name = 'account.returned.check'
    _description = 'Returned Check'

    return_date = fields.Date(string='Return Date', required=True)
    reason = fields.Many2one(comodel_name='reason.rejected.check', string='Reason',
                             domain="[('type', '=', 'returned')]", required=True)
    note = fields.Text(string='Observations')

    def action_return(self):
        record_id = self.env.context.get('active_ids', [])
        check_obj = self.env['account.issued.check'].browse(record_id)

        check_obj.write(
            {'return_date': self.return_date,
             'reason': self.reason,
             'note': self.note})

        # update invoice amounts
        self.update_invoice(check_obj)

        check_obj.return_check()
        return {'type': 'ir.actions.act_window_close'}

    def get_invoice_by_check(self, check):
        # hardcode invoice from check
        original_entry = check.payment_move_id
        ch_line = original_entry.line_ids.filtered(lambda x:
                                                   x.name == 'Cheque Propio ' + check.number and
                                                   x.debit == 0 and x.credit != 0)
        rev_line = original_entry.line_ids.filtered(lambda x:
                                                    x.debit == ch_line.credit and x.credit == 0 and
                                                    x.date_maturity == ch_line.date_maturity and
                                                    x.partner_id == ch_line.partner_id)
        return self.env['account.invoice'].search([('internal_number', '=', rev_line.name)])

    def update_invoice(self, check):
        ch_invoice = self.get_invoice_by_check(check)
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

        if check.payment_order_id:
            check.payment_order_id.cancel_voucher()
