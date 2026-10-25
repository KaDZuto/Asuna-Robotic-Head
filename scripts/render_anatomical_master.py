"""
Render master suite for the true anatomical animatronic model.
"""
import bpy
import math
import os
from mathutils import Vector

PROJECT_ROOT = "/home/alexius/Projects/Asuna Robotic head"
MASTER_BLEND = os.path.join(PROJECT_ROOT, "models/asuna_animatronic_master.blend")
RENDERS_DIR = os.path.join(PROJECT_ROOT, "renders")

print(">>> Loading master blend for anatomical renders...")
bpy.ops.wm.open_mainfile(filepath=MASTER_BLEND)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16
scene.cycles.use_denoising = True
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.film_transparent = False

# Collections
col_cams = bpy.data.collections.new("06_Master_Cameras_Lights")
scene.collection.children.link(col_cams)

# Lights
def add_light(name, ltype, loc, energy, color=(1.0, 1.0, 1.0), size=1.0):
    l_data = bpy.data.lights.new(name=name, type=ltype)
    l_data.energy = energy
    l_data.color = color
    if ltype == 'AREA':
        l_data.size = size
    l_obj = bpy.data.objects.new(name=name, object_data=l_data)
    l_obj.location = loc
    col_cams.objects.link(l_obj)
    return l_obj

add_light("Key_Light", 'AREA', (0.8, -1.4, 1.9), 320, (1.0, 0.98, 0.95), size=1.2)
add_light("Fill_Light", 'AREA', (-1.2, -1.0, 1.6), 160, (0.92, 0.95, 1.0), size=1.4)
add_light("Rim_Light", 'AREA', (0.0, 1.4, 1.8), 260, (1.0, 0.92, 0.85), size=1.5)
add_light("Bottom_Fill", 'POINT', (0.0, -0.5, 1.10), 60, (1.0, 0.96, 0.92))

# Dark studio backdrop
bpy.ops.mesh.primitive_plane_add(
    size=14.0,
    location=(0.0, 1.2, 1.2),
    rotation=(math.radians(90.0), 0, 0)
)
backdrop = bpy.context.active_object
backdrop.name = "Studio_Backdrop_Dark"
mat_backdrop = bpy.data.materials.new("Studio_Backdrop_Mat")
mat_backdrop.use_nodes = True
bsdf = mat_backdrop.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.06, 0.07, 0.09, 1.0)
bsdf.inputs['Roughness'].default_value = 0.8
backdrop.data.materials.append(mat_backdrop)
for c in list(backdrop.users_collection): c.objects.unlink(backdrop)
col_cams.objects.link(backdrop)

# Camera helper
def create_cam(name, loc, target, fov=36.0):
    cam_data = bpy.data.cameras.new(name)
    cam_data.angle = math.radians(fov)
    cam_obj = bpy.data.objects.new(name, cam_data)
    cam_obj.location = loc
    direction = Vector(target) - Vector(loc)
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    col_cams.objects.link(cam_obj)
    return cam_obj

cams = {
    "11_asuna_anatomical_front_xray": create_cam("Cam_11_Front_XRay", (0.0, -1.55, 1.30), (0.0, 0.0, 1.28), fov=44.0),
    "12_asuna_anatomical_threequarter": create_cam("Cam_12_ThreeQuarter", (0.95, -1.25, 1.48), (0.0, 0.0, 1.30), fov=42.0),
    "13_asuna_anatomical_head_jaw_detail": create_cam("Cam_13_Head_Jaw", (0.35, -0.45, 1.37), (0.0, -0.02, 1.37), fov=32.0),
    "14_asuna_tendon_arm_hand_detail": create_cam("Cam_14_Arm_Hand", (0.58, -0.32, 1.26), (0.42, 0.03, 1.255), fov=30.0),
}

# X-Ray ghost material for body and outfit
mat_ghost = bpy.data.materials.new("Exterior_Ghost_Material")
mat_ghost.use_nodes = True
bsdf_g = mat_ghost.node_tree.nodes['Principled BSDF']
bsdf_g.inputs['Base Color'].default_value = (0.88, 0.90, 0.94, 0.20)
bsdf_g.inputs['Roughness'].default_value = 0.25
bsdf_g.inputs['Alpha'].default_value = 0.20
mat_ghost.blend_method = 'BLEND'

body = bpy.data.objects.get('Body')
outfit = bpy.data.objects.get('Outfit 01')

# Set body and outfit to ghosted so internal skull, spine, and arm bones are clearly visible
for o in [body, outfit]:
    if o:
        o.data.materials.clear()
        o.data.materials.append(mat_ghost)

# Hide silicone molds during robot views
col_molds = bpy.data.collections.get("05_Silicone_Casting_Molds")
if col_molds:
    for o in col_molds.objects:
        o.hide_render = True

# Execute renders
for cname, cam in cams.items():
    out_file = os.path.join(RENDERS_DIR, f"{cname}.png")
    scene.camera = cam
    scene.render.filepath = out_file
    print(f"\n>>> [Rendering] {cname} -> {out_file}...")
    bpy.ops.render.render(write_still=True)
    print(f">>> [Done] {cname}.png saved ({os.path.getsize(out_file) // 1024} KB)")

# Save master scene with cameras
bpy.ops.wm.save_as_mainfile(filepath=MASTER_BLEND)
print("\n>>> [COMPLETE] All anatomical master views rendered successfully!")
