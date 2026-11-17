"""Blender ke andar chalta hai: blender -b --factory-startup -P blender3d_scene.py -- <theme> <seed> <out.png> <w> <h> <samples> <accent_hex>
v2.3.3: apna 3D (Gemini ke bina) - sirf apne banaye aakar (koi bahari model/copyright nahi), neon roshni, chamakta farsh, bloom.
Hindi text 3D mein nahi (Blender Devanagari theek nahi jodta) - sawal/vikalp upar se neon design lagata hai."""
import math
import random
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:]
THEME, SEED, OUT = argv[0], int(argv[1]), argv[2]
W, H, SAMPLES = int(argv[3]), int(argv[4]), int(argv[5])
ACC = tuple(int(argv[6][i:i + 2], 16) / 255 for i in (0, 2, 4)) if len(argv) > 6 else (0.0, 0.9, 1.0)
SIMPLE = len(argv) > 7 and argv[7] == "simple"      # v2.3.4: VM par atke to bina compositor/Filmic wala saada tareeka
rnd = random.Random(SEED)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = False          # Ubuntu ka Blender OIDN ke bina hai - shor wrapper (PIL) mein naram hota hai
sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = 0.05
sc.cycles.max_bounces = 4
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.resolution_percentage = 100
sc.render.film_transparent = False
try:                                              # v2.3.5: Blender 4 (Filmic) aur 5 (AgX) dono
    _vt = [i.identifier for i in sc.view_settings.bl_rna.properties["view_transform"].enum_items]
    sc.view_settings.view_transform = next((x for x in ("AgX", "Filmic", "Standard") if x in _vt), _vt[0])
except Exception:
    pass


def mat(name, color, metal=0.0, rough=0.4, emit=0.0, ecol=None, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Metallic"].default_value = metal
    b.inputs["Roughness"].default_value = rough
    for key in ("Emission Color", "Emission"):
        if key in b.inputs:
            b.inputs[key].default_value = (*(ecol or color), 1)
            break
    if "Emission Strength" in b.inputs:
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1 and "Alpha" in b.inputs:
        b.inputs["Alpha"].default_value = alpha
    return m


def add(obj, m):
    obj.data.materials.append(m)
    for p in getattr(obj.data, "polygons", []):
        p.use_smooth = True
    return obj


def sphere(loc, r, m, seg=48):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    return add(bpy.context.object, m)


def cyl(loc, r, d, m, rot=(0, 0, 0), v=64):
    bpy.ops.mesh.primitive_cylinder_add(vertices=v, radius=r, depth=d, location=loc, rotation=rot)
    o = bpy.context.object
    bev = o.modifiers.new("b", "BEVEL")
    bev.width, bev.segments = min(r, d) * 0.12, 3
    return add(o, m)


def cube(loc, s, m, rot=(0, 0, 0), bevel=0.05):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.scale = s
    bpy.ops.object.transform_apply(scale=True)
    bv = o.modifiers.new("b", "BEVEL")
    bv.width, bv.segments = bevel, 3
    return add(o, m)


def heart(loc, size, m, rot=(math.radians(90), 0, 0)):
    import bmesh
    me = bpy.data.meshes.new("heart")
    bm = bmesh.new()
    pts = []
    for i in range(64):
        t = 2 * math.pi * i / 64
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append(bm.verts.new((x / 17 * size, y / 17 * size, 0)))
    bm.faces.new(pts)
    bm.to_mesh(me)
    bm.free()
    o = bpy.data.objects.new("heart", me)
    bpy.context.collection.objects.link(o)
    o.location, o.rotation_euler = loc, rot
    so = o.modifiers.new("s", "SOLIDIFY")
    so.thickness = size * 0.35
    so.offset = 0
    bv = o.modifiers.new("b", "BEVEL")
    bv.width, bv.segments, bv.limit_method = size * 0.12, 4, "NONE"
    o.modifiers.new("sub", "SUBSURF").levels = 2
    return add(o, m)


def text3d(txt, loc, size, m, rot=(math.radians(90), 0, 0), depth=0.15):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    o = bpy.context.object
    o.data.body = txt
    o.data.size = size
    o.data.extrude = depth
    o.data.bevel_depth = depth * 0.25
    o.data.align_x = "CENTER"
    o.data.align_y = "CENTER"
    return add(o, m)


def person(x, body_col, face_toward, hair_col, girl=False):
    """Stylized (clay-toy) insaan: capsule shareer + sir + baal - koi asli vyakti nahi."""
    mb = mat("body", body_col, rough=0.45)
    ms = mat("skin", (0.95, 0.76, 0.62), rough=0.5)
    mh = mat("hair", hair_col, rough=0.6)
    cyl((x, 0, 0.9), 0.38, 1.2, mb)
    sphere((x, 0, 1.5), 0.38, mb)
    sphere((x, 0, 2.15), 0.42, ms)
    sphere((x, 0.05, 2.32), 0.44, mh).scale = (1.02, 1.0, 0.72)
    if girl:                          # lambe baal + phool
        hb = sphere((x, 0.28, 1.95), 0.40, mh)
        hb.scale = (1.0, 0.7, 1.25)
        sphere((x - 0.32 * face_toward, -0.1, 2.5), 0.09, mat("flower", (1, 0.4, 0.6), emit=1.5), seg=16)
    for dx in (-0.14, 0.14):          # aankhein
        sphere((x + dx * 0.7 + 0.25 * face_toward, -0.36, 2.18), 0.055, mat("eye", (0.05, 0.05, 0.08), rough=0.2), seg=16)
    sphere((x + 0.32 * face_toward, -0.18, 2.05), 0.06, mat("blush", (1.0, 0.45, 0.5), rough=0.6), seg=16)


# ---------- duniya: gehra neela-baingani, chamakta farsh, neon roshni ----------
world = bpy.data.worlds.new("w")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.012, 0.010, 0.035, 1)
bg.inputs[1].default_value = 1.0
floor = cube((0, 0, -0.05), (30, 30, 0.05), mat("floor", (0.02, 0.02, 0.05), metal=0.5, rough=0.3), bevel=0.0)
back = cube((0, 9, 6), (30, 0.1, 12), mat("back", (0.03, 0.02, 0.08), rough=0.8), bevel=0.0)

