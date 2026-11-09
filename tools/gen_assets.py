#!/usr/bin/env python3
"""Generate the Veyrion HUD resource pack + Java constants. Needs Pillow."""
import json, os, shutil, zipfile
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACK = os.path.join(ROOT, "resourcepack")
LOGO_SRC = os.environ.get("LOGO", "/mnt/user-data/uploads/LOGO_VEYRION_NO_BG.png")
S = 8  # supersample: 1 GUI px = 8 texture px
ICON_H, LOGO_H, TITLE_H = 10, 48, 9   # GUI px heights

if os.path.isdir(PACK): shutil.rmtree(PACK)
tex_dir = f"{PACK}/assets/veyrion/textures/font"
font_dir = f"{PACK}/assets/veyrion/font"
for d in (tex_dir, font_dir, f"{PACK}/assets/minecraft/shaders/core",
          f"{PACK}/assets/minecraft/textures/gui/sprites/boss_bar"):
    os.makedirs(d)

def mark_width(img):
    """Make sure the last column has a (practically invisible) alpha=1 pixel so the
    glyph advance is deterministic = full cell width."""
    px = img.load(); w, h = img.size
    if px[w-1, 0][3] == 0: px[w-1, 0] = (0, 0, 0, 1)
    return img

def advance(cell_w, cell_h, height):
    scale = height / cell_h
    return int(0.5 + cell_w * scale) + 1

BLACK = (12, 12, 12, 255)

# ---------------------------------------------------------------- icons (drawn at 32x, down to 80x80 cell)
BIG = 400
def canvas(): 
    im = Image.new("RGBA", (BIG, BIG), (0,0,0,0)); return im, ImageDraw.Draw(im)
def sc(pts): return [(x*BIG/100, y*BIG/100) for x, y in pts]
def finish(im): return mark_width(im.resize((ICON_H*S, ICON_H*S), Image.LANCZOS))

def icon_calendar():
    im, d = canvas()
    d.rounded_rectangle([10*4,16*4,90*4,92*4], radius=10*4, outline=BLACK, width=8*4)
    d.rectangle([10*4,16*4,90*4,38*4], fill=BLACK)
    for x in (30, 70): d.rounded_rectangle([(x-4)*4, 4*4, (x+4)*4, 26*4], radius=4*4, fill=BLACK)
    for r in range(2):
        for c in range(3):
            x = 26+c*24; y = 52+r*18
            d.rectangle([x*4,y*4,(x+10)*4,(y+10)*4], fill=BLACK)
    return finish(im)

def icon_clock():
    im, d = canvas()
    d.ellipse([6*4,6*4,94*4,94*4], outline=BLACK, width=9*4)
    d.line(sc([(50,24),(50,52),(68,64)]), fill=BLACK, width=8*4, joint="curve")
    for p in [(50,24),(68,64)]: d.ellipse([(p[0]-4)*4,(p[1]-4)*4,(p[0]+4)*4,(p[1]+4)*4], fill=BLACK)
    return finish(im)

def icon_players():
    im, d = canvas()
    # back person
    d.ellipse([52*4,10*4,78*4,36*4], fill=BLACK)
    d.pieslice([40*4,44*4,92*4,110*4], 180, 360, fill=BLACK)
    # front person (with transparent outline to separate)
    d.ellipse([20*4,20*4,50*4,50*4], fill=(0,0,0,0)); 
    gap = Image.new("RGBA",(BIG,BIG),(0,0,0,0)); gd = ImageDraw.Draw(gap)
    gd.ellipse([14*4,14*4,56*4,56*4], fill=(255,255,255,255))
    gd.pieslice([4*4,52*4,66*4,130*4], 180, 360, fill=(255,255,255,255))
    a = im.getchannel("A"); m = gap.getchannel("A")
    from PIL import ImageChops
    im.putalpha(ImageChops.subtract(a, m))
    d = ImageDraw.Draw(im)
    d.ellipse([20*4,20*4,50*4,50*4], fill=BLACK)
    d.pieslice([10*4,58*4,60*4,122*4], 180, 360, fill=BLACK)
    return finish(im)

