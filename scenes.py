"""Illustration library for makefun entry.
Provides scene drawing functions using Pillow.
"""
import math, random
from PIL import Image, ImageDraw, ImageFont

# Shared helpers

def vertical_gradient(draw, w, h, top_color, bottom_color):
    for y in range(h):
        ratio = y / (h - 1)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

def star_field(draw, w, h, seed=42, count=100):
    rnd = random.Random(seed)
    for _ in range(count):
        x = rnd.randint(0, w-1)
        y = rnd.randint(0, h-1)
        brightness = rnd.randint(150, 255)
        draw.point((x, y), fill=(brightness, brightness, brightness))

def sun_moon(draw, cx, cy, radius, color, glow_color):
    """Draw a sun or moon with a simple soft glow.

    The ``draw`` object is created on an ``RGBA`` layer, so we can use
    semi‑transparent fills directly. We draw several concentric ellipses
    with decreasing opacity to simulate a halo.
    """
    # Draw outer glow rings.
    for i in range(4, 0, -1):
        r = radius + i * 6
        # Alpha scales down for outer rings.
        alpha = int(80 / i)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=glow_color + (alpha,))
    # Core disc.
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)

def dashed_arc(draw, bbox, start, end, dash_len=5, gap_len=5, width=2, fill=(255,255,255)):
    # approximate with many points
    a0 = math.radians(start)
    a1 = math.radians(end)
    steps = int((a1-a0)*50)
    points = []
    cx = (bbox[0]+bbox[2])/2
    cy = (bbox[1]+bbox[3])/2
    rx = (bbox[2]-bbox[0])/2
    ry = (bbox[3]-bbox[1])/2
    for i in range(steps+1):
        a = a0 + (a1-a0)*i/steps
        x = cx + rx*math.cos(a)
        y = cy + ry*math.sin(a)
        points.append((x, y))
    # draw dashes
    dist = 0
    on = True
    seg_start = points[0]
    for i in range(1, len(points)):
        p0, p1 = points[i-1], points[i]
        seg_len = math.hypot(p1[0]-p0[0], p1[1]-p0[1])
        while seg_len > 0:
            step = min(dash_len if on else gap_len, seg_len)
            t = step/seg_len
            nx = p0[0] + (p1[0]-p0[0])*t
            ny = p0[1] + (p1[1]-p0[1])*t
            if on:
                draw.line([p0, (nx, ny)], fill=fill, width=width)
            p0 = (nx, ny)
            seg_len -= step
            if on:
                on = False
            else:
                on = True

def explosion_burst(draw, cx, cy, radius, seed=0):
    rnd = random.Random(seed)
    for i in range(12):
        angle = rnd.random()*2*math.pi
        x = cx + math.cos(angle)*radius
        y = cy + math.sin(angle)*radius
        draw.line([(cx, cy), (x, y)], fill=(255,180,0), width=2)
    draw.ellipse([cx-radius/3, cy-radius/3, cx+radius/3, cy+radius/3], fill=(255,200,50))

def silhouette_skyline(draw, w, h, building_count=7, seed=1):
    rnd = random.Random(seed)
    base = h*0.75
    x = 0
    for _ in range(building_count):
        bw = rnd.randint(int(w*0.08), int(w*0.15))
        bh = rnd.randint(int(h*0.2), int(h*0.5))
        draw.rectangle([x, base-bh, x+bw, base], fill=(30,30,30))
        # windows
        win_rows = rnd.randint(2,4)
        win_cols = rnd.randint(2,5)
        win_w = bw//(win_cols*2)
        win_h = bh//(win_rows*3)
        for r in range(win_rows):
            for c in range(win_cols):
                if rnd.random() < 0.3:
                    wx = x + (c*2+1)*win_w
                    wy = base - bh + (r*3+1)*win_h
                    draw.rectangle([wx, wy, wx+win_w, wy+win_h], fill=(255,215,0))
        x += bw + rnd.randint(5,15)

def ground_band(draw, w, h, height_ratio=0.1, color=(50,30,20)):
    y0 = int(h* (1 - height_ratio))
    draw.rectangle([0, y0, w, h], fill=color)

def scene_keys():
    return [
        "cop31_dome", "kryvyi_night", "riyadh_intercept", "mercury_capture",
        "warsaw_nato", "hague_scales", "hodeidah_port", "akvan_cyclone",
        "wellington_cricket", "copenhagen_court", "london_cyber", "sumy_himars",
        "delhi_forum", "delhi_vaccine", "jakarta_youtube", "newyork_vendors",
    ]

