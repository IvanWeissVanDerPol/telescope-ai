import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from telescope_ai import SatelliteTracker, TelescopeConfig, MountController


@pytest.fixture
def config():
    return TelescopeConfig()


@pytest.fixture
def tracker(config):
    return SatelliteTracker(config)


class TestSatellite:
    def test_fetch_tle(self, tracker):
        result = tracker.fetch_tle()
        if result:
            assert len(tracker.get_available_satellites()) > 0

    def test_get_available(self, tracker):
        sats = tracker.get_available_satellites()
        assert isinstance(sats, list)

    def test_get_position_no_tle(self, tracker):
        pos = tracker.get_current_position("NONEXISTENT")
        assert pos is None

    def test_iss_pass_list(self, tracker):
        passes = tracker.get_iss_pass_times()
        assert isinstance(passes, list)

    def test_direction_names(self, tracker):
        assert tracker._direction_name(0) == "N"
        assert tracker._direction_name(90) == "E"
        assert tracker._direction_name(180) == "S"
        assert tracker._direction_name(270) == "W"
