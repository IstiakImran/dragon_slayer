from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import math
import random
import time
import sys

# --- Global State Variables ---
camera_rot_x = -20
camera_rot_y = 0
camera_zoom = -50
last_mouse_pos = {'x': 0, 'y': 0}
mouse_dragging = False

wing_angle = 0
wing_fold_angle = 0
is_firing = False
fire_particles = []
last_time = 0

# --- Dragon Model Class (Perfected Hierarchical Model) ---


class Dragon:
    """
    Handles drawing a seamless, detailed, and animated dragon model.
    All parts are connected using chained transformations to prevent gaps.
    """

    def __init__(self):
        self.quadric = gluNewQuadric()
        gluQuadricNormals(self.quadric, GLU_SMOOTH)  # For smooth lighting

    def draw_cube(self, scale=(1, 1, 1), position=(0, 0, 0)):
        glPushMatrix()
        glTranslatef(*position)
        glScalef(*scale)
        glutSolidCube(1)
        glPopMatrix()

    def draw_pyramid(self, scale=(1, 1, 1), position=(0, 0, 0)):
        glPushMatrix()
        glTranslatef(*position)
        glScalef(*scale)
        glBegin(GL_TRIANGLES)
        glNormal3f(0, 0.5, 0.5)
        glVertex3f(0, 1, 0)
        glVertex3f(-1, -1, 1)
        glVertex3f(1, -1, 1)
        glNormal3f(0.5, 0.5, 0)
        glVertex3f(0, 1, 0)
        glVertex3f(1, -1, 1)
        glVertex3f(1, -1, -1)
        glNormal3f(0, 0.5, -0.5)
        glVertex3f(0, 1, 0)
        glVertex3f(1, -1, -1)
        glVertex3f(-1, -1, -1)
        glNormal3f(-0.5, 0.5, 0)
        glVertex3f(0, 1, 0)
        glVertex3f(-1, -1, -1)
        glVertex3f(-1, -1, 1)
        glEnd()
        glPopMatrix()

    def draw_sphere(self, radius=1, position=(0, 0, 0)):
        glPushMatrix()
        glTranslatef(*position)
        glutSolidSphere(radius, 20, 20)
        glPopMatrix()

    def draw_cylinder(self, radius, height):
        # Draws a cylinder oriented along the Z-axis with solid caps
        glPushMatrix()
        gluCylinder(self.quadric, radius, radius, height, 20, 20)  # Body
        glRotatef(180, 1, 0, 0)
        gluDisk(self.quadric, 0, radius, 20, 1)  # Base cap
        glRotatef(180, 1, 0, 0)
        glTranslatef(0, 0, height)
        gluDisk(self.quadric, 0, radius, 20, 1)  # Top cap
        glPopMatrix()

    def draw_torso(self, anim_time):
        glPushMatrix()
        torso_bob = math.sin(anim_time * 3) * 0.05
        glTranslatef(0, torso_bob, 0)
        glColor3f(0.05, 0.4, 0.15)
        self.draw_cube(scale=(3.5, 3, 6.5), position=(0, 1.5, 0))
        glColor3f(0.1, 0.5, 0.2)
        self.draw_cube(scale=(4.2, 3.7, 2.5), position=(0, 1.5, 1.8))
        glColor3f(0.8, 0.8, 0.15)
        for i in range(7):
            self.draw_cube(scale=(2.5, 0.4, 0.8),
                           position=(0, -0.4, 2.8 - i * 0.9))
        glColor3f(0.6, 0.1, 0.1)
        for i in range(6):
            self.draw_pyramid(scale=(0.8, 1.5, 0.3),
                              position=(0, 3.6, 2.5 - i * 1.2))
        glPopMatrix()

    def draw_head(self, anim_time):
        glPushMatrix()
        head_bob_y = math.sin(anim_time * 2) * 0.1
        head_bob_z = math.cos(anim_time * 2) * 0.1
        head_turn = math.sin(anim_time * 0.8) * 5
        glTranslatef(0, 0.5 + head_bob_y, 1.0 + head_bob_z)
        glRotatef(head_turn, 0, 1, 0)
        glColor3f(0.05, 0.4, 0.15)
        self.draw_cube(scale=(2, 1.8, 2.5), position=(0, 0, 0))
        self.draw_cube(scale=(1.5, 1.2, 2.5), position=(0, -0.2, 2.0))
        glColor3f(0.1, 0.5, 0.2)
        self.draw_cube(scale=(1.4, 0.5, 2.3), position=(0, -0.9, 2.0))
        glColor3f(0.9, 0.9, 0.8)
        for i in range(4):
            self.draw_pyramid(scale=(0.1, 0.3, 0.1),
                              position=(-0.6 + i*0.4, -0.55, 3.0))
        glColor3f(1.0, 0.1, 0.0)
        self.draw_sphere(radius=0.2, position=(-0.6, 0.5, 0.8))
        self.draw_sphere(radius=0.2, position=(0.6, 0.5, 0.8))
        glColor3f(0.8, 0.8, 0.15)
        self.draw_pyramid(scale=(0.4, 2.5, 0.4), position=(-0.8, 0.8, -0.5))
        self.draw_pyramid(scale=(0.4, 2.5, 0.4), position=(0.8, 0.8, -0.5))
        self.draw_pyramid(scale=(0.3, 2.0, 0.3), position=(-0.5, 0.8, -1.2))
        self.draw_pyramid(scale=(0.3, 2.0, 0.3), position=(0.5, 0.8, -1.2))
        glPopMatrix()

    def draw_neck_and_head(self, anim_time):
        glPushMatrix()
        glTranslatef(0, 2.5, 2.8)  # Connection point on torso
        glColor3f(0.05, 0.4, 0.15)
        glRotatef(-25, 1, 0, 0)
        self.draw_cube(scale=(2, 2, 1.5))  # First neck segment
        glTranslatef(0, 0.2, 1.4)  # Move to the end of the first segment
        glRotatef(15, 1, 0, 0)
        self.draw_cube(scale=(1.8, 1.8, 1.5))  # Second neck segment
        # Now draw the head at the end of the neck
        self.draw_head(anim_time)
        glPopMatrix()

    def draw_legs(self):
        self.draw_leg(position=(-2.0, 1.0, 1.8), is_rear=False)
        self.draw_leg(position=(2.0, 1.0, 1.8), is_rear=False)
        self.draw_leg(position=(-1.8, 1.0, -2.5), is_rear=True)
        self.draw_leg(position=(1.8, 1.0, -2.5), is_rear=True)

    def draw_leg(self, position, is_rear=False):
        glPushMatrix()
        glTranslatef(*position)
        thigh_angle = -45 if is_rear else -10
        glColor3f(0.05, 0.4, 0.15)
        # Thigh
        glPushMatrix()
        glRotatef(thigh_angle, 1, 0, 0)
        glRotatef(-90, 1, 0, 0)
        self.draw_cylinder(0.5, 2.0)
        glPopMatrix()
        # Shin
        glPushMatrix()
        glTranslatef(0, -2.0*math.cos(math.radians(thigh_angle)),
                     2.0*math.sin(math.radians(thigh_angle)))
        glRotatef(60 if is_rear else 20, 1, 0, 0)
        glRotatef(-90, 1, 0, 0)
        self.draw_cylinder(0.4, 1.8)
        glPopMatrix()
        # Foot
        glPushMatrix()
        glTranslatef(0, -3.2, -0.5)
        glColor3f(0.1, 0.5, 0.2)
        self.draw_cube(scale=(1.0, 0.4, 1.5), position=(0, -0.2, 0.5))
        glColor3f(0.8, 0.8, 0.15)
        self.draw_pyramid(scale=(0.2, 0.6, 0.2), position=(-0.3, -0.2, 1.2))
        self.draw_pyramid(scale=(0.2, 0.6, 0.2), position=(0, -0.2, 1.3))
        self.draw_pyramid(scale=(0.2, 0.6, 0.2), position=(0.3, -0.2, 1.2))
        glPopMatrix()
        glPopMatrix()

    def draw_tail(self, anim_time):
        glPushMatrix()
        glTranslatef(0, 1.5, -3.2)
        glColor3f(0.05, 0.4, 0.15)
        glRotatef(20, 1, 0, 0)
        for i in range(12):
            scale_factor = 1.0 - i * 0.07
            glPushMatrix()
            glScalef(scale_factor, scale_factor, 1.0)
            self.draw_cube(scale=(1.8, 1.8, 1.5))
            glPopMatrix()
            glTranslatef(0, -0.15, -1.5)
            glRotatef(2, 1, 0, 0)
            glRotatef(math.sin(anim_time * 3 + i * 0.5) * 4, 0, 1, 0)
            glRotatef(math.cos(anim_time * 2 + i * 0.5) * 3, 1, 0, 0)
        glColor3f(0.8, 0.8, 0.15)
        self.draw_pyramid(scale=(0.8, 1.5, 0.8), position=(0, 0, 0))
        glPopMatrix()

    def draw_wing(self, side, wing_angle, fold_angle):
        glPushMatrix()
        glColor3f(0.05, 0.4, 0.15)
        # Main arm bone
        glRotatef(side * -10, 0, 1, 0)
        glRotatef(90, 0, 1, 0)
        self.draw_cylinder(0.4, 5.0)
        # Forearm
        glTranslatef(0, 0, 5.0)
        glRotatef(side * -45 - fold_angle, 0, 1, 0)
        self.draw_cylinder(0.3, 6.0)
        # Wingtip
        glTranslatef(0, 0, 6.0)
        glRotatef(side * -30, 0, 1, 0)
        self.draw_cylinder(0.2, 4.0)

        # Draw Membrane
        glColor4f(0.6, 0.1, 0.1, 0.8)  # Semi-transparent red
        glEnable(GL_BLEND)
        glDepthMask(GL_FALSE)
        glBegin(GL_TRIANGLE_FAN)
        glNormal3f(-side, 0, 0)
        # Anchor points on the bones
        p_root = (0, 0, -11.0)  # Base of forearm
        p_mid = (0, 0, -4.0)  # Base of wingtip
        p_tip = (0, 0, 0)  # End of wingtip
        p_body_anchor = (side * 2.0, -2.0, -11.0)

        glVertex3fv(p_root)
        glVertex3fv(p_mid)
        glVertex3fv(p_tip)
        glVertex3fv(p_body_anchor)
        glEnd()
        glDepthMask(GL_TRUE)
        glDisable(GL_BLEND)
        glPopMatrix()

    def draw(self, angle=0, fold_angle=0, anim_time=0):
        self.draw_torso(anim_time)
        self.draw_neck_and_head(anim_time)
        self.draw_legs()
        self.draw_tail(anim_time)
        glPushMatrix()
        glTranslatef(1.8, 2.8, 0.0)
        glRotatef(angle, 0, 0, 1)
        self.draw_wing(1, angle, fold_angle)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-1.8, 2.8, 0.0)
        glRotatef(-angle, 0, 0, 1)
        self.draw_wing(-1, -angle, -fold_angle)
        glPopMatrix()


