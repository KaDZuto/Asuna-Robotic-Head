"""
Asuna Robotic Head & Modular Bust v1 - Master Builder Script
Extracts bust from kk_Asuna/asuna.blend, builds animatronic mechanisms,
exports models, STLs, and renders all engineering views.
"""
import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix, Euler

PROJECT_ROOT = "/home/alexius/Projects/Asuna Robotic head"
SRC_BLEND = os.path.join(PROJECT_ROOT, "kk_Asuna/asuna.blend")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
STL_DIR = os.path.join(MODELS_DIR, "stl")
RENDERS_DIR = os.path.join(PROJECT_ROOT, "renders")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(STL_DIR, exist_ok=True)
os.makedirs(RENDERS_DIR, exist_ok=True)

print(">>> [1/6] Loading source blend file:", SRC_BLEND)
bpy.ops.wm.open_mainfile(filepath=SRC_BLEND)

# Clean up non-bust objects and widgets
keep_names = {'Body', 'Hair Outfit 01', 'Outfit 01', 'Armature', 'Tongue (rigged)'}
to_remove = [o for o in bpy.data.objects if o.name not in keep_names]
for o in to_remove:
    bpy.data.objects.remove(o, do_unlink=True)

print(">>> Cleaned unnecessary objects, retained:", [o.name for o in bpy.data.objects])

# [2/6] Geometry Bust Isolation at Z >= 1.15m
# Cut Body
body = bpy.data.objects.get('Body')
if body:
    bm = bmesh.new()
    bm.from_mesh(body.data)
    del_verts = [v for v in bm.verts if v.co.z < 1.15]
    bmesh.ops.delete(bm, geom=del_verts, context='VERTS')
    bm.to_mesh(body.data)
    bm.free()
    body.data.update()
    print(f"Body trimmed: {len(body.data.vertices)} vertices remaining")

# Cut Outfit (keep high neck sweater, remove shoes/bottoms)
outfit = bpy.data.objects.get('Outfit 01')
if outfit:
    bm = bmesh.new()
    bm.from_mesh(outfit.data)
    del_verts = [v for v in bm.verts if v.co.z < 1.15]
    bmesh.ops.delete(bm, geom=del_verts, context='VERTS')
    bm.to_mesh(outfit.data)
    bm.free()
    outfit.data.update()
    print(f"Outfit trimmed: {len(outfit.data.vertices)} vertices remaining")

# Cut Hair (keep strands above Z >= 1.10m for clean bust silhouette)
hair = bpy.data.objects.get('Hair Outfit 01')
if hair:
    bm = bmesh.new()
    bm.from_mesh(hair.data)
    del_verts = [v for v in bm.verts if v.co.z < 1.10]
    bmesh.ops.delete(bm, geom=del_verts, context='VERTS')
    bm.to_mesh(hair.data)
    bm.free()
    hair.data.update()
    print(f"Hair trimmed: {len(hair.data.vertices)} vertices remaining")

# Create dedicated Collections for organized scene
scene_col = bpy.context.scene.collection
def get_or_create_col(name):
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        scene_col.children.link(col)
    return col

col_exterior = get_or_create_col("01_Exterior_Aesthetics")
col_displays = get_or_create_col("02_Display_Eyes_GC9A01")
col_vision = get_or_create_col("03_Vision_Sensors")
col_jaw = get_or_create_col("04_Jaw_Mechanism")
col_neck = get_or_create_col("05_Neck_3DOF_Gimbal")
col_chassis = get_or_create_col("06_Modular_Shoulder_Chassis")
col_cams = get_or_create_col("07_Cameras_and_Lights")

# Move base meshes to exterior collection
for o in [body, hair, outfit]:
    if o:
        for c in o.users_collection:
            c.objects.unlink(o)
        col_exterior.objects.link(o)

print(">>> [2/6] Bust geometry successfully isolated and organized.")
