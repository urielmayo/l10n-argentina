import pytest

# stock_picking
@pytest.fixture
def SP(env):
    return env['stock.picking']

# cancel_picking_done
@pytest.fixture
def CPD(env):
    return env['cancel.picking.done']
