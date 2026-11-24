# /// script
# requires-python = ">=3.12"
# dependencies = ["build123d==0.13.0", "trimesh==5.2.1"]
# ///
"""Generate the FT412 enclosure, oriented STLs, and a millimeter STEP assembly."""

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
import json
import math
from pathlib import Path

from build123d import (
    Align, Axis, Box, Color, Compound, Cone, Cylinder, Plane, Polygon, Pos,
    Solid, export_step, export_stl, extrude, import_step,
)
import trimesh


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "diseno-aprobado.json"
LAYOUT = json.loads(SOURCE.read_text())
BOX = LAYOUT["box"]
L, W, H = (BOX[key] for key in ("length", "width", "height"))
T, SPLIT, RUN = (BOX[key] for key in ("wall", "split", "frontRun"))
GAP = 0.30
EPS = 0.10
ANGLE = math.radians(BOX["frontAngle"])
SINE, COSINE = math.sin(ANGLE), math.cos(ANGLE)
LIP = H - RUN * math.tan(ANGLE)
ROOF = H - T
RAMP = Plane((0, 0, LIP), (0, 1, 0), (SINE, 0, -COSINE))
SIDE = Plane((0, 0, 0), (1, 0, 0), (0, -1, 0))
CENTER_MIN = (Align.CENTER, Align.CENTER, Align.MIN)
APERTURES = LAYOUT["apertureSchedule"]
PARTS = {part["id"]: part for part in LAYOUT["parts"]}
BASES = {base["owner"]: base for base in LAYOUT["floorBases"]}

LID_SCREWS = (
    [(62, 8.5), (124, 8.5), (62, W - 8.5), (115, W - 8.5)],
    [(150, 8.5), (266, 8.5), (150, W - 8.5), (234, W - 8.5)],
)
PANEL_SCREWS = [(u, v) for u in (8.5, W - 8.5) for v in (10, 60)]
SPLICE_Y = (7.6, 114)
SPLICE_DX = 7
SPLICE_Z = T + 1.2
TRAY_SCREWS = [(160, 7.9), (219, 90)]
CLIP_SCREWS = [(-5.2, -5), (5.2, -5)]
CLIP_PAD = 2.1
FAN_FIX_Y = (-24, 24)
FAN_FIX_Z = ROOF - 3.2
BRACKET_DX = 9.3
BRACKET_Z = BOX["profileBase"] + 20
PROFILE_Z = (BOX["profileBase"] + 10, BOX["profileBase"] + 30)
BRACKET_GAP = BOX["offset"]


def aperture(name):
    items = [entry for entry in APERTURES if entry["name"] == name]
    assert len(items) == 1, name
    return items[0]


