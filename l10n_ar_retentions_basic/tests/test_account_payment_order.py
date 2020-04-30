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

    def create_retention_tax_line(self, env):
        tax = env.ref('l10n_generic_coa.sale_tax_template')
        account = env.ref('l10n_generic_coa.1_a_capital')
        retention_id = self._create_retention(env, tax.id, 'vat').id
        retention = self._create_retention_tax_line(
            env, retention_id, account_id=account.id, amount=40)
        return retention

    def create_account_payment_order(self, env):
        partner = env.ref('base.res_partner_3')
        journal = self._create_account_journal(env, 'Journal', 'sale', 'STK00')
        retention = self.create_retention_tax_line(env)
        voucher = self._create_account_payment_order(
            env, partner.id, journal.id)
        retention.payment_order_id = voucher
        return voucher

    def test_01_get_retentions_amount(self, env):
        voucher = self.create_account_payment_order(env)
        # This only returns the sum of the amount of the retentions
        res = voucher.get_retentions_amount()
        assert res == 40

    def test_01_payment_order_amount_hook(self, env):
        voucher = self.create_account_payment_order(env)
        # This only returns the sum of the amount of the retention
        # lines plus the sum of the amount of the payment method lines
        res = voucher.payment_order_amount_hook()
        assert res == 40

    def test_01_onchange_retentions(self, env):
        voucher = self.create_account_payment_order(env)
        voucher._onchange_retentions()
        # _onchange_retentions() assign the amount obtained in
        # payment_order_amount_hook() to voucher amount
        assert voucher.amount == 40

    def test_01_prepare_retention_values(self, env):
        voucher = self.create_account_payment_order(env)
        res = voucher.prepare_retention_values(voucher)
        assert res['voucher_number'] == voucher.number
        assert res['partner_id'] == voucher.partner_id.id
