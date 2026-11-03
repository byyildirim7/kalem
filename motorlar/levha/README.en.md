# Plate engine (levha)

[Türkçe](README.md) | **English**

![Plate engine: pen-drawn build-up and text appearing line by line](demo.gif)

Takes a machine designed in code (lever, pulley system, crank-piston, gear train, catapult), draws it like an old Leonardo notebook plate, then **runs** it and turns it into a teaching video. The machine is drawn stroke by stroke, its parts move on their own joints, text appears one line at a time, dimensions show as dashed lines.

There is also a blue technical-drawing (blueprint) style that needs no Codex and runs entirely in code.

## How it works

1. **Design** (`<machine>/tasarla.py`): the machine is described with coordinates. Output: a plain line skeleton (`iskelet.png`), a body-only skeleton without moving parts (`iskelet-govde.png`) and `geometri.json`.
2. **Engrave with Codex**: the skeleton is turned into a notebook engraving by the Codex CLI `image_generation` tool. Two images come out: `levha.png` (full machine) and `govde.png` (body with the moving parts removed).
3. **Fit** (`incelt_mek.py`): the Codex drawing never lands exactly on the skeleton. Each part is searched for in the drawing, a shift of a few pixels is found, and the design is fitted to the drawing.
4. **Render** (`levha.py`): pen build-up, part and joint motion, teaching layer, mp4.
5. **Measure** (`ders_olc.py`): arrow lengths and dimensions are measured from the last frame of the video and compared to what the text says.

Output goes to `cikti/`: the mp4, check images and a measurement report.

## Install

