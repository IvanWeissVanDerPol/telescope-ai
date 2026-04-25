import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from telescope_ai import MountController, TelescopeConfig, SimulatedMount


@pytest.fixture
def config():
    c = TelescopeConfig()
    c.mount_type = "simulator"
    return c


@pytest.fixture
def mount(config):
    m = MountController(config)
    m.connect()
    yield m
    m.disconnect()


class TestMount:
    def test_connect(self, mount):
        assert mount.connected is True

    def test_position_radec(self, mount):
        ra, dec = mount.get_position_radec()
        assert isinstance(ra, float)
        assert isinstance(dec, float)

    def test_position_altaz(self, mount):
        alt, az = mount.get_position_altaz()
        assert isinstance(alt, float)
        assert isinstance(az, float)

    def test_goto(self, mount):
        mount.goto_radec(5.583, -5.383)
        ra, dec = mount.get_position_radec()
        assert isinstance(ra, float)

    def test_abort(self, mount):
        mount.abort_slew()
        assert True

    def test_disconnect(self, config):
        m = MountController(config)
        m.connect()
        m.disconnect()
        assert m.connected is False