acc2 = (1.0, 0.3, 0.6) if ACC[0] < 0.5 else (0.2, 0.6, 1.0)


def area(loc, color, power, size=4, rot=(0, 0, 0)):
    bpy.ops.object.light_add(type="AREA", location=loc, rotation=rot)
    l = bpy.context.object
    l.data.energy, l.data.color, l.data.size = power, color, size
    return l


area((0, -6, 8), (1, 0.95, 0.9), 900, 6, (math.radians(35), 0, 0))
area((-5, 2, 5.5), ACC, 1100, 3, (0, math.radians(-50), 0))
area((5, 2, 5.5), acc2, 1100, 3, (0, math.radians(50), 0))
for i in range(8):                                # peeche halki neon patti (dhyan na bhatke)
    x = rnd.choice([-1, 1]) * rnd.uniform(3.5, 7)
    cube((x, 8.8, rnd.uniform(1.5, 9)), (rnd.uniform(0.04, 0.08), 0.05, rnd.uniform(0.5, 1.6)),
         mat(f"neon{i}", ACC if i % 2 else acc2, emit=rnd.uniform(2, 4)), bevel=0.0)

T = THEME
if T == "couple":
    person(-0.85, (0.95, 0.35, 0.55), 1, (0.08, 0.05, 0.05), girl=True)
    person(0.85, (0.25, 0.45, 0.95), -1, (0.12, 0.08, 0.05))
    heart((0, -0.2, 3.2), 0.55, mat("heart", (0.9, 0.05, 0.2), rough=0.3, emit=1.6, ecol=(1, 0.05, 0.25)))
    for i in range(10):
        heart((rnd.uniform(-3.5, 3.5), rnd.uniform(0, 3), rnd.uniform(2.2, 5.0)), rnd.uniform(0.12, 0.25),
              mat(f"h{i}", (1, 0.25, 0.45), rough=0.3, emit=1.2, ecol=(1, 0.2, 0.45)), rot=(math.radians(90), rnd.uniform(-0.4, 0.4), 0))

