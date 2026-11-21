# Pulse Runner

A simple rhythm-platformer game built with Pygame.

## Setup & Run

```bash
pip install -r requirements.txt
python main.py
```

## Controls

| Input | Action |
|---|---|
| `Space` / Left Click | Start, jump, use orb, or retry |
| Hold Left Click | Ship lift |
| `P` | Toggle practice mode |
| `Left` / `Right` Arrow | Select player color on menu |
| `Esc` | Return to menu or quit |

## Custom Artwork (Optional)

Place `player.png` or `ship.png` in the same folder as `main.py` to override the default visuals.

Game logic advances in fixed 60 Hz steps from elapsed time, while the pulse
tracks 128 BPM in seconds. A frame stalled longer than 250 ms is capped to
avoid a large catch-up burst. Tests compare gameplay and beats at 30, 60,
and 120 drawing frames per second.

## License

[MIT](LICENSE)