def icon_coin():
    im, d = canvas()
    d.ellipse([4*4,4*4,96*4,96*4], fill=BLACK)
    d.ellipse([17*4,17*4,83*4,83*4], outline=(0,0,0,0), width=1)
    ring = Image.new("RGBA",(BIG,BIG),(0,0,0,0)); rd = ImageDraw.Draw(ring)
    rd.ellipse([17*4,17*4,83*4,83*4], outline=(255,255,255,255), width=5*4)
    rd.rectangle([46*4,28*4,54*4,72*4], fill=(255,255,255,255))
    rd.rectangle([36*4,36*4,64*4,44*4], fill=(255,255,255,255))
    rd.rectangle([36*4,56*4,64*4,64*4], fill=(255,255,255,255))
    from PIL import ImageChops
    im.putalpha(ImageChops.subtract(im.getchannel("A"), ring.getchannel("A")))
    return finish(im)

def icon_paw():
    im, d = canvas()
    d.ellipse([26*4,50*4,74*4,92*4], fill=BLACK)
    d.ellipse([20*4,44*4,44*4,66*4], fill=BLACK); d.ellipse([56*4,44*4,80*4,66*4], fill=BLACK)
    for (cx, cy, rx, ry) in [(14,40,9,13),(36,22,9,14),(64,22,9,14),(86,40,9,13)]:
        d.ellipse([(cx-rx)*4,(cy-ry)*4,(cx+rx)*4,(cy+ry)*4], fill=BLACK)
    return finish(im)

def icon_dragon():
    im, d = canvas()
    # dragon head (profile, facing right): horn, skull, snout, jaw, spikes
    head = [(14,70),(10,40),(22,26),(34,10),(40,30),(52,22),(64,26),(80,34),(96,34),(98,46),
            (84,52),(88,60),(70,62),(62,74),(50,86),(36,92),(24,86)]
    d.polygon(sc(head), fill=BLACK)
    d.polygon(sc([(40,30),(48,8),(54,26)]), fill=BLACK)          # 2nd horn
    d.polygon(sc([(14,70),(2,64),(8,80),(2,92),(24,86)]), fill=BLACK)  # neck spikes
    cut = Image.new("RGBA",(BIG,BIG),(0,0,0,0)); cd = ImageDraw.Draw(cut)
    cd.polygon(sc([(56,38),(70,38),(62,46)]), fill=(255,255,255,255))   # eye
    cd.ellipse([88*4,38*4,92*4,42*4], fill=(255,255,255,255))           # nostril
    cd.line(sc([(66,56),(86,56)]), fill=(255,255,255,255), width=2*4)  # mouth line
    from PIL import ImageChops
    im.putalpha(ImageChops.subtract(im.getchannel("A"), cut.getchannel("A")))
    return finish(im)

def icon_elf():
    im, d = canvas()
    # leaf + pointed ear hint
    leaf = [(50,2),(78,22),(90,50),(78,80),(50,98),(22,80),(10,50),(22,22)]
    d.polygon(sc(leaf), fill=BLACK)
    cut = Image.new("RGBA",(BIG,BIG),(0,0,0,0)); cd = ImageDraw.Draw(cut)
    cd.line(sc([(50,92),(50,22)]), fill=(255,255,255,255), width=5*4)
    for y, dx in [(40,22),(58,26),(76,22)]:
        cd.line(sc([(50,y+10),(50-dx,y-6)]), fill=(255,255,255,255), width=4*4)
        cd.line(sc([(50,y+10),(50+dx,y-6)]), fill=(255,255,255,255), width=4*4)
    from PIL import ImageChops
    im.putalpha(ImageChops.subtract(im.getchannel("A"), cut.getchannel("A")))
    return finish(im)

def icon_human():
    im, d = canvas()
    d.ellipse([30*4,6*4,70*4,46*4], fill=BLACK)
    d.pieslice([8*4,54*4,92*4,150*4], 180, 360, fill=BLACK)
    return finish(im)

