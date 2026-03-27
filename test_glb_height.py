import trimesh
import os

glb_dir = 'STOLAR/glb'
files = [f for f in os.listdir(glb_dir) if f.endswith('.glb')][:5]

for f in files:
    path = os.path.join(glb_dir, f)
    try:
        mesh = trimesh.load(path, force='mesh')
        # Height is the difference between max and min Y (standard for GLB export)
        # or Z depending on how it was exported. Trimesh bounds is [min, max]
        height = mesh.bounds[1][1] - mesh.bounds[0][1]
        print(f"{f}: Height = {height:.4f} units")
    except Exception as e:
        print(f"{f}: Error loading: {e}")
