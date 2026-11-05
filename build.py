"""
Heltec WiFi LoRa 32 V3 / V4 car + pocket enclosures  (parametric)
  - Dash Node   : dash-mount MeshMule node, upright SMA antenna tower,
                  USB-C cord clip, magnet / grip-pad base
  - Shelf Brick : battery pocket node for Shelf Lite / logger
                  (LiPo bay, SPI microSD module shelf, slide switch,
                   SD card slot, lid-mounted upright SMA antenna)
Change the numbers at the top and re-run:  python3 build.py
Needs:  pip install manifold3d trimesh numpy
All units mm.
"""
from manifold3d import Manifold, set_circular_segments
import numpy as np, trimesh, os

set_circular_segments(64)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl")
os.makedirs(OUT, exist_ok=True)

# ---------------- board (V3 and V4 share the same outline) -------------
BOARD_L, BOARD_W, PCB_T = 51.7, 25.4, 1.6
FIT = 1.0                          # total clearance around the board
POCKET_L, POCKET_W = BOARD_L + FIT, BOARD_W + FIT
UNDER_CLEAR = 3.5                  # parts on the board underside
OVER_CLEAR = 9.5                   # OLED + parts on top
WALL, FLOOR, LID_T = 2.2, 2.0, 2.0
LID_GAP = 0.25                     # lid lip clearance per side

OLED_WIN = (29.0, 15.0)            # window in lid (x, y)
OLED_OFF = 2.0                     # window shift toward USB end
USBC = (13.0, 7.5)                 # USB-C hole (w, h) - fits most plugs
SMA_HOLE = 6.6                     # 1/4-36 SMA bulkhead
MAGNET = (10.3, 3.2)               # 10 x 3 mm disc magnets (dia, depth)


def box(x, y, z, r=3.0):
    """rounded-corner box, corner at origin"""
    r = min(r, x / 2 - 0.01, y / 2 - 0.01)
    c = [Manifold.cylinder(z, r).translate([px, py, 0])
         for px in (r, x - r) for py in (r, y - r)]
    return Manifold.batch_hull(c)


def cube(x, y, z, at=(0, 0, 0)):
    return Manifold.cube([x, y, z]).translate(list(at))


def cyl(h, r, at=(0, 0, 0)):
    return Manifold.cylinder(h, r).translate(list(at))


def save(m, name):
    mesh = m.to_mesh()
    t = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3],
                        np.asarray(mesh.tri_verts), process=True)
    t.export(os.path.join(OUT, name))
    return t


def board_tub(inner_h_extra=0.0):
    """open-top tub that holds the board on two side rails"""
    in_l, in_w = POCKET_L, POCKET_W
    in_h = UNDER_CLEAR + PCB_T + OVER_CLEAR + inner_h_extra
    ox, oy, oz = in_l + 2 * WALL, in_w + 2 * WALL, FLOOR + in_h
    body = box(ox, oy, oz, 3.5) - cube(in_l, in_w, in_h + 1,
                                       (WALL, WALL, FLOOR))
    # rails along both long walls: board sits on top of them
    rail_h = UNDER_CLEAR + inner_h_extra
    for y in (WALL, WALL + in_w - 1.6):
        body += cube(in_l, 1.6, rail_h, (WALL, y, FLOOR))
    # little clips above the board edge keep it from rattling
    clip_z = FLOOR + rail_h + PCB_T + 0.15
    for x in (WALL + 8, WALL + in_l - 14):
        for y, d in ((WALL, 0.9), (WALL + in_w - 0.9, 0.9)):
            body += cube(6, d, 1.2, (x, y, clip_z))
    return body, (ox, oy, oz), FLOOR + rail_h


