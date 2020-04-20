import pytest
from odoo.exceptions import UserError, ValidationError

class TestFiscalPosition:

    def test_duplicated_fp(self, ENV):
        denomination = ENV.ref(
                'l10n_ar_point_of_sale.denomination_A')
        fiscal_position_obj = ENV['account.fiscal.position']
        fiscal_position_obj.create({
            'denomination_id': denomination.id,
            'denom_supplier_id': denomination.id,
            'name': 'TESTRI'
        })
        with pytest.raises(ValidationError,
                match=r".*fiscal position is duplicated.*"):
            fiscal_position_obj.create({
                'denomination_id': denomination.id,
                'denom_supplier_id': denomination.id,
                'name': 'TESTRI'
            })

        with pytest.raises(ValidationError,
                match=r".*fiscal position is duplicated.*"):
            fiscal_position_obj.create({
                'denomination_id': denomination.id,
                'denom_supplier_id': denomination.id,
                'name': '   TeStRi   '
            })

        fiscal_position_obj.create({
            'denomination_id': denomination.id,
            'denom_supplier_id': denomination.id,
            'name': 'TESTRI2'
        })
        return True

    def test_unlink_fp(self, ENV):
        partner = ENV.ref('base.res_partner_12')
        account_obj = ENV['account.account']
        invoice_obj = ENV['account.invoice']
        journal_obj = ENV['account.journal']
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
        acc_other  = account_obj.create({
            'code': '1234',
            'name': 'Other',
            'user_type_id': other_type.id,
            'reconcile': True,
        })
        partner.write({
            'property_account_receivable_id': acc_receivable.id,
            'property_account_payable_id': acc_payable.id,
            'property_account_position_id': position.id,
        })
        journal = journal_obj.create({
            'name': 'Sales Journal',
            'type': 'sale',
            'code': 'TEST',
        })
        invoice = invoice_obj.create({
            'partner_id': partner.id,
            'journal_id': journal.id,
            'fiscal_position_id': position.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': product.id,
                    'account_id': acc_other.id,
                    'name': 'Test',
                    'price_unit': 1,

                })
            ]
        })
        invoice._onchange_partner_id()
        with pytest.raises(ValidationError,
                match=r".*You can not unlink a fiscal position.*"):
            position.unlink()
        invoice.unlink()
        position.unlink()
        return True
