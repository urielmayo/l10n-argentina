import random, string, pytest
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase
from odoo.addons.base.models import ir_sequence
from .test_perception_tax_line import TestPerceptionTaxLine
from odoo import fields


class TestPerception:

    def name_generator(self):
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(6))

    def create_perception_tax_line(self, env, w_invoice=False, perception=False):
        TPTL = TestPerceptionTaxLine()
        return TPTL.create_perception_tax_line(env, perception=perception)

    def create_perception(self, env):
        TPTL = TestPerceptionTaxLine()
        return TPTL.create_perception(env)

    def test_unlink(self, env):
        perception = self.create_perception(env)
        with pytest.raises(UserError, match='.*Can not delete the record.*'):
            tax_line = self.create_perception_tax_line(env, perception=perception)
            perception.unlink()
        tax_line.perception_id = self.create_perception(env)
        perception.unlink()