def draw_scene(base_img, key, box, banner):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    layer = Image.new('RGBA', (w, h))
    d = ImageDraw.Draw(layer)
    scene_func = globals()["scene_" + key]
    scene_func(d, w, h)
    # banner strip
    banner_h = max(int(h*0.16), 14)
    banner_y = h - banner_h
    overlay = Image.new('RGBA', (w, banner_h), (0,0,0,180))
    layer.paste(overlay, (0, banner_y), overlay)
    # text
    txt = banner
    size = max(int(banner_h*0.6), 9)
    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    while True:
        try:
            font = ImageFont.truetype(font_path, size)
        except Exception:
            font = ImageFont.load_default()
            break
        bb = d.textbbox((0, 0), txt, font=font)
        if bb[2] - bb[0] <= w - 16 or size <= 9:
            break
        size -= 1
    # Pillow 10 removed ImageDraw.textsize; use textbbox for accurate dimensions
    bbox = d.textbbox((0, 0), txt, font=font)
    txt_w = bbox[2] - bbox[0]
    txt_h = bbox[3] - bbox[1]
    pad = 5
    d.text((pad, banner_y + (banner_h - txt_h)//2), txt, font=font, fill=(255,215,0))
    base_img.paste(layer.convert('RGB'), (x0, y0))
# Scene 1: cop31_dome
def scene_cop31_dome(d, w, h):
    # sky gradient sunrise
    vertical_gradient(d, w, h, (255,180,100), (255,220,180))
    # glass dome (large ellipse)
    dome_bbox = [w*0.1, h*0.2, w*0.9, h*0.8]
    d.ellipse(dome_bbox, outline=(180,180,255), width=3)
    # dome panel lines (vertical slices)
    for i in range(5, 95, 10):
        x = dome_bbox[0] + (dome_bbox[2]-dome_bbox[0])*i/100
        d.line([(x, dome_bbox[1]), (x, dome_bbox[3])], fill=(180,180,255), width=1)
    # rising sun behind dome
    sun_moon(d, int(w*0.3), int(h*0.75), int(h*0.12), (255,210,50), (255,255,200))
    # thermometer at right side
    th_x = int(w*0.85)
    d.rounded_rectangle([th_x, int(h*0.3), th_x+12, int(h*0.75)], radius=4, outline=(200,200,200), width=2)
    bulb_r = 8
    d.ellipse([th_x-2, int(h*0.75)-bulb_r, th_x+14, int(h*0.75)+bulb_r], fill=(255,0,0))
    # red line across dome (ribbon)
    d.line([ (dome_bbox[0]+5, dome_bbox[1]+20), (dome_bbox[2]-5, dome_bbox[3]-20) ], fill=(255,0,0), width=3)
    # small clock face on dome left
    cx = int(dome_bbox[0]+30)
    cy = int(dome_bbox[1]+30)
    r = 12
    d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(220,220,220), width=2)
    # hour hand
    d.line([ (cx, cy), (cx + r*0.5, cy) ], fill=(220,220,220), width=2)
    # minute hand
    d.line([ (cx, cy), (cx, cy - r*0.8) ], fill=(220,220,220), width=2)
    ground_band(d, w, h, 0.12, (70,50,30))

# Scene 2: kryvyi_night
def scene_kryvyi_night(d, w, h):
    # night sky gradient
    vertical_gradient(d, w, h, (10,10,40), (2,2,20))
    star_field(d, w, h, seed=7, count=150)
    # skyline silhouettes
    silhouette_skyline(d, w, h, building_count=6, seed=3)
    # two missile arcs descending
    dash_color = (255,120,0)
    # left missile
    bbox1 = [w*0.2, h*0.2, w*0.4, h*0.6]
    dashed_arc(d, bbox1, 45, 135, dash_len=6, gap_len=4, width=2, fill=dash_color)
    # right missile
    bbox2 = [w*0.6, h*0.25, w*0.8, h*0.65]
    dashed_arc(d, bbox2, 30, 120, dash_len=6, gap_len=4, width=2, fill=dash_color)
    # explosion burst over low restaurant block (approx center)
    explosion_burst(d, int(w*0.55), int(h*0.78), int(min(w,h)*0.08), seed=5)
    # ambulance lights at street level (red/blue dots)
    for i in range(4):
        x = int(w*0.1 + i* (w*0.2))
        y = int(h*0.85)
        d.ellipse([x-3, y-3, x+3, y+3], fill=(255,0,0))
        d.ellipse([x+6, y-3, x+12, y+3], fill=(0,0,255))
    ground_band(d, w, h, 0.15, (30,25,20))

def scene_riyadh_intercept(d, w, h):
    # Night sky gradient with deep blues
    vertical_gradient(d, w, h, (5,5,30), (0,0,10))
    # Pale crescent moon
    moon_cx, moon_cy, moon_r = int(w*0.8), int(h*0.2), int(min(w,h)*0.07)
    draw = d
    # moon core
    draw.ellipse([moon_cx-moon_r, moon_cy-moon_r, moon_cx+moon_r, moon_cy+moon_r], fill=(230,230,250))
    # crescent cutout
    draw.ellipse([moon_cx-moon_r*0.6, moon_cy-moon_r, moon_cx+moon_r*1.4, moon_cy+moon_r], fill=(0,0,10))
    # Modern skyline with one very tall tower
    silhouette_skyline(d, w, h, building_count=8, seed=42)
    # Tall tower overlay (white outline)
    tower_x = int(w*0.6)
    tower_height = int(h*0.55)
    base_y = int(h*0.75)
    draw.rectangle([tower_x-6, base_y-tower_height, tower_x+6, base_y], outline=(200,200,200), width=2)
    # Missile arcs with interception bursts
    dash_color = (255,150,0)
    for i, start in enumerate([30, 60, 90]):
        bbox = [w*0.1+i*0.3, h*0.2, w*0.3+i*0.3, h*0.6]
        dashed_arc(d, bbox, start, start+80, dash_len=5, gap_len=5, width=2, fill=dash_color)
        # burst at end of each arc
        cx = int(bbox[0] + (bbox[2]-bbox[0])*0.5)
        cy = int(bbox[1] + (bbox[3]-bbox[1])*0.5)
        explosion_burst(d, cx, cy, int(min(w,h)*0.04), seed=i)
    ground_band(d, w, h, 0.12, (30,20,10))

def scene_mercury_capture(d, w, h):
    # Star‑filled dark background
    vertical_gradient(d, w, h, (0,0,20), (0,0,5))
    star_field(d, w, h, seed=99, count=120)
    # Large cratered grey planet centered
    cx, cy, r = int(w*0.5), int(h*0.55), int(min(w,h)*0.3)
    draw = d
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=(130,130,130))
    # simple crater rings
    for i in range(3):
        cr = r*0.6 - i*0.15*r
        draw.ellipse([cx-cr, cy-cr, cx+cr, cy+cr], outline=(100,100,100), width=2)
    # shading for sphere
    for offset in range(0, r, 6):
        alpha = int(80 * (1 - offset/r))
        draw.ellipse([cx-r+offset, cy-r, cx+r-offset, cy+r], fill=(0,0,0,alpha))
    # Probe with solar panels approaching on dashed arc
    probe_x, probe_y = int(w*0.2), int(h*0.2)
    draw.rectangle([probe_x-4, probe_y-4, probe_x+4, probe_y+4], fill=(180,180,180))
    # solar panels wings
    panel_w, panel_h = int(w*0.08), int(h*0.04)
    draw.rectangle([probe_x- panel_w-4, probe_y- panel_h, probe_x-4, probe_y+ panel_h], fill=(220,220,0))
    draw.rectangle([probe_x+4, probe_y- panel_h, probe_x+ panel_w+4, probe_y+ panel_h], fill=(220,220,0))
    # dashed approach arc
    bbox = [probe_x-20, probe_y-20, cx- r, cy- r]
    dashed_arc(d, bbox, 45, 120, dash_len=4, gap_len=4, width=2, fill=(200,200,200))
    # sun rays from corner (top‑left)
    for i in range(8):
        angle = math.radians(i*45)
        x2 = int(0 + math.cos(angle)*w*0.4)
        y2 = int(0 + math.sin(angle)*h*0.4)
        draw.line([0,0,x2,y2], fill=(255,230,150), width=2)
    ground_band(d, w, h, 0.08, (40,30,20))

