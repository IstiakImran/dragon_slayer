from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random
import time
import sys  # Import sys for glutInit

# --- Global State Variables ---
# We use global variables here as is common in simple GLUT scripts.

# Camera and Mouse Controls
camera_rot_x = -20
camera_rot_y = 0
camera_zoom = -40
last_mouse_pos = {'x': 0, 'y': 0}
mouse_dragging = False

# Animation and Firing State
wing_angle = 0
body_bob = 0      # NEW: For vertical body hover
head_turn = 0     # NEW: For head looking side-to-side
is_firing = False
fire_particles = []
last_time = 0

# --- Dragon Model Class ---
# This class has been modified to accept new animation parameters.


class Dragon:
    """
    Handles drawing the different parts of the dragon model.
    This version is significantly more detailed, using more primitives.
    """

    def draw_cube(self, scale=(1, 1, 1), position=(0, 0, 0)):
        """Utility function to draw a scaled and positioned cube."""
        glPushMatrix()
        glTranslatef(*position)
        glScalef(*scale)
        glutSolidCube(1)
        glPopMatrix()

    def draw_pyramid(self, scale=(1, 1, 1), position=(0, 0, 0)):
        """Draws a pyramid with a square base."""
        vertices = [[0.5, -0.5, 0.5], [-0.5, -0.5, 0.5],
                    [-0.5, -0.5, -0.5], [0.5, -0.5, -0.5], [0, 0.5, 0]]
        indices = [[0, 1, 2], [0, 2, 3], [0, 4, 1],
                   [1, 4, 2], [2, 4, 3], [3, 4, 0]]

        glPushMatrix()
        glTranslatef(*position)
        glScalef(*scale)
        glBegin(GL_TRIANGLES)
        for face in indices:
            # A simple way to get normals for this specific pyramid shape
            v1 = [vertices[face[1]][i] - vertices[face[0]][i]
                  for i in range(3)]
            v2 = [vertices[face[2]][i] - vertices[face[0]][i]
                  for i in range(3)]
            normal = [v1[1]*v2[2] - v1[2]*v2[1], v1[2] *
                      v2[0] - v1[0]*v2[2], v1[0]*v2[1] - v1[1]*v2[0]]
            glNormal3fv(normal)
            for vertex in face:
                glVertex3fv(vertices[vertex])
        glEnd()
        glPopMatrix()

    def draw_sphere(self, radius=1, position=(0, 0, 0)):
        """Draws a sphere."""
        glPushMatrix()
        glTranslatef(*position)
        glutSolidSphere(radius, 20, 20)
        glPopMatrix()

    def draw_torso(self):
        """Draws the main body, chest, and spinal plates."""
        # Main Body
        glColor3f(0.1, 0.6, 0.2)  # Dark Green
        self.draw_cube(scale=(3.5, 3, 5.5), position=(0, 1.5, 0))
        # Chest
        glColor3f(0.2, 0.7, 0.3)  # Slightly Lighter Green
        self.draw_cube(scale=(4, 3.5, 2), position=(0, 1.5, 1.5))
        # Underbelly Plates
        glColor3f(0.9, 0.9, 0.2)  # Yellow
        for i in range(5):
            self.draw_cube(scale=(2.5, 0.4, 0.8),
                           position=(0, -0.2, 2.0 - i * 1.0))
        # Spinal Plates
        glColor3f(0.8, 0.1, 0.1)  # Red
        for i in range(5):
            self.draw_pyramid(scale=(0.8, 1.5, 0.3),
                              position=(0, 3.5, 2.0 - i * 1.2))

    def draw_head(self):
        """Draws a much more detailed head."""
        glPushMatrix()
        glTranslatef(0, 3.5, 3.0)  # Position the whole head assembly

        # Main Head Block
        glColor3f(0.1, 0.6, 0.2)  # Dark Green
        self.draw_cube(scale=(2, 1.8, 2.5), position=(0, 0, 0))

        # Snout
        self.draw_cube(scale=(1.5, 1.2, 2.5), position=(0, -0.2, 2.0))

        # Lower Jaw
        glColor3f(0.2, 0.7, 0.3)  # Lighter Green
        self.draw_cube(scale=(1.4, 0.5, 2.3), position=(0, -0.9, 2.0))

        # Teeth (small pyramids)
        glColor3f(1.0, 1.0, 0.9)  # Off-white
        for i in range(3):
            self.draw_pyramid(scale=(0.1, 0.2, 0.1),
                              position=(-0.5 + i*0.5, -0.55, 3.0))

        # Eyes
        glColor3f(1.0, 0.0, 0.0)  # Red Eyes
        self.draw_sphere(radius=0.2, position=(-0.6, 0.5, 0.8))
        self.draw_sphere(radius=0.2, position=(0.6, 0.5, 0.8))

        # Horns
        glColor3f(0.9, 0.9, 0.2)  # Yellow
        self.draw_pyramid(scale=(0.4, 2.0, 0.4), position=(-0.8, 0.8, -0.5))
        self.draw_pyramid(scale=(0.4, 2.0, 0.4), position=(0.8, 0.8, -0.5))
        self.draw_pyramid(scale=(0.3, 1.5, 0.3), position=(-0.5, 0.8, -1.2))
        self.draw_pyramid(scale=(0.3, 1.5, 0.3), position=(0.5, 0.8, -1.2))

        glPopMatrix()

    def draw_neck(self):
        """Draws a curved, segmented neck."""
        glColor3f(0.1, 0.6, 0.2)  # Dark Green
        glPushMatrix()
        glTranslatef(0, 2.5, 2.5)
        self.draw_cube(scale=(2, 2, 1))
        glRotatef(-15, 1, 0, 0)
        glTranslatef(0, 0.5, 0.8)
        self.draw_cube(scale=(1.8, 1.8, 1))
        glPopMatrix()

    def draw_legs(self):
        """Draws four jointed legs with claws."""
        # Front Legs
        self.draw_leg(position=(-2.2, 0, 1.5))
        self.draw_leg(position=(2.2, 0, 1.5))
        # Rear Legs (Hips)
        self.draw_leg(position=(-1.8, 0, -2.0), is_rear=True)
        self.draw_leg(position=(1.8, 0, -2.0), is_rear=True)

    def draw_leg(self, position, is_rear=False):
        """Helper to draw one complete leg."""
        glPushMatrix()
        glTranslatef(*position)

        # Thigh
        thigh_angle = -20 if is_rear else 10
        glColor3f(0.1, 0.6, 0.2)  # Dark Green
        glPushMatrix()
        glRotatef(thigh_angle, 1, 0, 0)
        self.draw_cube(scale=(0.8, 2.0, 1.0), position=(0, -1.0, 0))

        # Shin
        glTranslatef(0, -2.0, 0)
        glRotatef(-thigh_angle + 10, 1, 0, 0)
        self.draw_cube(scale=(0.7, 1.8, 0.7), position=(0, -0.8, 0))

        # Foot
        glColor3f(0.2, 0.7, 0.3)
        self.draw_cube(scale=(1.0, 0.4, 1.5), position=(0, -1.8, 0.5))

        # Claws
        glColor3f(0.9, 0.9, 0.2)  # Yellow
        self.draw_pyramid(scale=(0.2, 0.5, 0.2), position=(-0.3, -2.0, 1.2))
        self.draw_pyramid(scale=(0.2, 0.5, 0.2), position=(0, -2.0, 1.2))
        self.draw_pyramid(scale=(0.2, 0.5, 0.2), position=(0.3, -2.0, 1.2))

        glPopMatrix()  # Shin transform
        glPopMatrix()  # Main leg transform

    def draw_tail(self):
        """Draws a long, segmented tail WITH ENHANCED MOVEMENT."""
        glColor3f(0.1, 0.6, 0.2)  # Dark Green
        glPushMatrix()
        glTranslatef(0, 1.5, -2.5)  # Start of tail
        glRotatef(15, 1, 0, 0)  # Angle tail down slightly

        current_time = time.time()
        for i in range(8):
            scale_factor = 1.0 - i * 0.08
            self.draw_cube(scale=(1.5 * scale_factor, 1.5 * scale_factor, 1.5))
            glTranslatef(0, -0.1, -1.4)

            # --- MODIFIED TAIL ANIMATION ---
            # Dynamic vertical "flick" (around X-axis)
            flick = math.sin(current_time * 1.5 + i * 0.4) * \
                3  # A 3-degree flick
            glRotatef(2.0 + flick, 1, 0, 0)  # Base 2-degree down curve + flick

            # Stronger side-to-side "wag" (around Y-axis)
            wag = math.sin(current_time * 2.5 + i * 0.5) * \
                4   # A faster, 4-degree wag
            glRotatef(wag, 0, 1, 0)
            # --- END MODIFICATION ---

        # Tail Spike
        glColor3f(0.9, 0.9, 0.2)  # Yellow
        self.draw_pyramid(scale=(0.5, 1.0, 0.5), position=(0, 0, 0))
        glPopMatrix()

    def draw_wing(self, side):
        """Draws a detailed, structured wing."""
        # Main arm bone
        glColor3f(0.1, 0.6, 0.2)  # Dark Green
        self.draw_cube(scale=(3.0, 0.4, 0.4), position=(side * 1.5, 0, 0))

        # Wing spars/fingers
        glPushMatrix()
        glTranslatef(side*3, 0, 0)
        glRotatef(side * 20, 0, 1, 0)  # Angle spars back

        glColor3f(0.2, 0.7, 0.3)
        spar_positions = [
            {'pos': (0, 0, 0), 'rot': -10, 'scale': (0.3, 3.0, 0.3)},
            {'pos': (0, 0, 0), 'rot': 20, 'scale': (0.3, 4.0, 0.3)},
            {'pos': (0, 0, 0), 'rot': 50, 'scale': (0.3, 3.5, 0.3)},
        ]

        # Draw spars and membrane between them
        glColor3f(0.8, 0.1, 0.1)  # Red membrane
        glBegin(GL_TRIANGLES)
        for i in range(len(spar_positions) - 1):
            p1_info = spar_positions[i]
            p2_info = spar_positions[i+1]

            # Calculate spar endpoints
            angle1_rad = math.radians(p1_info['rot'])
            len1 = p1_info['scale'][1]
            p1_end = (side * len1 * math.sin(angle1_rad),
                      len1 * math.cos(angle1_rad), 0)

            angle2_rad = math.radians(p2_info['rot'])
            len2 = p2_info['scale'][1]
            p2_end = (side * len2 * math.sin(angle2_rad),
                      len2 * math.cos(angle2_rad), 0)

            glNormal3f(0, 0, side)
            glVertex3f(0, 0, 0)  # Pivot point
            glVertex3fv(p1_end)
            glVertex3fv(p2_end)

        glEnd()

        glColor3f(0.1, 0.6, 0.2)  # Dark Green for spars
        for info in spar_positions:
            glPushMatrix()
            glRotatef(info['rot'], 0, 0, side)
            self.draw_cube(scale=info['scale'],
                           position=(0, info['scale'][1]/2, 0))
            glPopMatrix()

        glPopMatrix()  # End spars transform

    def draw(self, wing_angle=0, head_angle=0):
        """
        Draws the complete, detailed dragon.
        NOW ACCEPTS a head_angle for animation.
        """
        self.draw_torso()

        # --- MODIFIED to apply head rotation ---
        # Apply head turn animation to both neck and head
        glPushMatrix()
        glRotatef(head_angle, 0, 1, 0)  # Rotate around the Y (vertical) axis
        self.draw_neck()
        self.draw_head()
        glPopMatrix()  # Restore matrix after drawing rotated head/neck
        # --- END MODIFICATION ---

        self.draw_legs()
        self.draw_tail()  # Tail animates itself using time.time()

        # Right Wing (flapping)
        glPushMatrix()
        glTranslatef(1.8, 2.5, 0.5)
        glRotatef(wing_angle, 0, 0, 1)  # Use passed-in wing_angle
        self.draw_wing(1)
        glPopMatrix()
        # Left Wing (flapping)
        glPushMatrix()
        glTranslatef(-1.8, 2.5, 0.5)
        glRotatef(-wing_angle, 0, 0, 1)  # Use passed-in wing_angle
        self.draw_wing(-1)
        glPopMatrix()