elif T == "heart_brain":
    gold = mat("gold", (1.0, 0.75, 0.25), metal=1.0, rough=0.25)
    cyl((0, 0, 1.2), 0.08, 2.4, gold)
    beam = cube((0, 0, 2.45), (1.8, 0.06, 0.06), gold, rot=(0, math.radians(rnd.choice([-8, 8])), 0))
    for sx in (-1.7, 1.7):
        cyl((sx, 0, 1.6 + (0.25 if sx < 0 else -0.25) * (1 if beam.rotation_euler[1] > 0 else -1)), 0.6, 0.08, gold)
    heart((-1.7, 0, 2.15), 0.45, mat("heart", (1, 0.1, 0.25), emit=5))
    b = sphere((1.7, 0, 2.05), 0.45, mat("brain", (1.0, 0.55, 0.75), rough=0.5, emit=1.5, ecol=(1, 0.5, 0.8)))
    d = b.modifiers.new("d", "DISPLACE")
    tex = bpy.data.textures.new("n", "CLOUDS")
    tex.noise_scale = 0.12
    d.texture, d.strength = tex, 0.12
    cyl((0, 0, 0.1), 1.0, 0.2, mat("base", (0.08, 0.08, 0.12), metal=0.8, rough=0.2))
elif T == "coins":
    gold = mat("gold", (1.0, 0.76, 0.2), metal=1.0, rough=0.22)
    for s in range(4):
        x = -2.0 + s * 1.3
        for k in range(rnd.randint(4, 11)):
            cyl((x + rnd.uniform(-0.04, 0.04), rnd.uniform(-0.2, 0.2), 0.08 + k * 0.17), 0.5, 0.15, gold)
    cube((1.8, 1.0, 0.5), (0.9, 0.35, 0.35), gold)
    text3d("%", (0.2, -0.6, 3.1), 1.6, mat("pc", ACC, emit=7), depth=0.25)
elif T == "mountains":
    sky = world.node_tree.nodes["Background"]
    sky.inputs[0].default_value = (0.05, 0.03, 0.12, 1)
    for i, (x, h, y) in enumerate([(-3.5, 4.5, 5), (0, 6.5, 6), (3.2, 5.0, 5.5), (-1.6, 3.2, 3), (2.0, 3.0, 2.5)]):
        bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=h * 0.55, depth=h, location=(x, y, h / 2))
        o = add(bpy.context.object, mat(f"m{i}", (0.12, 0.25, 0.35) if i < 3 else (0.1, 0.35, 0.25), rough=0.7))
        o.rotation_euler[2] = rnd.uniform(0, 1)
        bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=h * 0.17, depth=h * 0.3, location=(x, y, h - h * 0.15))
        sn = add(bpy.context.object, mat(f"s{i}", (0.95, 0.97, 1.0), rough=0.4, emit=0.4, ecol=(0.8, 0.9, 1)))
        sn.rotation_euler[2] = o.rotation_euler[2]
    sphere((2.6, 7.5, 7.5), 0.9, mat("sun", (1, 0.75, 0.3), emit=12, ecol=(1, 0.7, 0.3)))
    for i in range(8):                            # deodar ped
        x, y = rnd.uniform(-4, 4), rnd.uniform(-1, 1.5)
        bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.35, depth=1.3, location=(x, y, 0.65))
        add(bpy.context.object, mat(f"t{i}", (0.05, 0.3, 0.15), rough=0.7))
elif T == "clock":                                # sunehri jeb-ghadi
    gold = mat("gold", (1.0, 0.76, 0.3), metal=1.0, rough=0.2)
    cyl((0, 0, 2.4), 1.5, 0.25, gold, rot=(math.radians(90), 0, 0))
    cyl((0, -0.14, 2.4), 1.32, 0.05, mat("face", (0.95, 0.92, 0.85), rough=0.4), rot=(math.radians(90), 0, 0))
    for k in range(12):
        a = 2 * math.pi * k / 12
        cube((1.1 * math.sin(a), -0.18, 2.4 + 1.1 * math.cos(a)), (0.03, 0.02, 0.09), mat(f"tk{k}", (0.1, 0.1, 0.1)), rot=(0, a, 0), bevel=0)
    cube((0.3, -0.2, 2.65), (0.04, 0.02, 0.5), mat("hand", (0.1, 0.1, 0.12)), rot=(0, math.radians(30), 0), bevel=0)
    cube((0.0, -0.2, 2.75), (0.03, 0.02, 0.7), mat("hand2", (0.1, 0.1, 0.12)), rot=(0, 0, 0), bevel=0)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.25, minor_radius=0.06, location=(0, 0, 4.05), rotation=(math.radians(90), 0, 0))
    add(bpy.context.object, gold)
