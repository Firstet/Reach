"""Unit tests for Safety & Compliance Service."""

import pytest
from app.services.safety import (
    is_global_kill_switch_active,
    set_global_kill_switch,
)


class TestKillSwitch:
    def test_toggle_kill_switch(self):
        assert not is_global_kill_switch_active()
        set_global_kill_switch(True)
        assert is_global_kill_switch_active()
        set_global_kill_switch(False)
        assert not is_global_kill_switch_active()