# --- Main Application Code ---
# Create a single instance of the dragon model
dragon = Dragon()

# --- Fire Particle Functions ---


def create_fire_particle():
    """
    MODIFIED to emit particles based on the current head_turn angle.
    This ensures fire is breathed in the direction the head is facing.
    """
    global head_turn  # Read the current head animation state

    # Base position (snout tip, straight forward)
    base_pos = [0.0, 3.5, 6.0]
    # Base velocity (randomized, but mostly forward in Z)
    base_vel = [random.uniform(-0.1, 0.1),
                random.uniform(-0.1, 0.1),
                random.uniform(0.5, 0.8)]

    # Convert head turn angle to radians for trig
    angle_rad = math.radians(head_turn)
    sin_a = math.sin(angle_rad)
    cos_a = math.cos(angle_rad)

    # --- Rotate both the starting position and the velocity vector ---
    # by the head_turn angle around the Y-axis.

    # Rotate position:
    # new_x = x*cos - z*sin (original formula is x*cos + z*sin, but our z is positive 'forward')
    # Let's use standard rotation: x' = x*cos + z*sin, z' = -x*sin + z*cos
    # Since base_pos[0] (x) is 0:
    rotated_pos_x = base_pos[2] * sin_a
    rotated_pos_z = base_pos[2] * cos_a

    # Rotate velocity:
    vx = base_vel[0]
    vz = base_vel[2]
    rotated_vel_x = vx * cos_a + vz * sin_a
    rotated_vel_z = -vx * sin_a + vz * cos_a

    # Create the particle with the new rotated position and velocity
    particle = {
        'pos': [rotated_pos_x, base_pos[1], rotated_pos_z],
        'vel': [rotated_vel_x, base_vel[1], rotated_vel_z],
        'life': random.uniform(0.5, 1.5),
        'size': random.uniform(0.2, 0.4),
        'color': random.choice([(1, 0.2, 0), (1, 0.5, 0), (1, 1, 0)])
    }
    fire_particles.append(particle)


