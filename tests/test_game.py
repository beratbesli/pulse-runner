import importlib
import os
from pathlib import Path

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