def lid(ox, oy, window=True, sma_at=None, in_l=None, in_w=None):
    in_l = in_l or POCKET_L
    in_w = in_w or POCKET_W
    plate = box(ox, oy, LID_T, 3.5)
    lip = box(in_l - 2 * LID_GAP, in_w - 2 * LID_GAP, 2.0, 1.0).translate(
        [WALL + LID_GAP, WALL + LID_GAP, -2.0])
    lip -= box(in_l - 2 * LID_GAP - 3.2, in_w - 2 * LID_GAP - 3.2, 2.2,
               0.5).translate([WALL + LID_GAP + 1.6, WALL + LID_GAP + 1.6,
                               -2.1])
    l = plate + lip
    if window:
        wx, wy = OLED_WIN
        cx = ox / 2 - OLED_OFF
        l -= box(wx, wy, 10, 1.5).translate([cx - wx / 2, oy / 2 - wy / 2,
                                             -5])
    if sma_at is not None:
        l -= cyl(10, SMA_HOLE / 2, (sma_at[0], sma_at[1], -5))
    # flip so it prints flat (top face down)
    return l.mirror([0, 0, 1]).translate([0, 0, LID_T])


# =====================================================================
# 1) DASH NODE  - base + tub + antenna tower in one piece
# =====================================================================
def dash_node():
    tub, (ox, oy, oz), board_z = board_tub()
    TOWER_R, TOWER_H = 9.0, 34.0
    BASE_L, BASE_W, BASE_T = ox + 2 * TOWER_R + 26, oy + 20, 3.5
    # place tub on base, USB end toward the front (x=0 side of tub)
    tx, ty = 18.0, (BASE_W - oy) / 2
    base = box(BASE_L, BASE_W, BASE_T, 6)
    # gentle chamfer look: slightly smaller second layer
    base += box(BASE_L - 4, BASE_W - 4, 1.2, 5).translate([2, 2, BASE_T])
    tub = tub.translate([tx, ty, BASE_T])
    tower_cx = tx + ox + TOWER_R - 2
    tower_cy = BASE_W / 2
    tower = cyl(TOWER_H, TOWER_R, (tower_cx, tower_cy, BASE_T))
    tower += cyl(3, TOWER_R + 2, (tower_cx, tower_cy, BASE_T))  # flared foot
    body = base + tub + tower
    # hollow tower for the IPEX->SMA pigtail, solid 3 mm cap w/ SMA hole
    body -= cyl(TOWER_H - 3, TOWER_R - 2.2, (tower_cx, tower_cy, BASE_T + 2))
    body -= cyl(10, SMA_HOLE / 2, (tower_cx, tower_cy, BASE_T + TOWER_H - 5))
    # anti-rotation flat for the SMA nut is not needed; washer + nut on top
    # pigtail pass-through from tub into tower
    body -= cube(12, 8, 8, (tx + ox - 4, tower_cy - 4,
                            BASE_T + board_z - 1))
    # USB-C hole in front wall, centred on the pcb
    uz = BASE_T + board_z + PCB_T / 2 - USBC[1] / 2 + 0.6
    body -= box(10, USBC[0], USBC[1], 2.0).translate(
        [tx - 5, ty + oy / 2 - USBC[0] / 2, uz])
    # cord saddle in front of the USB hole: zip-tie strain relief
    sx = 4.0
    saddle = cube(10, 16, 7, (sx, BASE_W / 2 - 8, BASE_T))
    saddle -= cyl(20, 2.6, (0, 0, 0)).rotate([0, 90, 0]).translate(
        [sx - 1, BASE_W / 2, BASE_T + 4.6])            # cable groove
    saddle -= cube(3.5, 20, 1.8, (sx + 3.25, BASE_W / 2 - 10, BASE_T + 1.2))
    body += saddle
    # underside: grip-pad recess + 4 magnet pockets
    body -= box(BASE_L - 10, BASE_W - 10, 0.8, 4).translate([5, 5, -0.01])
    for px in (12, BASE_L - 12):
        for py in (10, BASE_W - 10):
            body -= cyl(MAGNET[1] + 0.01, MAGNET[0] / 2, (px, py, -0.01))
    # side vents (cars get hot)
    for i in range(5):
        x = tx + 12 + i * 7
        for y in (ty - 1, ty + oy - 3.2):
            body -= box(3.2, 4.2, 6, 1.2).translate([x, y, BASE_T + oz - 9])
    save(body, "dash_node_body.stl")
    save(lid(ox, oy, window=True), "dash_node_lid.stl")
    return body


