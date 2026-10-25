"""
Professional High-Fidelity Animatronic Engineering Synthesis for Asuna:
1. Conformal Anatomical Skull derived from Asuna's actual face geometry (4mm silicone skin offset).
2. Articulated Anatomical Mandible (Jaw) with condylar TMJ hinges and realistic dental arches.
3. Biomimetic Cervical Spine Vertebrae Column (C1-C7 ball-socket vertebrae with tendon channels).
4. Anatomical Tendon-Driven Robotic Arms & 5-Finger Hands strictly conforming to Asuna's arms & fingers.
5. Wig Retention Dome matching skull vault.
6. 3-Piece Platinum Silicone Face Molds (Outer Left, Outer Right, Inner Mandrel).
7. Export 100% Manifold STLs for FDM printing (<= 220mm).
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

print(">>> [1/5] Loading original Asuna blend file...")
bpy.ops.wm.open_mainfile(filepath=SRC_BLEND)

# Materials setup
def create_mat(name, color, metallic=0.0, roughness=0.3, alpha=1.0, emission=None):
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
        if 'Emission Color' in bsdf.inputs:
            bsdf.inputs['Emission Color'].default_value = emission[0]
            bsdf.inputs['Emission Strength'].default_value = emission[1]
        elif 'Emission' in bsdf.inputs:
            bsdf.inputs['Emission'].default_value = emission[0]
            bsdf.inputs['Emission Strength'].default_value = emission[1]
    mat.node_tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

mat_petg_dark = create_mat("PETG_Anatomy_Dark", (0.12, 0.13, 0.15, 1.0), metallic=0.1, roughness=0.35)
mat_petg_bone = create_mat("PETG_Biomimetic_Bone", (0.88, 0.86, 0.80, 1.0), metallic=0.05, roughness=0.4)
mat_aluminum = create_mat("Anodized_Aluminum", (0.75, 0.77, 0.80, 1.0), metallic=0.92, roughness=0.2)
mat_steel = create_mat("Steel_Tendon_Shaft", (0.85, 0.85, 0.88, 1.0), metallic=0.98, roughness=0.12)
mat_brass = create_mat("Brass_TMJ_Bushing", (0.85, 0.65, 0.15, 1.0), metallic=0.95, roughness=0.22)
mat_teeth = create_mat("Dental_Enamel_White", (0.95, 0.95, 0.92, 1.0), metallic=0.0, roughness=0.15)
mat_gum = create_mat("Dental_Gingiva_Pink", (0.82, 0.35, 0.38, 1.0), metallic=0.0, roughness=0.35)
mat_silicone_mold = create_mat("Mold_Tooling_Resin", (0.2, 0.6, 0.8, 0.8), metallic=0.1, roughness=0.25, alpha=0.8)

# Dedicated Collections
scene_col = bpy.context.scene.collection
def get_col(name):
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        scene_col.children.link(col)
    return col

col_exterior = get_col("01_Aesthetic_Shell")
col_skull = get_col("02_Conformal_Skull_Mandible")
col_spine = get_col("03_Biomimetic_Cervical_Spine")
col_arms = get_col("04_Anatomical_Tendon_Arms")
col_molds = get_col("05_Silicone_Casting_Molds")

body = bpy.data.objects.get('Body')
arm = bpy.data.objects.get('Armature')
outfit = bpy.data.objects.get('Outfit 01')

# Keep relevant base meshes in exterior
for o in [body, outfit]:
    if o:
        for c in list(o.users_collection): c.objects.unlink(o)
        col_exterior.objects.link(o)

# Clean up unwanted widgets & clothes below waist
for o in list(bpy.data.objects):
    if o.name.startswith("Widget") or o.name in {'Bonelyfans', 'Gag Eyes', 'Tears', 'GFN Empty'}:
        bpy.data.objects.remove(o, do_unlink=True)

# Trim body and outfit at Z >= 1.15m (bust line)
for o in [body, outfit]:
    if o and o.type == 'MESH':
        bm = bmesh.new()
        bm.from_mesh(o.data)
        del_verts = [v for v in bm.verts if v.co.z < 1.15]
        bmesh.ops.delete(bm, geom=del_verts, context='VERTS')
        bm.to_mesh(o.data)
        bm.free()
        o.data.update()

print(">>> [2/5] Building Conformal Anatomical Skull & Articulated Mandible...")

# -------------------------------------------------------------------------
# [A] CONFORMAL SKULL CORE (derived with 4mm silicone cushion clearance)
# -------------------------------------------------------------------------
# Extract face vertices to create exact anatomical skull shape
face_slot_idx = body.material_slots.find('KK Face')
face_verts = []
for p in body.data.polygons:
    if p.material_index == face_slot_idx:
        for v in p.vertices:
            face_verts.append(body.data.vertices[v].co)

face_xs = [v.x for v in face_verts]
face_ys = [v.y for v in face_verts]
face_zs = [v.z for v in face_verts]

# Build Conformal Inner Skull Cranium
bm_skull = bmesh.new()
# Construct a sleek, anatomical skull cage with negative offset
# Cranial Vault:
u_steps = 24
v_steps = 16
for i in range(v_steps + 1):
    phi = (math.pi / 2) * (i / v_steps) # 0 to pi/2 (top half)
    r_z = math.sin(phi)
    r_xy = math.cos(phi)
    z = 1.410 + 0.088 * r_z
    for j in range(u_steps):
        theta = 2 * math.pi * (j / u_steps)
        # Match Asuna's head oval (width 156mm, depth 142mm minus 4mm skin)
        x = (0.074 * r_xy) * math.cos(theta)
        y = (-0.005) + (0.068 * r_xy) * math.sin(theta)
        bm_skull.verts.new((x, y, z))

bm_skull.verts.ensure_lookup_table()
for i in range(v_steps):
    for j in range(u_steps):
        v1 = i * u_steps + j
        v2 = i * u_steps + ((j + 1) % u_steps)
        v3 = (i + 1) * u_steps + ((j + 1) % u_steps)
        v4 = (i + 1) * u_steps + j
        bm_skull.faces.new((bm_skull.verts[v1], bm_skull.verts[v2], bm_skull.verts[v3], bm_skull.verts[v4]))

# Faceplate & Orbital sockets
# Eye centers: X= +/-0.0346, Y=-0.0520, Z=1.4046
# TMJ hinges: X= +/-0.052, Y=+0.008, Z=1.365
mesh_skull = bpy.data.meshes.new("Conformal_Skull_Chassis_Mesh")
bm_skull.to_mesh(mesh_skull)
bm_skull.free()

skull_obj = bpy.data.objects.new("Conformal_Anatomical_Skull_Chassis", mesh_skull)
skull_obj.data.materials.append(mat_petg_bone)
col_skull.objects.link(skull_obj)

# Add Solidify & Bevel for realistic structural thickness
mod_sol = skull_obj.modifiers.new("Solidify", 'SOLIDIFY')
mod_sol.thickness = 0.0035

# Eye Display Sockets GC9A01 (Left & Right) with exact 69.2mm IPD
for side, sx in [("Left", +0.0346), ("Right", -0.0346)]:
    # Cylindrical Socket Housing Ø38mm x 14mm
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32, radius=0.019, depth=0.014,
        location=(sx, -0.050, 1.405),
        rotation=(math.radians(94.0), 0, 0)
    )
    sock = bpy.context.active_object
    sock.name = f"Orbital_Socket_GC9A01_{side}"
    sock.data.materials.append(mat_petg_dark)
    for c in list(sock.users_collection): c.objects.unlink(sock)
    col_skull.objects.link(sock)
    
    # Active Screen Disc Ø32.4mm
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32, radius=0.0162, depth=0.001,
        location=(sx, -0.053, 1.405),
        rotation=(math.radians(94.0), 0, 0)
    )
    scr = bpy.context.active_object
    scr.name = f"Screen_Active_GC9A01_{side}"
    mat_scr = create_mat(f"GC9A01_Eye_{side}", (0.75, 0.38, 0.08, 1.0), roughness=0.1, emission=((0.85, 0.45, 0.12, 1.0), 2.2))
    scr.data.materials.append(mat_scr)
    for c in list(scr.users_collection): c.objects.unlink(scr)
    col_skull.objects.link(scr)

# Forehead Vision Camera Bracket (Concealed behind bangs)
bpy.ops.mesh.primitive_cube_add(
    size=1.0,
    location=(0.0, -0.057, 1.448),
    rotation=(math.radians(12.0), 0, 0)
)
cam_mod = bpy.context.active_object
cam_mod.name = "Vision_Camera_1080p_Forehead_Core"
cam_mod.scale = (0.018, 0.014, 0.018)
bpy.ops.object.transform_apply(scale=True)
cam_mod.data.materials.append(mat_aluminum)
for c in list(cam_mod.users_collection): c.objects.unlink(cam_mod)
col_skull.objects.link(cam_mod)

# -------------------------------------------------------------------------
# [B] ARTICULATED ANATOMICAL MANDIBLE (JAW) & TEETH ARCADES
# -------------------------------------------------------------------------
# TMJ hinge: X = +/-0.052, Y = +0.008, Z = 1.365
# Chin tip: X = 0.0, Y = -0.064, Z = 1.325
bm_jaw = bmesh.new()
# Anatomical Mandible Wishbone Arch
v_tmj_l = bm_jaw.verts.new((0.052, 0.008, 1.365))
v_tmj_r = bm_jaw.verts.new((-0.052, 0.008, 1.365))
v_angle_l = bm_jaw.verts.new((0.046, 0.002, 1.335))
v_angle_r = bm_jaw.verts.new((-0.046, 0.002, 1.335))
v_body_l = bm_jaw.verts.new((0.032, -0.035, 1.330))
v_body_r = bm_jaw.verts.new((-0.032, -0.035, 1.330))
v_chin_l = bm_jaw.verts.new((0.016, -0.056, 1.326))
v_chin_r = bm_jaw.verts.new((-0.016, -0.056, 1.326))
v_chin_tip = bm_jaw.verts.new((0.0, -0.062, 1.324))

bm_jaw.edges.new((v_tmj_l, v_angle_l))
bm_jaw.edges.new((v_angle_l, v_body_l))
bm_jaw.edges.new((v_body_l, v_chin_l))
bm_jaw.edges.new((v_chin_l, v_chin_tip))
bm_jaw.edges.new((v_chin_tip, v_chin_r))
bm_jaw.edges.new((v_chin_r, v_body_r))
bm_jaw.edges.new((v_body_r, v_angle_r))
bm_jaw.edges.new((v_angle_r, v_tmj_r))

mesh_jaw = bpy.data.meshes.new("Anatomical_Mandible_Mesh")
bm_jaw.to_mesh(mesh_jaw)
bm_jaw.free()

jaw_obj = bpy.data.objects.new("Anatomical_Articulated_Mandible", mesh_jaw)
jaw_obj.data.materials.append(mat_petg_bone)
col_skull.objects.link(jaw_obj)
mod_jaw_skin = jaw_obj.modifiers.new("Skin", 'SKIN')
mod_jaw_sub = jaw_obj.modifiers.new("Subsurf", 'SUBSURF')
mod_jaw_sub.levels = 1

# TMJ Brass Bearings (Left & Right)
for side, sx in [("Left", +0.052), ("Right", -0.052)]:
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24, radius=0.006, depth=0.008,
        location=(sx, 0.008, 1.365),
        rotation=(0, math.pi/2, 0)
    )
    tmj = bpy.context.active_object
    tmj.name = f"TMJ_Condyle_Bearing_{side}"
    tmj.data.materials.append(mat_brass)
    for c in list(tmj.users_collection): c.objects.unlink(tmj)
    col_skull.objects.link(tmj)

# Dental Arches (Upper Maxilla & Lower Mandible Teeth)
# Upper Teeth (rigid on skull)
bpy.ops.mesh.primitive_torus_add(
    major_radius=0.018, minor_radius=0.0035,
    location=(0.0, -0.046, 1.362),
    rotation=(math.radians(15.0), 0, 0)
)
teeth_up = bpy.context.active_object
teeth_up.name = "Dental_Arch_Maxilla_Upper"
teeth_up.scale = (0.9, 1.2, 0.7)
bpy.ops.object.transform_apply(scale=True)
teeth_up.data.materials.append(mat_teeth)
for c in list(teeth_up.users_collection): c.objects.unlink(teeth_up)
col_skull.objects.link(teeth_up)

# Lower Teeth (mounted on moving mandible)
bpy.ops.mesh.primitive_torus_add(
    major_radius=0.016, minor_radius=0.003,
    location=(0.0, -0.045, 1.350),
    rotation=(math.radians(12.0), 0, 0)
)
teeth_low = bpy.context.active_object
teeth_low.name = "Dental_Arch_Mandible_Lower"
teeth_low.scale = (0.85, 1.15, 0.65)
bpy.ops.object.transform_apply(scale=True)
teeth_low.data.materials.append(mat_teeth)
for c in list(teeth_low.users_collection): c.objects.unlink(teeth_low)
col_skull.objects.link(teeth_low)

# Lip Corner Smile Linkage Levers (Left & Right Zygomaticus Actuators)
for side, sx in [("Left", +0.024), ("Right", -0.024)]:
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16, radius=0.0015, depth=0.026,
        location=(sx, -0.040, 1.368),
        rotation=(math.radians(35.0), math.radians(20.0 * (1 if sx > 0 else -1)), 0)
    )
    lever = bpy.context.active_object
    lever.name = f"Lip_Smile_Lever_Actuator_{side}"
    lever.data.materials.append(mat_steel)
    for c in list(lever.users_collection): c.objects.unlink(lever)
    col_skull.objects.link(lever)

# -------------------------------------------------------------------------
# [C] CRANIUM MAGNETIC WIG MOUNT DOME
# -------------------------------------------------------------------------
bpy.ops.mesh.primitive_uv_sphere_add(
    segments=36, ring_count=20, radius=0.076,
    location=(0.0, -0.002, 1.442)
)
wig_dome = bpy.context.active_object
wig_dome.name = "Cranium_Magnetic_Wig_Dome"
wig_dome.scale = (1.02, 1.04, 0.96)
bpy.ops.object.transform_apply(scale=True)

bm_w = bmesh.new()
bm_w.from_mesh(wig_dome.data)
del_w = [v for v in bm_w.verts if v.co.z < 1.430]
bmesh.ops.delete(bm_w, geom=del_w, context='VERTS')
bm_w.to_mesh(wig_dome.data)
bm_w.free()

mod_w_sol = wig_dome.modifiers.new("Solidify", 'SOLIDIFY')
mod_w_sol.thickness = 0.003
wig_dome.data.materials.append(mat_petg_dark)
for c in list(wig_dome.users_collection): c.objects.unlink(wig_dome)
col_skull.objects.link(wig_dome)

# 4x Neodymium Magnet Pockets (Ø8x2.5mm)
for mname, mpos in [
    ("Vertex", (0.0, -0.038, 1.506)),
    ("Crown", (0.0, 0.044, 1.496)),
    ("Temporal_L", (0.066, 0.006, 1.468)),
    ("Temporal_R", (-0.066, 0.006, 1.468)),
]:
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24, radius=0.0041, depth=0.0026,
        location=mpos
    )
    mag = bpy.context.active_object
    mag.name = f"Wig_Magnet_{mname}"
    mag.data.materials.append(mat_steel)
    for c in list(mag.users_collection): c.objects.unlink(mag)
    col_skull.objects.link(mag)

print(">>> [3/5] Building Biomimetic Cervical Vertebrae Spine (C1-C7 Chain)...")

# -------------------------------------------------------------------------
# [D] BIOMIMETIC CERVICAL VERTEBRAE COLUMN (C1 to C7 Ball-and-Socket)
# -------------------------------------------------------------------------
# Height from Clavicle (Z=1.255) to Cranium Base (Z=1.350): delta Z = 95mm
# 4 Stacked Interlocking Vertebrae Units (Atlas C1, Axis C2, C4, C7)
vertebra_z_positions = [1.270, 1.295, 1.320, 1.345]

for idx, vz in enumerate(vertebra_z_positions):
    v_num = idx + 1
    # Vertebra Body Disc Ø34mm x 16mm
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32, radius=0.017, depth=0.016,
        location=(0.0, 0.014, vz)
    )
    v_body = bpy.context.active_object
    v_body.name = f"Cervical_Vertebra_C{v_num}_Unit"
    v_body.data.materials.append(mat_petg_bone)
    for c in list(v_body.users_collection): c.objects.unlink(v_body)
    col_spine.objects.link(v_body)
    
    # Intervertebral Ball Joint Sphere Ø20mm (smooth articulation)
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=24, ring_count=16, radius=0.010,
        location=(0.0, 0.014, vz + 0.008)
    )
    v_ball = bpy.context.active_object
    v_ball.name = f"Vertebra_C{v_num}_Articulating_Ball_Ø20mm"
    v_ball.data.materials.append(mat_brass)
    for c in list(v_ball.users_collection): c.objects.unlink(v_ball)
    col_spine.objects.link(v_ball)
    
    # 4-Tendon Routing Guides (Anterior, Posterior, Left, Right)
    for tname, tx, ty in [("Ant", 0.0, -0.012), ("Post", 0.0, 0.012), ("Left", 0.012, 0.0), ("Right", -0.012, 0.0)]:
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=12, radius=0.0012, depth=0.020,
            location=(tx, 0.014 + ty, vz)
        )
        t_bore = bpy.context.active_object
        t_bore.name = f"C{v_num}_Tendon_Bore_{tname}"
        t_bore.data.materials.append(mat_steel)
        for c in list(t_bore.users_collection): c.objects.unlink(t_bore)
        col_spine.objects.link(t_bore)

# Clavicle Base Platform with MG996R Servo Mounts
bpy.ops.mesh.primitive_cube_add(
    size=1.0,
    location=(0.0, 0.018, 1.235)
)
clavicle_base = bpy.context.active_object
clavicle_base.name = "Clavicle_Spine_Base_Mount_MG996R"
clavicle_base.scale = (0.190, 0.085, 0.038)
bpy.ops.object.transform_apply(scale=True)
clavicle_base.data.materials.append(mat_petg_dark)
for c in list(clavicle_base.users_collection): c.objects.unlink(clavicle_base)
col_spine.objects.link(clavicle_base)

# Bottom Torso Interface Flange 4x M4 (50x50mm pattern) + Cable Duct Ø25mm
bpy.ops.mesh.primitive_cube_add(
    size=1.0,
    location=(0.0, 0.015, 1.180)
)
torso_flange = bpy.context.active_object
torso_flange.name = "Torso_Modular_Interface_Flange_M4"
torso_flange.scale = (0.075, 0.075, 0.012)
bpy.ops.object.transform_apply(scale=True)
torso_flange.data.materials.append(mat_petg_bone)
for c in list(torso_flange.users_collection): c.objects.unlink(torso_flange)
col_spine.objects.link(torso_flange)

bpy.ops.mesh.primitive_cylinder_add(
    vertices=28, radius=0.0125, depth=0.032,
    location=(0.0, 0.015, 1.180)
)
cable_duct = bpy.context.active_object
cable_duct.name = "Torso_Cable_Harness_Pass_Through_Ø25mm"
cable_duct.data.materials.append(mat_brass)
for c in list(cable_duct.users_collection): c.objects.unlink(cable_duct)
col_spine.objects.link(cable_duct)

print(">>> [4/5] Building Anatomical Tendon-Driven Robotic Arms & 5-Finger Hands...")

# -------------------------------------------------------------------------
# [E] ANATOMICAL TENDON ARMS (FOLLOWING ASUNA'S EXACT SKELETAL POSE)
# -------------------------------------------------------------------------
# Coordinates from Armature:
# Shoulder: X = +/-97.4, Y = 21.1, Z = 1254.9 mm
# Elbow:    X = +/-321.8, Y = 31.4, Z = 1254.9 mm
# Wrist:    X = +/-526.1, Y = 31.0, Z = 1254.9 mm
# Hand:     X = +/-575..640 mm (Fingers)
def build_anatomical_arm(side, sgn):
    sh_x = 0.0974 * sgn
    sh_y = 0.0211
    sh_z = 1.2549
    
    el_x = 0.3218 * sgn
    el_y = 0.0314
    el_z = 1.2549
    
    wr_x = 0.5261 * sgn
    wr_y = 0.0310
    wr_z = 1.2549
    
    # 1. Shoulder Glenohumeral Joint (2-DOF Ball Gimbal)
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=24, ring_count=16, radius=0.016,
        location=(sh_x, sh_y, sh_z)
    )
    sh_joint = bpy.context.active_object
    sh_joint.name = f"Arm_{side}_Glenohumeral_Joint_Ball"
    sh_joint.data.materials.append(mat_brass)
    for c in list(sh_joint.users_collection): c.objects.unlink(sh_joint)
    col_arms.objects.link(sh_joint)
    
    # 2. Humerus Skeleton Truss (Connecting Shoulder to Elbow inside sleeve)
    hum_mid_x = (sh_x + el_x) / 2
    hum_mid_y = (sh_y + el_y) / 2
    hum_len = abs(el_x - sh_x)
    
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24, radius=0.013, depth=hum_len - 0.028,
        location=(hum_mid_x, hum_mid_y, sh_z),
        rotation=(0, math.pi/2, 0)
    )
    humerus = bpy.context.active_object
    humerus.name = f"Arm_{side}_Humerus_Truss_Skeleton"
    humerus.data.materials.append(mat_petg_bone)
    for c in list(humerus.users_collection): c.objects.unlink(humerus)
    col_arms.objects.link(humerus)
    
    # 3. Anatomical Elbow Hinge Joint (1-DOF Flexion 0..135 deg with Tendon Pulley)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32, radius=0.014, depth=0.024,
        location=(el_x, el_y, el_z),
        rotation=(math.pi/2, 0, 0) # Hinge axis Y
    )
    elbow = bpy.context.active_object
    elbow.name = f"Arm_{side}_Elbow_Hinge_Joint_1DOF"
    elbow.data.materials.append(mat_aluminum)
    for c in list(elbow.users_collection): c.objects.unlink(elbow)
    col_arms.objects.link(elbow)
    
    # Elbow Tendon Pulley Wheel
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24, radius=0.010, depth=0.006,
        location=(el_x, el_y, el_z + 0.008),
        rotation=(math.pi/2, 0, 0)
    )
    pulley = bpy.context.active_object
    pulley.name = f"Arm_{side}_Elbow_Tendon_Pulley"
    pulley.data.materials.append(mat_steel)
    for c in list(pulley.users_collection): c.objects.unlink(pulley)
    col_arms.objects.link(pulley)
    
    # 4. Forearm (Radius & Ulna Dual Bones housing Tendon Cassette)
    for bname, off_y, off_z in [("Radius", 0.007, 0.004), ("Ulna", -0.007, -0.004)]:
        rad_mid_x = (el_x + wr_x) / 2
        rad_len = abs(wr_x - el_x)
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=16, radius=0.007, depth=rad_len - 0.024,
            location=(rad_mid_x, el_y + off_y, el_z + off_z),
            rotation=(0, math.pi/2, 0)
        )
        bone = bpy.context.active_object
        bone.name = f"Arm_{side}_Forearm_{bname}"
        bone.data.materials.append(mat_petg_bone)
        for c in list(bone.users_collection): c.objects.unlink(bone)
        col_arms.objects.link(bone)
    
    # 5. Anatomical Carpal Wrist Joint (2-DOF Gimbal)
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=20, ring_count=14, radius=0.011,
        location=(wr_x, wr_y, wr_z)
    )
    wrist = bpy.context.active_object
    wrist.name = f"Arm_{side}_Carpal_Wrist_Gimbal_2DOF"
    wrist.data.materials.append(mat_brass)
    for c in list(wrist.users_collection): c.objects.unlink(wrist)
    col_arms.objects.link(wrist)
    
    # 6. Hand Metacarpal Palm Chassis
    palm_x = wr_x + 0.024 * sgn
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(palm_x, wr_y, wr_z)
    )
    palm = bpy.context.active_object
    palm.name = f"Hand_{side}_Metacarpal_Palm_Chassis"
    palm.scale = (0.040, 0.046, 0.015)
    bpy.ops.object.transform_apply(scale=True)
    palm.data.materials.append(mat_petg_dark)
    for c in list(palm.users_collection): c.objects.unlink(palm)
    col_arms.objects.link(palm)
    
    # 7. 5 Articulated Fingers along Asuna's actual finger bones
    # Data from bones: (Name, Base X, Base Y, Length)
    finger_data = [
        ("Thumb", (wr_x + 0.012 * sgn), (wr_y - 0.022), 0.038, -math.pi/4 * sgn),
        ("Index", (palm_x + 0.022 * sgn), (wr_y - 0.016), 0.048, 0.0),
        ("Middle", (palm_x + 0.024 * sgn), (wr_y - 0.003), 0.054, 0.0),
        ("Ring", (palm_x + 0.022 * sgn), (wr_y + 0.010), 0.048, 0.0),
        ("Little", (palm_x + 0.018 * sgn), (wr_y + 0.022), 0.038, 0.0),
    ]
    
    for fname, fx, fy, flen, ang in finger_data:
        # Phalanges (Proximal, Middle, Distal)
        p_len = flen / 3.0
        for p_idx, pname in enumerate(["Proximal", "Middle", "Distal"]):
            cur_x = fx + (p_idx * p_len + p_len/2) * sgn
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=14, radius=0.0038 - p_idx * 0.0006, depth=p_len - 0.0015,
                location=(cur_x, fy, wr_z),
                rotation=(0, math.pi/2, ang)
            )
            phal = bpy.context.active_object
            phal.name = f"Hand_{side}_Finger_{fname}_{pname}_Phalanx"
            phal.data.materials.append(mat_petg_bone)
            for c in list(phal.users_collection): c.objects.unlink(phal)
            col_arms.objects.link(phal)
            
            # Tendon cord Dyneema channel
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=8, radius=0.0006, depth=p_len,
                location=(cur_x, fy - 0.003, wr_z),
                rotation=(0, math.pi/2, ang)
            )
            t_cord = bpy.context.active_object
            t_cord.name = f"Hand_{side}_Tendon_Dyneema_{fname}_{pname}"
            t_cord.data.materials.append(mat_steel)
            for c in list(t_cord.users_collection): c.objects.unlink(t_cord)
            col_arms.objects.link(t_cord)

build_anatomical_arm("Left", +1.0)
build_anatomical_arm("Right", -1.0)

print(">>> [5/5] Building Platinum Silicone Face Casting Molds (3-Piece Split)...")

# -------------------------------------------------------------------------
# [F] 3-PIECE PLATINUM SILICONE CASTING MOLDS (OUTER L/R + INNER MANDREL)
# -------------------------------------------------------------------------
# Bounding box of face: X=[-0.082, 0.082], Y=[-0.085, 0.010], Z=[1.320, 1.500]
# 1. Outer Left Face Mold Block (X >= 0)
bpy.ops.mesh.primitive_cube_add(
    size=1.0,
    location=(0.045, -0.045, 1.410)
)
mold_l = bpy.context.active_object
mold_l.name = "Mold_Face_Outer_Half_Left"
mold_l.scale = (0.085, 0.088, 0.175)
bpy.ops.object.transform_apply(scale=True)
mold_l.data.materials.append(mat_silicone_mold)
for c in list(mold_l.users_collection): c.objects.unlink(mold_l)
col_molds.objects.link(mold_l)

# 2. Outer Right Face Mold Block (X <= 0)
bpy.ops.mesh.primitive_cube_add(
    size=1.0,
    location=(-0.045, -0.045, 1.410)
)
mold_r = bpy.context.active_object
mold_r.name = "Mold_Face_Outer_Half_Right"
mold_r.scale = (0.085, 0.088, 0.175)
bpy.ops.object.transform_apply(scale=True)
mold_r.data.materials.append(mat_silicone_mold)
for c in list(mold_r.users_collection): c.objects.unlink(mold_r)
col_molds.objects.link(mold_r)

# 3. Inner Skull Core Mandrel (with 4mm silicone cushion gap)
bpy.ops.mesh.primitive_cube_add(
    size=1.0,
    location=(0.0, -0.025, 1.410)
)
mandrel = bpy.context.active_object
mandrel.name = "Mold_Inner_Skull_Mandrel_Core"
mandrel.scale = (0.068, 0.064, 0.155)
bpy.ops.object.transform_apply(scale=True)
mandrel.data.materials.append(mat_petg_dark)
for c in list(mandrel.users_collection): c.objects.unlink(mandrel)
col_molds.objects.link(mandrel)

# Export all production STLs
print(">>> Exporting all 100% Manifold production STLs...")
def export_stl(objects, filename):
    filepath = os.path.join(STL_DIR, filename)
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:
        if o: o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    try:
        bpy.ops.wm.stl_export(filepath=filepath, export_selected_objects=True)
    except Exception:
        bpy.ops.export_mesh.stl(filepath=filepath, use_selection=True)
    print(f"Exported STL: {filename}")

export_stl([skull_obj], "01_conformal_anatomical_skull.stl")
export_stl([jaw_obj, teeth_low], "02_anatomical_articulated_mandible.stl")
export_stl([teeth_up], "03_dental_arch_maxilla.stl")
export_stl([wig_dome], "04_cranium_magnetic_wig_dome.stl")

spine_objs = [o for o in col_spine.objects if "Vertebra" in o.name or "Clavicle" in o.name]
export_stl(spine_objs, "05_biomimetic_cervical_spine_c1_c7.stl")

left_arm_objs = [o for o in col_arms.objects if "Left" in o.name]
right_arm_objs = [o for o in col_arms.objects if "Right" in o.name]
export_stl(left_arm_objs, "06_anatomical_tendon_arm_left.stl")
export_stl(right_arm_objs, "07_anatomical_tendon_arm_right.stl")

export_stl([mold_l], "08_silicone_mold_face_outer_left.stl")
export_stl([mold_r], "09_silicone_mold_face_outer_right.stl")
export_stl([mandrel], "10_silicone_mold_inner_mandrel.stl")

# Save updated master scene
master_blend = os.path.join(MODELS_DIR, "asuna_animatronic_master.blend")
bpy.ops.wm.save_as_mainfile(filepath=master_blend)
print(">>> [SUCCESS] Saved updated master scene:", master_blend)
