import pytest

# stock_picking
@pytest.fixture
def PTL(env):
    return env['perception.tax.line']

# cancel_picking_done
@pytest.fixture
def AI(env):
    return env['account.invoice']
