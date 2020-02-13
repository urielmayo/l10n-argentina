import pytest
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase
from odoo.addons.base.models import ir_sequence


class TestStockPicking:

    def create_sequence(self, env):
        ir_sequence_obj = env['ir.sequence']
        return ir_sequence_obj.create({
            'code': 'test_sequence_type',
            'name': 'Test sequence',
        })

    def create_stock_picking_type(self, env):
        sequence_id = self.create_sequence(env).id
        stock_type_obj = env['stock.picking.type']
        return stock_type_obj.create({
            'name': 'Manufacturing',
            'code': 'internal',
            'sequence_id': sequence_id,
            'sequence_transfer_id': sequence_id
        })

    def create_stock_picking(self, SP, env):
        stock_location = env.ref('stock.stock_location_stock')
        customer_location = env.ref('stock.stock_location_customers')
        partner = env['res.partner'].create({'name': 'xxx'})
        picking_type_id = self.create_stock_picking_type(env).id
        return SP.create({
            'location_id': stock_location.id,
            'location_dest_id': customer_location.id,
            'partner_id': partner.id,
            'picking_type_id': picking_type_id,
        })

    def test_action_done(self, SP, env, mocker):
        stock_picking = self.create_stock_picking(SP, env)
        name_original = stock_picking.name
        sequence_id = stock_picking.picking_type_id.sequence_transfer_id.id
        if sequence_id > 99:
            future_code = ir_sequence._predict_nextval(SP, str(sequence_id))
        else:
            future_code = ir_sequence._predict_nextval(
                SP, '0' + str(sequence_id)
            )
        stock_picking.action_done()
        assert stock_picking.name_original == name_original
        assert stock_picking.name == str(future_code)