# --- Main Application Code ---
dragon = Dragon()


def create_fire_particle():
    # Fire now originates from the animated head's position
    head_pos = [0, 5.5 + math.sin(time.time()*2)
                * 0.1, 9.5 + math.cos(time.time()*2)*0.1]
    particle = {'pos': head_pos, 'vel': [random.uniform(-0.2, 0.2), random.uniform(0.1, 0.3), random.uniform(1.0, 1.5)],
                'life': 1.0, 'size': random.uniform(0.5, 0.8), 'color': [1.0, 1.0, 0.5, 0.9]}
    fire_particles.append(particle)


def update_fire_particles():
    global fire_particles
    for p in fire_particles:
        p['pos'][0] += p['vel'][0]
        p['pos'][1] += p['vel'][1]
        p['pos'][2] += p['vel'][2]
        p['vel'][1] -= 0.01
        p['life'] -= 0.015
        p['size'] *= 0.97
        p['color'][1] = max(0, p['color'][1] - 0.02)
        p['color'][3] = p['life'] * 0.9
    fire_particles = [p for p in fire_particles if p['life'] > 0]


def draw_fire():
    glDisable(GL_LIGHTING)
    glDepthMask(GL_FALSE)
    glBegin(GL_QUADS)
    for p in fire_particles:
        glColor4fv(p['color'])
        x, y, z = p['pos']
        s = p['size'] / 2
        glVertex3f(x - s, y - s, z)
        glVertex3f(x + s, y - s, z)
        glVertex3f(x + s, y + s, z)
        glVertex3f(x - s, y + s, z)
    glEnd()
    glDepthMask(GL_TRUE)
    glEnable(GL_LIGHTING)


