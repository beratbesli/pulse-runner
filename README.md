# Pulse Runner

Pulse Runner is an original, compact rhythm-platformer prototype built with
Pygame. It combines cube and ship movement, gravity changes, jump pads and
orbs, practice checkpoints, collectibles, generated sound effects, and one
hand-authored level.

The project is inspired by the broader rhythm-platformer genre. It is not
affiliated with or distributed by another game or publisher.

## Requirements

- Python 3.10 or newer
- Pygame 2.6

## Run

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
pulse-runner
```

On Windows, activate the environment with `.venv\Scripts\activate`.

## Controls

| Input | Action |
|---|---|
| `Space` or left click | Start, jump, use an orb, or retry |
| Hold left click | Control ship lift |
| `P` | Toggle practice mode |
| Left / right arrow | Select player colour on the menu |
| `Esc` | Return to the menu or quit |

## Optional artwork

Place `player.png` or `ship.png` next to `main.py` to replace the generated
player artwork. Assets are resolved relative to the installed game module, so
launching the command from another directory does not change their location.
If an image is absent or invalid, the built-in vector artwork is used.

Only use artwork that you created or have permission to redistribute. Personal
assets should not be committed unless their license is documented.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
python -m build
```

CI runs the same tests with dummy video and audio drivers, so core state and
asset-path behavior can be checked without opening a window.

The current version intentionally keeps the playable prototype in one module.
Future gameplay changes should first extract deterministic physics and level
state from rendering and audio rather than growing the `Game` class further.

## License

[MIT](LICENSE)
