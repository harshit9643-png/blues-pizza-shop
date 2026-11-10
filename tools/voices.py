"""Make the AI voice clips for every line the game says.

    python tools/voices.py                 # make any clips that are missing or changed
    python tools/voices.py --list          # show the lines and who says them

Reads  src/assets/vo/lines.json   [[speaker, text], ...]  (collected by playing the game; see tools/collect_lines.py)
Writes src/assets/vo/<key>-<sound hash>.mp3 and src/assets/vo/manifest.json  {key: file}

The key is the same FNV-1a hash the pages compute (VOICE.key) from "speaker|text", so the game finds
each clip by the line it is about to say. A line with no clip is said by the browser's own voice.
Voices are Microsoft neural voices through edge-tts (pip install edge-tts).
"""
import asyncio
import hashlib
import json
import os
import re
import sys

import edge_tts

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VO = os.path.join(REPO, "src", "assets", "vo")

# who says it -> (voice, rate, pitch)
CAST = {
    "narr":   ("en-IN-NeerjaNeural", "-6%", "-2Hz"),            # the storyteller
    "noori":  ("en-IN-NeerjaExpressiveNeural", "-8%", "-6Hz"),  # the wise old owl
    "billu":  ("en-IN-PrabhatNeural", "+0%", "+8Hz"),           # the cheerful chef cat
}
KIDS = {   # small customers and contestants: a cartoon child voice, each a little different
    "chintu": "+4Hz", "ant": "+14Hz", "monty": "+6Hz", "tez": "-6Hz", "squirrel": "+10Hz", "mouse": "+16Hz",
    "frog": "+2Hz", "madhu": "+12Hz", "peacock": "+0Hz", "jhumru": "+8Hz", "bijli and badal": "+6Hz", "parrot": "+10Hz",
    "rabbit": "+12Hz", "sloth": "-10Hz", "badal": "+4Hz", "bijli": "+8Hz",
}
BIG = {    # big animals: deeper grown-up voices
    "gorilla": ("en-US-GuyNeural", "-4%", "-8Hz"), "croc": ("en-GB-RyanNeural", "-2%", "-6Hz"),
    "hippo": ("en-US-RogerNeural", "-6%", "-10Hz"), "crocodile": ("en-GB-RyanNeural", "-2%", "-6Hz"), "bear": ("en-US-GuyNeural", "-6%", "-12Hz"),
    "giraffe": ("en-GB-LibbyNeural", "+0%", "+0Hz"), "guest": ("en-GB-LibbyNeural", "+0%", "+0Hz"),
}


def voice_for(who):
    if who in CAST:
        return CAST[who]
    if who in BIG:
        return BIG[who]
    return ("en-US-AnaNeural", "+0%", KIDS.get(who, "+4Hz"))


def norm(t):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", t or "")).strip()


def key(who, text):
    """FNV-1a over UTF-16 code units, exactly as VOICE.key in the pages."""
    s = f"{who}|{norm(text)}"
    h = 0x811C9DC5
    b = s.encode("utf-16-le")
    for i in range(0, len(b), 2):
        h ^= b[i] | (b[i + 1] << 8)
        h = (h * 16777619) & 0xFFFFFFFF
    return f"{h:08x}"


def spoken(text):
    """What the voice reads: fractions as "3 by 4" (as the sheet asks), no name tag before a quote, no emoji."""
    t = norm(text)
    t = re.sub(r"^\s*[A-Z][A-Za-z]+(?: and [A-Z][A-Za-z]+)?(?:\s*\([^)]*\))?:\s*(?=[“\"])", "", t)
    t = re.sub(r"(\d+)\s*/\s*(\d+)", r"\1 by \2", t)
    t = t.replace("…", ", ").replace("⭐", "").replace("▸", "").replace("✓", "")
    t = re.sub(r"[“”\"]", "", t)
    return re.sub(r"\s+", " ", t).strip()


async def make(sem, who, text, k, out, manifest, index):
    voice, rate, pitch = voice_for(who)
    say = spoken(text)
    sig = hashlib.sha1(f"{voice}|{rate}|{pitch}|{say}".encode()).hexdigest()[:6]
    fn = f"{k}-{sig}.mp3"
    manifest[k] = fn
    index[k] = {"who": who, "text": norm(text), "voice": voice, "file": fn}
    if os.path.isfile(os.path.join(out, fn)) or not say:
        return False
    async with sem:
        for attempt in range(4):
            try:
                await edge_tts.Communicate(say, voice, rate=rate, pitch=pitch).save(os.path.join(out, fn))
                return True
            except Exception as e:  # the service drops a connection now and then
                if attempt == 3:
                    print("FAILED", who, say[:60], e, file=sys.stderr)
                    manifest.pop(k, None)
                await asyncio.sleep(1.5 * (attempt + 1))
    return False


async def main():
    os.makedirs(VO, exist_ok=True)
    lines = json.load(open(os.path.join(VO, "lines.json"), encoding="utf-8"))
    seen, todo = set(), []
    for who, text in lines:
        k = key(who, text)
        if k not in seen and norm(text):
            seen.add(k)
            todo.append((who, text, k))
    if "--list" in sys.argv:
        for who, text, k in todo:
            print(f"{k} {who:10} {voice_for(who)[0]:30} {spoken(text)}")
        return
    manifest, index = {}, {}
    sem = asyncio.Semaphore(6)
    made = await asyncio.gather(*[make(sem, w, t, k, VO, manifest, index) for w, t, k in todo])
    # clips no line uses any more are removed
    keep = set(manifest.values())
    for fn in os.listdir(VO):
        if fn.endswith(".mp3") and fn not in keep:
            os.remove(os.path.join(VO, fn))
    json.dump(manifest, open(os.path.join(VO, "manifest.json"), "w", encoding="utf-8"), separators=(",", ":"), sort_keys=True)
    json.dump(index, open(os.path.join(VO, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0, sort_keys=True)
    print(f"{len(todo)} lines, {sum(made)} new clips, {len(manifest)} in the manifest")


if __name__ == "__main__":
    asyncio.run(main())
