"""Play the whole game in a muted browser and write down every line it says, for tools/voices.py.

    python tools/serve.py 8765            # in another terminal
    python tools/collect_lines.py         # writes src/assets/vo/lines.json

It plays the right answers all the way through (story, tutorials, every order and match, the Final), then
goes back over every order and round making wrong answers, so the hint lines are heard as well.
Needs Playwright (pip install playwright; python -m playwright install chromium).
"""
import json
import os
import sys
import time

from playwright.sync_api import sync_playwright

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "src", "assets", "vo", "lines.json")
BASE = (sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "http://127.0.0.1:8765/").rstrip("/") + "/"
LINES = {}
T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:6.1f}s] lines {len(LINES):4}", *a, flush=True)


def heard(who, text, k=None):
    if text:
        LINES[f"{who}|{text}"] = [who, text]


def save():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    old = []
    if os.path.isfile(OUT):
        old = json.load(open(OUT, encoding="utf-8"))
    for who, text in old:
        LINES.setdefault(f"{who}|{text}", [who, text])
    json.dump(sorted(LINES.values()), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)


def until(pg, js, timeout=90):
    end = time.time() + timeout
    while time.time() < end:
        try:
            if pg.evaluate(js):
                return True
        except Exception:
            pass
        pg.wait_for_timeout(300)
    return False


def tap(pg, sel):
    loc = pg.locator(sel).first
    box = loc.bounding_box()
    if box:
        pg.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)


def new_page(b):
    pg = b.new_page(viewport={"width": 1680, "height": 900})
    pg.expose_function("__vo", heard)
    return pg


def topping_order(pg, wrong=False):
    """One Level 1 order; with wrong=True it first makes three wrong tries at the mould and at the topping."""
    if pg.evaluate("S.phase==='mould' || LEVELS[S.lv].cut"):
        until(pg, "S.phase==='mould' && !S.busy", 30)
        d = pg.evaluate("cur().d")
        if wrong:
            others = pg.evaluate("[...document.querySelectorAll('.mould')].map(m=>m.dataset.m).filter(m=>+m!==cur().d)")
            for k in range(3):
                pg.wait_for_timeout(900)
                if others:
                    tap(pg, f'.mould[data-m="{others[k % len(others)]}"]')
                pg.wait_for_timeout(1500)
        for _ in range(6):
            pg.wait_for_timeout(700)
            tap(pg, f'.mould[data-m="{d}"]')
            pg.wait_for_timeout(900)
            if pg.evaluate("S.phase!=='mould' || S.busy"):
                break
    if not until(pg, "S.phase==='top' && !S.busy", 60):
        return
    pg.locator('.katori[data-top="tomato"]').click(force=True)
    pg.wait_for_timeout(250)
    n, d = pg.evaluate("[cur().n, cur().d]")
    if wrong:
        k = n + 1 if n < d else n - 1
        for i in range(max(k, 0)):
            tap(pg, f'.hit[data-i="{i}"]')
            pg.wait_for_timeout(250)
        tap(pg, '.hit[data-i="0"]')          # a slice that already has topping
        pg.wait_for_timeout(600)
        for _ in range(3):
            tap(pg, "#done")
            pg.wait_for_timeout(1800)
        return                               # the right way is played in the first pass
    for i in range(n):
        tap(pg, f'.hit[data-i="{i}"]')
        pg.wait_for_timeout(300)
    tap(pg, "#done")
    until(pg, "S.phase==='served' && !S.busy", 30)


def level1(b):
    pg = new_page(b)
    pg.goto(BASE)
    pg.wait_for_timeout(1500)
    pg.evaluate("$('mainPlay').click()")
    log("story 1")
    until(pg, "!$('tut').hidden && $('tut').classList.contains('open')", 300)
    log("tutorial 1.1")
    until(pg, "$('tutTray').classList.contains('ask')", 500)
    pg.locator('#tutTray .tp[data-top="corn"]').click(force=True)
    until(pg, "$('tut').classList.contains('taps')", 20)
    for k in range(pg.evaluate("TUT.o.n")):
        tap(pg, f'#tutPz .part[data-i="{k}"] .hl')
        pg.wait_for_timeout(300)
    pg.locator("#tutServe").click(force=True)
    until(pg, "$('tut').hidden && S.lv==='1.1'", 120)
    counts = pg.evaluate("[LEVELS['1.1'].orders.length, LEVELS['1.2'].orders.length]")
    for lv, n in zip(("1.1", "1.2"), counts):
        for i in range(n):
            pg.evaluate(f"jumpTo('{lv}',{i})")
            pg.wait_for_timeout(1500)
            topping_order(pg)
            pg.wait_for_timeout(2500)
            log("level", lv, "order", i + 1)
    # Tutorial 1.2: the parrot's order, made together
    pg.evaluate("$('jump').value='T2'; $('jump').dispatchEvent(new Event('change'))")
    until(pg, "/Which mould/.test(S.sayPlain) && !S.busy", 90)
    tap(pg, '.mould[data-m="3"]')
    until(pg, "S.phase==='top' && !S.busy", 90)
    pg.locator('.katori[data-top="corn"]').click(force=True)
    for k in range(2):
        tap(pg, f'.hit[data-i="{k}"]'); pg.wait_for_timeout(400)
    pg.wait_for_timeout(800); tap(pg, "#done")
    until(pg, "!S.tut && cur().cust==='frog'", 90)
    log("tutorial 1.2")
    # the end screen
    pg.evaluate("jumpTo('1.1',LEVELS['1.1'].orders.length-1)")
    pg.wait_for_timeout(1500); topping_order(pg); pg.wait_for_timeout(1500); tap(pg, "#done"); pg.wait_for_timeout(4000)
    pg.evaluate("jumpTo('1.2',LEVELS['1.2'].orders.length-1)")
    pg.wait_for_timeout(1500)
    topping_order(pg)
    pg.wait_for_timeout(1500)
    tap(pg, "#done")
    pg.wait_for_timeout(4000)
    save()
    log("wrong answers, level 1")
    for lv, n in zip(("1.1", "1.2"), counts):
        for i in range(n):
            pg.evaluate(f"jumpTo('{lv}',{i})")
            pg.wait_for_timeout(1500)
            topping_order(pg, wrong=True)
    pg.close()
    save()