def scene_warsaw_nato(d, w, h):
    # Dusk sky gradient
    vertical_gradient(d, w, h, (80,50,100), (30,20,60))
    # City skyline silhouettes
    silhouette_skyline(d, w, h, building_count=9, seed=7)
    draw = d
    # Four‑point NATO star in sky (center)
    star_center = (int(w*0.5), int(h*0.3))
    star_radius = int(min(w,h)*0.08)
    pts = []
    for i in range(8):
        angle = math.radians(i*45)
        r = star_radius if i%2==0 else star_radius*0.4
        x = star_center[0] + r*math.cos(angle)
        y = star_center[1] + r*math.sin(angle)
        pts.append((x,y))
    draw.polygon(pts, fill=(255,215,0))
    # Thin missile trail crossing sky
    trail_bbox = [w*0.2, h*0.2, w*0.8, h*0.6]
    dashed_arc(d, trail_bbox, 20, 140, dash_len=6, gap_len=3, width=2, fill=(180,180,255))
    # Searchlight beams (white cones)
    for base_x in (int(w*0.1), int(w*0.9)):
        for offset in range(-30,31,30):
            end = (base_x+offset, int(h*0.05))
            draw.polygon([ (base_x, h), (base_x-20, h-40), end, (base_x+20, h-40) ], fill=(255,255,255,30))
    ground_band(d, w, h, 0.10, (20,15,10))
# Scene 6: hague_scales
def scene_hague_scales(d, w, h):
    """Two classical columns framing a balance scale.
    Elements:
    * Gradient sky (dawn‑like)
    * Two Doric columns
    * Central balance beam with two pans, balanced
    * Pediment silhouette above the columns
    """
    vertical_gradient(d, w, h, (240,200,150), (200,150,100))
    col_w = w * 0.12
    col_h = h * 0.65
    left_x = w * 0.2
    right_x = w * 0.68
    for x in (left_x, right_x):
        d.rectangle([x, h - col_h, x + col_w, h], fill=(30,30,30))
        cap_h = col_h * 0.07
        d.rectangle([x - col_w * 0.1, h - col_h - cap_h, x + col_w * 1.1, h - col_h], fill=(30,30,30))
    beam_y = h * 0.35
    beam_len = w * 0.4
    beam_x0 = (w - beam_len) / 2
    beam_x1 = beam_x0 + beam_len
    d.line([beam_x0, beam_y, beam_x1, beam_y], fill=(220,220,220), width=3)
    d.line([w/2, beam_y, w/2, h*0.6], fill=(220,220,220), width=2)
    pan_r = w * 0.04
    for px in (beam_x0, beam_x1):
        d.ellipse([px - pan_r, beam_y + pan_r, px + pan_r, beam_y + 3*pan_r], outline=(200,200,200), width=2)
        d.line([px, beam_y, px, beam_y + pan_r], fill=(200,200,200), width=1)
    ped_top = h - col_h - col_h * 0.07 - h * 0.12
    ped_bottom = h - col_h - col_h * 0.07
    d.polygon([
        (left_x - col_w * 0.2, ped_bottom),
        (right_x + col_w * 1.2, ped_bottom),
        ((left_x + right_x + col_w)/2, ped_top)
    ], fill=(30,30,30))
    ground_band(d, w, h, 0.12, (70,50,30))
