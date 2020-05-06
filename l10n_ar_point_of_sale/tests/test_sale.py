import pytest
from odoo.exceptions import UserError, ValidationError, RedirectWarning
from odoo.tests.common import TransactionCase
from datetime import datetime, timedelta

class TestSale:

    def create_demo(self, ENV):
        partner = ENV.ref('base.res_partner_12')
        account_obj = ENV['account.account']
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
        return True

    def test_partner(self, ENV):
        self.create_demo(ENV)
        partner = ENV.ref('base.res_partner_12')
        sale_obj = ENV['sale.order']
        invoice_obj = ENV['account.invoice']
        pos_ar_obj = ENV['pos.ar']
        product = ENV.ref(
                'sale.advance_product_0')
        denomination = ENV.ref(
                'l10n_ar_point_of_sale.denomination_A')
        with pytest.raises(UserError,
                match=r".*You need to set up a Shop and/or a Fiscal.*"):
            so = sale_obj.create({
                'partner_id': partner.id,
                'date_order': datetime.today(),
                'partner_invoice_id': partner.id,
                'partner_invoice_id': partner.id,
                'partner_shipping_id': partner.id,
                'partner_shipping_id': partner.id,
                'warehouse_id': ENV.ref('stock.warehouse0').id,
                'order_line': [
                    (0, 0, {
                        'product_id': product.id,
                        'name': 'Test',
                        'price_unit': 12,
                    })
                ],
            })
            so.action_done()
            so.action_invoice_create()

        pos_ar = pos_ar_obj.create({
            'name': '0004',
            'priority': 1,
            'shop_id': ENV.ref('stock.warehouse0').id,
            'activity_start_date': datetime.today(),
            'denomination_ids': [
                (4, denomination.id, False)
            ]
        })
        so = sale_obj.create({
            'partner_id': partner.id,
            'date_order': datetime.today(),
            'partner_invoice_id': partner.id,
            'partner_invoice_id': partner.id,
            'partner_shipping_id': partner.id,
            'partner_shipping_id': partner.id,
            'warehouse_id': ENV.ref('stock.warehouse0').id,
            'order_line': [
                (0, 0, {
                    'product_id': product.id,
                    'name': 'Test',
                    'price_unit': 12,
                })
            ],
        })
        so.action_done()
        invoice_id = so.action_invoice_create()
        invoice = invoice_obj.browse(invoice_id)
        assert invoice.denomination_id.id == denomination.id
