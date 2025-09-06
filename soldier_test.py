# -----------------------------------------------------------------------------
# 3D Warrior Prince Model using Python and PyOpenGL
# Author: Gemini
#
# Description:
# This script renders an animated 3D model of a warrior prince. The model can
# run, jump, and use special abilities based on keyboard and mouse input. The
# rendering is done using PyOpenGL and the GLUT library.
#
# Interaction:
# - W, A, S, D keys: Trigger running animation.
# - Spacebar: Trigger a jump.
# - 'E' key: Deploy a temporary energy shield with an animation.
# - Right Mouse Click: Fire a power blast from the sword with an animation.
# - Left Click and drag: Rotate the camera.
# -----------------------------------------------------------------------------

import sys
import math
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

# --- Global Variables for Camera Control and State ---
window_width = 1280
window_height = 720
last_mouse_x = 0
last_mouse_y = 0
is_mouse_down = False
camera_azimuth = 45.0
camera_elevation = 25.0
camera_distance = 15.0

# --- Animation and Physics State ---
is_running = False
is_jumping = False
y_velocity = 0.0
warrior_y_pos = 0.0
animation_timer = 0.0
GRAVITY = 0.025
JUMP_STRENGTH = 0.7
pressed_keys = set()

# --- Special Abilities State ---
is_shield_active = False
shield_alpha = 0.0
shield_timer = 0.0
SHIELD_DURATION = 120  # How long the shield effect lasts in frames
projectiles = []
PROJECTILE_SPEED = 0.4
PROJECTILE_LIFESPAN = 120  # How long projectiles last in frames

# --- Animation Timers for Abilities ---
blast_animation_timer = 0
shield_pose_timer = 0
BLAST_ANIMATION_DURATION = 30
SHIELD_POSE_DURATION = 40


# --- Utility Functions ---

def draw_cube(scale_x, scale_y, scale_z):
    """Draws a solid color cube, scaled to the given dimensions."""
    glPushMatrix()
    glScalef(scale_x, scale_y, scale_z)
    vertices = [[0.5,  0.5, -0.5], [0.5, -0.5, -0.5], [-0.5, -0.5, -0.5], [-0.5,  0.5, -0.5],
                [0.5,  0.5,  0.5], [0.5, -0.5,  0.5], [-0.5, -0.5,  0.5], [-0.5,  0.5,  0.5]]
    faces = [[0, 1, 2, 3], [3, 2, 6, 7], [7, 6, 5, 4],
             [4, 5, 1, 0], [0, 3, 7, 4], [1, 5, 6, 2]]
    glBegin(GL_QUADS)
    for face in faces:
        for vertex_index in face:
            glVertex3fv(vertices[vertex_index])
    glEnd()
    glPopMatrix()


# --- Model Component Drawing Functions ---

def draw_head():
    """Draws the warrior's head, including crown and facial features."""
    glPushMatrix()
    glTranslatef(0, 2.95, 0)
    glColor3f(0.9, 0.7, 0.55)
    draw_cube(1.5, 1.5, 1.5)
    glColor3f(0.2, 0.1, 0.05)
    glPushMatrix()
    glTranslatef(0, 0.5, 0)
    draw_cube(1.55, 1.0, 1.55)
    glPopMatrix()
    glColor3f(0.2, 0.5, 0.9)
    glPushMatrix()
    glTranslatef(-0.3, 0.1, -0.76)
    draw_cube(0.25, 0.25, 0.05)
    glTranslatef(0.6, 0, 0)
    draw_cube(0.25, 0.25, 0.05)
    glPopMatrix()
    glColor3f(1.0, 0.85, 0.1)
    glPushMatrix()
    glTranslatef(0, 0.9, 0)
    draw_cube(1.6, 0.3, 1.6)
    glColor3f(0.8, 0.1, 0.1)
    glTranslatef(0, 0.25, -0.8)
    draw_cube(0.2, 0.2, 0.2)
    glColor3f(1.0, 0.85, 0.1)
    glTranslatef(-0.5, 0.05, 0)
    draw_cube(0.1, 0.3, 0.1)
    glTranslatef(1.0, 0, 0)
    draw_cube(0.1, 0.3, 0.1)
    glPopMatrix()
    glPopMatrix()


