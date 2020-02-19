import pytest

@pytest.fixture
def DP(env):
    return env['date.period']


@pytest.fixture
def FY(env):
    return env['account.fiscal.year']