def level2(b):
    pg = new_page(b)
    pg.goto(BASE + "level2")
    pg.wait_for_timeout(2000)
    pg.evaluate("$('play').click()")
    pg.evaluate("setInterval(()=>{ const b=document.getElementById('l2b'); if(b&&b.classList.contains('pick')) b.click(); },700)")   # Learning 2: tap the ant's plate
    log("story 2")
    until(pg, "!$('tut').hidden && $('tut').classList.contains('open')", 300)
    log("tutorial 2")
    until(pg, "TUT2.open.a", 200)
    for _ in range(pg.evaluate("TUT2.a.n")):
        pg.locator("#t2stack-a").click(force=True)
        pg.wait_for_timeout(300)
    until(pg, "TUT2.open.b", 60)
    for _ in range(pg.evaluate("TUT2.b.n")):
        pg.locator("#t2stack-b").click(force=True)
        pg.wait_for_timeout(300)
    until(pg, "$('t2check').classList.contains('on')", 30)
    pg.locator("#t2check").click(force=True)
    until(pg, "document.querySelector('#t2-b.pick')", 60)
    pg.locator("#t2-a").click(force=True)             # the wrong one first
    pg.wait_for_timeout(2500)
    pg.locator("#t2-b").click(force=True)
    until(pg, "$('tut').hidden", 120)
    kinds = pg.evaluate("STEPS.map(s=>s.kind)")
    for wrong in (False, True):
        for i, kind in enumerate(kinds):
            pg.evaluate(f"go({i})")
            pg.wait_for_timeout(2500)
            try:
                if kind == "match":
                    until(pg, "S.phase==='build'", 30)
                    pg.wait_for_timeout(1500)
                    a, bn, win = pg.evaluate("[STEPS[S.i].a.n,STEPS[S.i].b.n,STEPS[S.i].win]")
                    if wrong:
                        pg.locator("#stack-a").click(force=True)
                        for _ in range(3):
                            pg.locator("#done").click(force=True)
                            pg.wait_for_timeout(2200)
                        continue
                    for sd, n in (("a", a), ("b", bn)):
                        for _ in range(n):
                            pg.locator(f"#stack-{sd}").click(force=True)
                            pg.wait_for_timeout(250)
                    pg.locator("#done").click(force=True)
                    until(pg, "S.phase==='winner'", 30)
                    pg.wait_for_timeout(1500)
                    pg.locator(f"#side-{win}").click(force=True)
                    pg.wait_for_timeout(5000)
                elif kind == "cards":
                    until(pg, "S.phase==='winner'", 30)
                    pg.wait_for_timeout(1500)
                    win = pg.evaluate("STEPS[S.i].win")
                    if wrong:
                        lose = "a" if win == "b" else "b"
                        for _ in range(3):
                            pg.locator(f"#side-{lose}").click(force=True)
                            pg.wait_for_timeout(2500)
                        continue
                    pg.locator(f"#side-{win}").click(force=True)
                    pg.wait_for_timeout(5000)
                elif kind == "final":
                    until(pg, "S.phase==='order'", 30)
                    pg.wait_for_timeout(1500)
                    if wrong:
                        for _ in range(3):
                            pg.evaluate("[...FINALISTS.keys()].forEach((c,s)=>putIn($('fin-'+c),$('slot-'+s)))")
                            pg.wait_for_timeout(3000)
                            pg.evaluate("document.querySelectorAll('.fline .slot>.fin').forEach(f=>{ const c=f.id; })")
                        continue
                    pg.evaluate("(()=>{const w=[...FINALISTS.keys()].sort((x,y)=>FINALISTS[x].n/FINALISTS[x].d-FINALISTS[y].n/FINALISTS[y].d); w.forEach((c,s)=>putIn($('fin-'+c),$('slot-'+s)));})()")
                    until(pg, "S.phase==='finalPick'", 30)
                    pg.wait_for_timeout(1500)
                    pg.locator("#fin-0").click(force=True)
                    pg.wait_for_timeout(6000)
                else:
                    pg.wait_for_timeout(5000)
            except Exception as e:
                log("step", i, kind, "skipped:", str(e)[:80])
            log("level 2 step", i + 1, kind, "wrong" if wrong else "")
        save()
    pg.evaluate(f"go({kinds.index('champion')})")
    pg.wait_for_timeout(12000)
    pg.close()
    save()


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", args=["--mute-audio"])
        if "--level2" not in sys.argv:
            level1(b)
        level2(b)
        b.close()
    save()
    log("done:", OUT)


if __name__ == "__main__":
    main()