def draw_arm(is_left=False, sword_func=None, shield_func=None, is_blasting=False):
    """Draws a complete arm, with an optional corrective rotation for animations."""
    glPushMatrix()
    glColor3f(0.7, 0.7, 0.8)
    draw_cube(1.1, 1.1, 1.1)
    glColor3f(0.2, 0.2, 0.6)
    glTranslatef(0, -1.25, 0)
    draw_cube(0.9, 1.5, 0.9)
    glTranslatef(0, -1.25, 0)
    glRotatef(15, 1, 0, 0)
    glColor3f(0.7, 0.7, 0.8)
    draw_cube(0.8, 1.5, 0.8)
    if is_left and shield_func:
        shield_func()
    glColor3f(0.9, 0.7, 0.55)
    glTranslatef(0, -0.9, 0)
    draw_cube(0.7, 0.5, 0.7)

    # --- FIX: Apply corrective rotation for sword during blast animation ---
    if not is_left and sword_func:
        glPushMatrix()
        if is_blasting:
            # The sword function rotates the sword -75 degrees on X (downward).
            # We apply a +75 degree rotation here to cancel that out,
            # making the sword point straight forward from the arm.
            glRotatef(-180, 1, 0, 0)
        sword_func()
        glPopMatrix()

    glPopMatrix()


def draw_leg():
    """Draws a complete leg, including thigh and shin."""
    glPushMatrix()
    glColor3f(0.3, 0.3, 0.35)
    draw_cube(1.2, 2.0, 1.2)
    glTranslatef(0, -2.0, 0)
    glRotatef(5, 1, 0, 0)
    glColor3f(0.15, 0.1, 0.05)
    draw_cube(1.1, 2.0, 1.1)
    glTranslatef(0, -1.0, -0.2)
    draw_cube(1.1, 0.3, 1.5)
    glPopMatrix()


def draw_weapons_and_shield():
    """Defines functions to draw the weapons with local, small-offset transformations."""
    def draw_sword():
        glPushMatrix()
        glTranslatef(0.0, -0.4, 0.1)
        glRotatef(-75, 1, 0, 0)
        glRotatef(-10, 0, 1, 0)
        glColor3f(0.3, 0.15, 0.05)
        draw_cube(0.2, 1.0, 0.2)
        glColor3f(0.7, 0.7, 0.8)
        glTranslatef(0, -0.5, 0)
        draw_cube(0.3, 0.2, 0.3)
        glTranslatef(0, 0.7, 0)
        draw_cube(0.8, 0.2, 0.2)
        glColor3f(0.85, 0.85, 0.9)
        glTranslatef(0, 2.0, 0)
        draw_cube(0.15, 3.0, 0.15)
        glTranslatef(0, 1.5, 0)
        glRotatef(45, 0, 0, 1)
        draw_cube(0.1, 0.4, 0.15)
        glPopMatrix()

    def draw_shield():
        glPushMatrix()
        glTranslatef(-0.5, 0.2, 0)
        glRotatef(-10, 1, 0, 0)
        glRotatef(15, 0, 0, 1)
        glColor3f(0.6, 0.6, 0.7)
        draw_cube(0.2, 2.2, 2.2)
        glColor3f(1.0, 0.85, 0.1)
        glTranslatef(-0.11, 0, 0)
        draw_cube(0.05, 1.5, 1.8)
        glTranslatef(0, 0, -0.7)
        draw_cube(0.05, 0.6, 0.3)
        glTranslatef(0, 0, 1.4)
        draw_cube(0.05, 0.6, 0.3)
        glPopMatrix()

    def draw_axe():
        glPushMatrix()
        glColor3f(0.5, 0.3, 0.1)
        draw_cube(0.2, 3.5, 0.2)
        glColor3f(0.6, 0.6, 0.7)
        glTranslatef(0, 1.5, 0)
        glRotatef(90, 0, 0, 1)
        draw_cube(1.5, 0.3, 0.3)
        glTranslatef(0, -0.8, 0)
        draw_cube(0.2, 0.2, 0.2)
        glPopMatrix()

    return draw_sword, draw_shield, draw_axe


def draw_energy_shield():
    """Draws a large, semi-transparent shield in front of the warrior."""
    if not is_shield_active:
        return

    glPushMatrix()
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glTranslatef(0, 0.5, -4.0)

    glColor4f(0.3, 0.7, 1.0, shield_alpha)
    draw_cube(7, 7, 0.3)

    glDisable(GL_BLEND)
    glPopMatrix()


def draw_projectiles():
    """Draws all active power blasts."""
    global projectiles
    glPushMatrix()
    for proj in projectiles:
        glPushMatrix()
        glTranslatef(proj['pos'][0], proj['pos'][1], proj['pos'][2])
        glColor3f(0.2, 1.0, 0.8)  # Bright cyan
        draw_cube(0.4, 0.4, 0.4)
        glPopMatrix()
    glPopMatrix()


# --- Main Drawing Function ---

