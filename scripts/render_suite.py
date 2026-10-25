"""
Asuna Robotic Head & Modular Bust v1 - Production Render Suite
Sets up cameras, studio lighting, materials, and renders all 8 engineering master views.
"""
import bpy
import math
import os
from mathutils import Vector

PROJECT_ROOT = "/home/alexius/Projects/Asuna Robotic head"
MASTER_BLEND = os.path.join(PROJECT_ROOT, "models/asuna_animatronic_head_bust.blend")
RENDERS_DIR = os.path.join(PROJECT_ROOT, "renders")

print(">>> Loading master animatronic blend file...")
bpy.ops.wm.open_mainfile(filepath=MASTER_BLEND)

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16
scene.cycles.use_denoising = True
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.film_transparent = False

# Ensure cameras and lights collection
col_cams = bpy.data.collections.get("07_Cameras_and_Lights")
if not col_cams:
    col_cams = bpy.data.collections.new("07_Cameras_and_Lights")
    scene.collection.children.link(col_cams)

# Clean up existing test cameras or lights
for o in list(col_cams.objects):
    bpy.data.objects.remove(o, do_unlink=True)

# Studio Lights
def add_light(name, ltype, loc, energy, color=(1.0, 1.0, 1.0), size=1.0):
    l_data = bpy.data.lights.new(name=name, type=ltype)
    l_data.energy = energy
    l_data.color = color
    if ltype == 'AREA':
        l_data.size = size
    elif ltype == 'SPOT':
        l_data.spot_size = size
    l_obj = bpy.data.objects.new(name=name, object_data=l_data)
    l_obj.location = loc
    col_cams.objects.link(l_obj)
    return l_obj

add_light("Key_Light_Front", 'AREA', (0.7, -1.3, 1.8), 280, (1.0, 0.98, 0.95), size=0.9)
add_light("Fill_Light_Left", 'AREA', (-1.1, -0.9, 1.5), 140, (0.92, 0.96, 1.0), size=1.1)
add_light("Rim_Light_Back", 'AREA', (0.0, 1.3, 1.7), 220, (1.0, 0.92, 0.88), size=1.3)
add_light("Under_Chin_Fill", 'POINT', (0.0, -0.4, 1.15), 45, (1.0, 0.96, 0.92))
add_light("Detail_Spot_Eyes", 'SPOT', (0.0, -0.8, 1.45), 90, (1.0, 1.0, 1.0), size=0.4)

# Studio Dark Gradient Backdrop
bpy.ops.mesh.primitive_plane_add(
    size=12.0,
    location=(0.0, 0.9, 1.2),
    rotation=(math.radians(90.0), 0, 0)
)
backdrop = bpy.context.active_object
backdrop.name = "Studio_Backdrop"
mat_backdrop = bpy.data.materials.get("Studio_Backdrop_Mat")
if not mat_backdrop:
    mat_backdrop = bpy.data.materials.new("Studio_Backdrop_Mat")
    mat_backdrop.use_nodes = True
nodes = mat_backdrop.node_tree.nodes
nodes.clear()
out = nodes.new('ShaderNodeOutputMaterial')
bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Base Color'].default_value = (0.05, 0.06, 0.08, 1.0)
bsdf.inputs['Roughness'].default_value = 0.7
mat_backdrop.node_tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
backdrop.data.materials.append(mat_backdrop)
for c in list(backdrop.users_collection): c.objects.unlink(backdrop)
col_cams.objects.link(backdrop)

# Camera Factory
def create_cam(name, loc, target, fov=35.0):
    cam_data = bpy.data.cameras.new(name)
    cam_data.angle = math.radians(fov)
    cam_obj = bpy.data.objects.new(name, cam_data)
    cam_obj.location = loc
    direction = Vector(target) - Vector(loc)
    cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    col_cams.objects.link(cam_obj)
    return cam_obj

bust_focus = (0.0, -0.010, 1.340)
head_focus = (0.0, -0.020, 1.390)
eyes_focus = (0.0, -0.052, 1.410)
jaw_focus = (0.015, -0.020, 1.345)
modular_focus = (0.0, 0.015, 1.220)

