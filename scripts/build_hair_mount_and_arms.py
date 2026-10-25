"""
Asuna Animatronic Project - Phase 2:
1. Cranium Magnetic Wig Mount Dome (Hair retention rim & 4x magnet bays).
2. Modular Tendon-Driven Robotic Arms & Hands (Dyneema cord actuated fingers, wrist, elbow, MG996R shoulder).
3. Export STL models for 3D printing.
"""
import bpy
import bmesh
import math
import os
from mathutils import Vector, Euler

PROJECT_ROOT = "/home/alexius/Projects/Asuna Robotic head"
MASTER_BLEND = os.path.join(PROJECT_ROOT, "models/asuna_animatronic_head_bust.blend")
STL_DIR = os.path.join(PROJECT_ROOT, "models/stl")

print(">>> [Phase 2] Loading master blend:", MASTER_BLEND)
bpy.ops.wm.open_mainfile(filepath=MASTER_BLEND)

scene = bpy.context.scene

def get_col(name):
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        scene.collection.children.link(col)
    return col

col_hair_mount = get_col("08_Cranium_Wig_Mount")
col_arms = get_col("09_Tendon_Robotic_Arms")

# Materials
mat_petg_black = bpy.data.materials.get("PETG_Structural_Black")
mat_petg_orange = bpy.data.materials.get("PETG_Engineering_Orange")
mat_aluminum = bpy.data.materials.get("Anodized_Aluminum_CNC")
mat_steel = bpy.data.materials.get("Hardened_Steel_Shaft")
mat_brass = bpy.data.materials.get("Brass_Hardware")

# =========================================================================
# 1. CRANIUM MAGNETIC WIG MOUNT DOME (CHOPPING & SECURING HAIR)
# =========================================================================
# Head bounds: X=[-80, 80], Y=[-80, 66], Z=[1324, 1514] mm
# Skull cap dome at Z=1.42 to 1.514m
bpy.ops.mesh.primitive_uv_sphere_add(
    segments=36, ring_count=24, radius=0.078,
    location=(0.0, 0.005, 1.445)
)
wig_dome = bpy.context.active_object
wig_dome.name = "Cranium_Magnetic_Wig_Mount_Dome"
wig_dome.scale = (1.02, 1.05, 0.95)
bpy.ops.object.transform_apply(scale=True)

# Cut lower half below Z=1.425
bm = bmesh.new()
bm.from_mesh(wig_dome.data)
del_verts = [v for v in bm.verts if v.co.z < 1.425]
bmesh.ops.delete(bm, geom=del_verts, context='VERTS')
bm.to_mesh(wig_dome.data)
bm.free()

# Solidify modifier for 3mm wall
mod_sol = wig_dome.modifiers.new("Solidify", 'SOLIDIFY')
mod_sol.thickness = 0.003
wig_dome.data.materials.append(mat_petg_orange)
for c in list(wig_dome.users_collection): c.objects.unlink(wig_dome)
col_hair_mount.objects.link(wig_dome)

# 4x Neodymium Magnet Pockets (Ø8.2 x 2.6mm)
# Front-Vertex, Rear-Crown, Left-Temporal, Right-Temporal
magnet_coords = [
    ("Vertex_Front", (0.0, -0.045, 1.505)),
    ("Crown_Rear", (0.0, 0.048, 1.495)),
    ("Temporal_Left", (0.068, 0.008, 1.465)),
    ("Temporal_Right", (-0.068, 0.008, 1.465)),
]

for mname, mpos in magnet_coords:
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24, radius=0.0042, depth=0.0028,
        location=mpos
    )
    mag = bpy.context.active_object
    mag.name = f"Wig_Retention_Neodymium_Magnet_{mname}"
    mag.data.materials.append(mat_steel)
    for c in list(mag.users_collection): c.objects.unlink(mag)
    col_hair_mount.objects.link(mag)

