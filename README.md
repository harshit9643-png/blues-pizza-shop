# Billu's Pizza Kitchen

A fractions game for classes 6 and 7. Chef Billu the cat runs a pizza shop in the jungle, and jungle animals order parts of a pizza. Children read the order, cut the pizza into equal parts, add toppings to the right number of parts, and serve it. In Level 2 they compare fractions in the Big Eater Contest.

## Play it

- **Online:** https://harshit9643-png.github.io/blues-pizza-shop/ (opens `Final/`)
- **Offline:** open `Final/index.html`

Press **PLAY**: the story, Tutorial 1.1, Level 1.1, Level 1.2, then Level 2 (its story, Tutorial 2, the matches and the ending). The menu at the top jumps to any story, tutorial or order.

## Files

| Path | What it is |
|---|---|
| `Final/` | **The finished game.** Self-contained: copy this folder anywhere and open `index.html`. |
| `index.html` | Sends the online link to `Final/`. |
| `level1_draft2.html` | Source of Level 1 (story, tutorial, Levels 1.1 and 1.2). |
| `level2.html` | Source of Level 2 (story, tutorial, matches, ending). |
| `assets/` | Art the source pages use. |
| `tools/` | Scripts: `package_game.py` builds `Final/`, `serve.py` runs the source locally, `gen_*.py` and `rig_parts.py` make art. |

## After editing the game

```
python tools/package_game.py
```

This rebuilds `Final/` from `level1_draft2.html`, `level2.html` and `assets/`. To try the source pages directly, run `python tools/serve.py` and open http://localhost:8000.

Older versions and drafts are in the git history.
