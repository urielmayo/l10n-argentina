import pytest
from odoo.exceptions import UserError, ValidationError, RedirectWarning
from odoo.tests.common import TransactionCase
from datetime import datetime, timedelta
import time

class TestInvoice:

    def initialize_demo(self, ENV):
        account_obj = ENV['account.account']
        invoice_obj = ENV['account.invoice']
        journal_obj = ENV['account.journal']
        pos_ar_obj = ENV['pos.ar']
        denomination = ENV.ref(
                'l10n_ar_point_of_sale.denomination_A')
        receivable_type = ENV.ref(
                'account.data_account_type_receivable')
        payable_type = ENV.ref(
                'account.data_account_type_payable')
        other_type = ENV.ref(
                'account.data_account_type_other_income')
        position = ENV.ref(
                'l10n_ar_point_of_sale.fiscal_position_ri')
        product = ENV.ref(
                'sale.advance_product_0')
        partner = ENV.ref('base.res_partner_12')
        acc_payable = account_obj.create({
            'code': '1233',
            'name': 'Payable',
            'user_type_id': payable_type.id,
            'reconcile': True,
        })
        acc_receivable = account_obj.create({
            'code': '12333',
            'name': 'Receivable',
            'user_type_id': receivable_type.id,
            'reconcile': True,
        })
        partner.write({
            'property_account_receivable_id': acc_receivable.id,
            'property_account_payable_id': acc_payable.id,
            'property_account_position_id': position.id,
        })
        pos_ar = pos_ar_obj.create({
            'name': '0004',
            'priority': 1,
            'shop_id': ENV.ref('stock.warehouse0').id,
            'activity_start_date': datetime.today(),
            'denomination_ids': [
                (4, denomination.id, False)
            ]
        })
        journal = journal_obj.create({
            'name': 'Sales Journal',
            'type': 'sale',
            'code': 'TEST',
        })
        return True

    def get_invoice_vals(self, ENV):
        account_obj = ENV['account.account']
        invoice_obj = ENV['account.invoice']
        product = ENV.ref(
                'sale.advance_product_0')
        partner = ENV.ref('base.res_partner_12')
        denomination = ENV.ref(
                'l10n_ar_point_of_sale.denomination_A')
        other_type = ENV.ref(
                'account.data_account_type_other_income')
        acc_other  = account_obj.create({
            'code': '1234',
            'name': 'Other',
            'user_type_id': other_type.id,
            'reconcile': True,
        })
        invoice_vals = {
            'partner_id': partner.id,
            'type': 'out_invoice',
            'internal_number': '0001-00000001',
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': product.id,
                    'account_id': acc_other.id,
                    'name': 'Test',
                    'price_unit': 1,
                    'quantity': 1,
                })
            ]
        }
        return invoice_vals


    def test_duplicated_out_invoice(self, ENV):
        self.initialize_demo(ENV)
        invoice_obj = ENV['account.invoice']
        pos_ar_obj = ENV['pos.ar']
        invoice_vals = self.get_invoice_vals(ENV)
        invoice = invoice_obj.create(invoice_vals.copy())
        invoice._onchange_partner_id()

        denomination = ENV.ref(
                'l10n_ar_point_of_sale.denomination_A')
        with pytest.raises(ValidationError,
                match=r".*The Invoice is duplicated.*"):
            invoice = invoice_obj.create(invoice_vals.copy())
            invoice._onchange_partner_id()

        invoice_vals.update({
            'is_debit_note': True,
        })
        invoice = invoice_obj.create(invoice_vals.copy())
        invoice._onchange_partner_id()

        with pytest.raises(ValidationError,
                match=r".*The Invoice is duplicated.*"):
            invoice = invoice_obj.create(invoice_vals.copy())
            invoice._onchange_partner_id()

        pos_ar = pos_ar_obj.create({
            'name': '0005',
            'priority': 1,
            'shop_id': ENV.ref('stock.warehouse0').id,
            'activity_start_date': datetime.today(),
            'denomination_ids': [
                (4, denomination.id, False)
            ]
        })

        invoice_vals.update({
            'is_debit_note': False,
            'pos_ar_id': pos_ar.id,
        })
        invoice = invoice_obj.create(invoice_vals.copy())
        with pytest.raises(ValidationError,
                match=r".*The Invoice is duplicated.*"):
            invoice = invoice_obj.create(invoice_vals.copy())

        invoice_vals.update({
            'denomination_id': denomination.id,
        })
        invoice = invoice_obj.create(invoice_vals.copy())
        with pytest.raises(ValidationError,
                match=r".*The Invoice is duplicated.*"):
            invoice = invoice_obj.create(invoice_vals.copy())

        invoice_vals.update({
            'type': 'out_refund',
        })
        invoice = invoice_obj.create(invoice_vals.copy())
        with pytest.raises(ValidationError,
                match=r".*The Invoice is duplicated.*"):
            invoice = invoice_obj.create(invoice_vals.copy())
        return True

    def test_duplicated_in_invoice(self, ENV):
        self.initialize_demo(ENV)
        invoice_obj = ENV['account.invoice']
        pos_ar_obj = ENV['pos.ar']
        partner = ENV.ref('base.res_partner_12')
        invoice_vals = self.get_invoice_vals(ENV)
        invoice_vals.update({
            'type': 'in_invoice',
            'fiscal_position_id': partner.property_account_position_id.id,
        })
        invoice = invoice_obj.create(invoice_vals.copy())
        invoice._onchange_partner_id()

        denomination = ENV.ref(
                'l10n_ar_point_of_sale.denomination_A')
        with pytest.raises(ValidationError,
                match=r".*The Invoice is duplicated.*"):
            invoice = invoice_obj.create(invoice_vals.copy())
            invoice._onchange_partner_id()

        invoice_vals.update({
            'is_debit_note': True,
        })
        invoice = invoice_obj.create(invoice_vals.copy())
        invoice._onchange_partner_id()

        with pytest.raises(ValidationError,
                match=r".*The Invoice is duplicated.*"):
            invoice = invoice_obj.create(invoice_vals.copy())
            invoice._onchange_partner_id()

        pos_ar = pos_ar_obj.create({
            'name': '0005',
            'priority': 1,
            'shop_id': ENV.ref('stock.warehouse0').id,
            'activity_start_date': datetime.today(),
            'denomination_ids': [
                (4, denomination.id, False)
            ]
        })

        invoice_vals.update({
            'is_debit_note': False,
            'pos_ar_id': pos_ar.id,
        })
        invoice = invoice_obj.create(invoice_vals.copy())
        with pytest.raises(ValidationError,
                match=r".*The Invoice is duplicated.*"):
            invoice = invoice_obj.create(invoice_vals.copy())

        denomination = ENV.ref(
                'l10n_ar_point_of_sale.denomination_M')
        invoice_vals.update({
            'denomination_id': denomination.id,
        })
        invoice = invoice_obj.create(invoice_vals.copy())
        with pytest.raises(ValidationError,
                match=r".*The Invoice is duplicated.*"):
            invoice = invoice_obj.create(invoice_vals.copy())

        invoice_vals.update({
            'type': 'in_refund',
        })
        invoice = invoice_obj.create(invoice_vals.copy())
        with pytest.raises(ValidationError,
                match=r".*The Invoice is duplicated.*"):
            invoice = invoice_obj.create(invoice_vals.copy())
        return True

    def test_fiscal_values(self, ENV):
        self.initialize_demo(ENV)
        invoice_obj = ENV['account.invoice']
        pos_ar_obj = ENV['pos.ar']
        invoice_vals = self.get_invoice_vals(ENV)
        invoice = invoice_obj.create(invoice_vals.copy())
        with pytest.raises(ValidationError,
                match=r".*Denomination not set in invoice.*"):
            invoice._onchange_partner_id()
            invoice.write({
                'denomination_id': False
            })
            invoice.action_invoice_open()
        invoice.unlink()
        invoice = invoice_obj.create(invoice_vals.copy())
        with pytest.raises(ValidationError,
                match=r".*You have to select a Point of Sale.*"):
            invoice._onchange_partner_id()
            invoice.write({
                'pos_ar_id': False
            })
            invoice.action_invoice_open()
        invoice.unlink()
        invoice = invoice_obj.create(invoice_vals.copy())
        with pytest.raises(ValidationError,
                match=r".*has not the same denomination as the invoice.*"):
            invoice._onchange_partner_id()
            denomination = ENV.ref(
                'l10n_ar_point_of_sale.denomination_M')
            invoice.write({
                'denomination_id': denomination.id,
            })
            invoice.action_invoice_open()
        return True

    def test_fiscal_values_supp(self, ENV):
        self.initialize_demo(ENV)
        invoice_obj = ENV['account.invoice']
        pos_ar_obj = ENV['pos.ar']
        invoice_vals = self.get_invoice_vals(ENV)
        invoice_vals.update({
            'type': 'in_invoice',
        })
        invoice = invoice_obj.create(invoice_vals.copy())
        denomination = ENV.ref(
                'l10n_ar_point_of_sale.denomination_M')
        with pytest.raises(ValidationError,
                match=r".*Denomination not set in invoice.*"):
            invoice._onchange_partner_id()
            invoice.write({
                'denomination_id': False
            })
            invoice.action_invoice_open()
        invoice.unlink()
        invoice = invoice_obj.create(invoice_vals.copy())
        with pytest.raises(ValidationError,
                match=r".*corresponds with this fiscal position.*"):
            invoice._onchange_partner_id()
            invoice.write({
                'denomination_id': denomination.id
            })
            invoice.action_invoice_open()
        invoice.unlink()
        invoice = invoice_obj.create(invoice_vals.copy())
        return True

    def test_cancel_state(self, ENV):
        self.initialize_demo(ENV)
        invoice_obj = ENV['account.invoice']
        pos_ar_obj = ENV['pos.ar']
        journal_obj = ENV['account.journal']
        payment_obj = ENV['account.payment']
        invoice_vals = self.get_invoice_vals(ENV)
        invoice_vals.update({
            'type': 'out_refund',
        })
        invoice = invoice_obj.create(invoice_vals.copy())
        invoice._onchange_partner_id()
        invoice.action_cancel()
        return True

    def test_invoice_cancel(self, ENV):
        self.initialize_demo(ENV)
        invoice_obj = ENV['account.invoice']
        pos_ar_obj = ENV['pos.ar']
        journal_obj = ENV['account.journal']
        payment_obj = ENV['account.payment']
        invoice_vals = self.get_invoice_vals(ENV)
        invoice_vals.update({
            'type': 'out_refund',
        })
        invoice = invoice_obj.create(invoice_vals.copy())
        invoice._onchange_partner_id()
        invoice.action_invoice_open()
        bank_journal = journal_obj.create({
            'name': 'Bank',
            'type': 'bank',
            'code': 'BNK67'
        })
        payment_method_manual_out = ENV.ref("account.account_payment_method_manual_out")
        wz = payment_obj.create({
            'payment_date': time.strftime('%Y') + '-07-15',
            'payment_type': 'transfer',
            'amount': 1,
            'currency_id': ENV.user.company_id.currency_id.id,
            'journal_id': bank_journal.id,
            'destination_journal_id': bank_journal.id,
            'payment_method_id': payment_method_manual_out.id,
            'invoice_ids': [(4, invoice.id, False)]
        })
        wz.action_validate_invoice_payment()
        with pytest.raises(ValidationError,
                match=r".*Credit Note can only be cancelled in these.*"):
            invoice.action_cancel()

        inv_refunds = invoice.refund()
        for inv_refund in inv_refunds:
            assert inv_refund.pos_ar_id.id == invoice.pos_ar_id.id
            assert inv_refund.denomination_id.id == invoice.denomination_id.id
        return True

    def test_check_number(self, ENV):
        self.initialize_demo(ENV)
        invoice_obj = ENV['account.invoice']
        invoice_vals = self.get_invoice_vals(ENV)
        # invoice_vals.update({
        #     'internal_number': '',
        # })
        # with pytest.raises(ValidationError,
        #         match=r".*The Invoice Number should be filled.*"):
        #     invoice = invoice_obj.create(invoice_vals.copy())
        #     invoice._onchange_partner_id()
        #     invoice.action_invoice_open()

        #Bad Sequence
        invoice_vals.update({
            'internal_number': '0001-0000001',
        })
        invoice = invoice_obj.create(invoice_vals.copy())
        with pytest.raises(ValidationError,
                match=r".*The Invoice Number should be the format.*"):
            invoice._onchange_partner_id()
            invoice.action_invoice_open()

        #Good Sequence
        invoice.write({
            'internal_number': '0001-00000001',
        })
        invoice.action_invoice_open()

        #Bad Sequence
        invoice_vals.update({
            'internal_number': '0001-0000001',
            'type': 'out_refund',
        })
        invoice = invoice_obj.create(invoice_vals.copy())
        with pytest.raises(ValidationError,
                match=r".*The Invoice Number should be the format.*"):
            invoice._onchange_partner_id()
            invoice.action_invoice_open()

        #Good Sequence
        invoice.write({
            'internal_number': '0001-00000001',
        })
        invoice.action_invoice_open()

        #-----------Supplier Invoice---------------#
        invoice_vals.update({
            'internal_number': '',
            'type': 'in_invoice',
        })
        with pytest.raises(ValidationError,
                match=r".*The Invoice Number should be filled.*"):
            invoice = invoice_obj.create(invoice_vals.copy())
            invoice._onchange_partner_id()
            invoice.action_invoice_open()

        with pytest.raises(ValidationError,
                match=r".*The Invoice Number should be the format.*"):
            invoice.write({
                'internal_number': '0001-0000001',
            })
            invoice.action_invoice_open()

        invoice.write({
            'internal_number': '0001-00000001',
        })
        invoice.action_invoice_open()
        return True

