"""
Asuna Robotic Head & Modular Bust v1 - Master Builder & Renderer Script
Full animatronic engineering synthesis.
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

print(">>> [Step 1] Loading base blend...")
bpy.ops.wm.open_mainfile(filepath=SRC_BLEND)

# Clean up unwanted objects
keep_names = {'Body', 'Hair Outfit 01', 'Outfit 01', 'Armature', 'Tongue (rigged)'}
to_remove = [o for o in bpy.data.objects if o.name not in keep_names]
for o in to_remove:
    bpy.data.objects.remove(o, do_unlink=True)

# Helper for collections
scene_col = bpy.context.scene.collection
def get_col(name):
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        scene_col.children.link(col)
    return col

col_exterior = get_col("01_Exterior_Aesthetics")
col_displays = get_col("02_Display_Eyes_GC9A01")
col_vision = get_col("03_Vision_Sensors")
col_jaw = get_col("04_Jaw_Mechanism")
col_neck = get_col("05_Neck_3DOF_Gimbal")
col_chassis = get_col("06_Modular_Shoulder_Chassis")
col_cams = get_col("07_Cameras_and_Lights")

# Move base meshes to exterior
body = bpy.data.objects.get('Body')
hair = bpy.data.objects.get('Hair Outfit 01')
outfit = bpy.data.objects.get('Outfit 01')

for o in [body, hair, outfit]:
    if o:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col_exterior.objects.link(o)

print(">>> [Step 2] Isolating bust geometry at Z >= 1.15m...")
# Trim Body
if body:
    bm = bmesh.new()
    bm.from_mesh(body.data)
    del_verts = [v for v in bm.verts if v.co.z < 1.15]
    bmesh.ops.delete(bm, geom=del_verts, context='VERTS')
    bm.to_mesh(body.data)
    bm.free()
    body.data.update()

# Trim Outfit
if outfit:
    bm = bmesh.new()
    bm.from_mesh(outfit.data)
    del_verts = [v for v in bm.verts if v.co.z < 1.15]
    bmesh.ops.delete(bm, geom=del_verts, context='VERTS')
    bm.to_mesh(outfit.data)
    bm.free()
    outfit.data.update()

# Trim Hair
if hair:
    bm = bmesh.new()
    bm.from_mesh(hair.data)
    del_verts = [v for v in bm.verts if v.co.z < 1.10]
    bmesh.ops.delete(bm, geom=del_verts, context='VERTS')
    bm.to_mesh(hair.data)
    bm.free()
    hair.data.update()

print(">>> [Step 3] Material definitions for animatronic engineering...")
# Material helpers
def create_mat(name, color, metallic=0.0, roughness=0.3, emission=None, alpha=1.0):
    mat = bpy.data.materials.get(name)
    if not mat:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    if alpha < 1.0:
        bsdf.inputs['Alpha'].default_value = alpha
        mat.blend_method = 'BLEND'
    if emission:
        # Blender 4+ emission inputs
        if 'Emission Color' in bsdf.inputs:
            bsdf.inputs['Emission Color'].default_value = emission[0]
            bsdf.inputs['Emission Strength'].default_value = emission[1]
        elif 'Emission' in bsdf.inputs:
            bsdf.inputs['Emission'].default_value = emission[0]
            bsdf.inputs['Emission Strength'].default_value = emission[1]
    mat.node_tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

mat_petg_black = create_mat("PETG_Structural_Black", (0.05, 0.05, 0.05, 1.0), metallic=0.1, roughness=0.35)
mat_petg_orange = create_mat("PETG_Engineering_Orange", (0.85, 0.28, 0.03, 1.0), metallic=0.05, roughness=0.4)
mat_aluminum = create_mat("Anodized_Aluminum_CNC", (0.7, 0.72, 0.75, 1.0), metallic=0.9, roughness=0.2)
mat_brass = create_mat("Brass_Hardware", (0.85, 0.65, 0.15, 1.0), metallic=0.95, roughness=0.25)
mat_steel = create_mat("Hardened_Steel_Shaft", (0.8, 0.8, 0.82, 1.0), metallic=0.98, roughness=0.15)
mat_pcb_blue = create_mat("PCB_FR4_Blue", (0.02, 0.15, 0.45, 1.0), metallic=0.2, roughness=0.3)
mat_lens_glass = create_mat("Optical_Lens_Glass", (0.9, 0.95, 1.0, 0.3), metallic=0.0, roughness=0.05, alpha=0.3)
mat_camera_lens = create_mat("Camera_Optics_AR", (0.05, 0.02, 0.1, 1.0), metallic=0.8, roughness=0.1)

# Dynamic Anime Eye Screen Material (Emissive Hazel-Amber eye like Asuna)
mat_eye_display = bpy.data.materials.get("GC9A01_Eye_Display_Screen")
if not mat_eye_display:
    mat_eye_display = bpy.data.materials.new("GC9A01_Eye_Display_Screen")
    mat_eye_display.use_nodes = True
nodes = mat_eye_display.node_tree.nodes
nodes.clear()
out = nodes.new('ShaderNodeOutputMaterial')
bsdf = nodes.new('ShaderNodeBsdfPrincipled')
# Asuna has bright hazel-amber eyes:
bsdf.inputs['Base Color'].default_value = (0.75, 0.38, 0.08, 1.0)
bsdf.inputs['Roughness'].default_value = 0.1
if 'Emission Color' in bsdf.inputs:
    bsdf.inputs['Emission Color'].default_value = (0.85, 0.45, 0.12, 1.0)
    bsdf.inputs['Emission Strength'].default_value = 1.8
elif 'Emission' in bsdf.inputs:
    bsdf.inputs['Emission'].default_value = (0.85, 0.45, 0.12, 1.0)
    bsdf.inputs['Emission Strength'].default_value = 1.8
mat_eye_display.node_tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])

# X-Ray / Glass material for ghosted cutaway outer shell
mat_exterior_xray = create_mat("Exterior_Bust_XRay_Ghost", (0.9, 0.82, 0.80, 0.28), metallic=0.0, roughness=0.15, alpha=0.28)

print(">>> [Step 4] Building Animatronic CAD Mechanisms...")

# -------------------------------------------------------------------------
# [4.1] DISPLAY EYES GC9A01 1.28" MODULES & DUAL MOUNTING BRACKET
# -------------------------------------------------------------------------
# Center coordinates matching Asuna's eye geometry:
# Left: (+0.0346, -0.0520, 1.4046), Right: (-0.0346, -0.0520, 1.4046)
ipd = 0.0692
eye_z = 1.4046
eye_y = -0.0520
eye_pitch_angle = math.radians(4.0) # slight forward tilt

def build_gc9a01_module(name, center_x, col):
    # PCB disc Ø36.5mm, thk 1.6mm
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32, radius=0.01825, depth=0.0016,
        location=(center_x, eye_y, eye_z),
        rotation=(math.pi/2 - eye_pitch_angle, 0, 0)
    )
    pcb = bpy.context.active_object
    pcb.name = f"{name}_PCB"
    pcb.data.materials.append(mat_pcb_blue)
    for c in list(pcb.users_collection): c.objects.unlink(pcb)
    col.objects.link(pcb)
    
    # Active Screen Disc Ø32.4mm
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32, radius=0.0162, depth=0.0008,
        location=(center_x, eye_y - 0.0012, eye_z),
        rotation=(math.pi/2 - eye_pitch_angle, 0, 0)
    )
    screen = bpy.context.active_object
    screen.name = f"{name}_Active_LCD"
    screen.data.materials.append(mat_eye_display)
    for c in list(screen.users_collection): c.objects.unlink(screen)
    col.objects.link(screen)
    
    # Metal Bezel Ring Ø34mm
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32, radius=0.0170, depth=0.0012,
        location=(center_x, eye_y - 0.0008, eye_z),
        rotation=(math.pi/2 - eye_pitch_angle, 0, 0)
    )
    bezel = bpy.context.active_object
    bezel.name = f"{name}_Bezel"
    bezel.data.materials.append(mat_aluminum)
    for c in list(bezel.users_collection): c.objects.unlink(bezel)
    col.objects.link(bezel)
    
    # Protective Lens Glass
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32, radius=0.0165, depth=0.0010,
        location=(center_x, eye_y - 0.0022, eye_z),
        rotation=(math.pi/2 - eye_pitch_angle, 0, 0)
    )
    lens = bpy.context.active_object
    lens.name = f"{name}_Protective_Lens"
    lens.data.materials.append(mat_lens_glass)
    for c in list(lens.users_collection): c.objects.unlink(lens)
    col.objects.link(lens)
    
    return [pcb, screen, bezel, lens]

left_eye_objs = build_gc9a01_module("Eye_Module_Left", +0.0346, col_displays)
right_eye_objs = build_gc9a01_module("Eye_Module_Right", -0.0346, col_displays)

# Dual Eye Mounting Frame (Bridging both screens with M2 fastener lugs)
bpy.ops.mesh.primitive_cube_add(
    size=1.0,
    location=(0.0, eye_y + 0.003, eye_z)
)
eye_bridge = bpy.context.active_object
eye_bridge.name = "Dual_Eye_Mount_Bracket_GC9A01"
eye_bridge.scale = (0.092, 0.006, 0.034)
bpy.ops.object.transform_apply(scale=True)
eye_bridge.data.materials.append(mat_petg_orange)
for c in list(eye_bridge.users_collection): c.objects.unlink(eye_bridge)
col_displays.objects.link(eye_bridge)

# -------------------------------------------------------------------------
# [4.2] VISION CAMERA SENSOR MODULE (CONCEALED FOREHEAD INTEGRATION)
# -------------------------------------------------------------------------
# Position: X=0.0, Y=-0.0585, Z=1.445 (Behind central bangs, 12 deg tilt down)
cam_x = 0.0
cam_y = -0.0585
cam_z = 1.445
cam_tilt = math.radians(12.0)

# Camera PCB 16x16mm
bpy.ops.mesh.primitive_cube_add(
    size=1.0,
    location=(cam_x, cam_y, cam_z),
    rotation=(math.pi/2 - cam_tilt, 0, 0)
)
cam_pcb = bpy.context.active_object
cam_pcb.name = "Vision_Camera_PCB_1080p"
cam_pcb.scale = (0.016, 0.016, 0.0016)
bpy.ops.object.transform_apply(scale=True)
cam_pcb.data.materials.append(mat_pcb_blue)
for c in list(cam_pcb.users_collection): c.objects.unlink(cam_pcb)
col_vision.objects.link(cam_pcb)

# Camera Barrel Ø7mm x 8mm
bpy.ops.mesh.primitive_cylinder_add(
    vertices=24, radius=0.0035, depth=0.008,
    location=(cam_x, cam_y - 0.0045, cam_z - 0.001),
    rotation=(math.pi/2 - cam_tilt, 0, 0)
)
cam_barrel = bpy.context.active_object
cam_barrel.name = "Vision_Camera_Lens_Barrel"
cam_barrel.data.materials.append(mat_aluminum)
for c in list(cam_barrel.users_collection): c.objects.unlink(cam_barrel)
col_vision.objects.link(cam_barrel)

# Camera Front Optical Glass Lens Ø5mm
bpy.ops.mesh.primitive_cylinder_add(
    vertices=24, radius=0.0025, depth=0.001,
    location=(cam_x, cam_y - 0.0086, cam_z - 0.0018),
    rotation=(math.pi/2 - cam_tilt, 0, 0)
)
cam_optic = bpy.context.active_object
cam_optic.name = "Vision_Camera_Optic_Aperture"
cam_optic.data.materials.append(mat_camera_lens)
for c in list(cam_optic.users_collection): c.objects.unlink(cam_optic)
col_vision.objects.link(cam_optic)

# Forehead Camera Bracket (Secure mounting to skull chassis with M2 pitch adjust)
bpy.ops.mesh.primitive_cube_add(
    size=1.0,
    location=(cam_x, cam_y + 0.006, cam_z)
)
cam_bracket = bpy.context.active_object
cam_bracket.name = "Forehead_Vision_Camera_Bracket"
cam_bracket.scale = (0.024, 0.014, 0.022)
bpy.ops.object.transform_apply(scale=True)
cam_bracket.data.materials.append(mat_petg_orange)
for c in list(cam_bracket.users_collection): c.objects.unlink(cam_bracket)
col_vision.objects.link(cam_bracket)

# -------------------------------------------------------------------------
# [4.3] ARTICULATED JAW MECHANISM (1-DOF TMJ HINGE & SERVO DRIVE)
# -------------------------------------------------------------------------
# TMJ axis: X = +/-0.048, Y = +0.010, Z = 1.365
# Chin tip: X = 0.0, Y = -0.066, Z = 1.325
tmj_z = 1.365
tmj_y = 0.010
tmj_span = 0.048

# TMJ Cross Shaft / Pivot Hinge Ø4mm
bpy.ops.mesh.primitive_cylinder_add(
    vertices=24, radius=0.0025, depth=tmj_span * 2 + 0.012,
    location=(0.0, tmj_y, tmj_z),
    rotation=(0, math.pi/2, 0)
)
tmj_shaft = bpy.context.active_object
tmj_shaft.name = "Jaw_TMJ_Pivot_Shaft"
tmj_shaft.data.materials.append(mat_steel)
for c in list(tmj_shaft.users_collection): c.objects.unlink(tmj_shaft)
col_jaw.objects.link(tmj_shaft)

# TMJ Bearing Hubs (Left & Right)
for side, sx in [("L", tmj_span), ("R", -tmj_span)]:
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24, radius=0.0055, depth=0.008,
        location=(sx, tmj_y, tmj_z),
        rotation=(0, math.pi/2, 0)
    )
    hub = bpy.context.active_object
    hub.name = f"Jaw_TMJ_Bearing_Hub_{side}"
    hub.data.materials.append(mat_brass)
    for c in list(hub.users_collection): c.objects.unlink(hub)
    col_jaw.objects.link(hub)

# Mandible Structural Wishbone Frame (Connecting TMJ pivots to Chin Tip)
bm = bmesh.new()
# Construct a U-shaped mandible carrier
v_l_pivot = bm.verts.new((tmj_span - 0.004, tmj_y, tmj_z))
v_r_pivot = bm.verts.new((-tmj_span + 0.004, tmj_y, tmj_z))
v_chin_mid = bm.verts.new((0.0, -0.060, 1.328))
v_chin_tip = bm.verts.new((0.0, -0.065, 1.325))
v_chin_l = bm.verts.new((0.022, -0.052, 1.332))
v_chin_r = bm.verts.new((-0.022, -0.052, 1.332))
bm.edges.new((v_l_pivot, v_chin_l))
bm.edges.new((v_chin_l, v_chin_mid))
bm.edges.new((v_chin_mid, v_chin_tip))
bm.edges.new((v_chin_mid, v_chin_r))
bm.edges.new((v_chin_r, v_r_pivot))

mesh_mandible = bpy.data.meshes.new("Jaw_Mandible_Carrier_Mesh")
bm.to_mesh(mesh_mandible)
bm.free()

mandible_obj = bpy.data.objects.new("Jaw_Mandible_Structural_Carrier", mesh_mandible)
mandible_obj.data.materials.append(mat_petg_orange)
col_jaw.objects.link(mandible_obj)
# Add skin/solidify modifier to make it solid printable beam
mod_skin = mandible_obj.modifiers.new(name="Skin", type='SKIN')
mod_sub = mandible_obj.modifiers.new(name="Subsurf", type='SUBSURF')
mod_sub.levels = 1

# Micro-Servo MG90S for Jaw Articulation
# Placed in the rear cranium / base at X=0.015, Y=-0.005, Z=1.350
servo_x = 0.016
servo_y = -0.005
servo_z = 1.350
# Servo Body: 22.8 x 12.2 x 28.5 mm
bpy.ops.mesh.primitive_cube_add(
    size=1.0,
    location=(servo_x, servo_y, servo_z)
)
servo_body = bpy.context.active_object
servo_body.name = "Jaw_Actuator_Servo_MG90S"
servo_body.scale = (0.0122, 0.0228, 0.0285)
bpy.ops.object.transform_apply(scale=True)
servo_body.data.materials.append(mat_aluminum)
for c in list(servo_body.users_collection): c.objects.unlink(servo_body)
col_jaw.objects.link(servo_body)

# Servo Horn (Aluminum 16mm arm)
bpy.ops.mesh.primitive_cylinder_add(
    vertices=16, radius=0.003, depth=0.016,
    location=(servo_x, servo_y - 0.014, servo_z + 0.008),
    rotation=(math.pi/2, 0, 0)
)
servo_horn = bpy.context.active_object
servo_horn.name = "Jaw_Servo_Aluminum_Horn"
servo_horn.data.materials.append(mat_aluminum)
for c in list(servo_horn.users_collection): c.objects.unlink(servo_horn)
col_jaw.objects.link(servo_horn)

# Pushrod with M2 Ball Joints connecting Servo Horn to Jaw Lever
bpy.ops.mesh.primitive_cylinder_add(
    vertices=16, radius=0.0012, depth=0.038,
    location=(servo_x, servo_y - 0.028, servo_z - 0.006),
    rotation=(math.radians(35.0), 0, 0)
)
jaw_pushrod = bpy.context.active_object
jaw_pushrod.name = "Jaw_Kinematic_Pushrod_M2"
jaw_pushrod.data.materials.append(mat_steel)
for c in list(jaw_pushrod.users_collection): c.objects.unlink(jaw_pushrod)
col_jaw.objects.link(jaw_pushrod)

# -------------------------------------------------------------------------
# [4.4] INTERNAL CRANIUM CHASSIS (CENTRAL SKULL CARRIER FRAME)
# -------------------------------------------------------------------------
# Unibody structural spine connecting cranium base, eye mount, camera, and jaw
bpy.ops.mesh.primitive_cube_add(
    size=1.0,
    location=(0.0, -0.010, 1.395)
)
cranium_core = bpy.context.active_object
cranium_core.name = "Cranium_Internal_Chassis_Unibody"
cranium_core.scale = (0.076, 0.072, 0.088)
bpy.ops.object.transform_apply(scale=True)
# Bevel modifier for realistic rounded engineered look
mod_bev = cranium_core.modifiers.new("Bevel", 'BEVEL')
mod_bev.width = 0.008
mod_bev.segments = 2
cranium_core.data.materials.append(mat_petg_black)
for c in list(cranium_core.users_collection): c.objects.unlink(cranium_core)
col_exterior.objects.link(cranium_core)

# Eyebrow Actuator Mounts (Dual Micro-servos at Z=1.425, Y=-0.048)
for side, bx in [("L", 0.026), ("R", -0.026)]:
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(bx, -0.046, 1.428)
    )
    brow_srv = bpy.context.active_object
    brow_srv.name = f"Eyebrow_Micro_Servo_{side}"
    brow_srv.scale = (0.008, 0.014, 0.012)
    bpy.ops.object.transform_apply(scale=True)
    brow_srv.data.materials.append(mat_aluminum)
    for c in list(brow_srv.users_collection): c.objects.unlink(brow_srv)
    col_exterior.objects.link(brow_srv)

# -------------------------------------------------------------------------
# [4.5] 3-DOF ARTICULATED NECK MECHANISM (PITCH, YAW, ROLL GIMBAL)
# -------------------------------------------------------------------------
neck_base_z = 1.255
neck_mid_z = 1.300
neck_top_z = 1.345

# 1. Base Yaw Bearing Ring Ø64mm x 12mm at Z=1.265
bpy.ops.mesh.primitive_cylinder_add(
    vertices=36, radius=0.032, depth=0.012,
    location=(0.0, 0.015, neck_base_z + 0.010)
)
yaw_ring = bpy.context.active_object
yaw_ring.name = "Neck_Yaw_Base_Bearing_Ring"
yaw_ring.data.materials.append(mat_aluminum)
for c in list(yaw_ring.users_collection): c.objects.unlink(yaw_ring)
col_neck.objects.link(yaw_ring)

# 2. Central Universal / Cardan 2-Axis Joint (Pitch & Roll) at Z=1.305
bpy.ops.mesh.primitive_uv_sphere_add(
    segments=24, ring_count=16, radius=0.014,
    location=(0.0, 0.015, neck_mid_z)
)
neck_gimbal_core = bpy.context.active_object
neck_gimbal_core.name = "Neck_Cardan_Gimbal_Center"
neck_gimbal_core.data.materials.append(mat_brass)
for c in list(neck_gimbal_core.users_collection): c.objects.unlink(neck_gimbal_core)
col_neck.objects.link(neck_gimbal_core)

# Cardan Cross Pins (Pitch pin X-axis, Roll pin Y-axis)
bpy.ops.mesh.primitive_cylinder_add(
    vertices=16, radius=0.0035, depth=0.044,
    location=(0.0, 0.015, neck_mid_z),
    rotation=(0, math.pi/2, 0)
)
pitch_pin = bpy.context.active_object
pitch_pin.name = "Neck_Pitch_Pivot_Pin"
pitch_pin.data.materials.append(mat_steel)
for c in list(pitch_pin.users_collection): c.objects.unlink(pitch_pin)
col_neck.objects.link(pitch_pin)

# 3. High-Torque Heavy-Duty Neck Servos (3x Feetech STS3215 / RDS3115 Class: 40x20x40mm)
# Yaw Servo at base
bpy.ops.mesh.primitive_cube_add(
    size=1.0,
    location=(0.0, 0.038, neck_base_z + 0.020)
)
yaw_servo = bpy.context.active_object
yaw_servo.name = "Neck_Actuator_Yaw_Servo"
yaw_servo.scale = (0.040, 0.020, 0.040)
bpy.ops.object.transform_apply(scale=True)
yaw_servo.data.materials.append(mat_aluminum)
for c in list(yaw_servo.users_collection): c.objects.unlink(yaw_servo)
col_neck.objects.link(yaw_servo)

# Dual Differential Pitch/Roll Actuators (Left & Right)
for side, sx in [("L", 0.028), ("R", -0.028)]:
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(sx, -0.012, neck_base_z + 0.024)
    )
    diff_servo = bpy.context.active_object
    diff_servo.name = f"Neck_Actuator_PitchRoll_{side}"
    diff_servo.scale = (0.020, 0.040, 0.040)
    bpy.ops.object.transform_apply(scale=True)
    diff_servo.data.materials.append(mat_aluminum)
    for c in list(diff_servo.users_collection): c.objects.unlink(diff_servo)
    col_neck.objects.link(diff_servo)
    
    # Differential Connecting Rods (Heavy duty M3 turnbuckles)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16, radius=0.0025, depth=0.052,
        location=(sx, -0.002, neck_mid_z + 0.010),
        rotation=(math.radians(12.0), 0, 0)
    )
    diff_rod = bpy.context.active_object
    diff_rod.name = f"Neck_Differential_Turnbuckle_Rod_{side}"
    diff_rod.data.materials.append(mat_steel)
    for c in list(diff_rod.users_collection): c.objects.unlink(diff_rod)
    col_neck.objects.link(diff_rod)

# 4. Upper Neck Top Plate (Connecting C1 Atlas to Cranium Chassis)
bpy.ops.mesh.primitive_cylinder_add(
    vertices=32, radius=0.028, depth=0.008,
    location=(0.0, 0.015, neck_top_z)
)
neck_top_plate = bpy.context.active_object
neck_top_plate.name = "Neck_Top_Interface_Flange_Atlas"
neck_top_plate.data.materials.append(mat_petg_orange)
for c in list(neck_top_plate.users_collection): c.objects.unlink(neck_top_plate)
col_neck.objects.link(neck_top_plate)

# -------------------------------------------------------------------------
# [4.6] MODULAR CLAVICLE & SHOULDER BASE CHASSIS (TORSO & ARMS INTERFACES)
# -------------------------------------------------------------------------
chassis_z = 1.180

# 1. Structural Transverse Clavicle Truss Bridge (PETG Unibody)
bpy.ops.mesh.primitive_cube_add(
    size=1.0,
    location=(0.0, 0.018, chassis_z + 0.035)
)
clavicle_bridge = bpy.context.active_object
clavicle_bridge.name = "Modular_Clavicle_Shoulder_Truss_Bridge"
clavicle_bridge.scale = (0.210, 0.088, 0.045)
bpy.ops.object.transform_apply(scale=True)
mod_bev2 = clavicle_bridge.modifiers.new("Bevel", 'BEVEL')
mod_bev2.width = 0.006
mod_bev2.segments = 2
clavicle_bridge.data.materials.append(mat_petg_black)
for c in list(clavicle_bridge.users_collection): c.objects.unlink(clavicle_bridge)
col_chassis.objects.link(clavicle_bridge)

# 2. Standardized Torso Modular Docking Port (Bottom)
# 4x M4 Pattern 50x50mm + Central Cable Pass-Through Duct Ø25mm
bpy.ops.mesh.primitive_cube_add(
    size=1.0,
    location=(0.0, 0.015, chassis_z)
)
torso_flange = bpy.context.active_object
torso_flange.name = "Torso_Modular_Interface_Flange_M4"
torso_flange.scale = (0.075, 0.075, 0.012)
bpy.ops.object.transform_apply(scale=True)
torso_flange.data.materials.append(mat_petg_orange)
for c in list(torso_flange.users_collection): c.objects.unlink(torso_flange)
col_chassis.objects.link(torso_flange)

# Central Cable Pass-Through Duct Ring Ø25mm
bpy.ops.mesh.primitive_cylinder_add(
    vertices=28, radius=0.0125, depth=0.030,
    location=(0.0, 0.015, chassis_z)
)
cable_duct = bpy.context.active_object
cable_duct.name = "Torso_Cable_Harness_Pass_Through_Ø25mm"
cable_duct.data.materials.append(mat_brass)
for c in list(cable_duct.users_collection): c.objects.unlink(cable_duct)
col_chassis.objects.link(cable_duct)

# 4x M4 Mounting Bolt Bosses (50x50mm spacing)
for bx, by in [(-0.025, -0.010), (0.025, -0.010), (-0.025, 0.040), (0.025, 0.040)]:
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16, radius=0.0035, depth=0.018,
        location=(bx, by, chassis_z)
    )
    boss = bpy.context.active_object
    boss.name = f"Torso_Mount_M4_Insert_Boss_({bx*1000:+.0f},{by*1000:+.0f})"
    boss.data.materials.append(mat_brass)
    for c in list(boss.users_collection): c.objects.unlink(boss)
    col_chassis.objects.link(boss)

# 3. Symmetrical Arm Quick-Mount Docks (Left & Right Shoulder Joint Sockets)
# Centered at X = +/-0.098m, Y = +0.021m, Z = 1.255m
arm_span_x = 0.098
arm_span_y = 0.021
arm_span_z = 1.255

for side, ax in [("Left", arm_span_x), ("Right", -arm_span_x)]:
    # Socket Collar Ø26mm outer, Ø20mm inner
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32, radius=0.013, depth=0.018,
        location=(ax, arm_span_y, arm_span_z),
        rotation=(0, math.pi/2, 0)
    )
    arm_dock = bpy.context.active_object
    arm_dock.name = f"Arm_{side}_Quick_Mount_Socket_Ø20mm"
    arm_dock.data.materials.append(mat_aluminum)
    for c in list(arm_dock.users_collection): c.objects.unlink(arm_dock)
    col_chassis.objects.link(arm_dock)
    
    # Flange with 4x M3 Pattern for Bolting Arm Pitch/Roll Actuator
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32, radius=0.019, depth=0.005,
        location=(ax + (0.009 if ax > 0 else -0.009), arm_span_y, arm_span_z),
        rotation=(0, math.pi/2, 0)
    )
    flange = bpy.context.active_object
    flange.name = f"Arm_{side}_Modular_Bolting_Flange_M3"
    flange.data.materials.append(mat_petg_orange)
    for c in list(flange.users_collection): c.objects.unlink(flange)
    col_chassis.objects.link(flange)

print(">>> [Step 5] Exporting Modular 3D-Printable STL Parts...")
# STL Exporter helper
def export_stl(objects, filename):
    filepath = os.path.join(STL_DIR, filename)
    # Select target objects
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:
        if o: o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    try:
        # Blender 4+ wm.stl_export
        bpy.ops.wm.stl_export(filepath=filepath, export_selected_objects=True)
    except Exception:
        bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True)
    print(f"Exported STL: {filename}")

export_stl([cranium_core], "01_cranium_chassis.stl")
export_stl([mandible_obj, tmj_shaft], "02_jaw_mandible_mechanism.stl")
export_stl([eye_bridge, left_eye_objs[0], right_eye_objs[0]], "03_dual_eye_display_mount_gc9a01.stl")
export_stl([cam_bracket, cam_pcb], "04_forehead_vision_camera_bracket.stl")
export_stl([yaw_ring, neck_gimbal_core, pitch_pin, neck_top_plate], "05_neck_3dof_gimbal_assembly.stl")
export_stl([clavicle_bridge, torso_flange, cable_duct], "06_modular_shoulder_torso_chassis.stl")

# Save master animatronic blend file
master_blend = os.path.join(MODELS_DIR, "asuna_animatronic_head_bust.blend")
bpy.ops.wm.save_as_mainfile(filepath=master_blend)
print("Saved master blend file:", master_blend)

print(">>> [Step 6] Setting up Lighting, Studio, and Cameras for Renders...")
# Setup studio lighting
def add_light(name, ltype, loc, energy, color=(1.0, 1.0, 1.0), size=1.0):
    l_data = bpy.data.lights.new(name=name, type=ltype)
    l_data.energy = energy
    l_data.color = color
    if ltype in ('AREA', 'SPOT'):
        l_data.size = size
    l_obj = bpy.data.objects.new(name=name, object_data=l_data)
    l_obj.location = loc
    col_cams.objects.link(l_obj)
    return l_obj

add_light("Key_Light_Front", 'AREA', (0.6, -1.2, 1.8), 220, (1.0, 0.98, 0.95), size=0.8)
add_light("Fill_Light_Left", 'AREA', (-1.0, -0.8, 1.5), 110, (0.92, 0.95, 1.0), size=1.0)
add_light("Rim_Light_Back", 'AREA', (0.0, 1.2, 1.7), 180, (1.0, 0.90, 0.85), size=1.2)
add_light("Under_Chin_Light", 'POINT', (0.0, -0.4, 1.15), 35, (1.0, 0.95, 0.90))

# Studio Background Backdrop
bpy.ops.mesh.primitive_plane_add(
    size=10.0,
    location=(0.0, 0.8, 0.8),
    rotation=(math.radians(90.0), 0, 0)
)
backdrop = bpy.context.active_object
backdrop.name = "Studio_Backdrop"
mat_backdrop = create_mat("Studio_Matte_Dark", (0.08, 0.09, 0.11, 1.0), roughness=0.8)
backdrop.data.materials.append(mat_backdrop)
for c in list(backdrop.users_collection): c.objects.unlink(backdrop)
col_cams.objects.link(backdrop)

# Configure Render Engine (Workbench/EEVEE high-res for speed and clean technical rendering)
bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.context.scene.render.resolution_percentage = 100
bpy.context.scene.render.film_transparent = False

# Camera setup helper
def create_camera(name, loc, target, fov=45.0):
    cam_data = bpy.data.cameras.new(name)
    cam_data.angle = math.radians(fov)
    cam_obj = bpy.data.objects.new(name, cam_data)
    cam_obj.location = loc
    # Track to target
    direction = Vector(target) - Vector(loc)
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()
    col_cams.objects.link(cam_obj)
    return cam_obj

head_center = (0.0, -0.015, 1.390)
bust_center = (0.0, 0.000, 1.340)
eyes_center = (0.0, -0.052, 1.405)
jaw_neck_center = (0.0, -0.010, 1.320)
modular_center = (0.0, 0.015, 1.200)

cams = {
    "01_asuna_bust_front_hero": create_camera("Cam_Front_Hero", (0.0, -1.05, 1.37), bust_center, fov=34.0),
    "02_asuna_bust_threequarter": create_camera("Cam_ThreeQuarter", (0.75, -0.85, 1.46), bust_center, fov=36.0),
    "03_asuna_bust_side_profile": create_camera("Cam_Side_Profile", (1.10, -0.02, 1.36), bust_center, fov=34.0),
    "04_xray_internal_animatronics_front": create_camera("Cam_XRay_Front", (0.0, -0.98, 1.36), bust_center, fov=34.0),
    "05_xray_internal_animatronics_threequarter": create_camera("Cam_XRay_3Q", (0.72, -0.82, 1.45), bust_center, fov=36.0),
    "06_detail_eye_displays_and_camera": create_camera("Cam_Detail_Eyes", (0.0, -0.42, 1.415), (0.0, -0.055, 1.415), fov=38.0),
    "07_detail_jaw_mechanism_articulation": create_camera("Cam_Detail_Jaw", (0.42, -0.42, 1.335), (0.01, -0.025, 1.345), fov=36.0),
    "08_modular_interface_torso_and_arms": create_camera("Cam_Modular_Interface", (0.65, -0.65, 1.12), (0.0, 0.015, 1.22), fov=40.0),
}

print(">>> [Step 7] Rendering 8 Master Views...")

def render_view(cam_key, xray_mode=False):
    cam = cams[cam_key]
    bpy.context.scene.camera = cam
    output_path = os.path.join(RENDERS_DIR, f"{cam_key}.png")
    
    # Handle X-ray / ghosted shell mode
    if xray_mode:
        # Hide or ghost outer aesthetic skin
        for o in [body, hair, outfit]:
            if o:
                o.hide_render = False
                o.data.materials.clear()
                o.data.materials.append(mat_exterior_xray)
    else:
        # Normal solid appearance
        for o in [body, hair, outfit]:
            if o:
                o.hide_render = False
    
    bpy.context.scene.render.filepath = output_path
    print(f"Rendering {cam_key} -> {output_path}...")
    bpy.ops.render.render(write_still=True)
    print(f"Rendered {cam_key} successfully.")

# 1-3 External hero renders
render_view("01_asuna_bust_front_hero", xray_mode=False)
render_view("02_asuna_bust_threequarter", xray_mode=False)
render_view("03_asuna_bust_side_profile", xray_mode=False)

# 4-5 X-Ray Internal animatronics
render_view("04_xray_internal_animatronics_front", xray_mode=True)
render_view("05_xray_internal_animatronics_threequarter", xray_mode=True)

# 6-8 Technical detail views
render_view("06_detail_eye_displays_and_camera", xray_mode=True)
render_view("07_detail_jaw_mechanism_articulation", xray_mode=True)
render_view("08_modular_interface_torso_and_arms", xray_mode=False)

print(">>> [SUCCESS] All models, STLs, and renders generated cleanly!")