def draw_ground():
    glDisable(GL_LIGHTING)
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_LINES)
    for i in range(-40, 41, 2):
        glVertex3f(i, -5, -40)
        glVertex3f(i, -5, 40)
    for i in range(-40, 41, 2):
        glVertex3f(-40, -5, i)
        glVertex3f(40, -5, i)
    glEnd()
    glEnable(GL_LIGHTING)


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glTranslatef(0.0, 0.0, camera_zoom)
    glRotatef(camera_rot_x, 1, 0, 0)
    glRotatef(camera_rot_y, 0, 1, 0)
    draw_ground()
    glPushMatrix()
    glTranslatef(0, -2, 0)
    dragon.draw(wing_angle, wing_fold_angle, time.time())
    if fire_particles:
        draw_fire()
    glPopMatrix()
    glutSwapBuffers()


def reshape(w, h):
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    if h == 0:
        h = 1
    gluPerspective(45, (w / h), 0.1, 200.0)


def idle():
    global wing_angle, wing_fold_angle, last_time
    current_time = time.time()
    if last_time == 0:
        last_time = current_time
    wing_angle = math.sin(current_time * 8) * 45
    wing_fold_angle = math.sin(current_time * 8 + math.pi/2) * 20
    if is_firing and len(fire_particles) < 150:
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
        camera_rot_x = max(-90, min(90, camera_rot_x))
        last_mouse_pos['x'] = x
        last_mouse_pos['y'] = y
        glutPostRedisplay()


def init():
    global last_time
    glClearColor(0.1, 0.0, 0.2, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glLightfv(GL_LIGHT0, GL_POSITION, [0, 20, -10, 1])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.7, 0.7, 0.7, 1.0])
    last_time = time.time()


def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1200, 800)
    glutCreateWindow(b"Perfected 3D Dragon")
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
