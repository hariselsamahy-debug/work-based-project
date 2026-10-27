from app.vision.tracker import EventTracker


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def make(debounce=3, cooldown=60):
    clock = FakeClock()
    return EventTracker(debounce, cooldown, clock), clock


def test_fires_only_after_debounce_frames():
    tracker, _ = make(debounce=3)
    assert tracker.update("cam1", {"NO_HARDHAT"}) == []
    assert tracker.update("cam1", {"NO_HARDHAT"}) == []
    assert tracker.update("cam1", {"NO_HARDHAT"}) == ["NO_HARDHAT"]


def test_gap_resets_the_streak():
    tracker, _ = make(debounce=3)
    tracker.update("cam1", {"NO_HARDHAT"})
    tracker.update("cam1", {"NO_HARDHAT"})
    tracker.update("cam1", set())
    assert tracker.update("cam1", {"NO_HARDHAT"}) == []


def test_cooldown_suppresses_repeats_then_allows_again():
    tracker, clock = make(debounce=1, cooldown=60)
    assert tracker.update("cam1", {"FIRE"}) == ["FIRE"]
    clock.now = 30
    assert tracker.update("cam1", {"FIRE"}) == []
    clock.now = 61
    assert tracker.update("cam1", {"FIRE"}) == ["FIRE"]


def test_cameras_and_types_are_independent():
    tracker, _ = make(debounce=1)
    assert tracker.update("cam1", {"NO_VEST"}) == ["NO_VEST"]
    assert tracker.update("cam2", {"NO_VEST"}) == ["NO_VEST"]
    assert tracker.update("cam1", {"NO_VEST", "FIRE"}) == ["FIRE"]