def draw_warrior():
    """The main function to assemble and draw the entire warrior model."""
    draw_sword_func, draw_shield_func, draw_axe = draw_weapons_and_shield()
    run_angle = math.sin(animation_timer) * 40 if is_running else 0

    glPushMatrix()

    # --- Torso and Hips ---
    glPushMatrix()
    glColor3f(0.25, 0.25, 0.7)
    draw_cube(2.5, 3.0, 1.5)
    glPushMatrix()
    glTranslatef(0, 0.5, -0.76)
    glColor3f(1.0, 0.85, 0.1)
    draw_cube(2.0, 2.0, 0.1)
    glPopMatrix()
    glTranslatef(0, -1.5, 0)
    glColor3f(0.4, 0.2, 0.1)
    draw_cube(2.6, 0.4, 1.6)
    glTranslatef(0, -0.8, 0)
    glColor3f(0.3, 0.3, 0.35)
    draw_cube(2.0, 1.2, 1.2)
    glPopMatrix()

    # --- Head and Neck ---
    glPushMatrix()
    glTranslatef(0, 1.85, 0)
    glColor3f(0.9, 0.7, 0.55)
    draw_cube(0.7, 0.7, 0.7)
    glPopMatrix()
    draw_head()

    # --- Right Arm (Sword Arm) ---
    glPushMatrix()
    glTranslatef(-1.7, 1.0, 0)

    # Check if the blast animation is active
    is_blasting_pose = blast_animation_timer > 0

    if is_blasting_pose:  # Firing blast pose
        # Your rotation to bring the arm to the front
        glRotatef(-180, 0, 1, 0)
        # Lift the arm up
        glRotatef(-70, 1, 0, 0)
    elif is_running:  # Running pose
        glRotatef(run_angle, 1, 0, 0)
    else:  # New idle pose
        glRotatef(20, 1, 0, 0)
        glRotatef(15, 0, 0, 1)

    # Pass the is_blasting_pose flag to the draw_arm function
    draw_arm(is_left=False, sword_func=draw_sword_func,
             is_blasting=is_blasting_pose)
    glPopMatrix()

    # --- Left Arm (Shield Arm) ---
    glPushMatrix()
    glTranslatef(1.7, 1.0, 0)
    if shield_pose_timer > 0:  # Shielding pose
        glRotatef(60, 1, 0, 0)
        glRotatef(-80, 0, 1, 0)
        glRotatef(-20, 0, 0, 1)
    elif is_running:  # Running pose
        glRotatef(-run_angle, 1, 0, 0)
    else:  # New idle pose
        glRotatef(20, 1, 0, 0)
        glRotatef(-15, 0, 0, 1)
    draw_arm(is_left=True, shield_func=draw_shield_func)
    glPopMatrix()

    # --- Legs ---
    glPushMatrix()
    glTranslatef(0.7, -2.8, 0)
    if is_running:
        glRotatef(-run_angle, 1, 0, 0)
    else:
        glRotatef(-10, 1, 0, 0)
        glRotatef(5, 0, 0, 1)
    draw_leg()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-0.7, -2.8, 0)
    if is_running:
        glRotatef(run_angle, 1, 0, 0)
    else:
        glRotatef(15, 1, 0, 0)
        glRotatef(-5, 0, 0, 1)
    draw_leg()
    glPopMatrix()

    # --- Axe on back ---
    glPushMatrix()
    glTranslatef(0.5, 1.0, 0.8)
    glRotatef(25, 1, 0, 0)
    glRotatef(20, 0, 1, 0)
    glRotatef(20, 0, 0, 1)
    glScalef(0.8, 0.8, 0.8)
    draw_axe()
    glPopMatrix()

    # --- Draw Abilities ---
    draw_energy_shield()

    glPopMatrix()


# --- OpenGL Callback Functions ---

def display():
    """The main display callback."""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    glTranslatef(0.0, 0.0, -camera_distance)
    glRotatef(camera_elevation, 1.0, 0.0, 0.0)
    glRotatef(camera_azimuth, 0.0, 1.0, 0.0)

    draw_projectiles()  # Draw projectiles in world space

    glTranslatef(0.0, -2.0 + warrior_y_pos, 0.0)
    draw_warrior()

    glutSwapBuffers()


def reshape(width, height):
    """Called when the window is resized."""
    global window_width, window_height
    window_width = width
    window_height = height
    if height == 0:
        height = 1
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, float(width) / height, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()


