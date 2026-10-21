# Blue's Pizza Shop

A fractions game for classes 6 and 7. Chef Billu the cat runs a pizza shop in the jungle, and jungle animals order parts of a pizza. Children read the order, cut the pizza into equal parts, add toppings to the right number of parts, and serve it.

## Play it

```
python tools/serve.py
```

Then open http://localhost:8000. The server adds the page wrapper the game files expect, so open the game through it rather than double-clicking the HTML file.

## What's in the game (Level 1)

- **Level 1.1, Top and serve:** the pizza is cut for you. Drag a topping onto the slices the customer wants, then press DONE.
- **Level 1.2, Cut, top and serve:** pick the mould with the right number of parts, then add toppings and serve.
- 16 orders from the Level 1 storyboard, with round, square and rectangular pizzas.
- After each correct order, the pizza splits onto two plates: **Served** and **Left**.
- A drop-down at the top jumps to any order.

## Files

| Path | What it is |
|---|---|
| `level1_draft2.html` | The current game (Level 1, jungle table design) |
| `level1_draft1.html` | Draft 1, kept unchanged for comparison |
| `level1.html` | Working copy of Draft 1 |
| `billu-pizza-kitchen.html` | Early full-story prototype (story + Levels 1 and 2) |
| `drafts/` | Frozen, self-contained snapshots (ZIP + unzipped folder) |
| `assets/source/official/` | The original art that was supplied |
| `assets/characters`, `props`, `game`, `backgrounds` | Full-size art used by the game |
| `assets/web/`, `assets/draft2/` | Compressed versions the game loads |
| `tools/` | Scripts that generate, clean and compress the art, plus the local server |

## Tools

| Script | Purpose |
|---|---|
| `tools/serve.py` | Local server (port 8000) |
| `tools/optimize_assets.py` | Rebuild the compressed WebP art in `assets/web/` |
| `tools/make_draft_zip.py` | Freeze a version into `drafts/<name>/` and a ZIP |
| `tools/cut_tray.py`, `tools/clean_receipt.py` | Cut the supplied coconut tray and order receipt out of their backgrounds |
| `tools/gen_*.py` | Generate art with the Gemini image API (needs a key file; none is stored in this repository) |
