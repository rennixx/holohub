"""
Test script to display a GLB model directly.

This bypasses the backend and loads a local GLB file to test rendering.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import trimesh
    import pyglet
    from OpenGL.GL import (
        GL_DEPTH_TEST, GL_PROJECTION, GL_MODELVIEW,
        GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_TRIANGLES,
        glEnable, glClearColor, glMatrixMode, glLoadIdentity, glRotatef,
        glBegin, glEnd, glNormal3f, glColor3f, glVertex3f, glClear, glFlush,
    )
    from OpenGL.GLU import gluPerspective, gluLookAt
    import numpy as np
    import time

    # Load the test model
    test_file = Path(__file__).parent / "test_box.glb"
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        print("Downloading test file...")
        import urllib.request
        urllib.request.urlretrieve(
            'https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/master/2.0/Box/glTF-Binary/Box.glb',
            str(test_file)
        )
        print(f"Downloaded: {test_file}")

    print(f"Loading model: {test_file}")
    scene = trimesh.load(str(test_file), force_load_meshes=True)

    print(f"Scene geometries: {len(scene.geometry)}")
    for name, geom in scene.geometry.items():
        print(f"  - {name}: {len(geom.vertices)} vertices, {len(geom.faces)} faces")

    # Center the scene
    bounds = scene.bounds
    if bounds is not None and bounds.shape == (2, 3):
        centroid = (bounds[0] + bounds[1]) / 2
        translation = -centroid
        for geom in scene.geometry.values():
            geom.apply_translation(translation)

    # Create window
    from pyglet.gl import Config
    config = Config(
        double_buffer=True,
        depth_size=24,
        major_version=2,
        minor_version=1,
        forward_compatible=False,
    )

    window = pyglet.window.Window(
        width=800,
        height=800,
        caption="GLB Test Display",
        resizable=False,
        config=config,
    )

    # Setup OpenGL
    glEnable(GL_DEPTH_TEST)
    glClearColor(0.2, 0.2, 0.3, 1.0)  # Blue-ish background

    rotation = 0.0

    def render_scene():
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Set up camera
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (window.width / window.height), 0.1, 100.0)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0, 0, 3, 0, 0, 0, 0, 1, 0)

        # Apply rotation
        glRotatef(rotation, 0, 1, 0)
        glRotatef(20, 1, 0, 0)

        # Render each geometry
        for geom in scene.geometry.values():
            vertices = geom.vertices
            faces = geom.faces

            # Get colors or use default
            if hasattr(geom, 'visual') and hasattr(geom.visual, 'face_colors'):
                colors = geom.visual.face_colors
            else:
                colors = np.ones((len(faces), 3), dtype=np.float32) * [1.0, 0.5, 0.0]  # Orange

            # Draw faces
            for i, face in enumerate(faces):
                v0, v1, v2 = vertices[face[0]], vertices[face[1]], vertices[face[2]]

                if i < len(colors):
                    c = colors[i]
                    glColor3f(c[0], c[1], c[2])
                else:
                    glColor3f(1.0, 0.5, 0.0)

                glBegin(GL_TRIANGLES)
                glNormal3f(0, 0, 1)
                glVertex3f(v0[0], v0[1], v0[2])
                glVertex3f(v1[0], v1[1], v1[2])
                glVertex3f(v2[0], v2[1], v2[2])
                glEnd()

        glFlush()

    window.on_draw = render_scene

    print("Window created. Press ESC to exit.")

    # Use a list to allow mutation in event handlers
    running = [True]

    @window.event
    def on_key_press(symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            running[0] = False

    @window.event
    def on_close():
        running[0] = False

    # Main loop
    while running[0]:
        pyglet.clock.tick()
        rotation += 0.5
        window.switch_to()
        window.dispatch_events()
        render_scene()
        window.flip()
        time.sleep(0.016)

    print("Test complete.")

except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install trimesh pyglet PyOpenGL PyOpenGL_accelerate numpy")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