icons = [("calendar", icon_calendar), ("clock", icon_clock), ("players", icon_players),
         ("coin", icon_coin), ("beast", icon_paw), ("dragon", icon_dragon),
         ("elf", icon_elf), ("human", icon_human)]
ICON_BASE = 0xE100
sheet = Image.new("RGBA", (ICON_H*S*len(icons), ICON_H*S), (0,0,0,0))
for i, (n, fn) in enumerate(icons): sheet.paste(fn(), (i*ICON_H*S, 0))
sheet.save(f"{tex_dir}/icons.png")
json.dump({"providers": [{"type": "bitmap", "file": "veyrion:font/icons.png",
    "height": ICON_H, "ascent": ICON_H,
    "chars": ["".join(chr(ICON_BASE+i) for i in range(len(icons)))]}]},
    open(f"{font_dir}/icons.json", "w"), indent=2)
ICON_ADV = advance(ICON_H*S, ICON_H*S, ICON_H)

# ---------------------------------------------------------------- logo
logo = Image.open(LOGO_SRC).convert("RGBA")
bbox = logo.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
logo = logo.crop(bbox)
lh = LOGO_H*S; lw = round(logo.width*lh/logo.height)
logo = logo.resize((lw, lh), Image.LANCZOS)
if os.environ.get("LOGO_BLACK"):   # LOGO_BLACK=1 -> logo V jadi siluet hitam
    a_ = logo.getchannel("A"); logo = Image.new("RGBA", logo.size, (12, 12, 12, 255)); logo.putalpha(a_)
logo = mark_width(logo)
logo.save(f"{tex_dir}/logo.png")
json.dump({"providers": [{"type": "bitmap", "file": "veyrion:font/logo.png",
    "height": LOGO_H, "ascent": LOGO_H, "chars": ["\ue000"]}]}, open(f"{font_dir}/logo.json","w"), indent=2)
LOGO_ADV = advance(lw, lh, LOGO_H)

# ---------------------------------------------------------------- title "VEYRION ROLEPLAY" white -> dark gray
TEXT = "VEYRION ROLEPLAY"
fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
spacing = 4
widths = [fnt.getlength(c) for c in TEXT]
tw = int(sum(widths) + spacing*(len(TEXT)-1)) + 8
th = TITLE_H*S
mask = Image.new("L", (tw, th), 0); md = ImageDraw.Draw(mask)
x = 4
asc, desc = fnt.getmetrics()
y = (th - (asc+desc))//2 + 2
for c, w in zip(TEXT, widths):
    md.text((x, y), c, font=fnt, fill=255); x += w + spacing
bb = mask.getbbox(); mask = mask.crop(bb)
tw = mask.width
W0, W1 = (255,255,255), (58,58,58)            # white -> dark gray (not pure black)
grad = Image.new("RGBA", (tw, mask.height))
gp = grad.load()
for xx in range(tw):
    t = xx/(tw-1)
    col = tuple(round(W0[i]+(W1[i]-W0[i])*t) for i in range(3))
    for yy in range(mask.height): gp[xx, yy] = col+(255,)