You need Python 3.10+ and ffmpeg. For the Codex step also the [Codex CLI](https://github.com/openai/codex) (logged in).

```bash
cd motorlar/levha
python3 -m pip install -r requirements.txt
```

The Codex drawings of the bundled example machines are in their folders, so you can try it right away without Codex.

## One command

```bash
python3 yeni_levha.py <machine> [--codex-yok] [--stil blueprint] [--seviye 8|lise] [--varyant ...]
```

Examples:

```bash
python3 yeni_levha.py kaldirac --codex-yok --seviye lise --varyant acili           # notebook style, bundled drawing
python3 yeni_levha.py palanga --stil blueprint --seviye lise --varyant agirlikli   # blue technical drawing, no Codex
python3 yeni_levha.py iskelet-yolu --codex-yok                                       # gear train
python3 yeni_levha.py mancinik                                                       # runs Codex (costs money and time)
```

A render takes 15-25 seconds. When done, the path of the mp4 is printed (`cikti/<name>-v4-dur.mp4`).

| Option | What it does |
|---|---|
| `--codex-yok` ("no Codex") | Skips Codex and uses the `levha.png` and `govde.png` already in the folder. |
| `--stil blueprint` | Generates the images in code, no Codex needed. Navy ground, light lines, color = side (input, output, load). |
| `--seviye 8` | Teaching layer at Turkish 8th grade level: ratio and proportion. Default. |
| `--seviye lise` | 11th grade level: torque, equilibrium, efficiency. Motion ends in horizontal balance. |
| `--varyant` | A different question for the same machine. Lever: `tork`, `acili`, `agirlik`. Pulley: `temel`, `agirlikli`, `verim`. |

Note: the on-screen text and measurements are in Turkish.

## The Codex step

`yeni_levha.py` does it for you unless you pass `--codex-yok`. Two Codex jobs run at the same time (a: full machine, b: body). If you run it by hand, two rules apply:

- The prompt must come **before** the image given with `-i`. If it comes after, `-i` swallows the prompt and Codex works on nothing.
- The prompt must say "you MUST produce the image with image_generation, do not draw with Python or PIL". Without that, Codex takes the easy way and draws with code, and the engraving texture is lost.

```bash
codex exec --skip-git-repo-check --sandbox workspace-write -C kaldirac "<prompt>" -i kaldirac/iskelet.png
```

Ready-made prompts are in `ISTEK.md` and `ISTEK-govde.md`, written by `tasarla.py`. Codex writes `bitti.txt` when done. It may not get it right the first time: check `levha.png` by eye and rerun if needed.

## Teaching layer and checks

During render the numbers come from a solver and are also verified independently:

- **Text arrives line by line**, each line is one step of the calculation. Color marks the side: red is input force, blue is load.
- **Dashed dimension lines**: arm lengths, lift height, rope travel.
- **Physics check**: for the lever, the arm ratio against the arc length ratio; for the pulley, rope length and "rope pulled / load lifted", checked on every frame.
- **Collision check**: gears and parts must not overlap, and on-screen text must not land on parts (overlap must be 0 px).
- **Path check**: the ends of drawn paths must match the designed path within ±2 px.
- **Render measurement** (`ders_olc.py`): arrow lengths and dimensions are read from the pixels of the last frame ("G arrow 149.6 px = 29.92 N, text says 30 N"). Result in `cikti/<name>-v4-olcum.txt`.

If a check fails, the command stops with an error that says which one.

## Adding a new machine

1. Create `motorlar/levha/<name>/` with a `tasarla.py`. Easiest: copy `kaldirac/tasarla.py` and change it.
2. `tasarla.py` describes the part shapes with coordinates, draws two skeletons with `Iskelet` (a: everything, b: no moving parts), writes `geometri.json` with `geometri_yaz` and the Codex prompts with `istek_yaz`. Shared helpers are in `tasarim_ortak.py`.
3. Part shapes: `daire` (circle), `kutu` (box), `cokgen` (polygon), `kol` (bar with round ends).
4. Give each part a **joint** and a **motion** (`mekanizma.py`):

| Motion | Used for |
|---|---|
| `donme` | Rotates around a pivot at constant speed (wheel, gear). |
| `bagli` | Rotates tied to another part. For gears ratio = -Z1/Z2 (opposite direction). |
| `krank_kayma` | A sliding part (piston) moves along its axis as the crank turns. |
| `biyel` | The rigid rod between the crank pin and the sliding pin (connecting rod). |
| `anahtar` | Arm / lever: swings smoothly through a list of frame-angle keys, optional impact bounce. |
| `ip_sarma` | Drum: its angle follows the rope length, turning as rope winds on. |
| `dogrusal` | Both translates and rotates by one driver (distance): the moving pulley of a pulley system. |
| `takip` | Follows a point on another part without rotating: a hanging load. |
| `mermi` | Travels with a carrier, flies when released, bounces, stops: catapult. |
| `sabit` | Never moves. |

5. Try it with `python3 yeni_levha.py <name>`. The first time Codex runs and `levha.png` and `govde.png` land in the folder. Later, `--codex-yok` is enough.

The teaching layer (the `ders` section in `geometri.json`) depends on the machine type: lever, pulley and gear train are ready (crank-piston and catapult run as plain moving plates without a teaching layer); a new type needs a block in `ders.py`. If you only want a moving plate, leave `ders` out and the engine still works.

## Files

| File | Job |
|---|---|
| `yeni_levha.py` | The one command, runs every step in order. |
| `<machine>/tasarla.py` | The machine's geometry. |
| `tasarim_ortak.py` | Skeleton drawing, Codex prompt, geometry writing. |
| `incelt_mek.py` | Fits the design to the Codex drawing. |
| `levha.py` | Render: build-up, motion, teaching layer, mp4. |
| `mekanizma.py` | Joint types and a small kinematics solver. |
| `ders.py`, `ders_olc.py` | Teaching layer and after-render measurement. |
| `blueprint.py` | Codex-free blue technical drawing images. |
| `levhalar/` | Render definition of each machine (written automatically). |
| `font/` | Bundled fonts (EB Garamond, IM Fell, open licenses). |

Blueprint text uses Arial Narrow on macOS, Liberation Sans Narrow or DejaVu on Linux, whichever is present.

## History

The engine started as a prototype for one gear-counter plate (no pixel cutting, every part redrawn in code). It then moved to a general mechanism model, the teaching layer and the blueprint style. This folder is the clean, standalone version of that work.