elif T == "balance":                              # sone ka tarazu + heere
    gold = mat("gold", (1.0, 0.75, 0.25), metal=1.0, rough=0.25)
    cyl((0, 0, 1.3), 0.08, 2.6, gold)
    cube((0, 0, 2.65), (1.9, 0.06, 0.06), gold, rot=(0, math.radians(6), 0))
    for sx, z in ((-1.8, 1.75), (1.8, 1.4)):
        cyl((sx, 0, z), 0.65, 0.08, gold)
        for k in range(3):
            bpy.ops.mesh.primitive_cone_add(vertices=8, radius1=0.16, depth=0.24, location=(sx + (k - 1) * 0.28, 0, z + 0.18), rotation=(math.pi, 0, 0))
            add(bpy.context.object, mat(f"d{sx}{k}", (0.7, 0.9, 1.0), metal=0.0, rough=0.02, emit=1.0, ecol=(0.6, 0.9, 1)))
    cyl((0, 0, 0.1), 1.0, 0.2, mat("base", (0.08, 0.06, 0.04), metal=0.8, rough=0.2))
elif T in ("vault", "elevator"):                  # tijori / sheeshe ki lift
    if T == "vault":
        cube((0, 0.2, 2.0), (1.6, 0.6, 1.9), mat("steel", (0.6, 0.62, 0.7), metal=1.0, rough=0.15))
        cyl((0, -0.45, 2.0), 0.7, 0.15, mat("dial", (1.0, 0.8, 0.3), metal=1.0, rough=0.2), rot=(math.radians(90), 0, 0))
        for k in range(4):
            cyl((0, -0.55, 2.0), 0.06, 1.2, mat(f"sp{k}", (0.9, 0.9, 0.95), metal=1.0, rough=0.2), rot=(0, math.radians(45 * k), math.radians(90)))
    else:
        glass = mat("glass", (0.6, 0.9, 1.0), rough=0.05, emit=0.4, ecol=(0.3, 0.8, 1.0), alpha=0.3)
        cube((0, 0, 2.2), (1.2, 1.2, 2.2), glass)
        for k in range(10):
            cyl((1.35, -0.6, 0.9 + k * 0.28), 0.08, 0.05, mat(f"bt{k}", ACC if k == 9 else (0.8, 0.8, 0.85), emit=4 if k == 9 else 0),
                rot=(math.radians(90), 0, 0))
elif T == "chess":
    for i in range(6):
        for j in range(6):
            cube((-1.5 + i * 0.6, -1 + j * 0.6, 0.05), (0.3, 0.3, 0.05),
                 mat(f"sq{i}{j}", (0.95, 0.85, 0.6) if (i + j) % 2 else (0.25, 0.15, 0.08), metal=0.3, rough=0.3), bevel=0.01)
    gold = mat("gold", (1.0, 0.78, 0.3), metal=1.0, rough=0.2)
    for x, h in ((-0.6, 1.4), (0.3, 1.0), (0.9, 1.2)):
        cyl((x, 0, h / 2 + 0.1), 0.22, h, gold)
        sphere((x, 0, h + 0.25), 0.2, gold)
elif T == "bowls":
    gold = mat("gold", (1.0, 0.76, 0.3), metal=1.0, rough=0.2)
    for x in (-1.6, 0, 1.6):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.7, location=(x, 0, 0.75))
        o = add(bpy.context.object, gold)
        o.scale = (1, 1, 0.7)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.28, location=(rnd.choice([-1.6, 0, 1.6]), -0.9, 0.3))
    add(bpy.context.object, mat("dia", (0.7, 0.9, 1.0), rough=0.02, emit=2.5, ecol=(0.5, 0.85, 1)))
