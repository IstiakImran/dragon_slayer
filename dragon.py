from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random
import time
import sys

# --- Global State Variables ---

# Camera and Mouse Controls
camera_rot_x = -20
camera_rot_y = 0
camera_zoom = -40
head_rot_x = 0.0
head_rot_y = 0.0
last_mouse_pos = {'x': 0, 'y': 0}
mouse_dragging = False
right_mouse_dragging = False

# Animation and Firing State
wing_angle = 0
jaw_angle = 0.0
fireballs = []
embers = []
last_time = 0
delta_time = 0

# Centralized animation parameters
breathing_offset = 0.0
tail_sway_angle = 0.0

# --- Dragon Model Class ---


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
            size_multiplier = 1.0 - abs(i - 2) * 0.3
            self.draw_pyramid(scale=(0.8 * size_multiplier, 1.5 * size_multiplier, 0.3),
                              position=(0, 3.5, 2.0 - i * 1.2))

    def draw_torso(self):
        """Draws the main body, chest, and spinal plates."""
        glColor3f(0.1, 0.6, 0.2)
        self.draw_cube(scale=(3.5, 3, 5.5), position=(0, 1.5, 0))
        glColor3f(0.2, 0.7, 0.3)
        self.draw_cube(scale=(4, 3.5, 2), position=(0, 1.5, 1.5))
        glColor3f(0.9, 0.9, 0.2)
        for i in range(5):
            self.draw_cube(scale=(2.5, 0.4, 0.8),
                           position=(0, -0.2, 2.0 - i * 1.0))
        self.draw_spine()

    def draw_head(self, breathing_offset=0.0, head_rot_x=0.0, head_rot_y=0.0, jaw_angle=0.0):
        """Draws a much more detailed head that nods, aims, and opens its mouth."""
        glPushMatrix()
        glTranslatef(0, 3.5, 3.0)
        glRotatef(breathing_offset * -20, 1, 0, 0)
        glRotatef(head_rot_y, 0, 1, 0)
        glRotatef(head_rot_x, 1, 0, 0)

        # Main Head & Snout
        glColor3f(0.1, 0.6, 0.2)
        self.draw_cube(scale=(2, 1.8, 2.5), position=(0, 0, 0))
        self.draw_cube(scale=(1.5, 1.2, 2.5), position=(0, -0.2, 2.0))

        # ### FIX ###: Upper teeth are now rotated to point downwards.
        glColor3f(1.0, 1.0, 0.9)  # Off-white
        for i in range(5):
            glPushMatrix()
            # Move to the position under the snout
            glTranslatef(-0.6 + i*0.3, -0.55, 3.0)
            # Rotate 180 degrees around the X-axis to flip the pyramid
            glRotatef(180, 1, 0, 0)
            # Draw the pyramid at its new, rotated origin
            self.draw_pyramid(scale=(0.2, 0.8, 0.2), position=(0, 0, 0))
            glPopMatrix()

        # Lower Jaw
        glPushMatrix()
        glTranslatef(0, -0.7, 0.85)
        glRotatef(jaw_angle, 1, 0, 0)
        glTranslatef(0, -0.2, 1.15)
        glColor3f(0.2, 0.7, 0.3)
        self.draw_cube(scale=(1.4, 0.5, 2.3))

        # ### FIX ###: Lower teeth are made larger to be more visible.
        glColor3f(1.0, 1.0, 0.9)
        for i in range(4):
            # Left side
            self.draw_pyramid(scale=(0.2, 0.7, 0.2),  # Increased scale
                              position=(-0.5, 0.25, -0.8 + i*0.5))
            # Right side
            self.draw_pyramid(scale=(0.2, 0.7, 0.2),  # Increased scale
                              position=(0.5, 0.25, -0.8 + i*0.5))
        glPopMatrix()  # End jaw matrix

        # Eyes
        glColor3f(1.0, 0.0, 0.0)
        self.draw_sphere(radius=0.2, position=(-0.6, 0.5, 1.5))
        self.draw_sphere(radius=0.2, position=(0.6, 0.5, 1.5))
        # Horns
        glColor3f(0.9, 0.9, 0.2)
        self.draw_pyramid(scale=(0.4, 2.0, 0.4), position=(-0.8, 0.8, -0.5))
        self.draw_pyramid(scale=(0.4, 2.0, 0.4), position=(0.8, 0.8, -0.5))
        self.draw_pyramid(scale=(0.3, 1.5, 0.3), position=(-0.5, 0.8, -1.2))
        self.draw_pyramid(scale=(0.3, 1.5, 0.3), position=(0.5, 0.8, -1.2))

        glPopMatrix()

    def draw_neck(self):
        """Draws a curved, segmented neck."""
        glColor3f(0.1, 0.6, 0.2)
        glPushMatrix()
        glTranslatef(0, 2.5, 2.5)
        self.draw_cube(scale=(2, 2, 1))
        glRotatef(-15, 1, 0, 0)
        glTranslatef(0, 0.5, 0.8)
        self.draw_cube(scale=(1.8, 1.8, 1))
        glPopMatrix()

    def draw_legs(self):
        self.draw_leg(position=(-2.2, 0, 1.5))
        self.draw_leg(position=(2.2, 0, 1.5))
        self.draw_leg(position=(-1.8, 0, -2.0), is_rear=True)
        self.draw_leg(position=(1.8, 0, -2.0), is_rear=True)

    def draw_leg(self, position, is_rear=False):
        glPushMatrix()
        glTranslatef(*position)
        initial_leg_angle = 45 if is_rear else 55
        glRotatef(initial_leg_angle, 1, 0, 0)
        glColor3f(0.1, 0.6, 0.2)
        glPushMatrix()
        glRotatef(-40, 1, 0, 0)
        self.draw_cube(scale=(0.8, 2.0, 1.0), position=(0, -1.0, 0))
        glTranslatef(0, -2.0, 0)
        glRotatef(80, 1, 0, 0)
        self.draw_cube(scale=(0.7, 1.8, 0.7), position=(0, -0.8, 0))
        glColor3f(0.2, 0.7, 0.3)
        foot_z_offset = 0.5
        glRotatef(-20, 1, 0, 0)
        self.draw_cube(scale=(1.0, 0.4, 1.5),
                       position=(0, -1.8, foot_z_offset))
        glColor3f(0.9, 0.9, 0.2)
        claw_y_pos = -1.8
        claw_z_offset = 0.8 + foot_z_offset
        self.draw_pyramid(scale=(0.2, 0.5, 0.2),
                          position=(-0.3, claw_y_pos, claw_z_offset))
        self.draw_pyramid(scale=(0.2, 0.5, 0.2), position=(
            0, claw_y_pos, claw_z_offset))
        self.draw_pyramid(scale=(0.2, 0.5, 0.2), position=(
            0.3, claw_y_pos, claw_z_offset))
        glPopMatrix()
        glPopMatrix()

    def draw_tail(self, sway_angle=0.0):
        glColor3f(0.1, 0.6, 0.2)
        glPushMatrix()
        glTranslatef(0, 1.5, -2.5)
        glRotatef(sway_angle, 0, 1, 0)
        glRotatef(15, 1, 0, 0)
        current_time = time.time()
        for i in range(8):
            scale_factor = 1.0 - i * 0.08
            self.draw_cube(scale=(1.5*scale_factor, 1.5*scale_factor, 1.5))
            glTranslatef(0, -0.1, -1.4)
            glRotatef(math.sin(current_time * 3 + i * 0.8) * 4, 1, 0, 0)
            glRotatef(math.sin(current_time * 2 + i * 0.5) * 5, 0, 1, 0)
        glColor3f(0.9, 0.9, 0.2)
        self.draw_pyramid(scale=(0.5, 1.0, 0.5), position=(0, 0, 0))
        glPopMatrix()

    def draw_wing(self, side):
        glPushMatrix()
        glColor3f(0.1, 0.6, 0.2)
        self.draw_cube(scale=(2.0, 0.4, 0.4), position=(side * 1.0, 0, 0))
        glTranslatef(side * 2.0, 0, 0)
        glRotatef(-side * 30, 0, 1, 0)
        self.draw_cube(scale=(2.5, 0.4, 0.4), position=(side * 1.25, 0, 0))
        glTranslatef(side * 2.5, 0, 0)
        spar_definitions = [{'angle': -20, 'length': 4.0},
                            {'angle': 15, 'length': 6.0}, {'angle': 50, 'length': 5.0}]
        spar_endpoints = []
        for spar in spar_definitions:
            angle_rad = math.radians(spar['angle'])
            end_point = (side * spar['length'] * math.sin(angle_rad),
                         0, -spar['length'] * math.cos(angle_rad))
            spar_endpoints.append(end_point)
        glColor3f(0.8, 0.1, 0.1)
        glBegin(GL_TRIANGLES)
        glNormal3f(0, side, 0)
        wrist_pos = (0, 0, 0)
        elbow_pos = (-side * 2.5, 0, 0)
        glVertex3fv(elbow_pos)
        glVertex3fv(wrist_pos)
        glVertex3fv(spar_endpoints[0])
        for i in range(len(spar_endpoints) - 1):
            glVertex3fv(wrist_pos)
            glVertex3fv(spar_endpoints[i])
            glVertex3fv(spar_endpoints[i+1])
        glEnd()
        glColor3f(0.1, 0.6, 0.2)
        for i, spar in enumerate(spar_definitions):
            glPushMatrix()
            glRotatef(spar['angle'], 0, side, 0)
            self.draw_cube(scale=(0.2, 0.2, spar['length']), position=(
                0, 0, -spar['length']/2))
            glPopMatrix()
        glPopMatrix()

    def draw(self, wing_angle=0, breathing_offset=0.0, tail_sway_angle=0.0, head_rot_x=0.0, head_rot_y=0.0, jaw_angle=0.0):
        glPushMatrix()
        glTranslatef(0, breathing_offset, 0)
        self.draw_torso()
        self.draw_neck()
        self.draw_head(breathing_offset, head_rot_x, head_rot_y, jaw_angle)
        self.draw_legs()
        self.draw_tail(tail_sway_angle)
        glPushMatrix()
        glTranslatef(1.8, 2.5, 0.5)
        glRotatef(wing_angle, 0, 0, 1)
        self.draw_wing(1)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-1.8, 2.5, 0.5)
        glRotatef(-wing_angle, 0, 0, 1)
        self.draw_wing(-1)
        glPopMatrix()
        glPopMatrix()