# Scene 7: hodeidah_port
def scene_hodeidah_port(d, w, h):
    """Port scene with cranes, cargo ship, containers and a warning sign.
    Elements:
    * Twilight sky gradient
    * Two dockside cranes (silhouetted)
    * Cargo ship hull silhouette
    * Stacked containers on quay
    * Yellow warning triangle on the quay
    """
    vertical_gradient(d, w, h, (30,30,80), (10,10,40))
    water_y = h * 0.65
    d.rectangle([0, water_y, w, h], fill=(15,25,60))
    crane_xs = [w * 0.2, w * 0.75]
    for cx in crane_xs:
        d.line([cx, water_y, cx, water_y - h * 0.25], fill=(30,30,30), width=4)
        arm_len = w * 0.12
        d.line([cx, water_y - h * 0.25, cx + arm_len, water_y - h * 0.25], fill=(30,30,30), width=4)
        hook_y = water_y - h * 0.25 + h * 0.05
        d.line([cx + arm_len, water_y - h * 0.25, cx + arm_len, hook_y], fill=(30,30,30), width=3)
    ship_h = h * 0.07
    ship_y = water_y - ship_h - h * 0.02
    d.rectangle([w*0.35, ship_y, w*0.85, ship_y + ship_h], fill=(30,30,30))
    d.rectangle([w*0.45, ship_y - ship_h*0.6, w*0.75, ship_y], fill=(30,30,30))
    cont_w = w * 0.08
    cont_h = h * 0.04
    base_x = w * 0.05
    base_y = water_y
    for row in range(3):
        for col in range(2):
            x0 = base_x + col * (cont_w + 4)
            y0 = base_y - (row+1)*(cont_h+2)
            d.rectangle([x0, y0, x0+cont_w, y0+cont_h], fill=(45,45,45))
    tri_center_x = w * 0.4
    tri_center_y = water_y - cont_h*3 - 10
    size = 12
    d.polygon([
        (tri_center_x, tri_center_y - size),
        (tri_center_x - size, tri_center_y + size),
        (tri_center_x + size, tri_center_y + size)
    ], fill=(255,215,0))
    ground_band(d, w, h, 0.12, (50,30,20))
# Scene 8: akvan_cyclone
def scene_akvan_cyclone(d, w, h):
    """Coastal cyclone with spiraling arcs, palm trees, shelters and rain.
    Elements:
    * Dark storm sky gradient
    * Concentric arcs forming a cyclone swirl
    * Silhouetted palm trees bending in wind
    * Shelter tents on higher ground
    * Diagonal rain streaks
    """
    vertical_gradient(d, w, h, (20,20,60), (5,5,30))
    center_x = w * 0.3
    center_y = h * 0.4
    max_radius = min(w, h) * 0.35
    for i in range(4):
        r = max_radius * (0.6 - i*0.1)
        bbox = [center_x - r, center_y - r, center_x + r, center_y + r]
        dashed_arc(d, bbox, 0, 360, dash_len=8, gap_len=6, width=2, fill=(200,200,255))
    trunk_h = h * 0.25
    for tx in (w*0.15, w*0.55):
        d.line([tx, h*0.75, tx, h*0.75 - trunk_h], fill=(30,30,30), width=4)
        for ang in (-30, 0, 30):
            rad = math.radians(ang)
            leaf_len = trunk_h * 0.5
            x1 = tx + leaf_len * math.cos(rad)
            y1 = h*0.75 - trunk_h + leaf_len * math.sin(rad)
            d.line([tx, h*0.75 - trunk_h, x1, y1], fill=(30,30,30), width=3)
    ground_y = h * 0.85
    for cx in (w*0.4, w*0.7):
        size = w * 0.08
        d.polygon([
            (cx - size, ground_y),
            (cx + size, ground_y),
            (cx, ground_y - size*1.2)
        ], outline=(200,200,200), fill=None)
    rnd = random.Random(777)
    for i in range(30):
        x0 = rnd.randint(0, w)
        y0 = rnd.randint(0, int(h*0.6))
        length = h * 0.07
        x1 = x0 + length * 0.3
        y1 = y0 + length
        d.line([x0, y0, x1, y1], fill=(180,180,255), width=1)
    ground_band(d, w, h, 0.15, (30,20,15))

# Scene 9: Wellington Cricket
def scene_wellington_cricket(d, w, h):
    """Green pitch, three stumps, a bat, red ball, crowd silhouette."""
    vertical_gradient(d, w, h, (135, 206, 250), (180, 220, 250))
    # Pitch trapezoid for perspective
    pitch = [
        (w * 0.30, h * 0.65),
        (w * 0.70, h * 0.65),
        (w * 0.62, h * 0.40),
        (w * 0.38, h * 0.40),
    ]
    d.polygon(pitch, fill=(34, 139, 34))
    # Stumps
    stump_w = w * 0.008
    stump_h = h * 0.12
    base_x = w * 0.5 - stump_w * 1.5
    top_y = h * 0.40
    for i in range(3):
        x0 = base_x + i * (stump_w * 2)
        d.rectangle([x0, top_y, x0 + stump_w, top_y + stump_h], fill=(200,200,200))
        # Bails
        bail_y = top_y + stump_h * 0.2
        d.rectangle([x0 - stump_w * 0.3, bail_y, x0 + stump_w * 1.3, bail_y + stump_w * 0.4], fill=(220,220,220))
    # Bat (simple shape)
    bat_handle = [
        (w * 0.42, h * 0.48), (w * 0.425, h * 0.55), (w * 0.435, h * 0.55), (w * 0.44, h * 0.48)
    ]
    bat_blade = [
        (w * 0.44, h * 0.48), (w * 0.51, h * 0.42), (w * 0.515, h * 0.425), (w * 0.445, h * 0.48)
    ]
    d.polygon(bat_handle, fill=(100,70,30))
    d.polygon(bat_blade, fill=(150,100,50))
    # Red ball
    r = w * 0.015
    cx, cy = w * 0.48, h * 0.45
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(220,20,60))
    # Crowd silhouette band
    d.rectangle([0, h * 0.20, w, h * 0.20 + h * 0.12], fill=(30,30,30))
    ground_band(d, w, h, 0.10, (50,30,20))