def update_fire_particles():
    """Particles update themselves based on their own velocity. (Unchanged)"""
    global fire_particles
    for p in fire_particles:
        p['pos'][0] += p['vel'][0]
        p['pos'][1] += p['vel'][1]
        p['pos'][2] += p['vel'][2]
        p['life'] -= 0.02
        p['size'] *= 0.98
    fire_particles = [p for p in fire_particles if p['life'] > 0]


def draw_fire():
    """Draws particles in their calculated world-space positions. (Unchanged)"""
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)  # Added blending for a nicer fire effect
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)  # Additive blending
    glDepthMask(GL_FALSE)  # Don't write to depth buffer, prevents ugly squares

    glBegin(GL_QUADS)
    for p in fire_particles:
        # Fade particle out as it dies
        alpha = p['life'] / 1.5  # Assume max life is 1.5
        glColor4f(p['color'][0], p['color'][1], p['color'][2], alpha)
        x, y, z = p['pos']
        s = p['size'] / 2

        # Simple billboard (always faces camera, but this is good enough)
        glVertex3f(x - s, y - s, z)
        glVertex3f(x + s, y - s, z)
        glVertex3f(x + s, y + s, z)
        glVertex3f(x - s, y + s, z)
    glEnd()

    glDepthMask(GL_TRUE)  # Re-enable depth writing
    glDisable(GL_BLEND)  # Disable blending
    glEnable(GL_LIGHTING)