# --- Main Application Code ---
dragon = Dragon()

# --- Fire & Ember Functions ---


def create_fireball():
    global fireballs, head_rot_x, head_rot_y, breathing_offset
    speed = 25.0
    pitch_rad = math.radians(head_rot_x)
    yaw_rad = math.radians(head_rot_y)
    vel_x = speed * math.cos(pitch_rad) * math.sin(yaw_rad)
    vel_y = -speed * math.sin(pitch_rad)
    vel_z = speed * math.cos(pitch_rad) * math.cos(yaw_rad)
    local_mouth_pos = [0, 0, 4.5]
    y1 = local_mouth_pos[1]*math.cos(pitch_rad) - \
        local_mouth_pos[2]*math.sin(pitch_rad)
    z1 = local_mouth_pos[1]*math.sin(pitch_rad) + \
        local_mouth_pos[2]*math.cos(pitch_rad)
    pos_after_pitch = [local_mouth_pos[0], y1, z1]
    x2 = pos_after_pitch[0]*math.cos(yaw_rad) + \
        pos_after_pitch[2]*math.sin(yaw_rad)
    z2 = -pos_after_pitch[0]*math.sin(yaw_rad) + \
        pos_after_pitch[2]*math.cos(yaw_rad)
    final_rotated_offset = [x2, pos_after_pitch[1], z2]
    pivot_pos = [0, (1.5 + breathing_offset - 2.0), 3.0]
    start_pos = [pivot_pos[i] + final_rotated_offset[i] for i in range(3)]
    fireball = {'pos': start_pos, 'vel': [
        vel_x, vel_y, vel_z], 'life': 2.5, 'max_life': 2.5, 'size': 1.0}
    fireballs.append(fireball)