# Scene 10: Copenhagen Court
def scene_copenhagen_court(d, w, h):
    """Courthouse façade with columns, steps, gavel and Danish‑red flag accent."""
    vertical_gradient(d, w, h, (250,220,180), (220,190,150))
    # Steps
    step_h = h * 0.03
    step_start = w * 0.4
    step_end = w * 0.6
    for i in range(5):
        y = h * 0.65 + i * step_h
        x0 = step_start - i * (step_start - step_end) / 10
        x1 = step_end + i * (step_start - step_end) / 10
        d.rectangle([x0, y, x1, y + step_h], fill=(70,70,70))
    # Columns
    col_w = w * 0.04
    col_h = h * 0.25
    for cx in (w * 0.45, w * 0.55):
        d.rectangle([cx - col_w/2, h * 0.40, cx + col_w/2, h * 0.40 + col_h], fill=(30,30,30))
        d.rectangle([cx - col_w*0.6, h * 0.38, cx + col_w*0.6, h * 0.40], fill=(30,30,30))
    # Gavel
    d.rectangle([w*0.5 - w*0.005, h*0.55, w*0.5 + w*0.005, h*0.70], fill=(100,70,30))
    d.rectangle([w*0.5 - w*0.015, h*0.55 - w*0.015, w*0.5 + w*0.015, h*0.55], fill=(100,70,30))
    # Danish‑red flag
    d.rectangle([w*0.68, h*0.35, w*0.68 + w*0.04, h*0.35 + h*0.06], fill=(255,0,0))
    ground_band(d, w, h, 0.12, (50,30,20))

# Scene 11: London Cyber
def scene_london_cyber(d, w, h):
    """Dark cyber‑punk: glowing circuit lines, central shield, skyline silhouette."""
    vertical_gradient(d, w, h, (10,10,20), (5,5,10))
    rnd = random.Random(1234)
    for _ in range(60):
        x0 = rnd.randint(0, w)
        y0 = rnd.randint(0, h)
        x1 = x0 + rnd.randint(-30,30)
        y1 = y0 + rnd.randint(-30,30)
        d.line([x0, y0, x1, y1], fill=(0,255,100,120), width=1)
        r = w * 0.008
        d.ellipse([x0 - r, y0 - r, x0 + r, y0 + r], fill=(0,255,100))
    # Shield outline (hexagon)
    cx, cy = w*0.5, h*0.45
    rad = min(w,h) * 0.12
    pts = []
    for i in range(6):
        ang = math.radians(60*i - 30)
        pts.append((cx + rad*math.cos(ang), cy + rad*math.sin(ang)))
    d.polygon(pts, outline=(0,255,100), fill=None)
    silhouette_skyline(d, w, h, building_count=8, seed=9)
    ground_band(d, w, h, 0.10, (30,20,25))

# Scene 12: sumy_himars
def scene_sumy_himars(d, w, h):
    """Wheeled HIMARS launcher on a ridge firing a bright rocket arc towards a distant bunker.
    Elements:
    * Dusky gradient sky (orange‑to‑deep purple)
    * Ridge silhouette (dark shape across bottom)
    * Launcher silhouette with two wheels
    * Dashed rocket trajectory arc with a glow
    * Distant bunker block silhouette
    """
    # Sky gradient
    vertical_gradient(d, w, h, (255, 140, 60), (80, 30, 100))
    # Ridge silhouette near bottom
    ridge_h = h * 0.2
    d.polygon([
        (0, h - ridge_h),
        (w * 0.3, h - ridge_h * 1.3),
        (w * 0.6, h - ridge_h),
        (w, h - ridge_h * 1.2),
        (w, h),
        (0, h)
    ], fill=(30, 30, 30))
    # Launcher body
    launch_w = w * 0.15
    launch_h = h * 0.08
    lx = w * 0.25
    ly = h - ridge_h - launch_h
    d.rectangle([lx, ly, lx + launch_w, ly + launch_h], fill=(30, 30, 30))
    # Wheels (two circles)
    wheel_r = launch_h * 0.4
    for wx in (lx + launch_w * 0.25, lx + launch_w * 0.75):
        d.ellipse([wx - wheel_r, ly + launch_h - wheel_r,
                   wx + wheel_r, ly + launch_h + wheel_r], fill=(30, 30, 30))
    # Rocket arc – bright orange dashed line
    arc_bbox = [lx + launch_w, ly - h * 0.3, w * 0.85, ly]
    dashed_arc(d, arc_bbox, 45, 120, dash_len=5, gap_len=4, width=3, fill=(255, 165, 0))
    # Explosion burst at target area
    explosion_burst(d, int(w * 0.78), int(h * 0.45), int(min(w, h) * 0.04), seed=9)
    # Distant bunker block silhouette
    bunker_w = w * 0.12
    bunker_h = h * 0.15
    bx = w * 0.75
    by = h * 0.55
    d.rectangle([bx, by, bx + bunker_w, by + bunker_h], fill=(40, 40, 40))
    # Ground band
    ground_band(d, w, h, 0.12, (70, 50, 30))

# Scene 13: delhi_forum
def scene_delhi_forum(d, w, h):
    """Parliament‑like domed building with a row of small flags at dawn.
    Elements:
    * Dawn sky gradient (soft pink to light blue)
    * Central domed silhouette
    * Flagpoles with tiny flags
    * Ground band
    """
    vertical_gradient(d, w, h, (255, 200, 180), (180, 210, 255))
    # Domed building silhouette – large ellipse atop a rectangle
    base_h = h * 0.25
    base_y = h - base_h - h * 0.1
    d.rectangle([w * 0.35, base_y, w * 0.65, base_y + base_h], fill=(30, 30, 30))
    dome_r = w * 0.12
    cx = w * 0.5
    cy = base_y
    d.ellipse([cx - dome_r, cy - dome_r, cx + dome_r, cy + dome_r], outline=(30, 30, 30), width=2)
    # Flagpoles in front (small vertical lines)
    pole_count = 5
    for i in range(pole_count):
        px = w * 0.38 + i * (w * 0.04)
        pole_h = h * 0.08
        d.line([(px, base_y + base_h), (px, base_y + base_h - pole_h)], fill=(30, 30, 30), width=2)
        # Small triangular flag
        flag_w = w * 0.015
        flag_h = pole_h * 0.5
        d.polygon([
            (px, base_y + base_h - pole_h),
            (px + flag_w, base_y + base_h - pole_h + flag_h / 2),
            (px, base_y + base_h - pole_h + flag_h)
        ], fill=(255, 215, 0))
    ground_band(d, w, h, 0.10, (50, 30, 20))

