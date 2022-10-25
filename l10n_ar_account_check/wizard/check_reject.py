###############################################################################
#   Copyright (C) 2008-2011  Thymbra
#   Copyright (c) 2012-2018 Eynes/E-MIPS (http://www.e-mips.com.ar)
#   Copyright (c) 2014-2018 Aconcagua Team
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
###############################################################################

import odoo.addons.decimal_precision as dp
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountCheckReject(models.Model):
    _name = 'account.check.reject'
    _description = 'Third Check Reject'

    @api.model
    def _get_journal(self):
        user = self.env.user
        company_id = self.env.context.get('company_id', user.company_id.id)
        journal_obj = self.env['account.journal']
        domain = [('company_id', '=', company_id), ('type', '=', 'sale')]

        res = journal_obj.search(domain, limit=1)
        return res and res.id or False

    reject_date = fields.Date(string='Reject Date', default=fields.Date.context_today, required=True)
    reason_id = fields.Many2one(
        comodel_name='reason.rejected.check', string='Reason',
        domain="[('type', '=', 'rejected')]")
    journal_id = fields.Many2one(
        comodel_name='account.journal', string='Journal',
        default=_get_journal)
    expense_line_ids = fields.One2many(
        comodel_name='check.reject.expense', inverse_name='reject_id',
        string='Expenses')
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'account.invoice'))
    generate_rejection_journal_entry = fields.Boolean(string='Generate Rejection Journal Entry', default=True)
    note = fields.Text(string='Note')

    @api.multi
    def action_reject(self):
        third_check_obj = self.env['account.third.check']
        record_ids = self.env.context.get('active_ids', [])
        check_objs = third_check_obj.browse(record_ids)

        for check in check_objs:
            if check.state not in ('wallet', 'delivered', 'deposited'):
                raise ValidationError(_('You can not reject a check in this state.'))

            check.write({
                'reject_date': self.reject_date,
                'reason_id': self.reason_id.id or False,
                'note': self.note,
            })

            if self.generate_rejection_journal_entry:
                self.create_rejected_journal_entry(check)
                check.reject_check()
            else:
                # debit_note_id = self.create_debit_note(check)
                pass  # la creación de nota de débito queda deshabilitada hasta nuevo aviso. Ver versiones anteriores
        return {'type': 'ir.actions.act_window_close'}

    def create_rejected_journal_entry(self, check):
        # TODO: Improve Methods
        account_obj = self.env['account.account']
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        payment = check.source_payment_order_id
        company = self.env.user.company_id
        check_conf_obj = self.env['account.check.config']
        def_check_account = check_conf_obj.search([('company_id', '=', company.id)]).deferred_account_id.id
        ctx = {
            'date': self.reject_date,
            'check_move_validity': False,
        }
        for payment_line in payment.move_line_ids:
            if payment_line.third_check_id == check:
            # Create the account move record.
                # TODO: change hardcoded journal_id
                original_move_data = payment.account_move_get()
                original_move_data['journal_id'] = 3  # operaciones varias
                original_move_data['state'] = 'posted'
                move_recordset = move_obj.with_context(ctx).create(
                    original_move_data)

            # Get the name of the account_move just created
                move_id = move_recordset.id
                counterpart_account = account_obj.search([('code', '=', payment_line.counterpart)]).id
                inverse_supplier_line = {
                    'name': '/',
                    'account_id': counterpart_account,
                    'move_id': move_id,
                    'partner_id': payment_line.partner_id.id,
                    'period_id': payment_line.period_id.id,
                    'date': self.reject_date,
                    'credit': 0,
                    'debit': payment_line.debit,
                    'amount_currency': payment_line.amount_currency,
                    'journal_id': original_move_data['journal_id'],
                    'currency_id': payment_line.currency_id.id,
                    'analytic_account_id': payment_line.analytic_account_id.id,
                    'ref': _('Rechazado Cheque')+': '+(payment_line.name or '/'),
                }
                move_line_obj.with_context(ctx)\
                    .create(inverse_supplier_line)

                inverse_check_line = {
                    'name': _('Cheque Rechazado')+': '+(payment_line.name or '/'),
                    'account_id': def_check_account,
                    'move_id': move_id,
                    'partner_id': payment_line.partner_id.id,
                    'period_id': payment_line.period_id.id,
                    'date': self.reject_date,
                    'credit': payment_line.debit,
                    'debit': 0,
                    'amount_currency': payment_line.amount_currency,
                    'journal_id': original_move_data['journal_id'],
                    'currency_id': payment_line.currency_id.id,
                    'analytic_account_id': payment_line.analytic_account_id.id,
                    'ref': _('Rechazado Cheque')+': '+(payment_line.name or '/'),
                }
                move_line_obj.with_context(ctx)\
                    .create(inverse_check_line)

    def create_debit_note(self, check):
        check_config_obj = self.env['account.check.config']
        invoice_obj = self.env['account.invoice']
        partner = check.source_partner_id

        config = check_config_obj.search(
            [('company_id', '=', check.company_id.id)])
        if not config:
            raise ValidationError(_('ERROR! There is no check \
                configuration for this Company!'))

        inv_account_id = config.receivable_rejected_account_id
        if not inv_account_id:
            inv_account_id = partner.property_account_receivable_id

        invoice_vals = {
            'origin': _('Check : %s') % check.number,
            'name': _('Debit Note due to rejected check %s [%s]') %
            (check.number or '', check.source_payment_order_id.number),
            'type': 'out_invoice',
            'is_debit_note': True,
            'account_id': inv_account_id.id,
            'partner_id': partner.id,
            'journal_id': self.journal_id.id,
            'fiscal_position': partner.property_account_position_id.id,
            'company_id': self.company_id.id,
        }

        lines = []
        # Linea del cheque rechazado

        account_id = False
        if check.state == 'delivered':
            account_id = config.rejected_account_id.id
        elif check.state == 'deposited':
            account_id = check.deposit_bank_id.account_id.id
        elif check.state == 'wallet':
            account_id = config.account_id.id

        date_format = self.env["res.lang"].search([("code", "=", self.env.user.lang)]).date_format
        rejected_date = self.reject_date.strftime(date_format)
        name = _('Check Rejected %s %s') % (check.number, rejected_date)

        invoice_line_vals = {
            'name': name,
            'quantity': 1,
            'price_unit': check.amount,
            'account_id': account_id,
        }

        lines.append((0, 0, invoice_line_vals))

        # Lineas de gastos
        for expense in self.expense_line_ids:

            product = expense.product_id
            account_id = product.property_account_expense_id
            if not account_id:
                account_id = product.categ_id.\
                    property_account_expense_categ_id
            if not account_id:
                raise ValidationError(
                    _('Please, fill the expense account in the product.'))

            invoice_line_vals = {
                'name': expense.product_id.name,
                'product_id': expense.product_id.id,
                'quantity': 1,
                'price_unit': expense.price,
                'account_id': account_id.id,
                'invoice_line_tax_ids': [
                    (6, 0, expense.product_id.taxes_id.ids)],
            }

            lines.append((0, 0, invoice_line_vals))

        invoice_vals['invoice_line_ids'] = lines

        # Creamos la nota de debito
        debit_note_id = invoice_obj.create(invoice_vals)

        debit_note_id._onchange_partner_id()

        # Volvemos a cambiar la cuenta que sobreescribio el onchange
        debit_note_id.account_id = inv_account_id

        debit_note_id._onchange_invoice_line_ids()
        return debit_note_id