def update_fireballs_and_embers(delta_time):
    """Updates fireballs and spawns embers from them."""
    global fireballs, embers
    gravity = 9.8
    # Update fireballs
    for p in fireballs:
        for i in range(3):
            p['pos'][i] += p['vel'][i] * delta_time
        p['vel'][1] -= gravity * delta_time
        p['life'] -= delta_time
        # Spawn embers from active fireballs
        if random.random() < 0.8:
            vel_spread = 0.2
            ember_vel = [
                p['vel'][i]*0.1 + random.uniform(-vel_spread, vel_spread) for i in range(3)]
            embers.append(
                {'pos': p['pos'][:], 'vel': ember_vel, 'life': 0.8, 'max_life': 0.8})
    fireballs = [p for p in fireballs if p['life'] > 0]
    # Update embers
    for p in embers:
        for i in range(3):
            p['pos'][i] += p['vel'][i] * delta_time
        p['vel'][1] -= gravity * 0.5 * delta_time
        p['life'] -= delta_time
    embers = [p for p in embers if p['life'] > 0]


def draw_billboard_particles(particles, modelview_matrix):
    """Generic function to draw a list of particles as camera-facing quads."""
    cam_right = [modelview_matrix[0][0],
                 modelview_matrix[1][0], modelview_matrix[2][0]]
    cam_up = [modelview_matrix[0][1],
              modelview_matrix[1][1], modelview_matrix[2][1]]

    glBegin(GL_QUADS)
    for p in particles:
        life_ratio = p['life'] / p['max_life']
        size = p.get('size', 0.1) * life_ratio
        pos = p['pos']
        color = p['color'] + (life_ratio,)
        glColor4fv(color)

        p1 = [pos[i] - (cam_right[i] + cam_up[i]) * size for i in range(3)]
        p2 = [pos[i] + (cam_right[i] - cam_up[i]) * size for i in range(3)]
        p3 = [pos[i] + (cam_right[i] + cam_up[i]) * size for i in range(3)]
        p4 = [pos[i] - (cam_right[i] - cam_up[i]) * size for i in range(3)]

        glVertex3fv(p1)
        glVertex3fv(p2)
        glVertex3fv(p3)
        glVertex3fv(p4)
    glEnd()


