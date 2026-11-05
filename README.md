# Billu's Pizza Kitchen

A fractions game for classes 6 and 7. Chef Billu the cat runs a pizza shop in the jungle, and the jungle animals order parts of a pizza. Children read the order, cut the pizza into equal parts, top the right number of slices and serve it. In Level 2 they compare fractions in the Big Eater Contest.

**Play:** https://billus-pizza-shop.vercel.app

Press **PLAY**: Story 1 → Tutorial 1.1 → Level 1.1 → Level 1.2 → Story 2 → Tutorial 2 → the matches → the Final → the Champion. The **QA** button (bottom right) jumps to any story, tutorial, order or match.

The game is landscape. It fits any screen from a phone held sideways to a wide monitor; a phone held upright is asked to turn sideways.

## Project structure

```
src/                    the game source
  level1.html           main screen, Story 1, Tutorial 1.1, Levels 1.1 and 1.2
  level2.html           Story 2, Tutorial 2, the matches, the Final, the Champion
  assets/               all art (story pictures, characters, pizzas, boards)
tools/
  build.py              builds dist/ from src/ (Vercel runs this on every deploy)
  serve.py              builds, then serves dist/ at http://localhost:8000
  art/                  one-off scripts that generated or cut some of the art
docs/                   design references
vercel.json             build command, output folder, clean URLs, caching
```

`dist/` is the build output and is not committed.

## Develop

Requires Python 3.9+ (no packages needed to build or serve).

```bash
python3 tools/serve.py       # build and open http://localhost:8000
python3 tools/build.py       # build only, into dist/
```

The pages in `src/` are page bodies; the build wraps each in a full HTML document (head, title, description, icon) and copies only the art the pages use. After a build, `dist/index.html` also opens directly from disk.

## Deploy

Vercel is connected to this repository: every push to `main` builds and publishes to production, and every other branch gets a preview URL. The settings live in `vercel.json`:

| Setting | Value |
|---|---|
| Build command | `python3 tools/build.py` |
| Output directory | `dist` |
| Addresses | `/` (Level 1) and `/level2` (Level 2); old `/Final/...` links redirect |