elif T == "camels":                               # mahal + oont (saade aakar)
    sand = mat("sand", (0.85, 0.62, 0.35), rough=0.8)
    cube((0, 4, 1.5), (2.4, 0.6, 1.5), sand)
    sphere((0, 4, 3.2), 1.1, mat("dome", (0.95, 0.85, 0.6), metal=0.3, rough=0.3))
    for x in (-2.0, 2.0):
        cyl((x, 4, 2.2), 0.35, 4.4, sand)
        sphere((x, 4, 4.6), 0.4, sand)
    for k in range(5):
        x = -3 + k * 1.5
        cube((x, -0.5, 0.9), (0.45, 0.2, 0.25), sand)
        sphere((x, -0.5, 1.3), 0.25, sand)
        cube((x + 0.5, -0.5, 1.3), (0.08, 0.08, 0.35), sand, bevel=0.02)
elif T in ("matrix", "grid"):                     # chamakte number tile
    for i in range(4):
        for j in range(4):
            col = ACC if (i + j) % 2 else acc2
            cube((-1.5 + i, 0, 0.8 + j), (0.42, 0.1, 0.42), mat(f"g{i}{j}", (0.05, 0.05, 0.1), emit=0.2, ecol=col))
            text3d(str(rnd.randint(1, 9)), (-1.5 + i, -0.15, 0.8 + j), 0.55, mat(f"n{i}{j}", col, emit=6), depth=0.05)
elif T == "gates":
    for x in (-1.4, 1.4):
        cube((x, 1.0, 2.0), (0.9, 0.15, 2.0), mat(f"gate{x}", (0.06, 0.07, 0.12), metal=0.8, rough=0.2))
        cube((x, 0.8, 2.0), (0.8, 0.05, 1.9), mat(f"gl{x}", ACC if x < 0 else acc2, emit=3), bevel=0.0)
    person(-2.9, (0.3, 0.35, 0.45), 1, (0.05, 0.05, 0.05))
    person(2.9, (0.45, 0.3, 0.3), -1, (0.05, 0.05, 0.05))
elif T == "laser":
    for k in range(9):
        y = rnd.uniform(-1, 3)
        cube((rnd.uniform(-2, 2), y, 0.06), (rnd.uniform(0.6, 2.5), 0.025, 0.02), mat(f"l{k}", ACC if k % 2 else acc2, emit=10),
             rot=(0, 0, rnd.choice([0, math.pi / 2])), bevel=0)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.35, location=(0, 0, 0.6))
    add(bpy.context.object, mat("gem", (0.7, 0.9, 1.0), rough=0.02, emit=3, ecol=(0.6, 0.9, 1)))
elif T == "family":
    for k, x in enumerate((-2.2, 0, 2.2)):
        person(x, [(0.9, 0.4, 0.5), (0.3, 0.5, 0.9), (0.4, 0.8, 0.5)][k], 0, (0.06, 0.05, 0.05), girl=(k == 0))
    for x in (-1.1, 1.1):
        cube((x, 0, 3.2), (0.9, 0.03, 0.03), mat(f"ln{x}", ACC, emit=8), bevel=0)
elif T == "cube":
    cols = [(1, 0.2, 0.2), (0.2, 0.5, 1), (0.2, 0.9, 0.4), (1, 0.85, 0.2), (1, 0.5, 0.1), (0.95, 0.95, 0.95)]
    for i in range(3):
        for j in range(3):
            for k in range(3):
                cube((-0.65 + i * 0.65, -0.65 + j * 0.65, 1.0 + k * 0.65), (0.3, 0.3, 0.3),
                     mat(f"c{i}{j}{k}", rnd.choice(cols), rough=0.25, emit=0.3), bevel=0.06)
elif T == "train":
    bpy.ops.mesh.primitive_torus_add(major_radius=2.2, minor_radius=0.45, location=(0, 3, 0), rotation=(math.radians(90), 0, 0))
    add(bpy.context.object, mat("tun", (0.25, 0.22, 0.2), rough=0.8))
    for k in range(4):
        cube((-3.5 + k * 1.5, -0.5, 0.7), (0.65, 0.5, 0.55), mat(f"tr{k}", (0.8, 0.15, 0.15) if k == 0 else (0.2, 0.35, 0.7), metal=0.4, rough=0.3))
    sphere((-4.1, -0.9, 0.8), 0.15, mat("lamp", (1, 0.95, 0.7), emit=15))
