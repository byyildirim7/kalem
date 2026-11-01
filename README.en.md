<p align="center"><img src=".github/logo.png" width="200" alt="Kalem logo"></p>

# Kalem

[Türkçe](README.md) | **English**

> Every scene has its own pen.

When you ask an AI to make a video with code, the results all look alike, because every scene is drawn with the same engine. **Kalem** ("pen" in Turkish) is a Claude Code skill that splits your video into scenes, looks at what happens inside each one and picks the engine that draws it best. It then renders each scene with that engine, joins them with transitions such as a page flip, and adds sound effects locked to the frame.

You describe what you want. The skill decides which pen draws which scene.

![Flying machine example: six scenes, six engines](ornek/ucan-makine/kontrol.png)

## Which scene, which engine

| Inside the scene... | Engine |
|---|---|
| A line that draws itself, a sketch | Paper.js |
| A character, walking, one shape morphing into another | Plain canvas |
| Explosions, light, dust, thousands of particles | PixiJS |
| Text, numbers, counters, info cards | HyperFrames (HTML + GSAP) |
| Real 3D: orbiting camera, light, shadow | Three.js |
| Formulas, graphs, diagrams | Manim |

Helpers: Matter.js and Rapier (physics), gl-transitions (125 transitions incl. page flip), Tone.js (frame-locked sound effects), Anime.js, tsParticles, glTF-Transform.

The table reflects one person's taste: 20 tools raced on the same scene and were scored by eye. Run your own tests and change it. It lives in `.claude/skills/kalem/SKILL.md`. The skill and its prompts are written in Turkish; Claude follows them in any language.

## Install

Needs macOS or Linux, Node 20+, Python 3, ffmpeg, Google Chrome and [Claude Code](https://claude.com/claude-code). Manim is optional.

```bash
git clone https://github.com/leodavincs/kalem.git
cd kalem
./kurulum.sh
```

## Use

Open Claude Code in the repo folder and describe your video:

```
claude
/kalem A 50-second landscape video about Leonardo da Vinci's flying machine...
```

Claude first shows the scene table (scene, engine, why) and waits for your approval, then renders every scene in its own folder, checks the frames and joins them into `projeler/<name>/cikti.mp4`.

Manual join: `python3 birlestir.py projeler/<name> --gecis BookFlip --etiket` (`--etiket` stamps a small card naming the engine on each scene).

## How it works

- Time comes from the frame number; randomness is seeded, so the same command gives the same frames.
- Browser engines are captured frame by frame in Chrome (`ortak/yakala.py`), not recorded in real time, so heavy scenes never stutter.
- Each scene writes `olaylar.json` (a line starts, something drops, a wing flaps). Sound is generated from that list, so it never drifts from the picture.
- Scenes are independent and can be rendered in parallel.

## License

MIT. Fonts in `ortak/font/` are under the SIL Open Font License 1.1.

Leo (leodavincs)
