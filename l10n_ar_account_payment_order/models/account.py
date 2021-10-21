##############################################################################
#   Copyright (c) 2018 Eynes/E-MIPS (www.eynes.com.ar)
#   License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
##############################################################################

from odoo import api, fields, models
from odoo.osv import expression


class AccountJournal(models.Model):
    _name = "account.journal"
    _inherit = "account.journal"

    code = fields.Char(
        string='Code', size=8, required=True,
        help="The code will be displayed on reports.")
    type = fields.Selection(selection=[
        ('sale_refund', 'Sale Refund'),
        ('purchase_refund', 'Purchase Refund'),
        ('purchase', 'Purchase'),
        ('receipt', 'Receipts'),
        ('sale', 'Sale'),
        ('cash', 'Cash'),
        ('general', 'General'),
        ('bank', 'Bank and Checks'),
        ('situation', 'Opening/Closing Situation'),
        ('payment', 'Payment')], string='Type', size=32, required=True,
        help="Select 'Sale' for customer invoices journals.\n\
              Select 'Purchase' for supplier invoices journals.\n\
              Select 'Cash' or 'Bank' for journals that are \
              used in customer or supplier payments.\n\
              Select 'General' for miscellaneous operations journals.\n\
              Select 'Opening/Closing Situation' for \
              entries generated for new fiscal years.\n\
              Select 'Receipt' for Receipt Vouchers.\n\
              Select 'Payment' for Payment Vouchers.")
    priority = fields.Integer()

    @api.model
    def create_sequence(self, vals):
        """
        Create new no_gap entry sequence for every new Joural
        """

        # Creacion de secuencia. Si es de tipo payment o receipt
        # la secuencia la armamos de otra manera
        journal_type = vals['type']

        if journal_type not in ['receipt', 'payment']:
            return super().create_sequence(vals)

        # in account.journal code is actually the prefix of the sequence
        # whereas ir.sequence code is a key to lookup global sequences.
        prefix = vals['code'].upper()

        seq = {
            'name': vals['name'],
            'implementation': 'no_gap',
            'prefix': prefix + '-',
            'padding': 8,
            'number_increment': 1
        }
        if 'company_id' in vals:
            seq['company_id'] = vals['company_id']
        sequence = self.env['ir.sequence'].create(seq)
        return sequence.id

    def open_action(self):
        # TODO: Search another way to do that, im overwriting the default method
        """return action based on type for related journals"""
        action_name = self._context.get('action_name', False)
        if not action_name:
            if self.type == 'bank':
                action_name = 'action_bank_statement_tree'
            elif self.type == 'cash':
                action_name = 'action_view_bank_statement_tree'
            elif self.type == 'sale':
                action_name = 'action_invoice_tree1'
                use_domain = expression.AND(
                    [self.env.context.get('use_domain', []), [('journal_id', '=', self.id)]]
                )
                self = self.with_context(use_domain=use_domain)
            elif self.type == 'purchase':
                action_name = 'action_vendor_bill_template'
                use_domain = expression.AND(
                    [self.env.context.get('use_domain', []), [('journal_id', '=', self.id)]]
                )
                self = self.with_context(use_domain=use_domain)
            else:
                action_name = 'action_move_journal_line'

        _journal_invoice_type_map = {
            ('sale', None): 'out_invoice',
            ('purchase', None): 'in_invoice',
            ('sale', 'refund'): 'out_refund',
            ('purchase', 'refund'): 'in_refund',
            ('bank', None): 'bank',
            ('cash', None): 'cash',
            ('general', None): 'general',
            ('payment', None): 'payment',
        }
        
        invoice_type = _journal_invoice_type_map[(self.type, self._context.get('invoice_type'))]

        ctx = self._context.copy()
        ctx.pop('group_by', None)
        ctx.update({
            'journal_type': self.type,
            'default_journal_id': self.id,
            'default_type': invoice_type,
            'type': invoice_type
        })

        [action] = self.env.ref('account.%s' % action_name).read()
        if not self.env.context.get('use_domain'):
            ctx['search_default_journal_id'] = self.id
        action['context'] = ctx
        action['domain'] = self._context.get('use_domain', [])
        account_invoice_filter = self.env.ref('account.view_account_invoice_filter', False)
        if action_name in ['action_invoice_tree1', 'action_vendor_bill_template']:
            action['search_view_id'] = account_invoice_filter and account_invoice_filter.id or False
        if action_name in ['action_bank_statement_tree', 'action_view_bank_statement_tree']:
            action['views'] = False
            action['view_id'] = False
        if self.type == 'purchase':
            new_help = self.env['account.invoice'].with_context(ctx).complete_empty_list_help()
            action.update({'help': (action.get('help') or '') + new_help})
        return action
