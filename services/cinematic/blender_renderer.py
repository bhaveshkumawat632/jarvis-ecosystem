import os
import sys
import argparse

# Blender Python API imports (only work inside Blender's python runtime)
try:
    import bpy
    import math
except ImportError:
    # Allow script to be viewed/loaded outside Blender without throwing immediate crash
    pass

def setup_scene(mesh_path, output_path, duration_seconds, fps=24):
    """Orchestrates headless Blender loading, lighting, camera animation, and rendering."""
    # 1. Clear existing objects in default scene
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    
    # 2. Import generated 3D mesh (supports GLTF/GLB or OBJ)
    ext = os.path.splitext(mesh_path)[1].lower()
    if ext in ['.gltf', '.glb']:
        bpy.ops.import_scene.gltf(filepath=mesh_path)
    elif ext == '.obj':
        bpy.ops.import_scene.obj(filepath=mesh_path)
    else:
        raise ValueError(f"Unsupported 3D format: {ext}")
        
    # Ensure imported objects are centered and scaled
    imported_objs = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not imported_objs:
        raise RuntimeError("No imported meshes found in the file.")
        
    # Center the object
    bpy.ops.object.select_all(action='DESELECT')
    for obj in imported_objs:
        obj.select_set(True)
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    
    # 3. Create a Cinematic Three-Point Lighting System
    # Key Light (Strong front-side illumination)
    key_light_data = bpy.data.lights.new(name="Key_Light", type='SUN')
    key_light_data.energy = 5.0
    key_light_obj = bpy.data.objects.new(name="Key_Light", object_data=key_light_data)
    bpy.context.collection.objects.link(key_light_obj)
    key_light_obj.location = (5.0, -5.0, 6.0)
    key_light_obj.rotation_euler = (math.radians(35), math.radians(0), math.radians(45))
    
    # Fill Light (Softer fill to reduce harsh shadows)
    fill_light_data = bpy.data.lights.new(name="Fill_Light", type='POINT')
    fill_light_data.energy = 1500.0
    fill_light_obj = bpy.data.objects.new(name="Fill_Light", object_data=fill_light_data)
    bpy.context.collection.objects.link(fill_light_obj)
    fill_light_obj.location = (-6.0, -4.0, 3.0)
    
    # Rim/Back Light (Separates the asset from background)
    rim_light_data = bpy.data.lights.new(name="Rim_Light", type='SPOT')
    rim_light_data.energy = 3000.0
    rim_light_obj = bpy.data.objects.new(name="Rim_Light", object_data=rim_light_data)
    bpy.context.collection.objects.link(rim_light_obj)
    rim_light_obj.location = (0.0, 6.0, 5.0)
    rim_light_obj.rotation_euler = (math.radians(-45), math.radians(0), math.radians(180))
    
    # 4. Create and Animate Camera
    # Create target empty object for camera tracking
    target = bpy.data.objects.new("Tracker", None)
    bpy.context.collection.objects.link(target)
    target.location = (0.0, 0.0, 0.0)
    
    # Add camera
    cam_data = bpy.data.cameras.new("Cinematic_Camera")
    cam_obj = bpy.data.objects.new("Cinematic_Camera", cam_data)
    bpy.context.collection.objects.link(cam_obj)
    cam_obj.location = (0.0, -8.0, 2.0)
    
    # Track-To Constraint to keep camera locked on the asset
    track_constraint = cam_obj.constraints.new(type='TRACK_TO')
    track_constraint.target = target
    track_constraint.track_axis = 'TRACK_NEGATIVE_Z'
    track_constraint.up_axis = 'UP_Y'
    
    # Animate Camera Orbit
    bpy.context.scene.frame_start = 1
    total_frames = int(duration_seconds * fps)
    bpy.context.scene.frame_end = total_frames
    
    # Add keyframe parent rotations
    cam_parent = bpy.data.objects.new("Camera_Rig", None)
    bpy.context.collection.objects.link(cam_parent)
    cam_parent.location = (0.0, 0.0, 0.0)
    cam_obj.parent = cam_parent
    
    # Rotate parent Empty to orbit the camera around center
    cam_parent.rotation_euler[2] = 0.0
    cam_parent.keyframe_insert(data_path="rotation_euler", index=2, frame=1)
    
    # Standard 45 degree cinematic orbit pan
    cam_parent.rotation_euler[2] = math.radians(45)
    cam_parent.keyframe_insert(data_path="rotation_euler", index=2, frame=total_frames)
    
    # Set keyframe interpolation to linear for smooth constant speed orbit
    for fcurve in cam_parent.animation_data.action.fcurves:
        for kp in fcurve.keyframe_points:
            kp.interpolation = 'LINEAR'
            
    # 5. Render settings configuration
    bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
    bpy.context.scene.render.ffmpeg.format = 'MPEG4'
    bpy.context.scene.render.ffmpeg.codec = 'H264'
    bpy.context.scene.render.ffmpeg.constant_rate_factor = 'HIGH'
    bpy.context.scene.render.ffmpeg.audio_codec = 'NONE' # Audio mixed separately
    
    bpy.context.scene.render.resolution_x = 1024
    bpy.context.scene.render.resolution_y = 576
    bpy.context.scene.render.fps = fps
    
    # Set output filepath
    bpy.context.scene.render.filepath = output_path
    
    # Render animation headlessly
    print(f"Blender starting render: {total_frames} frames to {output_path}")
    bpy.ops.render.render(animation=True)
    print("Blender render completed successfully.")

if __name__ == "__main__":
    # Check if run inside Blender
    if "bpy" in sys.modules:
        # Extract arguments after "--"
        args = []
        if "--" in sys.argv:
            args = sys.argv[sys.argv.index("--") + 1:]
            
        parser = argparse.ArgumentParser(description="Blender Headless Renderer")
        parser.add_argument("--mesh", required=True, help="Path to imported 3D mesh")
        parser.add_argument("--output", required=True, help="Render destination path")
        parser.add_argument("--duration", type=float, default=6.0, help="Movie segment duration")
        
        parsed_args = parser.parse_args(args)
        setup_scene(parsed_args.mesh, parsed_args.output, parsed_args.duration)
