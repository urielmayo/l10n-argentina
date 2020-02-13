import pytest
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase
from odoo.addons.base.models import ir_sequence


class TestCancelStockPicking:

    def create_cancel_picking(self, CPD, next_action):
        return CPD.create({
            'reason': 'Some reason',
            'next_action': next_action,
        })

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

    def create_stock_picking(self, SP, env, qty=1):
        stock_location = env.ref('stock.stock_location_stock')
        customer_location = env.ref('stock.stock_location_customers')
        partner = env['res.partner'].create({'name': 'xxx'})
        picking_type_id = self.create_stock_picking_type(env).id
        if qty > 1:
            stocks = []
            for i in range(qty):
                stocks.append(SP.create({
                    'name': i + 10 * i,
                    'location_id': stock_location.id,
                    'location_dest_id': customer_location.id,
                    'partner_id': partner.id,
                    'picking_type_id': picking_type_id,
                }))
            return stocks
        return SP.create({
            'location_id': stock_location.id,
            'location_dest_id': customer_location.id,
            'partner_id': partner.id,
            'picking_type_id': picking_type_id,
        })

    def create_stock_move(self, stock_picking, env, qty=1):
        stock_move_obj = env['stock.move']
        product_obj = env['product.product']
        unit = env.ref("uom.product_uom_unit")
        product = product_obj.create({
            'name': 'Usb Keyboard',
            'type': 'product',
            'uom_id': unit.id
        })
        for i in range(qty):
            stock_move_obj.create({
                'name': 'name',
                'picking_id': stock_picking.id,
                'product_id': product.id,
                'product_uom': unit.id,
                'location_id': env.ref('stock.stock_location_stock').id,
                'location_dest_id': env.ref('stock.stock_location_customers').id
            })

    def test_create_returns_cancel(self, SP, CPD, env, mocker):
        cancel_picking = self.create_cancel_picking(CPD, 'cancel')
        stock_picking = self.create_stock_picking(SP, env)
        self.create_stock_move(stock_picking, env)
        cancel_picking.with_context({
            'active_id': stock_picking.id
        }).create_returns()
        assert stock_picking.state == 'cancel'
        assert not stock_picking.renum_pick_id
        for line in stock_picking.move_lines:
            assert line.state == 'cancel'

    def test_create_returns_renumerate(self, SP, CPD, env, mocker):
        cancel_picking = self.create_cancel_picking(CPD, 'renumerate')
        stock_picking = self.create_stock_picking(SP, env)
        self.create_stock_move(stock_picking, env, 2)
        assert not stock_picking.renum_pick_id
        res = cancel_picking.with_context({
            'active_id': stock_picking.id
        }).create_returns()
        form = env.ref('stock.view_picking_form')
        assert stock_picking.state == 'cancel'
        assert stock_picking.renum_pick_id.id == stock_picking.id + 1
        for line in stock_picking.move_lines:
            assert line.state == 'cancel'
        assert res['res_model'] == 'stock.picking' and \
            res['type'] == 'ir.actions.act_window' and \
            res['res_id'] == stock_picking.id + 1 and \
            res['view_id'] == form.id

    def test_create_returns_w_2_stock_picking(self, SP, CPD, env, mocker):
        cancel_picking = self.create_cancel_picking(CPD, 'renumerate')
        stock_picking = self.create_stock_picking(SP, env, 2)
        assert not stock_picking[0].renum_pick_id
        assert not stock_picking[1].renum_pick_id
        res = cancel_picking.with_context({
            'active_id': [stock_picking[0].id, stock_picking[1].id]
        }).create_returns()
        form = env.ref('stock.view_picking_form')
        tree = env.ref('stock.action_picking_tree')
        assert stock_picking[0].state == 'cancel'
        assert stock_picking[1].state == 'cancel'
        assert not stock_picking[0].renum_pick_id.id == stock_picking[0].id + 1
        assert not stock_picking[1].renum_pick_id.id == stock_picking[1].id + 1
        assert res['res_model'] == 'stock.picking' and \
            res['type'] == 'ir.actions.act_window' and \
            res['views'] == [(tree.id, 'tree'), (form.id, 'form')] and \
            res['domain'] == [('id', 'in', [
                stock_picking[0].id + 2, stock_picking[1].id + 2
            ])]
