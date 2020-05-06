import pytest

@pytest.fixture
def ENV(env):
    return env


@pytest.fixture
def FY(env):
    return env['account.fiscal.year']

@pytest.fixture
def INV(env):
    return env['account.invoice']

@pytest.fixture
def ENV(env):
    return env

@pytest.fixture
def MV(env):
    return env['account.move']

@pytest.fixture
def MVL(env):
    return env['account.move.line']
