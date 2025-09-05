from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random
import time
import sys

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
is_firing = False
fire_particles = []
last_time = 0

# Centralized animation parameters
breathing_offset = 0.0  # For the body's up/down breathing motion
tail_sway_angle = 0.0   # For the tail's base side-to-side sway

# --- Dragon Model Class ---
# This class has been updated with more dynamic and detailed parts.


class Dragon:
    """
    Handles drawing the different parts of the dragon model.
    This version includes more animations and geometric detail.
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

    def draw_spine(self):
        """Draws the spinal plates with variable sizes."""
        glColor3f(0.8, 0.1, 0.1)  # Red
        for i in range(5):
            # Make plates in the middle larger, tapering at the ends
            size_multiplier = 1.0 - abs(i - 2) * 0.3
            self.draw_pyramid(scale=(0.8 * size_multiplier, 1.5 * size_multiplier, 0.3),
                              position=(0, 3.5, 2.0 - i * 1.2))

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
        self.draw_spine()

    def draw_head(self, breathing_offset=0.0):
        """Draws a much more detailed head that nods with breathing, now with eyes."""
        glPushMatrix()
        glTranslatef(0, 3.5, 3.0)  # Position the whole head assembly

        # Add a subtle nod with the breathing
        glRotatef(breathing_offset * -20, 1, 0, 0)

        # Main Head Block
        glColor3f(0.1, 0.6, 0.2)  # Dark Green
        self.draw_cube(scale=(2, 1.8, 2.5), position=(0, 0, 0))
        # Snout
        self.draw_cube(scale=(1.5, 1.2, 2.5), position=(0, -0.2, 2.0))
        # Lower Jaw
        glColor3f(0.2, 0.7, 0.3)  # Lighter Green
        self.draw_cube(scale=(1.4, 0.5, 2.3), position=(0, -0.9, 2.0))
        # Teeth
        glColor3f(1.0, 1.0, 0.9)  # Off-white
        for i in range(3):
            self.draw_pyramid(scale=(0.1, 0.2, 0.1),
                              position=(-0.5 + i*0.5, -0.55, 3.0))
        # Eyes - NEW
        glColor3f(1.0, 0.0, 0.0)  # Red Eyes
        self.draw_sphere(radius=0.2, position=(-0.6, 0.5, 1.5)
                         )  # Adjusted Z for snout
        self.draw_sphere(radius=0.2, position=(
            0.6, 0.5, 1.5))  # Adjusted Z for snout
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
        self.draw_leg(position=(-2.2, 0, 1.5))
        self.draw_leg(position=(2.2, 0, 1.5))
        self.draw_leg(position=(-1.8, 0, -2.0), is_rear=True)
        self.draw_leg(position=(1.8, 0, -2.0), is_rear=True)

    def draw_leg(self, position, is_rear=False):
        """Helper to draw one complete leg."""
        glPushMatrix()
        glTranslatef(*position)

        thigh_angle = -20 if is_rear else 10
        glColor3f(0.1, 0.6, 0.2)  # Dark Green
        glPushMatrix()
        glRotatef(thigh_angle, 1, 0, 0)
        self.draw_cube(scale=(0.8, 2.0, 1.0), position=(0, -1.0, 0))

        glTranslatef(0, -2.0, 0)
        glRotatef(-thigh_angle + 10, 1, 0, 0)
        self.draw_cube(scale=(0.7, 1.8, 0.7), position=(0, -0.8, 0))

        glColor3f(0.2, 0.7, 0.3)
        self.draw_cube(scale=(1.0, 0.4, 1.5), position=(0, -1.8, 0.5))

        glColor3f(0.9, 0.9, 0.2)  # Yellow
        self.draw_pyramid(scale=(0.2, 0.5, 0.2), position=(-0.3, -2.0, 1.2))
        self.draw_pyramid(scale=(0.2, 0.5, 0.2), position=(0, -2.0, 1.2))
        self.draw_pyramid(scale=(0.2, 0.5, 0.2), position=(0.3, -2.0, 1.2))

        glPopMatrix()
        glPopMatrix()

    def draw_tail(self, sway_angle=0.0):
        """Draws a long, segmented tail with fluid animation."""
        glColor3f(0.1, 0.6, 0.2)  # Dark Green
        glPushMatrix()
        glTranslatef(0, 1.5, -2.5)  # Start of tail
        glRotatef(sway_angle, 0, 1, 0)
        glRotatef(15, 1, 0, 0)  # Angle tail down slightly

        current_time = time.time()
        for i in range(8):
            scale_factor = 1.0 - i * 0.08
            self.draw_cube(scale=(1.5 * scale_factor, 1.5 * scale_factor, 1.5))
            glTranslatef(0, -0.1, -1.4)
            vertical_wave = math.sin(current_time * 3 + i * 0.8) * 4
            glRotatef(vertical_wave, 1, 0, 0)
            horizontal_wave = math.sin(current_time * 2 + i * 0.5) * 5
            glRotatef(horizontal_wave, 0, 1, 0)

        glColor3f(0.9, 0.9, 0.2)  # Yellow
        self.draw_pyramid(scale=(0.5, 1.0, 0.5), position=(0, 0, 0))
        glPopMatrix()

    def draw_wing(self, side):
        """
        Draws a more detailed and anatomically plausible wing with an articulated
        arm and proper membrane panels. This version is built horizontally (in the XZ plane)
        to allow for correct up-and-down flapping.
        Side: 1 for right, -1 for left.
        """
        glPushMatrix()

        # --- 1. Draw the Wing Bones (Arm) ---
        glColor3f(0.1, 0.6, 0.2)  # Dark Green for bones

        # Humerus (Upper Arm) - Connects to the body, extends along X axis
        self.draw_cube(scale=(2.0, 0.4, 0.4), position=(side * 1.0, 0, 0))

        # Move to the "elbow" joint
        glTranslatef(side * 2.0, 0, 0)
        # Angle the forearm back in the horizontal plane (rotation around Y-axis)
        glRotatef(-side * 30, 0, 1, 0)

        # Radius/Ulna (Forearm)
        self.draw_cube(scale=(2.5, 0.4, 0.4), position=(side * 1.25, 0, 0))

        # --- 2. Draw the Spars (Fingers) and Membrane ---
        # Move the drawing origin to the "wrist" joint
        glTranslatef(side * 2.5, 0, 0)

        spar_definitions = [
            {'angle': -20, 'length': 4.0},
            {'angle': 15,  'length': 6.0},
            {'angle': 50,  'length': 5.0},
        ]

        spar_endpoints = []
        for spar in spar_definitions:
            angle_rad = math.radians(spar['angle'])
            # Calculate endpoint in the horizontal XZ plane
            end_point = (
                side * spar['length'] * math.sin(angle_rad),
                0,  # Y is 0 for a horizontal wing
                -spar['length'] * math.cos(angle_rad)  # Adjusted Z
            )
            spar_endpoints.append(end_point)

        # --- Draw the Membrane ---
        glColor3f(0.8, 0.1, 0.1)  # Red membrane
        glBegin(GL_TRIANGLES)
        # The normal for a horizontal wing points up (or down), i.e., along the Y axis
        glNormal3f(0, side, 0)

        wrist_pos = (0, 0, 0)
        elbow_pos = (-side * 2.5, 0, 0)  # Relative to the wrist

        # Membrane Panel 1: Connects Forearm to the first spar
        glVertex3fv(elbow_pos)
        glVertex3fv(wrist_pos)
        glVertex3fv(spar_endpoints[0])

        # Membrane Panels between spars
        for i in range(len(spar_endpoints) - 1):
            glVertex3fv(wrist_pos)
            glVertex3fv(spar_endpoints[i])
            glVertex3fv(spar_endpoints[i+1])
        glEnd()

        # --- Draw the Spars (bones) ---
        glColor3f(0.1, 0.6, 0.2)  # Back to dark green
        for i, spar in enumerate(spar_definitions):
            glPushMatrix()
            # To spread the spars in the XZ plane, we rotate around the Y axis
            glRotatef(spar['angle'], 0, side, 0)
            # The spar is a long, thin cube pointing "backwards" along the Z axis
            self.draw_cube(scale=(0.2, 0.2, spar['length']),
                           position=(0, 0, -spar['length'] / 2))  # Adjusted Z
            glPopMatrix()

        glPopMatrix()  # End of the wing transform

    def draw(self, wing_angle=0, breathing_offset=0.0, tail_sway_angle=0.0):
        """Draws the complete, detailed dragon."""
        glPushMatrix()
        glTranslatef(0, breathing_offset, 0)

        self.draw_torso()
        self.draw_neck()
        self.draw_head(breathing_offset)
        self.draw_legs()
        self.draw_tail(tail_sway_angle)

        # Right Wing
        glPushMatrix()
        glTranslatef(1.8, 2.5, 0.5)
        # The wing is now built horizontally, so rotating around the Z-axis
        # correctly produces an up-and-down flapping motion.
        glRotatef(wing_angle, 0, 0, 1)
        self.draw_wing(1)
        glPopMatrix()

        # Left Wing
        glPushMatrix()
        glTranslatef(-1.8, 2.5, 0.5)
        glRotatef(-wing_angle, 0, 0, 1)
        self.draw_wing(-1)
        glPopMatrix()

        glPopMatrix()


# --- Main Application Code ---
dragon = Dragon()

# --- Fire Particle Functions ---


def create_fire_particle():
    particle = {
        # Start closer to snout
        'pos': [random.uniform(-0.1, 0.1), 3.0 + random.uniform(-0.1, 0.1), 5.5],
        # More forward, slight upward
        'vel': [random.uniform(-0.05, 0.05), random.uniform(0.05, 0.1), random.uniform(0.8, 1.2)],
        'life': random.uniform(0.3, 0.8),  # Shorter life for dynamic feel
        'max_life': 0,  # Will be set below
        'size': random.uniform(0.1, 0.3),  # Smaller particles
        'color': random.choice([(1, 0.2, 0), (1, 0.5, 0), (1, 1, 0)])
    }
    particle['max_life'] = particle['life']  # Store for alpha calculation
    fire_particles.append(particle)


def update_fire_particles():
    global fire_particles
    for p in fire_particles:
        p['pos'][0] += p['vel'][0]
        p['pos'][1] += p['vel'][1] * 0.5  # Less upward momentum than forward
        p['pos'][2] += p['vel'][2]
        p['life'] -= 0.02  # Faster decay
        p['size'] *= 0.96  # Shrink faster
    fire_particles = [p for p in fire_particles if p['life'] > 0]


def draw_fire():
    glDisable(GL_LIGHTING)
    # Don't write to depth buffer for transparent particles
    glDepthMask(GL_FALSE)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    # glEnable(GL_ALPHA_TEST) # Sometimes used with blending, depends on effect
    # glAlphaFunc(GL_GREATER, 0.1)

    glBegin(GL_QUADS)
    for p in fire_particles:
        # Calculate alpha based on remaining life
        alpha = p['life'] / p['max_life']

        # Color fading from red/orange to yellow
        color_fade = 1.0 - alpha  # 0 when full life, 1 when no life
        r = p['color'][0]
        g = p['color'][1] + (1 - p['color'][1]) * \
            color_fade * 0.5  # Fade towards yellow
        b = p['color'][2] - p['color'][2] * \
            color_fade * 0.5  # Fade away from blue

        glColor4f(r, g, b, alpha)  # Use glColor4f for alpha

        x, y, z = p['pos']
        s = p['size'] / 2
        # Billboarding effect - make particles always face the camera (simple way)
        # This draws squares that are aligned with the Z-axis, which is often sufficient for fire
        glVertex3f(x - s, y - s, z)
        glVertex3f(x + s, y - s, z)
        glVertex3f(x + s, y + s, z)
        glVertex3f(x - s, y + s, z)
    glEnd()

    # glDisable(GL_ALPHA_TEST)
    glDisable(GL_BLEND)
    glDepthMask(GL_TRUE)  # Re-enable depth writing
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
    """Main display callback function."""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glTranslatef(0.0, 0.0, camera_zoom)
    glRotatef(camera_rot_x, 1, 0, 0)
    glRotatef(camera_rot_y, 0, 1, 0)

    draw_ground()

    glPushMatrix()
    glTranslatef(0, -2, 0)
    dragon.draw(wing_angle, breathing_offset, tail_sway_angle)

    if fire_particles:
        glPushMatrix()
        # Fire particles relative to the dragon's head
        glTranslatef(0, 0, -1)  # adjust fire origin back slightly for effect
        draw_fire()
        glPopMatrix()
    glPopMatrix()

    glutSwapBuffers()

# --- GLUT Callback Functions ---


def reshape(w, h):
    if h == 0:
        h = 1
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (w / h), 0.1, 100.0)


def idle():
    global wing_angle, last_time, breathing_offset, tail_sway_angle

    current_time = time.time()
    if last_time == 0:
        last_time = current_time

    wing_angle = math.sin(current_time * 5) * 40
    breathing_offset = math.sin(current_time * 2.0) * 0.1
    tail_sway_angle = math.sin(current_time * 1.0) * 8

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

    # Enable point sprites for a potentially more advanced fire effect
    # This might require some adjustments to the particle drawing logic
    # glEnable(GL_POINT_SPRITE)
    # glTexEnvi(GL_POINT_SPRITE, GL_COORD_REPLACE, GL_TRUE)
    # glPointSize(10.0) # Example size, actual size depends on texture


def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1200, 800)
    glutCreateWindow(b"Detailed and Animated 3D Dragon Viewer")
    init()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    print("Controls:\n  - Left Click + Drag: Rotate\n  - 'f' (hold): Breathe Fire\n  - 'w'/'s': Zoom")
    glutMainLoop()


if __name__ == "__main__":
    main()