def mouse(button, state, x, y):
    """Called for mouse button events."""
    global is_mouse_down, last_mouse_x, last_mouse_y, projectiles, blast_animation_timer
    if button == GLUT_LEFT_BUTTON:
        is_mouse_down = (state == GLUT_DOWN)
        last_mouse_x, last_mouse_y = x, y
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        blast_animation_timer = BLAST_ANIMATION_DURATION

        # --- NEW FIX BASED ON YOUR EXAMPLE ---
        # 1. Get the camera's angles (just like gun_angle in your code)
        azimuth_rad = math.radians(camera_azimuth)
        elevation_rad = math.radians(camera_elevation)

        # 2. Calculate the 3D direction vector using sin/cos
        # This is the 3D equivalent of your 2D direction calculation
        dir_x = -math.sin(azimuth_rad) * math.cos(elevation_rad)
        dir_y = math.sin(elevation_rad)
        dir_z = -math.cos(azimuth_rad) * math.cos(elevation_rad)
        
        # 3. Define a clean starting position at the warrior's chest
        start_pos = [0, 1.5 + warrior_y_pos, 0]

        # 4. Create the projectile with the calculated position and direction
        projectiles.append({
            'pos': start_pos,
            'vel': [dir_x * PROJECTILE_SPEED, dir_y * PROJECTILE_SPEED, dir_z * PROJECTILE_SPEED],
            'life': PROJECTILE_LIFESPAN
        })
        # --- END OF FIX ---


def motion(x, y):
    """Called when the mouse moves with a button pressed."""
    global camera_azimuth, camera_elevation, last_mouse_x, last_mouse_y
    if is_mouse_down:
        dx, dy = x - last_mouse_x, y - last_mouse_y
        camera_azimuth += dx * 0.25
        camera_elevation += dy * 0.25
        camera_elevation = max(-80.0, min(80.0, camera_elevation))
        last_mouse_x, last_mouse_y = x, y
        glutPostRedisplay()


def keyboard(key, x, y):
    """Called for key press events."""
    global is_jumping, y_velocity, is_running, is_shield_active, shield_timer, shield_pose_timer
    key_lower = key.lower()

    if key_lower == b' ' and not is_jumping:
        is_jumping = True
        y_velocity = JUMP_STRENGTH
    elif key_lower in b'wasd':
        is_running = True
        pressed_keys.add(key_lower)
    elif key_lower == b'e' and not is_shield_active:
        is_shield_active = True
        shield_timer = SHIELD_DURATION
        shield_pose_timer = SHIELD_POSE_DURATION


def keyboard_up(key, x, y):
    """Called for key release events."""
    global is_running
    key_lower = key.lower()
    if key_lower in pressed_keys:
        pressed_keys.remove(key_lower)
    if not pressed_keys:
        is_running = False


def idle():
    """The main animation loop, called when no other events are happening."""
    global animation_timer, warrior_y_pos, y_velocity, is_jumping, shield_timer, is_shield_active, shield_alpha, projectiles
    global blast_animation_timer, shield_pose_timer

    if is_running:
        animation_timer += 0.15

    if is_jumping:
        warrior_y_pos += y_velocity
        y_velocity -= GRAVITY
        if warrior_y_pos < 0.0:
            is_jumping = False
            warrior_y_pos = 0.0
            y_velocity = 0.0

    if blast_animation_timer > 0:
        blast_animation_timer -= 1
    if shield_pose_timer > 0:
        shield_pose_timer -= 1

    if is_shield_active:
        shield_timer -= 1
        fade_speed = 0.05
        if shield_timer > SHIELD_DURATION * 0.8:
            shield_alpha = min(0.6, shield_alpha + fade_speed)
        elif shield_timer < SHIELD_DURATION * 0.3:
            shield_alpha = max(0.0, shield_alpha - fade_speed)
        else:
            shield_alpha = 0.6

        if shield_timer <= 0:
            is_shield_active = False

    updated_projectiles = []
    for proj in projectiles:
        proj['pos'][0] += proj['vel'][0]
        proj['pos'][1] += proj['vel'][1]
        proj['pos'][2] += proj['vel'][2]
        proj['life'] -= 1
        if proj['life'] > 0:
            updated_projectiles.append(proj)
    projectiles = updated_projectiles

    glutPostRedisplay()

# --- Main Program Execution ---


def main():
    """Initializes GLUT and enters the main loop."""
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(window_width, window_height)
    glutCreateWindow(b"3D Warrior Prince Model")

    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_FLAT)
    glClearColor(0.1, 0.12, 0.15, 1.0)

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutIdleFunc(idle)

    print("Controls:")
    print("  W, A, S, D: Run")
    print("  Spacebar: Jump")
    print("  'E' key: Deploy Energy Shield")
    print("  Right Mouse Click: Fire Power Blast")
    print("  Left Mouse Drag: Rotate Camera")

    glutMainLoop()


if __name__ == "__main__":
    main()