cameras = {
    "01_asuna_bust_front_hero": create_cam("Cam_01_Front_Hero", (0.0, -1.05, 1.36), bust_focus, fov=34.0),
    "02_asuna_bust_threequarter": create_cam("Cam_02_ThreeQuarter", (0.75, -0.85, 1.45), bust_focus, fov=36.0),
    "03_asuna_bust_side_profile": create_cam("Cam_03_Side_Profile", (1.10, -0.02, 1.35), bust_focus, fov=34.0),
    "04_xray_internal_animatronics_front": create_cam("Cam_04_XRay_Front", (0.0, -0.98, 1.35), bust_focus, fov=34.0),
    "05_xray_internal_animatronics_threequarter": create_cam("Cam_05_XRay_3Q", (0.72, -0.82, 1.44), bust_focus, fov=36.0),
    "06_detail_eye_displays_and_camera": create_cam("Cam_06_Detail_Eyes", (0.0, -0.38, 1.415), eyes_focus, fov=36.0),
    "07_detail_jaw_mechanism_articulation": create_cam("Cam_07_Detail_Jaw", (0.38, -0.38, 1.330), jaw_focus, fov=34.0),
    "08_modular_interface_torso_and_arms": create_cam("Cam_08_Modular_Interface", (0.65, -0.65, 1.10), modular_focus, fov=38.0),
}

# Save updated blend file with cameras and lights
bpy.ops.wm.save_as_mainfile(filepath=MASTER_BLEND)
print("Saved blend with camera suite:", MASTER_BLEND)

# Material for X-Ray ghosting
mat_ghost = bpy.data.materials.get("Ghost_XRay_Mat")
if not mat_ghost:
    mat_ghost = bpy.data.materials.new("Ghost_XRay_Mat")
    mat_ghost.use_nodes = True
nodes = mat_ghost.node_tree.nodes
nodes.clear()
out = nodes.new('ShaderNodeOutputMaterial')
bsdf = nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Base Color'].default_value = (0.85, 0.88, 0.92, 0.22)
bsdf.inputs['Roughness'].default_value = 0.2
bsdf.inputs['Alpha'].default_value = 0.22
mat_ghost.node_tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

body = bpy.data.objects.get('Body')
hair = bpy.data.objects.get('Hair Outfit 01')
outfit = bpy.data.objects.get('Outfit 01')

# Store original materials for Body, Hair, Outfit
orig_mats = {}
for o in [body, hair, outfit]:
    if o:
        orig_mats[o.name] = [s.material for s in o.material_slots]

def set_exterior_mode(mode="SOLID"):
    for o in [body, hair, outfit]:
        if not o: continue
        if mode == "SOLID":
            o.hide_render = False
            o.data.materials.clear()
            for m in orig_mats.get(o.name, []):
                o.data.materials.append(m)
        elif mode == "GHOST":
            o.hide_render = False
            o.data.materials.clear()
            o.data.materials.append(mat_ghost)
        elif mode == "HIDDEN":
            o.hide_render = True

# Execute Renders
plan = [
    ("01_asuna_bust_front_hero", "SOLID"),
    ("02_asuna_bust_threequarter", "SOLID"),
    ("03_asuna_bust_side_profile", "SOLID"),
    ("04_xray_internal_animatronics_front", "GHOST"),
    ("05_xray_internal_animatronics_threequarter", "GHOST"),
    ("06_detail_eye_displays_and_camera", "GHOST"),
    ("07_detail_jaw_mechanism_articulation", "GHOST"),
    ("08_modular_interface_torso_and_arms", "SOLID"),
]

for cam_key, ext_mode in plan:
    out_file = os.path.join(RENDERS_DIR, f"{cam_key}.png")
    scene.camera = cameras[cam_key]
    set_exterior_mode(ext_mode)
    scene.render.filepath = out_file
    print(f"\n>>> [Rendering] {cam_key} (mode={ext_mode}) -> {out_file}...")
    bpy.ops.render.render(write_still=True)
    print(f">>> [Done] {cam_key}.png saved ({os.path.getsize(out_file) // 1024} KB)")

print("\n>>> [ALL RENDERS COMPLETE] Output directory:", RENDERS_DIR)
