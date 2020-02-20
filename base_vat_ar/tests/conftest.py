import pytest


@pytest.fixture
def DCC(env):
    return env['dst_cuit.codes']


@pytest.fixture
def RDT(env):
    return env['res.document.type']


@pytest.fixture
def RP(env):
    return env['res.partner']


@pytest.fixture
def RCS(env):
    return env['res.country.state']