# Circumferential Wig Retention Groove (Линия фиксации парика)
bpy.ops.mesh.primitive_torus_add(
    major_radius=0.076, minor_radius=0.0025,
    location=(0.0, 0.005, 1.432),
    rotation=(math.radians(8.0), 0, 0)
)
wig_rim = bpy.context.active_object
wig_rim.name = "Wig_Elastic_Retention_Rim_Groove"
wig_rim.scale = (1.02, 1.08, 1.0)
bpy.ops.object.transform_apply(scale=True)
wig_rim.data.materials.append(mat_petg_black)
for c in list(wig_rim.users_collection): c.objects.unlink(wig_rim)
col_hair_mount.objects.link(wig_rim)

# =========================================================================
# 2. MODULAR TENDON-DRIVEN ROBOTIC ARMS & HANDS
# =========================================================================
# Mating directly into shoulder sockets at X = +/-0.098m, Y = +0.021m, Z = 1.255m
def build_tendon_arm(side, sx):
    sgn = 1.0 if sx > 0 else -1.0
    
    # 2.1 Shoulder Quick-Mount Plug Ø20mm x 15mm
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32, radius=0.0098, depth=0.015,
        location=(sx, 0.021, 1.255),
        rotation=(0, math.pi/2, 0)
    )
    plug = bpy.context.active_object
    plug.name = f"Arm_{side}_Quick_Mount_Plug_Ø20mm"
    plug.data.materials.append(mat_aluminum)
    for c in list(plug.users_collection): c.objects.unlink(plug)
    col_arms.objects.link(plug)
    
    # 2.2 Shoulder Actuator Box (Houses MG996R Pitch/Roll)
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(sx + 0.022 * sgn, 0.021, 1.240)
    )
    sh_box = bpy.context.active_object
    sh_box.name = f"Arm_{side}_Shoulder_PitchRoll_Gimbal"
    sh_box.scale = (0.038, 0.052, 0.058)
    bpy.ops.object.transform_apply(scale=True)
    sh_box.data.materials.append(mat_petg_black)
    for c in list(sh_box.users_collection): c.objects.unlink(sh_box)
    col_arms.objects.link(sh_box)
    
    # 2.3 Upper Arm Bone (Humerus Truss, length ~240mm)
    elbow_z = 1.020
    elbow_x = sx + 0.035 * sgn
    elbow_y = 0.021
    
    humerus_mid_z = (1.240 + elbow_z) / 2
    humerus_mid_x = (sx + 0.022 * sgn + elbow_x) / 2
    
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24, radius=0.014, depth=0.210,
        location=(humerus_mid_x, elbow_y, humerus_mid_z)
    )
    humerus = bpy.context.active_object
    humerus.name = f"Arm_{side}_Humerus_Tendon_Truss"
    humerus.data.materials.append(mat_petg_orange)
    for c in list(humerus.users_collection): c.objects.unlink(humerus)
    col_arms.objects.link(humerus)
    
    # 2.4 Elbow Hinge Joint (1-DOF Flexion 0..135 deg)
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24, radius=0.012, depth=0.028,
        location=(elbow_x, elbow_y, elbow_z),
        rotation=(0, math.pi/2, 0)
    )
    elbow = bpy.context.active_object
    elbow.name = f"Arm_{side}_Elbow_Hinge_Joint_1DOF"
    elbow.data.materials.append(mat_aluminum)
    for c in list(elbow.users_collection): c.objects.unlink(elbow)
    col_arms.objects.link(elbow)
    
    # 2.5 Forearm (Radius/Ulna Tendon Actuator Cassette, length ~200mm)
    wrist_z = 0.835
    wrist_x = elbow_x + 0.010 * sgn
    wrist_y = elbow_y - 0.015 # slight forward natural angle
    
    forearm_mid_z = (elbow_z + wrist_z) / 2
    forearm_mid_x = (elbow_x + wrist_x) / 2
    forearm_mid_y = (elbow_y + wrist_y) / 2
    
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(forearm_mid_x, forearm_mid_y, forearm_mid_z)
    )
    forearm = bpy.context.active_object
    forearm.name = f"Arm_{side}_Forearm_Tendon_Cassette"
    forearm.scale = (0.028, 0.034, 0.170)
    bpy.ops.object.transform_apply(scale=True)
    forearm.data.materials.append(mat_petg_black)
    for c in list(forearm.users_collection): c.objects.unlink(forearm)
    col_arms.objects.link(forearm)
    
    # 2.6 Wrist Joint (2-DOF Gimbal: Flexion/Extension + Deviation)
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=20, ring_count=14, radius=0.011,
        location=(wrist_x, wrist_y, wrist_z)
    )
    wrist = bpy.context.active_object
    wrist.name = f"Arm_{side}_Wrist_Gimbal_2DOF"
    wrist.data.materials.append(mat_brass)
    for c in list(wrist.users_collection): c.objects.unlink(wrist)
    col_arms.objects.link(wrist)
    
    # 2.7 Animatronic Hand Palm (Dyneema Cord Pulley Manifold)
    hand_z = wrist_z - 0.038
    bpy.ops.mesh.primitive_cube_add(
        size=1.0,
        location=(wrist_x, wrist_y, hand_z)
    )
    palm = bpy.context.active_object
    palm.name = f"Hand_{side}_Tendon_Palm_Manifold"
    palm.scale = (0.016, 0.042, 0.052)
    bpy.ops.object.transform_apply(scale=True)
    palm.data.materials.append(mat_petg_orange)
    for c in list(palm.users_collection): c.objects.unlink(palm)
    col_arms.objects.link(palm)
    
    # 2.8 5 Articulated Fingers (Thumb, Index, Middle, Ring, Pinky)
    finger_configs = [
        ("Thumb", (0.012 * sgn, -0.018, hand_z + 0.010), 0.036),
        ("Index", (0.000, -0.014, hand_z - 0.032), 0.048),
        ("Middle", (0.000, -0.004, hand_z - 0.036), 0.054),
        ("Ring", (0.000, +0.006, hand_z - 0.032), 0.048),
        ("Pinky", (0.000, +0.015, hand_z - 0.026), 0.038),
    ]
    
    for fname, offset, flen in finger_configs:
        fx = wrist_x + offset[0]
        fy = wrist_y + offset[1]
        fz = offset[2]
        
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=16, radius=0.004, depth=flen,
            location=(fx, fy, fz)
        )
        fin = bpy.context.active_object
        fin.name = f"Hand_{side}_Finger_{fname}_Tendon_Phalanges"
        fin.data.materials.append(mat_aluminum)
        for c in list(fin.users_collection): c.objects.unlink(fin)
        col_arms.objects.link(fin)
        
        # Dyneema flexor tendon cord guide (Ø0.8mm channel indicator)
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=8, radius=0.0008, depth=flen + 0.015,
            location=(fx - 0.0035, fy, fz + 0.005)
        )
        cord = bpy.context.active_object
        cord.name = f"Hand_{side}_Tendon_Cord_Dyneema_{fname}"
        cord.data.materials.append(mat_steel)
        for c in list(cord.users_collection): c.objects.unlink(cord)
        col_arms.objects.link(cord)

build_tendon_arm("Left", +0.098)
build_tendon_arm("Right", -0.098)

print(">>> [Phase 2] Exporting New Modular STLs...")
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

export_stl([wig_dome, wig_rim], "07_cranium_magnetic_wig_mount_dome.stl")

left_arm_objs = [o for o in col_arms.objects if "Left" in o.name]
right_arm_objs = [o for o in col_arms.objects if "Right" in o.name]
export_stl(left_arm_objs, "08_tendon_robotic_arm_left.stl")
export_stl(right_arm_objs, "09_tendon_robotic_arm_right.stl")

# Save updated blend file
bpy.ops.wm.save_as_mainfile(filepath=MASTER_BLEND)
print(">>> [Phase 2 Complete] Master blend and STLs updated!")
