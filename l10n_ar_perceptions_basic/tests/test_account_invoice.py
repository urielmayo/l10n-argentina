import random, string, pytest
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase
from odoo.addons.base.models import ir_sequence
from .test_perception_tax_line import TestPerceptionTaxLine
from odoo import fields


class TestAccountInvoice:

    def name_generator(self):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(6))

    def create_perception_tax_line(self, env, invoice_id):
        TPTL = TestPerceptionTaxLine()
        res = TPTL.create_perception_tax_line(env, w_invoice=invoice_id)
        return res

    def create_account_invoice(self, env):
        account_invoice_obj = env['account.invoice']
        return account_invoice_obj.create({
            'name': self.name_generator(),
        })
    def create_accounts(self, env):
        account_type_obj = env['account.account.type']
        account_obj = env['account.account']
        account_type = account_type_obj.create({
            'name': 'RCV type',
            'type': 'receivable'
        })
        account_payable = account_obj.create({
            'code': 'X1111',
            'name': 'HR Expense - Test Payable Account',
            'user_type_id': env.ref('account.data_account_type_payable').id,
            'reconcile': True
        })
        account_receiv = account_obj.create({
            'name': 'Receivable',
            'code': 'RCV00',
            'user_type_id': account_type.id,
            'reconcile': True
        })
        return account_payable, account_receiv

    def test_onchange_partner_id(self, env, PTL):
        account_invoice = self.create_account_invoice(env)
        perception = self.create_perception_tax_line(env, account_invoice.id)
        account_payable, account_receiv = self.create_accounts(env)
        partner = env.ref('base.res_partner_1')
        partner.property_account_payable_id = account_payable
        partner.property_account_receivable_id = account_receiv
        account_invoice.write({
            'partner_id': partner.id
        })
        account_invoice._onchange_partner_id()
        # _onchange_partner_id is supposed to set
        # the new partner on all related perceptions (perception.tax.line).
        # here we assert if the related perception has the new partner
        assert perception.partner_id == partner

    def test_onchange_perception_ids(self, env):
        account_invoice = self.create_account_invoice(env)
        perception = self.create_perception_tax_line(env, account_invoice.id)
        account_invoice._onchange_perception_ids()
        tax_line_name = account_invoice.tax_line_ids.mapped('name')
        assert perception.name in tax_line_name

    def test_finalize_invoice_move_lines(self, env):
        account_invoice = self.create_account_invoice(env)
        perception = self.create_perception_tax_line(env, account_invoice.id)
        # we make sure he does not have date
        assert not perception.date
        account_invoice.finalize_invoice_move_lines({})
        # if the perception of account invoice does not have
        # date_invoice this function will create one with current date
        assert perception.date == fields.Date.context_today(account_invoice)
        perception.date = False
        account_invoice.date_invoice = '2019-06-27'
        account_invoice.finalize_invoice_move_lines({})
        # and then we assert that the perception date is the same
        # as the date_invoice of account_invoice
        assert perception.date == account_invoice.date_invoice
