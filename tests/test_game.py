import importlib
import os
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

game = importlib.import_module("main")


def test_asset_path_is_independent_of_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert game.asset_path("player.png") == Path(game.__file__).resolve().parent / "player.png"


def test_level_progress_is_bounded():
    level = game.LevelManager()

    assert level.get_progress() == 0
    level.distance_traveled = level.total_distance * 2
    assert level.get_progress() == 1


def test_cube_jump_changes_vertical_velocity():
    player = game.Player()

    assert player.jump() is True
    assert player.on_ground is False
    assert player.vel_y == game.JUMP_FORCE
    assert player.jump() is False


@pytest.mark.parametrize("draw_fps", [30, 60, 120])
def test_scroll_distance_uses_elapsed_time(draw_fps):
    instance = game.Game()
    instance.reset()

    for _ in range(draw_fps):
        instance.sim_clock.advance(1 / draw_fps, instance._update)

    assert instance.state == 'playing'
    assert instance.level.distance_traveled == game.GAME_SPEED * game.FPS
    assert instance.ground_offset == (game.GAME_SPEED * game.FPS) % 40


@pytest.mark.parametrize("draw_fps", [30, 60, 120])
def test_beats_keep_bpm_at_different_draw_rates(draw_fps):
    class CountingColumn:
        def __init__(self):
            self.pulses = 0

        def pulse(self):
            self.pulses += 1

        def update(self):
            pass

    instance = game.Game()
    column = CountingColumn()
    instance.pulse_columns = [column]
    for _ in range(draw_fps * 112 // 15):
        instance.sim_clock.advance(1 / draw_fps, instance._update)

    assert instance.pulse_timer == 448
    assert column.pulses == 15