class CheckRejectExpense(models.Model):
    _name = 'check.reject.expense'
    _description = 'Reject Expense'

    product_id = fields.Many2one(
        comodel_name='product.product', string='Product', required=True)
    reject_id = fields.Many2one(
        comodel_name='account.check.reject', string='Reject')
    price = fields.Float(
        string='Amount', digits=dp.get_precision('Account'), required=True)


class CheckRejectIssuedCheck(models.Model):
    _name = 'check.reject.issued.check'
    _description = 'Reject Issued Check'

    reject_date = fields.Date(string='Reject Date', required=True)
    reason_id = fields.Many2one(comodel_name='reason.rejected.check',
                                domain="[('type', '=', 'rejected')]", string='Reason')
    generate_rejection_journal_entry = fields.Boolean(string='Generate Rejection Journal Entry', default=True)
    note = fields.Text(string='Note')

    def action_reject(self):
        issued_check_obj = self.env['account.issued.check']
        record_ids = self.env.context.get('active_ids', [])

        check_objs = issued_check_obj.browse(record_ids)
        for check in check_objs:
            check.write(
                {'reject_date': self.reject_date,
                 'reason_id': self.reason_id.id or False,
                 'generate_rejection_journal_entry': self.generate_rejection_journal_entry,
                 'note': self.note})
            if self.generate_rejection_journal_entry:
                self.create_rejected_journal_entry(check)
            check.reject_check()                
        return {'type': 'ir.actions.act_window_close'}

    def create_rejected_journal_entry(self, check):
        # TODO: Improve Methods
        account_obj = self.env['account.account']
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        payment = check.payment_order_id
        company = self.env.user.company_id
        check_conf_obj = self.env['account.check.config']
        def_check_account = check_conf_obj.search([('company_id', '=', company.id)]).deferred_account_id.id
        ctx = {
            'date': self.reject_date,
            'check_move_validity': False,
        }
        for payment_line in payment.move_line_ids:
            if payment_line.issued_check_id == check:
            # Create the account move record.
                # TODO: change hardcoded journal_id            
                original_move_data = payment.account_move_get()
                original_move_data['journal_id'] = 3  # operaciones varias
                original_move_data['state'] = 'posted'
                move_recordset = move_obj.with_context(ctx).create(
                    original_move_data)

            # Get the name of the account_move just created
                move_id = move_recordset.id
                counterpart_account = account_obj.search([('code', '=', payment_line.counterpart)]).id                
                inverse_supplier_line = {
                    'name': '/',
                    'account_id': counterpart_account,
                    'move_id': move_id,
                    'partner_id': payment_line.partner_id.id,
                    'period_id': payment_line.period_id.id,
                    'date': self.reject_date,
                    'credit': payment_line.credit,
                    'debit': 0,
                    'amount_currency': payment_line.amount_currency,
                    'journal_id': original_move_data['journal_id'],
                    'currency_id': payment_line.currency_id.id,
                    'analytic_account_id': payment_line.analytic_account_id.id,
                    'ref': _('Rechazado Cheque')+': '+(payment_line.name or '/'),
                    'invoice_id': check.invoice_id.id or False,
                }
                move_line_obj.with_context(ctx)\
                    .create(inverse_supplier_line)

                inverse_check_line = {
                    'name': _('Cheque Rechazado')+': '+(payment_line.name or '/'),
                    'account_id': def_check_account,
                    'move_id': move_id,
                    'partner_id': payment_line.partner_id.id,
                    'period_id': payment_line.period_id.id,
                    'date': self.reject_date,
                    'credit': 0,
                    'debit': payment_line.credit,
                    'amount_currency': payment_line.amount_currency,
                    'journal_id': original_move_data['journal_id'],
                    'currency_id': payment_line.currency_id.id,
                    'analytic_account_id': payment_line.analytic_account_id.id,
                    'ref': _('Rechazado Cheque')+': '+(payment_line.name or '/'),
                    'invoice_id': check.invoice_id.id or False,
                }
                move_line_obj.with_context(ctx)\
                    .create(inverse_check_line)