grad.putalpha(mask)
# pad vertical to exactly TITLE_H*S
final = Image.new("RGBA", (tw, th), (0,0,0,0)); final.paste(grad, (0, (th-grad.height)//2))
mark_width(final).save(f"{tex_dir}/title.png")
json.dump({"providers": [{"type": "bitmap", "file": "veyrion:font/title.png",
    "height": TITLE_H, "ascent": TITLE_H, "chars": ["\ue001"]}]}, open(f"{font_dir}/title.json","w"), indent=2)
TITLE_ADV = advance(tw, th, TITLE_H)

# ---------------------------------------------------------------- space font (negative/positive advances)
adv = {}
for i in range(11):
    adv[chr(0xF100+i)] = 2**i
    adv[chr(0xF200+i)] = -(2**i)
json.dump({"providers": [{"type": "space", "advances": adv}]}, open(f"{font_dir}/space.json","w"), indent=2)

# ---------------------------------------------------------------- shader (only the vertex shader is replaced)
VSH_121_11 = r'''#version 330

#moj_import <minecraft:dynamictransforms.glsl>
#moj_import <minecraft:projection.glsl>

in vec3 Position;
in vec4 Color;
in vec2 UV0;
in ivec2 UV2;

uniform sampler2D Sampler2;

out float sphericalVertexDistance;
out float cylindricalVertexDistance;
out vec4 vertexColor;
out vec2 texCoord0;

// Veyrion HUD (Minecraft 1.21.6 - 1.21.11)
// marker colour: R=78, B=36 (text) / 37 (image), G = 92 + rowOffset (GUI px). Shadow = colour*0.25 -> hidden.
void main() {
    gl_Position = ProjMat * ModelViewMat * vec4(Position, 1.0);
    sphericalVertexDistance = 0.0;
    cylindricalVertexDistance = 0.0;
    vertexColor = Color * texelFetch(Sampler2, UV2 / 16, 0);
    texCoord0 = UV0;

    vec3 c = Color.rgb * 255.0;
    bool real   = abs(c.r - 78.0) < 0.6 && (abs(c.b - 36.0) < 0.6 || abs(c.b - 37.0) < 0.6);
    bool shadow = abs(c.r - 19.0) < 1.1 && abs(c.b - 9.0) < 1.1;
    if (real || shadow) {
        float W = floor(2.0 / abs(ProjMat[0][0]) + 0.5);
        float H = floor(2.0 / abs(ProjMat[1][1]) + 0.5);
        float row = real ? (c.g - 92.0) : 0.0;
        gl_Position.x += 2.0 * ceil(W / 2.0) / W;
        gl_Position.y -= 2.0 * floor(row + 0.5) / H;
        if (shadow) {
            vertexColor = vec4(0.0);
        } else if (abs(c.b - 36.0) < 0.6) {
            vertexColor = vec4(1.0, 1.0, 1.0, Color.a);   // HUD text colour (putih)
        } else {
            vertexColor = vec4(1.0, 1.0, 1.0, Color.a);   // pre-coloured image glyphs
        }
    }
}
'''
VSH_121_1 = r'''#version 150

in vec3 Position;
in vec4 Color;
in vec2 UV0;
in ivec2 UV2;

uniform sampler2D Sampler2;
uniform mat4 ModelViewMat;
uniform mat4 ProjMat;

out float vertexDistance;
out vec4 vertexColor;
out vec2 texCoord0;

// Veyrion HUD marker colour: R=78 (0x4E), B=36 (text) / 37 (image), G = 92 + rowOffset (GUI px)
// Vanilla drop-shadow of that colour is (19, x, 9) -> hidden.
void main() {
    gl_Position = ProjMat * ModelViewMat * vec4(Position, 1.0);
    vertexDistance = 0.0;
    vertexColor = Color * texelFetch(Sampler2, UV2 / 16, 0);
    texCoord0 = UV0;

    vec3 c = Color.rgb * 255.0;
    bool real   = abs(c.r - 78.0) < 0.6 && (abs(c.b - 36.0) < 0.6 || abs(c.b - 37.0) < 0.6);
    bool shadow = abs(c.r - 19.0) < 0.6 && abs(c.b - 9.0) < 0.6 ;
    if (real || shadow) {
        float W = floor(2.0 / abs(ProjMat[0][0]) + 0.5);   // GUI-scaled width
        float H = floor(2.0 / abs(ProjMat[1][1]) + 0.5);   // GUI-scaled height
        float row = real ? (c.g - 92.0) : 0.0;
        // text starts at the screen centre (component width = 0) -> push to the right edge
        gl_Position.x += 2.0 * ceil(W / 2.0) / W;
        gl_Position.y -= 2.0 * floor(row + 0.5) / H;
        if (shadow) {
            vertexColor = vec4(0.0);
        } else if (abs(c.b - 36.0) < 0.6) {
            vertexColor = vec4(1.0, 1.0, 1.0, Color.a);   // HUD text colour (putih)
        } else {
            vertexColor = vec4(1.0, 1.0, 1.0, Color.a);                           // pre-coloured image glyphs
        }
    }
}
'''
open(f"{PACK}/assets/minecraft/shaders/core/rendertype_text.vsh","w").write(VSH_121_11)
os.makedirs(f"{ROOT}/tools", exist_ok=True)
open(f"{ROOT}/tools/rendertype_text_1.21.1.vsh","w").write(VSH_121_1)


# ---------------------------------------------------------------- hide boss bar sprites
transparent = Image.new("RGBA", (182, 5), (0,0,0,0))
names = []
for col in ("pink","blue","red","green","yellow","purple","white"):
    names += [f"{col}_background", f"{col}_progress"]
for n in (6,10,12,20): names += [f"notched_{n}_background", f"notched_{n}_progress"]
for n in names: transparent.save(f"{PACK}/assets/minecraft/textures/gui/sprites/boss_bar/{n}.png")

json.dump({"pack": {"pack_format": 75, "supported_formats": [34, 99], "description": "Veyrion Roleplay HUD"}}, open(f"{PACK}/pack.mcmeta","w"), indent=2)
try: shutil.copy(LOGO_SRC, f"{PACK}/pack.png")
except Exception: pass

# ---------------------------------------------------------------- ItemsAdder contents folder
IA = os.path.join(ROOT, "ItemsAdder")
if os.path.isdir(IA): shutil.rmtree(IA)
ia_ns = f"{IA}/contents/veyrion"
os.makedirs(f"{ia_ns}/configs")
shutil.copytree(f"{PACK}/assets", f"{ia_ns}/resourcepack")   # IA: resourcepack/ == assets/
open(f"{ia_ns}/configs/veyrion_hud.yml", "w").write("info:\n  namespace: veyrion\n")
iz = os.path.join(ROOT, "VeyrionHUD-ItemsAdder.zip")
with zipfile.ZipFile(iz, "w", zipfile.ZIP_DEFLATED) as z:
    for dp, _, fs in os.walk(IA):
        for f in fs:
            full = os.path.join(dp, f); z.write(full, os.path.relpath(full, IA))

# ---------------------------------------------------------------- zip + java constants
zp = os.path.join(ROOT, "VeyrionHUD-ResourcePack.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for dp, _, fs in os.walk(PACK):
        for f in fs:
            full = os.path.join(dp, f); z.write(full, os.path.relpath(full, PACK))
consts = f'''package id.veyrion.hud;

/** GENERATED by tools/gen_assets.py - do not edit by hand. */
final class Generated {{
    private Generated() {{}}
    static final int LOGO_ADV = {LOGO_ADV};
    static final int LOGO_H = {LOGO_H};
    static final int TITLE_ADV = {TITLE_ADV};
    static final int TITLE_H = {TITLE_H};
    static final int ICON_ADV = {ICON_ADV};
    static final int ICON_H = {ICON_H};
    static final char ICON_BASE = (char) 0x{ICON_BASE:X};
    static final String[] ICON_NAMES = {{{", ".join('"'+n+'"' for n,_ in icons)}}};
}}
'''
os.makedirs(f"{ROOT}/src/main/java/id/veyrion/hud", exist_ok=True)
open(f"{ROOT}/src/main/java/id/veyrion/hud/Generated.java","w").write(consts)
print("advances logo/title/icon:", LOGO_ADV, TITLE_ADV, ICON_ADV, "title px", tw, th)

# contact sheet for preview
prev = Image.new("RGBA", (sheet.width+20, 260), (150,170,200,255))
prev.paste(sheet, (10,10), sheet)
prev.paste(logo, (10,100), logo)
t = Image.open(f"{tex_dir}/title.png"); prev.paste(t, (200,100), t)
prev.save("/tmp/preview.png")