elif T == "compass":
    cyl((0, 0, 0.12), 1.8, 0.2, mat("cmp", (0.85, 0.7, 0.4), metal=0.9, rough=0.25))
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.25, depth=2.6, location=(0, 0, 0.35), rotation=(0, math.radians(90), 0))
    add(bpy.context.object, mat("needle", (1, 0.2, 0.2), emit=2))
    sphere((-3.5, 4, 3.0), 0.8, mat("sun", (1, 0.7, 0.3), emit=12, ecol=(1, 0.65, 0.3)))
    person(1.9, (0.4, 0.5, 0.8), -1, (0.05, 0.05, 0.05))
elif T == "well":
    stone = mat("stone", (0.5, 0.5, 0.52), rough=0.85)
    cyl((0, 0, 0.6), 1.3, 1.2, stone)
    cyl((0, 0, 0.7), 1.0, 1.3, mat("hole", (0.01, 0.01, 0.02), rough=1.0))
    sphere((0.5, -0.9, 1.35), 0.28, mat("frog", (0.2, 0.75, 0.25), rough=0.4))
    for dx in (-0.1, 0.1):
        sphere((0.5 + dx, -1.12, 1.55), 0.08, mat("eye", (1, 1, 1), rough=0.2), seg=16)
    sphere((0, 0, 0.9), 0.35, mat("gold", (1, 0.8, 0.3), metal=1, rough=0.2, emit=1))
elif T in ("bridges", "river"):
    water = mat("water", (0.05, 0.25, 0.45), metal=0.0, rough=0.05, emit=0.3, ecol=(0.1, 0.4, 0.8))
    cube((0, 1.0, 0.0), (12, 2.2, 0.02), water, bevel=0)
    if T == "bridges":
        for k, x in enumerate((-2.5, 0, 2.5)):
            cube((x, 1.0, 0.45), (0.45, 2.4, 0.05), mat(f"br{k}", (0.45, 0.28, 0.15), rough=0.7), bevel=0.02)
            cube((x - 0.45, 1.0, 0.8), (0.03, 2.4, 0.03), mat(f"rl{k}", [ACC, acc2, (1, 0.8, 0.2)][k], emit=6), bevel=0)
    else:
        cube((0, 1.0, 0.25), (0.9, 0.35, 0.18), mat("boat", (0.55, 0.32, 0.15), rough=0.6))
        sphere((-0.3, 1.0, 0.6), 0.22, mat("goat", (0.95, 0.95, 0.95), rough=0.6))
        sphere((0.35, 1.0, 0.55), 0.2, mat("cab", (0.4, 0.85, 0.35), rough=0.5))
elif T == "flasks":
    for k, x in enumerate((-1.8, -0.6, 0.6, 1.8)):
        col = [(0.2, 1, 0.4), (0.4, 0.6, 1), (1, 0.4, 0.8), (1, 0.85, 0.2)][k]
        cyl((x, 0, 0.8), 0.42, 1.4, mat(f"fl{k}", col, rough=0.05, emit=2.5 if k == 0 else 1.0, ecol=col))
        cyl((x, 0, 1.75), 0.14, 0.5, mat(f"nk{k}", (0.8, 0.9, 1.0), rough=0.05, alpha=0.4))
elif T == "blackhole":
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.0, 0.0, 0.01, 1)
    sphere((0, 1.5, 2.6), 0.9, mat("bh", (0, 0, 0), rough=1.0))
    for r, w in ((1.6, 0.18), (2.2, 0.1), (2.9, 0.06)):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=w, location=(0, 1.5, 2.6), rotation=(math.radians(75), 0, 0))
        add(bpy.context.object, mat(f"ring{r}", (1, 0.6, 0.2), emit=8, ecol=(1, 0.55, 0.15)))
elif T == "candles":
    for x, h in ((-0.8, 1.6), (0.8, 1.1)):
        cyl((x, 0, h / 2), 0.32, h, mat(f"wax{x}", (0.95, 0.9, 0.8), rough=0.5))
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.12, depth=0.4, location=(x, 0, h + 0.25))
        add(bpy.context.object, mat(f"flame{x}", (1, 0.6, 0.15), emit=25, ecol=(1, 0.55, 0.1)))
