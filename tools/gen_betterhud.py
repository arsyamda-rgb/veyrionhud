#!/usr/bin/env python3
"""Generate BetterHud config + PNGs. Run AFTER gen_assets.py. Output: BetterHud/ and VeyrionHUD-BetterHud.zip"""
import os, shutil, zipfile
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = f"{ROOT}/resourcepack/assets/veyrion/textures/font/"
OUT = f"{ROOT}/BetterHud"
if os.path.isdir(OUT): shutil.rmtree(OUT)
for d in ("huds", "layouts", "images/veyrion", "texts"): os.makedirs(f"{OUT}/{d}")

def clean(im):            # drop the invisible alpha=1 marker pixel used for the font pack
    px = im.load(); w, h = im.size
    for y in range(h):
        if px[w-1, y][3] <= 2: px[w-1, y] = (0, 0, 0, 0)
    return im

icons = Image.open(T + "icons.png").convert("RGBA")
names = ["calendar", "clock", "players", "coin", "beast", "dragon", "elf", "human"]
for i, n in enumerate(names):
    clean(icons.crop((i*80, 0, i*80+80, 80))).save(f"{OUT}/images/veyrion/{n}.png")
logo = clean(Image.open(T + "logo.png").convert("RGBA")); logo.save(f"{OUT}/images/veyrion/logo.png")
title = clean(Image.open(T + "title.png").convert("RGBA")); title.save(f"{OUT}/images/veyrion/title.png")
S = 0.125   # 8 texture px = 1 GUI px
LW, LH = round(logo.width*S), round(logo.height*S)
TW, TH = round(title.width*S), round(title.height*S)

# ---- images/
y = ""
for n in ["logo", "title"] + names:
    y += f"veyrion_{n}:\n  type: single\n  file: \"veyrion/{n}.png\"\n"
open(f"{OUT}/images/veyrion.yml", "w").write(y)

# ---- texts/ (font used by the layout)
open(f"{OUT}/texts/veyrion.yml", "w").write(
    "veyrion_font:\n  merge-default-bitmap: true\n  use-unifont: false\n")

# ---- layout (all numbers = GUI pixels, origin = right edge minus margin, top of screen)
LOGO_CY, ROW0, ROWH, ICON, GAP, GGAP = 58, 100, 18, 10, 3, 6
rows = [ROW0 + i*ROWH for i in range(4)]
TIME_W, DATE_W = 46, 60      # "19:52 WIB" and "09/11/2026" in vanilla font widths
img = []; txt = []
def image(name, x, yy, extra=""):
    img.append(f"    {len(img)+1}:\n      name: veyrion_{name}\n      x: {x}\n      y: {yy}\n      scale: {S}\n{extra}")
def text(pattern, x, cy):
    txt.append(f"    {len(txt)+1}:\n      name: veyrion_font\n      pattern: \"{pattern}\"\n      align: right\n      x: {x}\n      y: {cy-4}\n      scale: 1\n")

image("logo", -LW, LOGO_CY - LH//2)
image("title", -LW - 4 - TW, LOGO_CY - TH//2)
# row 1: date + calendar + time + clock
cy = rows[0]
image("clock", -ICON, cy-5)
text("[papi:veyrion_time]", -(ICON+GAP), cy)
time_left = ICON + GAP + TIME_W
image("calendar", -(time_left + GGAP + ICON), cy-5)
text("[papi:veyrion_date]", -(time_left + GGAP + ICON + GAP), cy)
# row 2: online
cy = rows[1]; image("players", -ICON, cy-5); text("[papi:veyrion_online]", -(ICON+GAP), cy)
# row 3: race (text + icon per race, chosen by condition)
cy = rows[2]; text("[papi:veyrion_race]", -(ICON+GAP), cy)
for r in ["beast", "dragon", "elf", "human"]:
    image(r, -ICON, cy-5,
          f"      conditions:\n        1:\n          first: \"papi:veyrion_race_id\"\n          second: \"'{r}'\"\n          operation: '=='\n")
# row 4: money
cy = rows[3]; image("coin", -ICON, cy-5); text("[papi:veyrion_money]", -(ICON+GAP), cy)
open(f"{OUT}/layouts/veyrion.yml", "w").write(
    "veyrion_layout:\n  images:\n" + "".join(img) + "  texts:\n" + "".join(txt))

# ---- hud
open(f"{OUT}/huds/veyrion.yml", "w").write(f"""veyrion:
  default: true
  update:
    tick: 20
  layouts:
    1:
      name: veyrion_layout
      gui:
        x: 100
        y: 0
      pixel:
        x: -22
        y: 0
""")
open(f"{OUT}/README.txt", "w").write(
"Extract ke plugins/BetterHud/ (gabung folder), lalu /betterhud reload.\n"
"Butuh: BetterHud, PlaceholderAPI, VeyrionHUD (plugin), AwakeningCutscene.\n")
with zipfile.ZipFile(f"{ROOT}/VeyrionHUD-BetterHud.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for dp, _, fs in os.walk(OUT):
        for f in fs:
            full = os.path.join(dp, f); z.write(full, "BetterHud/" + os.path.relpath(full, OUT))
print("logo", LW, LH, "title", TW, TH)
