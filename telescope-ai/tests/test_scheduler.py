import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import pytest
from telescope_ai import NightScheduler, WeatherService, TelescopeConfig


@pytest.fixture
def config():
    return TelescopeConfig()


@pytest.fixture
def weather(config):
    return WeatherService(config)


@pytest.fixture
def scheduler(config, weather):
    return NightScheduler(config, weather)


class TestScheduler:
    def test_generate_plan(self, scheduler):
        plan = scheduler.generate_plan(max_targets=3)
        assert len(plan) <= 3
        for item in plan:
            assert item.target.name
            assert item.target.object_type
            assert isinstance(item.altitude, float)
            assert isinstance(item.priority, int)
            assert item.reason

    def test_plan_ordering(self, scheduler):
        plan = scheduler.generate_plan(max_targets=10)
        priorities = [p.priority for p in plan]
        assert priorities == sorted(priorities)

    def test_add_target(self, scheduler):
        from telescope_ai.scheduler import Target
        t = Target("Test", 0, 0, 10, "test")
        scheduler.add_target(t)
        assert len(scheduler._targets) == 16

    def test_load_defaults(self, scheduler):
        assert len(scheduler._targets) == 15

    def test_moon_phase(self, scheduler):
        phase = scheduler._get_moon_phase()
        assert 0 <= phase <= 1
