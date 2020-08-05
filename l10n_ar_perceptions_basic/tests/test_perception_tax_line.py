import random, string, pytest
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase
from odoo.addons.base.models import ir_sequence


class TestPerceptionTaxLine:

    def name_generator(self):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(6))

    def create_account(self, env):
        account_obj = env['account.account']
        n = random.uniform(1, 100)
        return account_obj.create({
            'name': self.name_generator(),
            'code': n,
            'user_type_id': env.ref('account.data_account_type_non_current_liabilities').id
        })

    def create_account_tax(self, env):
        tax_obj = env['account.tax']
        return tax_obj.create({
            'name': self.name_generator(),
            'account_id': self.create_account(env).id,
            'amount': 21
        })

    def create_perception(self, env):
        perception_obj = env['perception.perception']
        state_obj = env['res.country.state']
        state_id = state_obj.browse(4).id
        return perception_obj.create({
            'name': self.name_generator(),
            'tax_id': self.create_account_tax(env).id,
            'type_tax_use': 'sale',
            'state_id': state_id
        })

    def create_perception_tax_line(self, env, w_invoice=False, perception=False):
        perception_tax_line = env['perception.tax.line']
        vals = {
            'name': self.name_generator(),
            'perception_id': self.create_perception(env).id,
            'partner_id': env.ref("base.res_partner_3").id,
            'account_id': self.create_account(env).id
        }
        if w_invoice:
            vals['invoice_id'] = w_invoice
        if perception:
            vals['perception_id'] = perception.id
        return perception_tax_line.create(vals)

    def test_onchange_perception(self, env, PTL):
        perception_tax_line = self.create_perception_tax_line(env)
        name = perception_tax_line.perception_id.name
        account_id = perception_tax_line.perception_id.tax_id.account_id
        state_id = perception_tax_line.perception_id.state_id
        perception_tax_line._onchange_perception()
        # _onchange_perception() is supposed to set
        # name, account_id and state_id of the
        # perception of perception_tax_line
        assert perception_tax_line.name == name
        assert perception_tax_line.account_id == account_id
        assert perception_tax_line.state_id == state_id

    def test_compute_all(self, env, PTL):
        perception_tax_line = self.create_perception_tax_line(env)
        taxes = perception_tax_line.compute_all()
        values = {
            'id': perception_tax_line.perception_id.tax_id.id,
            'name': perception_tax_line.name,
            'amount': perception_tax_line.amount,
            'base': perception_tax_line.base,
            'account_id': perception_tax_line.account_id.id
        }
        # compute_all() is supposed to return
        # a list of dictionaries with
        # taxes information
        assert taxes[0] == values