# Scene 14: delhi_vaccine
def scene_delhi_vaccine(d, w, h):
    """Large hen silhouette, shield with syringe, and egg shapes at base.
    Elements:
    * Soft barn‑red accent sky (light rust to deep brown)
    * Hen silhouette (profile)
    * Shield beside hen containing a syringe
    * Small egg ellipses at the bottom
    * Ground band with brown tone
    """
    vertical_gradient(d, w, h, (230, 170, 150), (120, 70, 50))
    # Hen silhouette – simple angular shape
    hen_center_x = w * 0.35
    hen_center_y = h * 0.55
    hen_w = w * 0.25
    hen_h = h * 0.3
    hen_pts = [
        (hen_center_x, hen_center_y - hen_h * 0.4),
        (hen_center_x + hen_w * 0.2, hen_center_y - hen_h * 0.2),
        (hen_center_x + hen_w * 0.4, hen_center_y),
        (hen_center_x + hen_w * 0.2, hen_center_y + hen_h * 0.2),
        (hen_center_x, hen_center_y + hen_h * 0.4),
        (hen_center_x - hen_w * 0.1, hen_center_y + hen_h * 0.2),
        (hen_center_x - hen_w * 0.2, hen_center_y)
    ]
    d.polygon(hen_pts, fill=(30, 30, 30))
    # Shield with syringe to the right of hen
    shield_cx = w * 0.65
    shield_cy = hen_center_y
    shield_r = min(w, h) * 0.08
    # Shield outline (simple hexagon)
    shield_pts = []
    for i in range(6):
        ang = math.radians(60 * i - 30)
        shield_pts.append((shield_cx + shield_r * math.cos(ang), shield_cy + shield_r * math.sin(ang)))
    d.polygon(shield_pts, outline=(30, 30, 30), fill=None)
    # Syringe – vertical line with a small barrel
    syr_x = shield_cx
    syr_y0 = shield_cy - shield_r * 0.6
    syr_y1 = shield_cy + shield_r * 0.6
    d.line([(syr_x, syr_y0), (syr_x, syr_y1)], fill=(30, 30, 30), width=2)
    barrel_r = shield_r * 0.15
    d.ellipse([syr_x - barrel_r, syr_y0 - barrel_r, syr_x + barrel_r, syr_y0 + barrel_r], fill=(30, 30, 30))
    # Small eggs at base
    egg_r = w * 0.015
    for i in range(3):
        ex = w * 0.55 + i * egg_r * 3
        ey = h * 0.78
        d.ellipse([ex - egg_r, ey - egg_r, ex + egg_r, ey + egg_r], fill=(255, 250, 240))
    ground_band(d, w, h, 0.12, (70, 45, 30))

# Scene 15: Jakarta YouTube
def scene_jakarta_youtube(d, w, h):
    """Illustrates a YouTube‑style interface.
    Elements:
    * Rounded‑rectangle play button with a triangle.
    * Grid of small account tiles, each crossed out with an "X".
    * One oversized question‑mark tile.
    * Subtle gradient sky and ground band for consistency.
    """
    # Sky gradient (soft blue to darker)
    vertical_gradient(d, w, h, (180, 210, 255), (30, 30, 80))

    # Play button – centered, rounded rectangle with triangle inside
    btn_w, btn_h = w * 0.25, h * 0.15
    btn_x0 = (w - btn_w) / 2
    btn_y0 = h * 0.1
    d.rounded_rectangle([btn_x0, btn_y0, btn_x0 + btn_w, btn_y0 + btn_h], radius=8, fill=(255, 0, 0))
    # Triangle (pointing right) inside the button
    tri_center_x = btn_x0 + btn_w * 0.45
    tri_center_y = btn_y0 + btn_h / 2
    tri_size = min(btn_w, btn_h) * 0.3
    d.polygon([
        (tri_center_x - tri_size / 2, tri_center_y - tri_size),
        (tri_center_x - tri_size / 2, tri_center_y + tri_size),
        (tri_center_x + tri_size, tri_center_y)
    ], fill=(255, 255, 255))

    # Grid of account tiles
    rows, cols = 4, 5
    tile_w = w * 0.12
    tile_h = h * 0.08
    start_x = w * 0.05
    start_y = h * 0.35
    for r in range(rows):
        for c in range(cols):
            x0 = start_x + c * (tile_w + w * 0.02)
            y0 = start_y + r * (tile_h + h * 0.02)
            # Randomly decide oversized question mark for the first tile
            if r == 0 and c == 0:
                # Large question‑mark using text for simplicity
                try:
                    font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
                    font = ImageFont.truetype(font_path, int(tile_h * 1.5))
                except Exception:
                    font = ImageFont.load_default()
                d.text((x0, y0), "?", font=font, fill=(255, 215, 0))
                continue
            # Normal tile background
            d.rectangle([x0, y0, x0 + tile_w, y0 + tile_h], fill=(30, 30, 30))
            # X mark across the tile
            d.line([x0, y0, x0 + tile_w, y0 + tile_h], fill=(255, 215, 0), width=2)
            d.line([x0 + tile_w, y0, x0, y0 + tile_h], fill=(255, 215, 0), width=2)

    ground_band(d, w, h, 0.12, (50, 30, 20))

