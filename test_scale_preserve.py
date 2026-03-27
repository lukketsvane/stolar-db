import trimesh
import os

test_file = 'STOLAR/glb/O1779763.glb'
out_file = 'STOLAR/glb/test_scale_preserve.glb'

try:
    # Load scene instead of mesh to preserve textures/hierarchy
    scene = trimesh.load(test_file)
    print(f"Loaded {test_file} as {type(scene)}")
    
    # Scale the scene
    # For a scene, we might need to iterate over geometry or use scene-level scaling
    # Let's see if scene has bounds
    height = scene.bounds[1][1] - scene.bounds[0][1]
    print(f"Current height: {height:.4f}")
    
    # Apply scale to the whole scene
    scale_factor = 1.1 # scale up 10% for testing
    scene.apply_scale(scale_factor)
    
    # Export back
    scene.export(out_file)
    print(f"Exported to {out_file}")
    
    # Check size of new file
    orig_size = os.path.getsize(test_file)
    new_size = os.path.getsize(out_file)
    print(f"Original size: {orig_size} bytes")
    print(f"New size: {new_size} bytes")
    
    if abs(new_size - orig_size) < 1000:
        print("Size is similar, textures likely preserved.")
    else:
        print(f"Size difference: {new_size - orig_size} bytes. WARNING: textures might be lost if it's much smaller.")

except Exception as e:
    print(f"Error: {e}")