elif T == "triangle":                             # Penrose jaisa trikon - teen chaukor beam kinaaron par
    vs = [(1.6 * math.sin(2 * math.pi * k / 3), 1.95 + 1.6 * math.cos(2 * math.pi * k / 3)) for k in range(3)]
    for k in range(3):
        (x1, z1), (x2, z2) = vs[k], vs[(k + 1) % 3]
        ln = math.hypot(x2 - x1, z2 - z1)
        ang = math.atan2(z2 - z1, x2 - x1)
        cube(((x1 + x2) / 2, -0.1 * k, (z1 + z2) / 2), (ln / 2 + 0.22, 0.24, 0.24),
             mat(f"tb{k}", [(1, 0.3, 0.3), (1, 0.7, 0.2), (0.9, 0.2, 0.5)][k], metal=0.3, rough=0.25, emit=0.8),
             rot=(0, -ang, 0))
elif T == "crime":
    for k in range(5):
        cube((rnd.uniform(-2, 2), rnd.uniform(-0.8, 1.2), 0.03), (0.45, 0.6, 0.01), mat(f"pp{k}", (0.95, 0.92, 0.8), rough=0.7),
             rot=(0, 0, rnd.uniform(-0.6, 0.6)), bevel=0)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.6, minor_radius=0.07, location=(0.4, -0.4, 0.6), rotation=(math.radians(70), 0, 0))
    add(bpy.context.object, mat("mag", (0.2, 0.2, 0.22), metal=1, rough=0.2))
    cyl((1.1, -0.9, 0.35), 0.07, 0.9, mat("hd", (0.15, 0.1, 0.05), rough=0.6), rot=(math.radians(70), 0, math.radians(-30)))
    cube((-1.5, 0.5, 0.05), (0.04, 0.9, 0.01), mat("tape", (1, 0.85, 0.1), emit=2), bevel=0)
else:                                             # question: bada chamakta '?' + ghoomte chhalle
    text3d("?", (0, 0, 2.6), 3.2, mat("q", ACC, emit=8), depth=0.35)
    for i, r in enumerate((1.6, 2.1, 2.6)):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.04, location=(0, 0, 2.5),
                                         rotation=(math.radians(rnd.uniform(60, 120)), math.radians(rnd.uniform(-30, 30)), 0))
        add(bpy.context.object, mat(f"r{i}", acc2 if i % 2 else ACC, emit=6))
    cyl((0, 0, 0.15), 1.4, 0.3, mat("ped", (0.08, 0.08, 0.14), metal=0.9, rough=0.15))

# ---------- camera ----------
if W > H:                                          # chauda (thumbnail/panel) frame
    close = T in ("couple", "heart_brain", "clock", "balance", "vault", "bowls", "candles", "cube", "flasks", "well", "triangle")
    bpy.ops.object.camera_add(location=(0, -7.6 if close else -10.5, 2.3 if close else 2.6), rotation=(math.radians(86), 0, 0))
else:
    bpy.ops.object.camera_add(location=(0, -9.5, 3.2), rotation=(math.radians(84), 0, 0))
cam = bpy.context.object
cam.data.lens = 34 if W > H else 40
cam.data.dof.use_dof = True
cam.data.dof.focus_distance = 9.3
cam.data.dof.aperture_fstop = 4.5
sc.camera = cam

# ---------- bloom (compositor glare) ----------
# v2.3.5: Blender 5.0 mein scene.node_tree hat gaya (isi se 'full' atakta tha). Chamak (bloom) ab bahar PIL mein -
# har Blender version par ek jaisa. Yahan compositor sirf purane Blender par, wo bhi try ke andar.
nt = None
if not SIMPLE and hasattr(sc, "node_tree"):
    try:
        sc.use_nodes = True
        nt = sc.node_tree
    except Exception:
        nt = None
if nt is not None:
    try:
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        rl = nt.nodes.new("CompositorNodeRLayers")
        gl = nt.nodes.new("CompositorNodeGlare")
        gl.glare_type = "FOG_GLOW"
        gl.quality = "MEDIUM"
        gl.threshold = 0.8
        gl.size = 8
        co = nt.nodes.new("CompositorNodeComposite")
        nt.links.new(rl.outputs["Image"], gl.inputs["Image"])
        nt.links.new(gl.outputs["Image"], co.inputs["Image"])
    except Exception as e:
        print("glare skip:", e)
        sc.use_nodes = False

sc.render.filepath = OUT
sc.render.image_settings.file_format = "PNG"
bpy.ops.render.render(write_still=True)