def draw_fire_and_embers(modelview_matrix):
    """Main drawing function for all fire effects."""
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glDepthMask(GL_FALSE)

    # Draw main fireball clouds
    fire_particles = []
    for p in fireballs:
        life_ratio = p['life'] / p['max_life']
        for _ in range(30):
            offset = [random.uniform(-1, 1) * p['size']
                      * life_ratio for _ in range(3)]
            dist_from_center = math.sqrt(sum(x*x for x in offset))
            g_channel = max(0, 1.0 - dist_from_center /
                            (p['size'] * life_ratio))
            particle_color = (1.0, 0.5 + g_channel*0.5, 0.0)
            fire_particles.append({'pos': [p['pos'][i] + offset[i] for i in range(3)],
                                   'life': p['life'], 'max_life': p['max_life'],
                                   'size': 0.4, 'color': particle_color})
    if fire_particles:
        draw_billboard_particles(fire_particles, modelview_matrix)

    # Draw embers
    ember_particles = []
    for p in embers:
        ember_particles.append({'pos': p['pos'], 'life': p['life'], 'max_life': p['max_life'],
                                'size': 0.1, 'color': (1.0, 0.4, 0.0)})
    if ember_particles:
        draw_billboard_particles(ember_particles, modelview_matrix)

    glDepthMask(GL_TRUE)
    glDisable(GL_BLEND)
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

    modelview_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)

    draw_ground()
    glPushMatrix()
    glTranslatef(0, -2, 0)
    dragon.draw(wing_angle, breathing_offset, tail_sway_angle,
                head_rot_x, head_rot_y, jaw_angle)
    glPopMatrix()

    if fireballs or embers:
        draw_fire_and_embers(modelview_matrix)

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
    global wing_angle, last_time, delta_time, breathing_offset, tail_sway_angle, jaw_angle
    current_time = time.time()
    if last_time == 0:
        last_time = current_time
    delta_time = current_time - last_time
    last_time = current_time
    if delta_time == 0:
        return

    wing_angle = math.sin(current_time * 5) * 40
    breathing_offset = math.sin(current_time * 2.0) * 0.1
    tail_sway_angle = math.sin(current_time * 1.0) * 8

    if jaw_angle > 0:
        jaw_angle = max(0, jaw_angle - 50 * delta_time)

    update_fireballs_and_embers(delta_time)

    glutPostRedisplay()


def keyboard(key, x, y):
    global jaw_angle, camera_zoom
    key = key.decode("utf-8")
    if key == 'f':
        if jaw_angle < 5:
            jaw_angle = 25
            create_fireball()
    elif key == 'w':
        camera_zoom += 1
    elif key == 's':
        camera_zoom -= 1


def keyboard_up(key, x, y): pass


def mouse(button, state, x, y):
    global mouse_dragging, right_mouse_dragging, last_mouse_pos
    if button == GLUT_LEFT_BUTTON:
        mouse_dragging = (state == GLUT_DOWN)
        if mouse_dragging:
            last_mouse_pos = {'x': x, 'y': y}
    elif button == GLUT_RIGHT_BUTTON:
        right_mouse_dragging = (state == GLUT_DOWN)
        if right_mouse_dragging:
            last_mouse_pos = {'x': x, 'y': y}


def motion(x, y):
    global camera_rot_x, camera_rot_y, head_rot_x, head_rot_y, last_mouse_pos
    dx = x - last_mouse_pos['x']
    dy = y - last_mouse_pos['y']
    if mouse_dragging:
        camera_rot_y += dx * 0.5
        camera_rot_x += dy * 0.5
        camera_rot_x = max(-90, min(90, camera_rot_x))
    elif right_mouse_dragging:
        head_rot_y += dx * 0.5
        head_rot_x += dy * 0.5
        head_rot_x = max(-45, min(30, head_rot_x))
        head_rot_y = max(-60, min(60, head_rot_y))
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


def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1200, 800)
    glutCreateWindow(b"Interactive Animated 3D Dragon")
    init()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    print("Controls:\n  - Left Click + Drag: Rotate Camera\n  - Right Click + Drag: Aim Head\n  - 'f': Shoot a Fireball\n  - 'w'/'s': Zoom Camera")
    glutMainLoop()


if __name__ == "__main__":
    main()