# --- Drawing and Scene Functions ---


def draw_ground():
    glDisable(GL_LIGHTING)
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_LINES)
    for i in range(-20, 21):
        glVertex3f(i, -5, -20)
        glVertex3f(i, -5, 20)
        glVertex3f(-20, -5, i)
        glVertex3f(20, -5, i)
    glEnd()
    glEnable(GL_LIGHTING)


def display():
    """Main display callback function. MODIFIED for new animations."""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    # Camera transforms (unchanged)
    glTranslatef(0.0, 0.0, camera_zoom)
    glRotatef(camera_rot_x, 1, 0, 0)
    glRotatef(camera_rot_y, 0, 1, 0)

    draw_ground()

    glPushMatrix()

    # --- MODIFIED to apply body bob animation ---
    # Apply the global body_bob to the dragon's main translation
    glTranslatef(0, -2 + body_bob, 0)

    # Pass BOTH animation angles to the draw method
    dragon.draw(wing_angle, head_turn)

    # Draw fire particles. They exist in this coordinate space.
    # We DO NOT rotate the particle system, as particles are spawned
    # with the correct rotation and live independently.
    if fire_particles:
        draw_fire()  # Removed the extra push/pop/translate

    glPopMatrix()

    glutSwapBuffers()

# --- GLUT Callback Functions ---


