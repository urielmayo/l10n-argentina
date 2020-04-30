import random
import string


class TestRetentionTaxLine:

    def name_generator(self):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(6))

    def _create_retention(self, env, tax_id, type, name=False,
                          type_tax_use=False, state_id=False,
                          jurisdiccion=False):
        retention_obj = env['retention.retention']
        return retention_obj.create({
            'name': name or self.name_generator(),
            'tax_id': tax_id,
            'type': type,
            'type_tax_use': type_tax_use,
            'state_id': state_id,
            'jurisdiccion': jurisdiccion
        })

    def _create_retention_tax_line(self, env, retention_id, date=False,
                                   certificate_no=False, base=False,
                                   amount=False, account_id=False,
                                   payment_order_id=False):
        retention_obj = env['retention.tax.line']
        return retention_obj.create({
            'retention_id': retention_id,
            'date': date,
            'certificate_no': certificate_no,
            'base': base,
            'amount': amount,
            'account_id': account_id,
            'payment_order_id': payment_order_id,
        })

    def _create_account_payment_order(self, env, partner_id, journal_id,
                                      date=False):
        payment_order_obj = env['account.payment.order']
        return payment_order_obj.create({
            'partner_id': partner_id,
            'journal_id': journal_id,
            'date': date,
        })

    def _create_account_journal(self, env, name, type, code):
        journal_obj = env['account.journal']
        return journal_obj.create({
            'name': name,
            'type': type,
            'code': code
        })

    def test_create_retention_tax_line(self, env):
        tax = env.ref('l10n_generic_coa.sale_tax_template')
        account = env.ref('l10n_generic_coa.1_a_capital')
        partner = env.ref('base.res_partner_3')
        journal = self._create_account_journal(env, 'Journal', 'sale', 'STK00')
        retention_id = self._create_retention(env, tax.id, 'vat').id
        voucher = self._create_account_payment_order(
            env, partner.id, journal.id, date='30/04/2020')
        retention = self._create_retention_tax_line(
            env, retention_id, account_id=account.id,
            payment_order_id=voucher.id)
        return retention

    def test_01_create_voucher_move_line(self, env):
        retention = self.test_create_retention_tax_line(env)
        retention.amount = 1

        retention.payment_order_id.type = 'sale'
        res = retention.create_voucher_move_line()
        assert retention.date == retention.payment_order_id.date
        assert res['debit'] == 1
        assert res['credit'] == 0

        retention.amount = -1

        # if the credit is negative it becomes 0
        # and the debit will become the credit but positive
        # The same backwards

        retention.payment_order_id.type = 'sale'

        res = retention.create_voucher_move_line()
        assert res['debit'] == 0
        assert res['credit'] == 1

    def test_02_create_voucher_move_line(self, env):
        retention = self.test_create_retention_tax_line(env)

        retention.amount = 1

        retention.payment_order_id.type = 'purchase'
        res = retention.create_voucher_move_line()
        assert retention.date == retention.payment_order_id.date
        assert res['debit'] == 0
        assert res['credit'] == 1

        retention.amount = -1

        # if the credit is negative it becomes 0
        # and the debit will become the credit but positive
        # The same backwards

        res = retention.create_voucher_move_line()
        assert res['debit'] == 1
        assert res['credit'] == 0

    def test_03_create_voucher_move_line(self, env):
        retention = self.test_create_retention_tax_line(env)

        # if retetion.tax.line has 0 amount the function return {}
        retention.amount = 0
        res = retention.create_voucher_move_line()
        assert res == {}

    def test_01_onchange_retention(self, env):
        retention_tax_line = self.test_create_retention_tax_line(env)
        retention = retention_tax_line.retention_id
        retention_tax_line._onchange_retention()

        assert retention_tax_line.name == retention.name
        assert retention_tax_line.account_id == retention.tax_id.account_id

        # if retention does not have state_id will set
        # the state_id of retention.tax.line on false

        assert not retention_tax_line.state_id

        state = env.ref('base.state_ar_t')
        retention.state_id = state
        retention_tax_line._onchange_retention()

        assert retention_tax_line.state_id == retention.state_id