# Scene 16: New York Vendors
def scene_newyork_vendors(d, w, h):
    """Payment card on a street with skyscrapers.
    Elements:
    * Perspective payment card with chip and circuit‑style traces.
    * Warning triangle in the foreground.
    * Silhouette skyline behind the card.
    * Gradient sky and ground band.
    """
    # Sky gradient – dusk tones
    vertical_gradient(d, w, h, (80, 50, 100), (30, 20, 60))

    # Skyscraper silhouettes (reuse helper)
    silhouette_skyline(d, w, h, building_count=9, seed=11)

    # Payment card – drawn as a tilted rectangle (simple perspective)
    card_w = w * 0.4
    card_h = h * 0.25
    # Define four corners for a slight rotation
    top_left = (w * 0.3, h * 0.45)
    top_right = (top_left[0] + card_w, top_left[1] - h * 0.03)
    bottom_right = (top_right[0], top_right[1] + card_h)
    bottom_left = (top_left[0], top_left[1] + card_h)
    d.polygon([top_left, top_right, bottom_right, bottom_left], fill=(10, 120, 200))

    # Chip – small rectangle near left side of card
    chip_w, chip_h = card_w * 0.12, card_h * 0.18
    chip_x = top_left[0] + card_w * 0.2
    chip_y = top_left[1] + card_h * 0.3
    d.rectangle([chip_x, chip_y, chip_x + chip_w, chip_y + chip_h], fill=(200, 200, 30))

    # Simple circuit traces – lines radiating from chip
    for i in range(5):
        x1 = chip_x + chip_w / 2
        y1 = chip_y + chip_h / 2
        x2 = x1 + (chip_w + card_w * 0.2) * (i - 2) / 2
        y2 = y1 - chip_h * 2
        d.line([x1, y1, x2, y2], fill=(255, 255, 0), width=1)

    # Warning triangle in foreground (pointing up)
    tri_size = w * 0.08
    tri_center_x = w * 0.7
    tri_center_y = h * 0.8
    d.polygon([
        (tri_center_x, tri_center_y - tri_size),
        (tri_center_x - tri_size, tri_center_y + tri_size),
        (tri_center_x + tri_size, tri_center_y + tri_size)
    ], fill=(255, 0, 0))

    ground_band(d, w, h, 0.12, (70, 50, 30))

# Self‑test: render a 4×4 contact sheet of all 16 scenes.
if __name__ == "__main__":
    from stories import CARDS
    panel = 256
    cols = 4
    rows = 4
    sheet = Image.new('RGB', (cols * panel, rows * panel))
    for idx, card in enumerate(CARDS):
        r, c = divmod(idx, cols)
        box = (c * panel, r * panel, (c + 1) * panel, (r + 1) * panel)
        draw_scene(sheet, card["art"], box, card["banner"])
    out_path = "/tmp/ni21-scenes.png"
    sheet.save(out_path)
    print("Rendered scenes:", [c["art"] for c in CARDS])
def scene_cop31_dome(d, w, h):
    # Dawn gradient peach → pale
    vertical_gradient(d, w, h, (250,200,150), (250,235,200))
    # Sun low‑left with glow rings
    sun_moon(d, int(w*0.2), int(h*0.75), int(h*0.12), (255,220,100), (255,255,180))
    # Large glass dome – semicircle outline with base band
    dome_center_x = w*0.5
    dome_radius = min(w, h)*0.35
    # semicircle (upper half)
    d.arc([dome_center_x-dome_radius, h*0.2, dome_center_x+dome_radius, h*0.9], start=180, end=0, fill=(180,180,255), width=4)
    # base band (straight line)
    base_y = h*0.75
    d.line([dome_center_x-dome_radius, base_y, dome_center_x+dome_radius, base_y], fill=(180,180,255), width=4)
    # vertical panel lines inside dome (5)
    for i in range(1,6):
        x = dome_center_x - dome_radius + i*(2*dome_radius/6)
        d.line([x, h*0.2, x, base_y], fill=(180,180,255), width=2)
    # two horizontal arcs inside dome
    for offset in (0.15, 0.30):
        r = dome_radius * (1 - offset)
        d.arc([dome_center_x-r, h*0.2+offset*dome_radius, dome_center_x+r, h*0.2+offset*dome_radius*2], start=180, end=0, fill=(180,180,255), width=2)
    # thermometer at right
    th_x0 = int(w*0.78)
    th_y0 = int(h*0.35)
    th_x1 = th_x0 + 12
    th_y1 = int(h*0.75)
    d.rounded_rectangle([th_x0, th_y0, th_x1, th_y1], radius=4, outline=(200,200,200), width=2)
    # red mercury column (70%)
    mercury_top = th_y0 + int((th_y1-th_y0)*0.30)
    d.rectangle([th_x0+2, mercury_top, th_x1-2, th_y1-12], fill=(255,0,0))
    # bulb
    bulb_r = 8
    d.ellipse([th_x0-2, th_y1-12-bulb_r, th_x0+14, th_y1-12+bulb_r], fill=(255,0,0))
    # clock face near top‑right of dome
    cx = int(dome_center_x + dome_radius*0.5)
    cy = int(h*0.3)
    r = 12
    d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(230,230,230), width=2)
    # hour hand (pointing 2 o'clock)
    d.line([cx, cy, cx + r*0.6, cy - r*0.3], fill=(230,230,230), width=2)
    # minute hand (pointing up)
    d.line([cx, cy, cx, cy - r*0.8], fill=(230,230,230), width=2)
    # gold ribbon band across lower third of dome
    ribbon_y0 = int(h*0.55)
    ribbon_h = int(h*0.07)
    d.rectangle([dome_center_x-dome_radius, ribbon_y0, dome_center_x+dome_radius, ribbon_y0+ribbon_h], fill=(255,215,0))
    # thick red diagonal slash inside ribbon
    d.line([dome_center_x-dome_radius+5, ribbon_y0+5, dome_center_x+dome_radius-5, ribbon_y0+ribbon_h-5], fill=(255,0,0), width=6)
    # ground band
    ground_band(d, w, h, 0.12, (70,50,30))