def reshape(w, h):
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (w / h), 0.1, 100.0)


def idle():
    """MODIFIED to update all animation variables."""
    global wing_angle, last_time, body_bob, head_turn
    current_time = time.time()
    if last_time == 0:
        last_time = current_time

    # --- UPDATE ALL ANIMATION GLOBALS ---
    # Wing flap (original)
    wing_angle = math.sin(current_time * 5) * 40

    # NEW: Body bob (syncs with wings but has a smaller motion)
    body_bob = math.sin(current_time * 5) * 0.2

    # NEW: Head turn (a slower, independent motion)
    head_turn = math.sin(current_time * 0.8) * \
        12  # A 12-degree turn side-to-side
    # --- END OF ANIMATION UPDATES ---

    if is_firing and len(fire_particles) < 100:
        create_fire_particle()

    update_fire_particles()
    glutPostRedisplay()


def keyboard(key, x, y):
    global is_firing, camera_zoom
    key = key.decode("utf-8")
    if key == 'f':
        is_firing = True
    elif key == 'w':
        camera_zoom += 1
    elif key == 's':
        camera_zoom -= 1
    elif key == 'q' or key == chr(27):  # Add 'q' or ESC to quit
        sys.exit(0)


def keyboard_up(key, x, y):
    global is_firing
    if key.decode("utf-8") == 'f':
        is_firing = False


def mouse(button, state, x, y):
    global mouse_dragging, last_mouse_pos
    if button == GLUT_LEFT_BUTTON:
        if state == GLUT_DOWN:
            mouse_dragging = True
            last_mouse_pos['x'] = x
            last_mouse_pos['y'] = y
        elif state == GLUT_UP:
            mouse_dragging = False


def motion(x, y):
    global camera_rot_x, camera_rot_y, last_mouse_pos
    if mouse_dragging:
        dx = x - last_mouse_pos['x']
        dy = y - last_mouse_pos['y']
        camera_rot_y += dx * 0.5
        camera_rot_x += dy * 0.5
        if camera_rot_x > 90:
            camera_rot_x = 90
        if camera_rot_x < -90:
            camera_rot_x = -90
        last_mouse_pos['x'] = x
        last_mouse_pos['y'] = y
        glutPostRedisplay()


def init():
    global last_time
    glClearColor(0.5, 0.7, 0.9, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glLightfv(GL_LIGHT0, GL_POSITION, [0, 15, -5, 1])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.8, 0.8, 0.8, 1.0])
    last_time = time.time()

# --- Main Execution ---


def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1200, 800)
    glutCreateWindow(b"Detailed Animated 3D Dragon Viewer")  # Updated title
    init()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    print("Controls:\n  - Left Click + Drag: Rotate\n  - 'f' (hold): Breathe Fire\n  - 'w'/'s': Zoom\n  - 'q' or ESC: Quit")
    glutMainLoop()


if __name__ == "__main__":
    main()