# =====================================================================
# 2) SHELF BRICK - battery + microSD module + board, lid antenna
# =====================================================================
LIPO = (51.0, 35.0, 11.0)          # 103450 2000 mAh pouch (+ margin)
SDMOD = (42.0, 24.5, 8.5)          # common 6-pin SPI microSD module
SWITCH = (9.2, 4.2)                # SS12D00 slide switch


def shelf_brick():
    in_l = max(POCKET_L, LIPO[0] + 1.0)
    in_w = max(POCKET_W, LIPO[1] + 1.0)
    bat_h = LIPO[2] + 0.5
    sd_h = SDMOD[2]
    top_h = UNDER_CLEAR + PCB_T + OVER_CLEAR
    in_h = bat_h + 1.6 + sd_h + 1.6 + top_h - UNDER_CLEAR
    ox, oy, oz = in_l + 2 * WALL, in_w + 2 * WALL, FLOOR + in_h
    body = box(ox, oy, oz, 4) - cube(in_l, in_w, in_h + 1,
                                     (WALL, WALL, FLOOR))
    # level 1 rails: SD module tray rests on these (prints w/o support)
    z1 = FLOOR + bat_h
    for y in (WALL, WALL + in_w - 2.0):
        body += cube(in_l - 12, 2.0, 1.6, (WALL + 6, y, z1))
    # level 2: board rails - board narrower than LiPo, so step in
    z2 = z1 + 1.6 + sd_h
    rail_w = (in_w - POCKET_W) / 2 + 1.4
    for y in (WALL, WALL + in_w - rail_w):
        body += cube(POCKET_L - 10, rail_w, 1.6, (WALL + 5, y, z2))
    board_top = z2 + 1.6
    # USB-C at front end on board level
    uz = board_top + PCB_T / 2 - USBC[1] / 2 + 0.6
    body -= box(10, USBC[0], USBC[1], 2).translate(
        [-5, oy / 2 - USBC[0] / 2, uz])
    # SD card slot at back end, SD level
    body -= box(10, 15, 4.5, 1).translate([ox - 5, oy / 2 - 7.5,
                                          z1 + 1.6 + 1.0])
    # slide switch on side near battery
    body -= box(SWITCH[0], 10, SWITCH[1], 1).translate(
        [ox / 2 - SWITCH[0] / 2, -5, FLOOR + bat_h / 2 - SWITCH[1] / 2])
    # screw holes for the switch (2 mm, 15 mm apart)
    for dx in (-7.5, 7.5):
        body -= cyl(10, 1.0, (0, 0, 0)).rotate([90, 0, 0]).translate(
            [ox / 2 + dx, 5, FLOOR + bat_h / 2])
    # lanyard loop on the back end
    loop = box(12, 12, 4, 3).translate([ox - 2, oy / 2 - 6, 0])
    loop -= box(6, 6, 6, 2).translate([ox + 1, oy / 2 - 3, -1])
    body += loop
    # underside magnets so it can also ride on the dash plate
    for px in (ox * 0.28, ox * 0.72):
        body -= cyl(MAGNET[1] + 0.01, MAGNET[0] / 2, (px, oy / 2, -0.01))
    # SD module tray (separate print): plate the module screws/tapes onto
    tray = box(in_l - 0.8, in_w - 0.8, 1.6, 1)
    tray -= box(in_l - 14, in_w - 14, 3, 2).translate([7, 7, -1])  # cutout
    for px in (8, in_l - 8.8):                   # wire notches at ends
        tray -= cube(6, 10, 3, (px - 3, (in_w - 0.8) / 2 - 5, -1))
    save(body, "shelf_brick_body.stl")
    save(tray, "shelf_brick_sd_tray.stl")
    # lid: OLED window + upright SMA at the back end
    save(lid(ox, oy, window=True, sma_at=(ox - 9.5, oy / 2),
             in_l=in_l, in_w=in_w),
         "shelf_brick_lid.stl")
    return body


if __name__ == "__main__":
    dash_node()
    shelf_brick()
    for f in sorted(os.listdir(OUT)):
        t = trimesh.load(os.path.join(OUT, f))
        print(f"{f:28s} {np.round(t.extents,1)}  watertight={t.is_watertight}")