# Scene: delhi_forum
def scene_delhi_forum(d, w, h):
    # Dawn gradient pale blue → warm orange
    vertical_gradient(d, w, h, (180,210,255), (255,180,130))
    # Parliament block base rectangle
    base_y = int(h*0.65)
    d.rectangle([w*0.15, base_y, w*0.85, h], fill=(200,200,200))
    # 6 column lines
    for i in range(1,6):
        x = w*0.15 + i*(w*0.7/6)
        d.line([x, base_y, x, h], fill=(150,150,150), width=2)
    # triangular pediment
    ped_top = h*0.45
    d.polygon([ (w*0.15, base_y), (w*0.5, ped_top), (w*0.85, base_y) ], fill=(170,170,170))
    # central dome (semicircle + finial)
    dome_cx = w*0.5
    dome_r = w*0.12
    d.arc([dome_cx-dome_r, ped_top-dome_r, dome_cx+dome_r, ped_top+dome_r], start=180, end=0, fill=(100,100,255), width=3)
    # finial spike
    d.line([dome_cx, ped_top-dome_r, dome_cx, ped_top-dome_r-10], fill=(100,100,255), width=3)
    # flag poles row of 5
    pole_y0 = base_y - 5
    pole_height = h*0.15
    for i, col in enumerate(['saffron','white','green','blue','gold']):
        px = w*0.2 + i*(w*0.5/4)
        d.line([px, pole_y0, px, pole_y0-pole_height], fill=(80,80,80), width=2)
        # flag rectangle
        flag_w = w*0.04
        flag_h = pole_height*0.3
        if col == 'saffron': clr = (255,165,0)
        elif col == 'white': clr = (255,255,255)
        elif col == 'green': clr = (0,150,0)
        elif col == 'blue': clr = (0,0,200)
        else: clr = (255,215,0)
        d.rectangle([px, pole_y0-pole_height, px+flag_w, pole_y0-pole_height+flag_h], fill=clr)
    # ground band
    ground_band(d, w, h, 0.10, (60,45,30))

# Scene: delhi_vaccine
def scene_delhi_vaccine(d, w, h):
    # Soft gradient cream → pale green
    vertical_gradient(d, w, h, (240,240,220), (200,230,200))
    # Hen silhouette left (dark brown)
    hb = (80,50,30)
    # body ellipse
    body_cx, body_cy = w*0.25, h*0.6
    body_rx, body_ry = w*0.15, h*0.12
    d.ellipse([body_cx-body_rx, body_cy-body_ry, body_cx+body_rx, body_cy+body_ry], fill=hb)
    # head circle
    head_r = h*0.06
    head_cx = body_cx + body_rx*0.6
    head_cy = body_cy - body_ry*0.5
    d.ellipse([head_cx-head_r, head_cy-head_r, head_cx+head_r, head_cy+head_r], fill=hb)
    # red comb (3 small circles)
    for i in range(3):
        cr = head_r*0.2
        cx = head_cx - cr + i*cr*1.5
        cy = head_cy - head_r*0.6
        d.ellipse([cx-cr, cy-cr, cx+cr, cy+cr], fill=(200,0,0))
    # beak triangle (orange)
    beak = [(head_cx+head_r, head_cy), (head_cx+head_r+head_r*0.8, head_cy-head_r*0.3), (head_cx+head_r+head_r*0.8, head_cy+head_r*0.3)]
    d.polygon(beak, fill=(255,165,0))
    # tail feathers (3 polygons)
    for i in range(3):
        tx = body_cx - body_rx - i*5
        ty = body_cy - body_ry + i*5
        d.polygon([ (tx, ty), (tx-12, ty-4), (tx-12, ty+4) ], fill=hb)
    # single leg line
    d.line([body_cx-body_rx*0.3, body_cy+body_ry, body_cx-body_rx*0.3, body_cy+body_ry+20], fill=hb, width=2)
    # Shield outline right side
    shield_center_x = w*0.75
    shield_center_y = h*0.55
    shield_w = w*0.2
    shield_h = h*0.4
    d.polygon([
        (shield_center_x-shield_w/2, shield_center_y-shield_h/2),
        (shield_center_x+shield_w/2, shield_center_y-shield_h/2),
        (shield_center_x+shield_w/2, shield_center_y+shield_h/2),
        (shield_center_x, shield_center_y+shield_h/2+20),
        (shield_center_x-shield_w/2, shield_center_y+shield_h/2)
    ], outline=(255,215,0), width=4)
    # syringe inside shield (rotated polygon barrel)
    barrel = [
        (shield_center_x-30, shield_center_y-10),
        (shield_center_x-10, shield_center_y-10),
        (shield_center_x-10, shield_center_y+40),
        (shield_center_x-30, shield_center_y+40)
    ]
    d.polygon(barrel, fill=(180,180,180))
    # plunger cross
    d.line([shield_center_x-28, shield_center_y+10, shield_center_x-12, shield_center_y+30], fill=(100,100,100), width=2)
    d.line([shield_center_x-12, shield_center_y+10, shield_center_x-28, shield_center_y+30], fill=(100,100,100), width=2)
    # needle line
    d.line([shield_center_x-30, shield_center_y+45, shield_center_x-30, shield_center_y+70], fill=(250,250,250), width=2)
    # three white eggs at base
    for i in range(3):
        ex = shield_center_x - 40 + i*30
        ey = shield_center_y + shield_h/2 + 10
        d.ellipse([ex-8, ey-10, ex+8, ey+10], fill=(255,255,255))
    # ground band
    ground_band(d, w, h, 0.10, (80,60,40))