def rect(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(
        x1 - x0, y1 - y0, z1 - z0
    )


def prism(points, z0, z1):
    return Pos(0, 0, z0) * extrude(Polygon(*points, align=None), amount=z1 - z0)


def bore(origin, diameter, length, axis=(0, 0, 1)):
    return Plane(origin=origin, z_dir=axis).location * Cylinder(
        diameter / 2, length, align=CENTER_MIN
    )


def countersink(origin, from_diameter, to_diameter, axis):
    height = abs(from_diameter - to_diameter) / 2
    return Plane(origin=origin, z_dir=axis).location * Cone(
        from_diameter / 2, to_diameter / 2, height, align=CENTER_MIN
    )


def slot(a, b, diameter, z0, z1):
    """Capsule centered along line a–b at the requested depth."""
    heading = math.atan2(b[1] - a[1], b[0] - a[0])
    middle = [(x + y) / 2 for x, y in zip(a, b)]
    bridge = rect(
        -math.dist(a, b) / 2, math.dist(a, b) / 2, -diameter / 2,
        diameter / 2, z0, z1,
    ).rotate(Axis.Z, math.degrees(heading)).moved(Pos(*middle, 0))
    return bridge.fuse(*(bore((*end, z0), diameter, z1 - z0) for end in (a, b)))


def one_solid(shape, name):
    assert shape is not None and len(shape.solids()) == 1, name
    solid = shape.solids()[0]
    assert solid.is_valid and solid.volume > 0, name
    return solid


def outer_clip_plane(part):
    """Map a clip's flat back to the inside of its panel."""
    x, y, z = (part[key] for key in ("x", "y", "z"))
    if part["face"] == "inner":
        return Plane((x, T + CLIP_PAD, z), (-1, 0, 0), (0, 1, 0))
    if part["face"] == "outer":
        return Plane((x, W - T - CLIP_PAD, z), (1, 0, 0), (0, -1, 0))
    assert part["face"] == "lid", part
    angle = math.radians(part["rotation"])
    return Plane((x, y, ROOF - CLIP_PAD), (math.cos(angle), -math.sin(angle), 0), (0, 0, -1))


CLIPS = [(part["id"], outer_clip_plane(part)) for part in LAYOUT["parts"] if part["type"] == "clip"]


def clip_hardware(plane):
    mounts = [bore((u, v, -CLIP_PAD - 0.35), 8.2, CLIP_PAD + 0.35) for u, v in CLIP_SCREWS]
    pilots = [bore((u, v, -3.8), 2.55, 3.8 + EPS) for u, v in CLIP_SCREWS]
    return ([plane.location * shape for shape in mounts], [plane.location * shape for shape in pilots])


def pcb_bosses(owner, z0, z1, pilot):
    seats = BASES[owner]["seats"]
    bosses = [bore((*seat["center"][:2], z0), seat["outsideDiameterMM"], z1 - z0) for seat in seats]
    # Leave solid material under each pilot so the screw does not emerge underneath.
    bores = [bore((*seat["center"][:2], z0 + 0.90), pilot, z1 - z0 - 0.90 + EPS) for seat in seats]
    return bosses, bores


def roof_boss(x, y):
    reach = 12.8
    xz_section = [(0, ROOF - 16), (reach, ROOF - 4), (reach, ROOF), (0, ROOF)]
    if y > W / 2:
        xz_section = [(W - reach_from_side, z) for reach_from_side, z in xz_section][::-1]
    plane = Plane((x - 5.4, 0, 0), (0, 1, 0), (1, 0, 0))
    support = plane.location * prism(xz_section, 0, 10.8)
    return support, bore((x, y, ROOF - 5.6), 2.55, 5.6 + EPS)


def ramp_boss(u, v):
    # Taper the underside back to the sidewall to avoid a wide flat overhang.
    reach = min(u, W - u) + 5
    depth = T + 7.0
    root = depth + (reach - T) / COSINE
    section = [(0, T), (reach, T), (reach, depth), (T, root), (0, root)]
    if u > W / 2:
        section = [(W - x, z) for x, z in section][::-1]
    return RAMP.location * SIDE.location * prism(section, -v - 4.6, -v + 4.6)


def honeycomb_tool(entry):
    x, _, z = entry["center"]
    radius = entry["size"][0] / 2
    theta = math.radians(entry["rotation"])
    points = [(x + radius * math.cos(theta + i * math.tau / 6),
               z + radius * math.sin(theta + i * math.tau / 6)) for i in range(6)]
    return SIDE.location * prism(points, -T - EPS, EPS)


def rear_opening_tool(entry):
    x, y, z = entry["center"]
    return bore((x - T - EPS, y, z), entry["size"][0], T + 2 * EPS, (1, 0, 0))


def body_sections():
    slope_floor = T / COSINE
    side_profile = [
        (0, 0), (L, 0), (L, ROOF), (RUN, ROOF), (RUN, H - slope_floor),
        (0, LIP - slope_floor),
    ]
    front_profile = [(0, 0), (T, 0), (T, LIP + T * math.tan(ANGLE) - slope_floor), (0, LIP - slope_floor)]
    body = rect(0, L, 0, W, 0, T).fuse(
        SIDE.location * prism(side_profile, -T, 0),
        SIDE.location * prism(side_profile, -W, T - W),
        SIDE.location * prism(front_profile, -W, 0),
        rect(L - T, L, 0, W, 0, ROOF),
    )
    joins = []
    holes = []
    for owner in ("pi", "mosfet"):
        posts, pilots = pcb_bosses(owner, T - 0.15, PARTS[owner]["z"], 2.15)
        joins.extend(posts)
        holes.extend(pilots)
    for y in SPLICE_Y:
        joins.append(rect(SPLIT - 13, SPLIT + 13, y - 4.25, y + 4.25, T - 0.2, SPLICE_Z))
        for x in (SPLIT - SPLICE_DX, SPLIT + SPLICE_DX):
            holes.append(bore((x, y, 1), 2.55, SPLICE_Z - 1 + EPS))
    for x, y in TRAY_SCREWS + [tuple(seat["center"][:2]) for seat in BASES["fuse"]["seats"]]:
        holes.append(bore((x, y, -EPS), 3.35, T + 2 * EPS))
        holes.append(countersink((x, y, 0), 6.4, 3.35, (0, 0, 1)))
    for x, y in LID_SCREWS[0] + LID_SCREWS[1]:
        mount, opening = roof_boss(x, y)
        joins.append(mount)
        holes.append(opening)
    for u, v in PANEL_SCREWS:
        joins.append(ramp_boss(u, v))
        holes.append(RAMP.location * bore((u, v, T - EPS), 2.55, 5.7))
    for _, plane in CLIPS:
        if plane.z_dir.Z == 0:
            mounts, pilots = clip_hardware(plane)
            joins.extend(mounts)
            holes.extend(pilots)
    for station in BOX["anchors"]:
        for dx in (-BRACKET_DX, BRACKET_DX):
            holes.append(bore((station + dx, -EPS, BRACKET_Z), 4.4, T + 2 * EPS, (0, 1, 0)))
    holes.extend(honeycomb_tool(entry) for entry in APERTURES if entry["kind"] == "hexagon")
    holes.extend(rear_opening_tool(aperture(name)) for name in ("Paso de corriente", "Interruptor"))
    united = one_solid(body.fuse(*joins).cut(*holes), "body before split")
    front = united.intersect(rect(-1, SPLIT - GAP / 2, -1, W + 1, -1, H + 1))
    rear = united.intersect(rect(SPLIT + GAP / 2, L + 1, -1, W + 1, -1, H + 1))
    return one_solid(front, "front shell"), one_solid(rear, "rear shell")


def display_panel():
    x0, x1 = 0.20, RUN - 0.20
    z0 = LIP + x0 * math.tan(ANGLE)
    z1 = LIP + x1 * math.tan(ANGLE)
    dz = T / COSINE
    section = [(x0, z0 - dz), (x1, z1 - dz), (x1, z1), (x0, z0)]
    panel = SIDE.location * prism(section, -W, 0)
    window = aperture("Ventana pantalla")
    u = window["center"][1]
    v = window["center"][0] / COSINE
    half_w, half_h = (s / 2 for s in window["size"])
    # The rear pocket clears the glass bezel while retaining the selected visible window.
    opening = rect(u - half_w, u + half_w, v - half_h, v + half_h, -EPS, T + EPS)
    recess = rect(u - 32.5, u + 32.5, v - 23, v + 23, 1.2, T + EPS)
    plate_screws = [bore((x, y, -EPS), 3.35, T + 2 * EPS) for x, y in PANEL_SCREWS]
    board_screws = [
        slot((x - 1.45, y), (x + 1.45, y), 4.1, -EPS, T + EPS)
        for x in (u - 36.5, u + 36.5) for y in (v - 22.25, v + 22.25)
    ]
    return one_solid(panel.cut(*(RAMP.location * tool for tool in (
        [opening, recess] + plate_screws + board_screws
    ))), "screen panel")


def roof_lid(index):
    x0, x1 = ((RUN + 0.20, SPLIT - GAP / 2) if index == 0 else (SPLIT + GAP / 2, L))
    support_start, support_end = ((54, 131) if index == 0 else (151, 237))
    lid = rect(x0, x1, 0, W, ROOF, H)
    rails = [rect(support_start, support_end, y - 1.2, y + 1.2, ROOF - 3.2, ROOF + 0.2) for y in (19, 110)]
    joins = list(rails)
    holes = [bore((x, y, ROOF - EPS), 3.35, T + 2 * EPS) for x, y in LID_SCREWS[index]]
    for clip_id, plane in CLIPS:
        if clip_id == f"clip-lid-{index + 1}":
            mounts, pilots = clip_hardware(plane)
            joins.extend(mounts)
            holes.extend(pilots)
    if index == 0:
        fan = aperture("Abertura ventilador")
        fx, fy = fan["center"][:2]
        holes.append(bore((fx, fy, ROOF - EPS), fan["size"][0], T + 2 * EPS))
        for dy in FAN_FIX_Y:
            joins.append(bore((fx, fy + dy, FAN_FIX_Z), 8.0, ROOF - FAN_FIX_Z + 0.3))
            holes.append(bore((fx, fy + dy, FAN_FIX_Z - EPS), 2.55, 4.1))
    return one_solid(lid.fuse(*joins).cut(*holes), f"lid {index + 1}")


def rail_bracket():
    bracket = rect(-14, 14, -BRACKET_GAP, 0, BOX["profileBase"] + 2, BOX["profileBase"] + 38)
    holes = []
    # Screw #6674 has a 12 mm overall length. A 6.8 mm seat leaves 5.2 mm in the slot.
    rail_face = -BRACKET_GAP
    seat = rail_face + 6.8
    for z in PROFILE_Z:
        holes.append(bore((0, rail_face - EPS, z), 5.5, BRACKET_GAP + 2 * EPS, (0, 1, 0)))
        holes.append(countersink((0, seat, z), 10.3, 5.5, (0, -1, 0)))
        holes.append(bore((0, seat, z), 11.2, -seat + EPS, (0, 1, 0)))
    # Two rear-entry M4 nut traps, held by the rail after mounting.
    for dx in (-BRACKET_DX, BRACKET_DX):
        holes.append(bore((dx, rail_face - EPS, BRACKET_Z), 4.4, BRACKET_GAP + 2 * EPS, (0, 1, 0)))
        nut_radius = 7.35 / math.sqrt(3)
        hex_points = [(nut_radius * math.cos(i * math.tau / 6),
                       nut_radius * math.sin(i * math.tau / 6)) for i in range(6)]
        center = Plane((dx, rail_face - EPS, BRACKET_Z), (-1, 0, 0), (0, 1, 0))
        holes.append(center.location * prism(hex_points, 0, BRACKET_GAP - 4.9 + EPS))
    return one_solid(bracket.cut(*holes), "rail bracket")


def floor_splice():
    strap = rect(-11, 11, -4.25, 4.25, 0, 3.2)
    return one_solid(strap.cut(*(bore((x, 0, -EPS), 3.35, 3.2 + 2 * EPS)
                               for x in (-SPLICE_DX, SPLICE_DX))), "floor splice")


def mks_carrier():
    # A removable carrier keeps the case independent of any V2.2 PCB revision.
    centers = [seat["center"][:2] for seat in BASES["mks"]["seats"]]
    xs, ys = list(zip(*centers))
    x0, x1 = min(xs) - 6.5, max(xs) + 6.5
    y0, y1 = min(ys) - 5, max(ys) + 5
    z1 = T + 2.4
    frame = rect(x0, x1, y0, y0 + 11, T, z1).fuse(
        rect(x0, x1, y1 - 11, y1, T, z1),
        rect(x0, x0 + 10.5, y0, y1, T, z1),
        rect(x1 - 10.5, x1, y0, y1, T, z1),
        rect(154.5, 165.5, 5.05, 15, T, z1),
        rect(213.5, 224.5, 80, 92.3, T, z1),
        *(bore((x, y, T), 8.65, z1 - T) for x, y in TRAY_SCREWS),
    )
    seats, _ = pcb_bosses("mks", z1 - EPS, PARTS["mks"]["z"], 2.55)
    # Extend the pilots into the replaceable carrier without perforating its underside.
    bores = [bore((x, y, T + 0.75), 2.55, PARTS["mks"]["z"] - T - 0.75 + EPS) for x, y in centers]
    attachment = [bore((x, y, T - EPS), 3.35, z1 - T + 2 * EPS) for x, y in TRAY_SCREWS]
    return one_solid(frame.fuse(*seats).cut(*(bores + attachment)), "MKS carrier")


def fuse_cradle():
    x, y, top = (PARTS["fuse"][key] for key in ("x", "y", "z"))
    seats = [tuple(seat["center"][:2]) for seat in BASES["fuse"]["seats"]]
    xs = x - 16.5, x + 16.5
    ys = min(s[1] for s in seats), max(s[1] for s in seats)
    platform = rect(*xs, y - 24.75, y + 24.75, T, top)
    spine = rect(x - 4, x + 4, ys[0] - 3.6, ys[1] + 3.6, T, T + 2.4)
    guides = [rect(a, b, y - 19, y + 19, top - EPS, top + 3)
              for a, b in ((xs[0], x - 14.8), (x + 14.8, xs[1]))]
    ties = [rect(xs[0] - EPS, xs[1] + EPS, y + dy - 1.9, y + dy + 1.9, T - EPS, T + 2.25)
            for dy in (-14, 14)]
    holes = [bore((fx, fy, T - EPS), 3.35, top - T + 2 * EPS) for fx, fy in seats]
    return one_solid(platform.fuse(spine, *guides).cut(*(ties + holes)), "fuse cradle")


def fan_carrier():
    # Square fan with slotted diagonal patterns. The lid still has its exact Ø32 opening.
    profile = [(-21.3, -20), (-12, -28), (12, -28), (21.3, -20), (21.3, 7),
               (19.5, 11), (17.4, 21), (10, 28), (-12, 28), (-21.3, 20)]
    top = 4.2
    piece = prism(profile, 0, top).fuse(bore((0, 0, top - EPS), 31.50, 3.2 + EPS))
    passage = bore((0, 0, -EPS), 27, 8)
    perforations = [bore((0, y, -EPS), 3.4, top + 2 * EPS) for y in FAN_FIX_Y]
    for sx in (-1, 1):
        for sy in (-1, 1):
            perforations.append(slot((sx * 12, sy * 12), (sx * 16, sy * 16), 3.30, -EPS, top + 2 * EPS))
            perforations.append(rect(sx * 9 - 1.35, sx * 9 + 1.35, sy * 22 - 1.6, sy * 22 + 1.6, -EPS, top + EPS))
    # Small parallel bars keep fingers out of the fan from above.
    bar_outline = bore((0, 0, 0), 27.7, 2.4)
    bars = [
        one_solid(rect(x - 0.7, x + 0.7, -14.3, 14.3, 0, 2.4).intersect(bar_outline), "fan guard bar")
        for x in (-7, 0, 7)
    ]
    return one_solid(piece.cut(passage, *perforations).fuse(*bars), "fan carrier")


def cable_clip():
    plate = rect(-8.2, 8.2, -8, 8, 0, 2.5)
    hook_section = [(5.2, 2.0), (7.8, 2.0), (7.8, 6.25), (6.0, 9.75),
                    (0.25, 9.75), (-0.35, 9.15), (-0.35, 8.0), (4.7, 7.8), (5.2, 6.3)]
    hook_plane = Plane((-8.2, 0, 0), (0, 1, 0), (1, 0, 0))
    hook = hook_plane.location * prism(hook_section, 0, 16.4)
    return one_solid(plate.fuse(hook).cut(*(
        bore((u, v, -EPS), 3.3, 2.5 + 2 * EPS) for u, v in CLIP_SCREWS
    )), "cable clip")


def fit_sample():
    strip = rect(0, 56, 0, 25, 0, T)
    for x, name in ((15, "Paso de corriente"), (40, "Interruptor")):
        strip -= bore((x, 12.5, -EPS), aperture(name)["size"][0], T + 2 * EPS)
    return one_solid(strip, "test of the two rear openings")


def center_on_bed(solid):
    bounds = solid.bounding_box()
    return solid.moved(Pos(-bounds.min.X, -bounds.min.Y, -bounds.min.Z))


@dataclass
class Printable:
    name: str
    assembly: list[Solid]
    oriented: Solid
    color: str

    def export(self, out):
        condition = one_solid(self.oriented, self.name)
        print_path = out / "STL" / f"{self.name}.stl"
        stl = center_on_bed(condition)
        export_stl(stl, print_path, tolerance=0.012, angular_tolerance=0.10)
        mesh = trimesh.load_mesh(print_path)
        assert mesh.is_watertight and mesh.is_winding_consistent, self.name
        assert mesh.body_count == 1 and mesh.volume > 0, self.name
        assert abs(mesh.volume - stl.volume) / stl.volume < 0.005, self.name
        assert min(mesh.bounds[0]) >= -0.001 and max(mesh.extents[:2]) < 246, self.name
        return {
            "archivo": print_path.name, "unidades_montaje": len(self.assembly),
            "orientada_en_cama_mm": [round(x, 3) for x in mesh.extents],
            "volumen_solido_cm3": round(float(mesh.volume) / 1000, 3),
            "triangulos": len(mesh.faces), "malla_cerrada": True,
            "sha256": sha256(print_path.read_bytes()).hexdigest(),
        }


def aabb_overlap(a, b):
    delta = [min(hi1, hi2) - max(lo1, lo2)
             for lo1, hi1, lo2, hi2 in zip(a.min, a.max, b.min, b.max)]
    return min(delta) > 0.001


def collision_volume(a, b):
    if not aabb_overlap(a.bounding_box(), b.bounding_box()):
        return 0.0
    result = a.intersect(b)
    return sum(s.volume for s in result.solids()) if result is not None else 0.0


def build():
    assert (L, W, H, T, SPLIT, RUN) == (280, 130, 85, 3, 135, 50), "wrong design revision"
    assert BOX["mountSide"] == "left" and BOX["anchors"] == [78, 231]
    assert aperture("Paso de corriente")["size"] == [16, 16]
    assert aperture("Paso de corriente")["kind"] == "circle"
    print("Construyendo ambas secciones y sus alojamientos…", flush=True)
    front, rear = body_sections()
    lid1, lid2 = roof_lid(0), roof_lid(1)
    display = display_panel()
    bracket, splice = rail_bracket(), floor_splice()
    mks, fuse = mks_carrier(), fuse_cradle()
    fan, clip, sample = fan_carrier(), cable_clip(), fit_sample()
    fx, fy = aperture("Abertura ventilador")["center"][:2]
    slate, yellow, grey = "#282d35", "#e6b927", "#596670"
    items = [
        Printable("01_Cuerpo_delantero", [front], front, slate),
        Printable("02_Cuerpo_trasero", [rear], rear, slate),
        Printable("03_Tapa_ventilador", [lid1], lid1.rotate(Axis.X, 180), slate),
        Printable("04_Tapa_trasera", [lid2], lid2.rotate(Axis.X, 180), slate),
        Printable("05_Frente_TS24", [display], RAMP.location.inverse() * display, slate),
        Printable("06_Anclaje_perfil_x2", [Pos(x, 0, 0) * bracket for x in BOX["anchors"]], bracket, yellow),
        Printable("07_Unidor_piso_x2", [Pos(SPLIT, y, SPLICE_Z) * splice for y in SPLICE_Y], splice, yellow),
        Printable("08_Base_MKS_extraible", [mks], mks, grey),
        Printable("09_Cuna_portafusible", [fuse], fuse, grey),
        Printable("10_Adaptador_ventilador", [Pos(fx, fy, FAN_FIX_Z - 4.2) * fan], fan, grey),
        Printable("11_Clip_cables_x6", [plane.location * clip for _, plane in CLIPS], clip.rotate(Axis.Y, 90), yellow),
        Printable("00_Cupon_pasacable_interruptor", [], sample, grey),
    ]
    for item in items:
        # Separate solid definitions retain unambiguous instance names in the STEP.
        if len(item.assembly) > 1:
            item.assembly = [deepcopy(solid) for solid in item.assembly]
        for i, solid in enumerate(item.assembly, start=1):
            solid.label = item.name if len(item.assembly) == 1 else f"{item.name}_{i:02d}"
            solid.color = Color(item.color)
    return items


def write_package():
    stl_dir = ROOT / "STL"
    stl_dir.mkdir(exist_ok=True)
    items = build()
    assembled = [solid for item in items for solid in item.assembly]
    print(f"Comprobando interferencias entre {len(assembled)} piezas…", flush=True)
    intersections = []
    for one, two in combinations(assembled, 2):
        overlap = collision_volume(one, two)
        if overlap >= 0.002:
            intersections.append((one.label, two.label, round(overlap, 4)))
    assert not intersections, intersections
    core = Compound(children=assembled[:5]).bounding_box()
    assert all(abs(size - nominal) < 0.001 for size, nominal in zip(core.size, (L, W, H)))
    # Verify the entire cylinder through the rear wall, including the inlet where
    # a CAD viewer would otherwise hide a residual membrane.
    rear = items[1].assembly[0]
    for name in ("Paso de corriente", "Interruptor"):
        entry = aperture(name)
        x, y, z = entry["center"]
        gauge = bore((x - T + 0.02, y, z), entry["size"][0] - 0.02, T - 0.04, (1, 0, 0))
        assert collision_volume(rear, gauge) < 0.002, name
    cells = [entry for entry in APERTURES if entry["kind"] == "hexagon"]
    for cell in cells:
        gauge = honeycomb_tool({**cell, "size": [side - 0.03 for side in cell["size"]]})
        shell = items[int(cell["center"][0] > SPLIT)].assembly[0]
        assert collision_volume(shell, gauge) < 0.002, cell["center"]
    report = []
    for item in items:
        print(f"Exportando {item.name}", flush=True)
        report.append(item.export(ROOT))
    step = ROOT / "FT412_Modulo_Lateral_Ensamblado_REV01.step"
    export_step(Compound(label="FT412 Modulo lateral REV01", children=assembled), step)
    restored = {solid.label: solid for solid in import_step(step).children}
    assert set(restored) == {solid.label for solid in assembled}
    for native in assembled:
        recovered = restored[native.label]
        assert abs(native.volume - recovered.volume) < 0.001
        assert (native.bounding_box().center() - recovered.bounding_box().center()).length < 0.001
    (ROOT / "verificacion.json").write_text(json.dumps({
        "diseno_sha256": sha256(SOURCE.read_bytes()).hexdigest(),
        "caja_mm": [L, W, H], "angulo_frente_grados": BOX["frontAngle"],
        "secciones_mm": [SPLIT, L - SPLIT], "holgura_union_mm": GAP,
        "panal_celdas_verificadas": len(cells),
        "agujero_alimentacion": aperture("Paso de corriente"),
        "interferencias_solidos_impresos": 0, "piezas_montadas": len(assembled),
        "ajuste_fisico_verificado": False, "archivos": report,
        "ensamble_step_sha256": sha256(step.read_bytes()).hexdigest(),
    }, indent=2, ensure_ascii=False) + "\n")
    print(f"{len(report)} STL verificados. Ensamble STEP exportado.", flush=True)


if __name__ == "__main__":
    write_package()
