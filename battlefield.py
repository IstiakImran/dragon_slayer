import sys
import math
import random
import time

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    from OpenGL.GLUT import *
except ImportError:
    print("PyOpenGL and GLUT are required to run this program.")
    print("Please install them with: pip install PyOpenGL PyOpenGL_accelerate")
    print("On some systems, you may also need to install FreeGLUT (e.g., 'sudo apt-get install freeglut3-dev' on Debian/Ubuntu).")
    sys.exit(1)

# --- Constants ---
WINDOW_WIDTH, WINDOW_HEIGHT = 1200, 800
WORLD_SIZE = 100
CULLING_DISTANCE = 100.0
WALL_BLOCK_SIZE = 1.5
TREE_COLLISION_SIZE = 1.0  # For collision with tree trunks
SHRUB_COLLISION_SIZE = 2.0  # For collision with shrubs
SKY_COLOR = (0.5, 0.7, 1.0, 1.0)

# --- Gameplay Constants ---
NUM_BOMBS = 5  # Number of active bombs in the world
BOMB_TRIGGER_RADIUS = 5.0
BOMB_FUSE_TIME = 1.0  # Shortened fuse time
BOMB_EXPLOSION_DURATION = 1.5
BOMB_EXPLOSION_MAX_RADIUS = 15.0
WALL_SPAWN_CHANCE = 0.40  # Increased chance
WALL_SPAWN_INTERVAL = 5.0  # More frequent checks
WALL_SPAWN_DISTANCE = 10.0
WALL_LIFETIME = 8.0

# --- Global State Variables ---
camera = None
keys = {b'w': False, b's': False, b'a': False,
        b'd': False, b' ': False, b'shift': False}
last_mouse_pos = {'x': 0, 'y': 0}
is_mouse_warping = False
object_positions = {}
bombs = []  # Changed to a list to hold multiple bombs
game_state = {}


# --- Display List Handles ---
LIST_IDS = {
    'tree': 1,
    'rock': 2,
    'wall': 3,
    'shrub': 4
}


# --- Camera Class (Unchanged) ---
class Camera:
    def __init__(self, position=(0, 5, 10), rotation=(0, 0)):
        self.position = list(position)
        self.rotation = list(rotation)
        self.speed = 0.2
        self.sensitivity = 0.15
        self.player_radius = 0.5

    def is_colliding(self, next_pos):
        collidable_types = {
            'boundary_walls': WALL_BLOCK_SIZE,
            'random_walls': WALL_BLOCK_SIZE,
            'trees': TREE_COLLISION_SIZE,
            'shrubs': SHRUB_COLLISION_SIZE,
            'temp_walls': WALL_BLOCK_SIZE
        }

        for obj_key, obj_size in collidable_types.items():
            # Handle temp walls which have a different data structure
            positions = object_positions.get(obj_key, [])
            if obj_key == 'temp_walls':
                positions = [item['pos'] for item in positions]

            for obj_pos in positions:
                player_min_x = next_pos[0] - self.player_radius
                player_max_x = next_pos[0] + self.player_radius
                player_min_z = next_pos[2] - self.player_radius
                player_max_z = next_pos[2] + self.player_radius

                obj_min_x = obj_pos[0] - obj_size / 2
                obj_max_x = obj_pos[0] + obj_size / 2
                obj_min_z = obj_pos[2] - obj_size / 2
                obj_max_z = obj_pos[2] + obj_size / 2

                if (player_max_x > obj_min_x and player_min_x < obj_max_x and
                        player_max_z > obj_min_z and player_min_z < obj_max_z):
                    return True
        return False

    def update(self):
        yaw_rad = math.radians(self.rotation[0])
        forward_vec = [math.sin(yaw_rad), 0, -math.cos(yaw_rad)]
        strafe_vec = [math.cos(yaw_rad), 0, math.sin(yaw_rad)]

        move_vec = [0, 0, 0]
        if keys[b'w']:
            move_vec[0] += forward_vec[0]
            move_vec[2] += forward_vec[2]
        if keys[b's']:
            move_vec[0] -= forward_vec[0]
            move_vec[2] -= forward_vec[2]
        if keys[b'a']:
            move_vec[0] -= strafe_vec[0]
            move_vec[2] -= strafe_vec[2]
        if keys[b'd']:
            move_vec[0] += strafe_vec[0]
            move_vec[2] += strafe_vec[2]

        magnitude = math.sqrt(move_vec[0]**2 + move_vec[2]**2)
        if magnitude > 0:
            move_vec[0] = (move_vec[0] / magnitude) * self.speed
            move_vec[2] = (move_vec[2] / magnitude) * self.speed

        if keys[b' ']:
            self.position[1] += self.speed
        if keys[b'shift']:
            self.position[1] -= self.speed

        next_pos_x = [self.position[0] + move_vec[0],
                      self.position[1], self.position[2]]
        if not self.is_colliding(next_pos_x):
            self.position[0] += move_vec[0]

        next_pos_z = [self.position[0], self.position[1],
                      self.position[2] + move_vec[2]]
        if not self.is_colliding(next_pos_z):
            self.position[2] += move_vec[2]

        if self.position[1] < 1.8:
            self.position[1] = 1.8

    def handle_mouse(self, x, y):
        global is_mouse_warping, last_mouse_pos
        if is_mouse_warping:
            is_mouse_warping = False
            last_mouse_pos['x'], last_mouse_pos['y'] = x, y
            return

        dx = x - last_mouse_pos['x']
        dy = y - last_mouse_pos['y']
        self.rotation[0] += dx * self.sensitivity
        self.rotation[1] = max(-89.0, min(89.0,
                               self.rotation[1] - dy * self.sensitivity))

        center_x, center_y = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
        if abs(x - center_x) > 200 or abs(y - center_y) > 200:
            is_mouse_warping = True
            glutWarpPointer(center_x, center_y)
        else:
            last_mouse_pos['x'], last_mouse_pos['y'] = x, y

    def look(self):
        glLoadIdentity()
        pitch_rad = math.radians(self.rotation[1])
        yaw_rad = math.radians(self.rotation[0])
        look_at_point = [
            self.position[0] + math.sin(yaw_rad) * math.cos(pitch_rad),
            self.position[1] + math.sin(pitch_rad),
            self.position[2] - math.cos(yaw_rad) * math.cos(pitch_rad)
        ]
        gluLookAt(self.position[0], self.position[1], self.position[2],
                  look_at_point[0], look_at_point[1], look_at_point[2], 0, 1, 0)


# --- Drawing Functions ---
def draw_cube(size, colors):
    s = size / 2.0
    vertices = [[-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s],
                [-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s]]
    faces = [(0, 1, 2, 3), (1, 5, 6, 2), (5, 4, 7, 6),
             (4, 0, 3, 7), (3, 2, 6, 7), (4, 5, 1, 0)]
    glBegin(GL_QUADS)
    for i, face in enumerate(faces):
        glColor3fv(colors[i % len(colors)])
        for v_idx in face:
            glVertex3fv(vertices[v_idx])
    glEnd()


def draw_tree_geometry():
    glPushMatrix()
    trunk_color = [(0.4, 0.2, 0.0)] * 6
    trunk_size = 1.0
    draw_cube(trunk_size, trunk_color)
    glTranslatef(0, trunk_size, 0)
    draw_cube(trunk_size, trunk_color)
    glTranslatef(0, trunk_size, 0)
    draw_cube(trunk_size, trunk_color)
    glTranslatef(0, trunk_size, 0)
    draw_cube(trunk_size, trunk_color)
    glTranslatef(0, trunk_size, 0)
    draw_cube(trunk_size, trunk_color)
    leaf_colors = [(0.0, 0.5, 0.0), (0.0, 0.6, 0.0)]
    glTranslatef(0, 2, 0)
    draw_cube(4, leaf_colors)
    glTranslatef(1.5, -1, 0)
    draw_cube(2.5, leaf_colors)
    glTranslatef(-1.5, 1, 0)
    glTranslatef(-1.5, -1, 0)
    draw_cube(2.5, leaf_colors)
    glTranslatef(1.5, 1, 0)
    glTranslatef(0, -1, 1.5)
    draw_cube(2.5, leaf_colors)
    glTranslatef(0, 1, -1.5)
    glTranslatef(0, -1, -1.5)
    draw_cube(2.5, leaf_colors)
    glPopMatrix()


def draw_wall_geometry():
    glPushMatrix()
    wall_colors = [(0.6, 0.6, 0.6), (0.55, 0.55, 0.55)]
    draw_cube(WALL_BLOCK_SIZE, wall_colors)
    glTranslatef(0, WALL_BLOCK_SIZE, 0)
    draw_cube(WALL_BLOCK_SIZE, wall_colors)
    glPopMatrix()


def draw_shrub_geometry():
    glPushMatrix()
    leaf_colors = [(0.1, 0.4, 0.1), (0.1, 0.5, 0.1)]
    draw_cube(2.0, leaf_colors)
    glTranslatef(0.75, -0.5, 0)
    draw_cube(1.5, leaf_colors)
    glTranslatef(-0.75, 0.5, 0)
    glTranslatef(-0.75, -0.5, 0)
    draw_cube(1.5, leaf_colors)
    glTranslatef(0.75, 0.5, 0)
    glTranslatef(0, -0.5, 0.75)
    draw_cube(1.5, leaf_colors)
    glTranslatef(0, 0.5, -0.75)
    glTranslatef(0, -0.5, -0.75)
    draw_cube(1.5, leaf_colors)
    glPopMatrix()


def draw_ground():
    glColor3f(0.1, 0.6, 0.1)
    glBegin(GL_QUADS)
    glVertex3f(-WORLD_SIZE, 0, -WORLD_SIZE)
    glVertex3f(-WORLD_SIZE, 0, WORLD_SIZE)
    glVertex3f(WORLD_SIZE, 0, WORLD_SIZE)
    glVertex3f(WORLD_SIZE, 0, -WORLD_SIZE)
    glEnd()

# --- Gameplay and Scene Logic ---


def spawn_bomb():
    global bombs
    new_bomb = {
        'position': [random.uniform(-WORLD_SIZE, WORLD_SIZE), 0.5, random.uniform(-WORLD_SIZE, WORLD_SIZE)],
        'state': 'idle',  # idle, triggered, exploding
        'triggered_time': 0,
        'explosion_start_time': 0
    }
    bombs.append(new_bomb)


def spawn_blocking_wall():
    global object_positions
    yaw_rad = math.radians(camera.rotation[0])
    forward_vec = [math.sin(yaw_rad), 0, -math.cos(yaw_rad)]
    strafe_vec = [math.cos(yaw_rad), 0, math.sin(yaw_rad)]

    # Calculate center position for the 3-segment wall
    center_pos = [
        camera.position[0] + forward_vec[0] * WALL_SPAWN_DISTANCE,
        0,
        camera.position[2] + forward_vec[2] * WALL_SPAWN_DISTANCE
    ]

    # Spawn three wall segments to make a 'big wall'
    for i in range(-1, 2):  # -1 for left, 0 for center, 1 for right
        wall_pos = [
            center_pos[0] + strafe_vec[0] * i * WALL_BLOCK_SIZE,
            center_pos[1],
            center_pos[2] + strafe_vec[2] * i * WALL_BLOCK_SIZE
        ]
        object_positions['temp_walls'].append({
            'pos': wall_pos,
            'despawn_time': time.time() + WALL_LIFETIME
        })
    print("A big wall appears!")


def update_game_logic():
    global bombs, object_positions, game_state
    current_time = time.time()

    # --- Bomb Logic ---
    # Iterate over a copy of the list to allow safe removal
    for bomb in bombs[:]:
        if bomb.get('state') == 'idle':
            dist_sq = (bomb['position'][0] - camera.position[0]
                       )**2 + (bomb['position'][2] - camera.position[2])**2
            if dist_sq < BOMB_TRIGGER_RADIUS**2:
                bomb['state'] = 'triggered'
                bomb['triggered_time'] = current_time
                print("Bomb triggered! Get away!")

        elif bomb.get('state') == 'triggered':
            if current_time > bomb['triggered_time'] + BOMB_FUSE_TIME:
                bomb['state'] = 'exploding'
                bomb['explosion_start_time'] = current_time
                dist_sq = (bomb['position'][0] - camera.position[0]
                           )**2 + (bomb['position'][2] - camera.position[2])**2
                if dist_sq < BOMB_EXPLOSION_MAX_RADIUS**2:
                    print("You were caught in the blast!")
                else:
                    print("Phew, safe distance.")

        elif bomb.get('state') == 'exploding':
            if current_time > bomb['explosion_start_time'] + BOMB_EXPLOSION_DURATION:
                # Remove the exploded bomb and spawn a new one to replace it
                bombs.remove(bomb)
                spawn_bomb()

    # --- Wall Logic ---
    # Remove old walls
    object_positions['temp_walls'] = [
        w for w in object_positions['temp_walls'] if current_time < w['despawn_time']]

    # Check to spawn a new wall
    if current_time > game_state.get('last_wall_check', 0) + WALL_SPAWN_INTERVAL:
        game_state['last_wall_check'] = current_time
        # Removed the check for existing walls to make them more frequent
        if random.random() < WALL_SPAWN_CHANCE:
            spawn_blocking_wall()


def compile_display_lists():
    glNewList(LIST_IDS['tree'], GL_COMPILE)
    draw_tree_geometry()
    glEndList()
    glNewList(LIST_IDS['wall'], GL_COMPILE)
    draw_wall_geometry()
    glEndList()
    glNewList(LIST_IDS['rock'], GL_COMPILE)
    draw_cube(1, [(0.5, 0.5, 0.5)])
    glEndList()
    glNewList(LIST_IDS['shrub'], GL_COMPILE)
    draw_shrub_geometry()
    glEndList()
    print("Display lists compiled.")


def generate_world():
    global object_positions
    wall_spacing = WALL_BLOCK_SIZE
    num_boundary_walls = int(WORLD_SIZE * 2 / wall_spacing)
    object_positions = {
        'trees': [(random.uniform(-WORLD_SIZE, WORLD_SIZE), 0, random.uniform(-WORLD_SIZE, WORLD_SIZE)) for _ in range(150)],
        'rocks': [(random.uniform(-WORLD_SIZE, WORLD_SIZE), 0.5, random.uniform(-WORLD_SIZE, WORLD_SIZE)) for _ in range(70)],
        'shrubs': [(random.uniform(-WORLD_SIZE, WORLD_SIZE), 1, random.uniform(-WORLD_SIZE, WORLD_SIZE)) for _ in range(800)],
        'random_walls': [(random.randint(-WORLD_SIZE, WORLD_SIZE), 0, random.randint(-WORLD_SIZE, WORLD_SIZE)) for _ in range(30)],
        'boundary_walls': (
            [(i * wall_spacing - WORLD_SIZE, 0, -WORLD_SIZE) for i in range(num_boundary_walls + 1)] +
            [(i * wall_spacing - WORLD_SIZE, 0, WORLD_SIZE) for i in range(num_boundary_walls + 1)] +
            [(-WORLD_SIZE, 0, i * wall_spacing - WORLD_SIZE) for i in range(num_boundary_walls + 1)] +
            [(WORLD_SIZE, 0, i * wall_spacing - WORLD_SIZE)
             for i in range(num_boundary_walls + 1)]
        ),
        'temp_walls': []  # Initialize list for dynamic walls
    }


def setup_opengl():
    glClearColor(*SKY_COLOR)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)
    glShadeModel(GL_SMOOTH)

# --- GLUT Callbacks ---


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    camera.look()

    draw_ground()

    # --- Draw static and dynamic objects ---
    culling_dist_sq = CULLING_DISTANCE * CULLING_DISTANCE
    cam_pos = camera.position
    object_map = [
        ('trees', LIST_IDS['tree']), ('rocks', LIST_IDS['rock']),
        ('shrubs', LIST_IDS['shrub']), ('random_walls', LIST_IDS['wall']),
        ('boundary_walls', LIST_IDS['wall'])
    ]
    for key, list_id in object_map:
        for pos in object_positions[key]:
            dist_sq = (pos[0] - cam_pos[0])**2 + (pos[2] - cam_pos[2])**2
            if dist_sq < culling_dist_sq:
                glPushMatrix()
                glTranslatef(pos[0], pos[1], pos[2])
                glCallList(list_id)
                glPopMatrix()

    # Draw temp walls separately as they are not in the map
    for wall in object_positions['temp_walls']:
        pos = wall['pos']
        dist_sq = (pos[0] - cam_pos[0])**2 + (pos[2] - cam_pos[2])**2
        if dist_sq < culling_dist_sq:
            glPushMatrix()
            glTranslatef(pos[0], pos[1], pos[2])
            glCallList(LIST_IDS['wall'])
            glPopMatrix()

    # --- Draw bombs and explosions ---
    for bomb in bombs:
        if bomb.get('state') in ['idle', 'triggered']:
            glPushMatrix()
            glTranslatef(*bomb['position'])
            if bomb['state'] == 'triggered' and int(time.time() * 10) % 2 == 0:
                glColor3f(1, 0, 0)  # Flashing red
            else:
                glColor3f(0.8, 0.8, 0)  # Yellow
            glutSolidSphere(0.5, 16, 16)
            glPopMatrix()
        elif bomb.get('state') == 'exploding':
            progress = (
                time.time() - bomb['explosion_start_time']) / BOMB_EXPLOSION_DURATION
            radius = progress * BOMB_EXPLOSION_MAX_RADIUS
            alpha = 0.8 * (1.0 - progress)  # Fade out
            glPushMatrix()
            glTranslatef(*bomb['position'])
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glColor4f(1.0, 0.5, 0.0, alpha)
            glutSolidSphere(radius, 32, 32)
            glDisable(GL_BLEND)
            glPopMatrix()

    glutSwapBuffers()


def keyboard(key, x, y):
    if key == b'\x1b':
        sys.exit()
    if key == b'1':
        camera.sensitivity = max(0.05, camera.sensitivity - 0.01)
        print(f"Sensitivity decreased to {camera.sensitivity:.2f}")
    if key == b'2':
        camera.sensitivity += 0.01
        print(f"Sensitivity increased to {camera.sensitivity:.2f}")

    if glutGetModifiers() & GLUT_ACTIVE_SHIFT:
        keys[b'shift'] = True
    else:
        keys[b'shift'] = False
        if key.lower() in keys:
            keys[key.lower()] = True


def keyboard_up(key, x, y):
    if not (glutGetModifiers() & GLUT_ACTIVE_SHIFT):
        keys[b'shift'] = False
    if key.lower() in keys:
        keys[key.lower()] = False


def mouse_motion(x, y): camera.handle_mouse(x, y)


def idle():
    update_game_logic()
    camera.update()
    glutPostRedisplay()


def reshape(width, height):
    global WINDOW_WIDTH, WINDOW_HEIGHT
    WINDOW_WIDTH, WINDOW_HEIGHT = width, height
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(55, (width / max(1, height)), 0.1, 500.0)
    glMatrixMode(GL_MODELVIEW)

# --- Main Application ---


def main():
    global camera, last_mouse_pos, game_state
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutCreateWindow(b"OpenGL Dynamic Battleground")

    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutPassiveMotionFunc(mouse_motion)
    glutIdleFunc(idle)

    setup_opengl()
    generate_world()
    compile_display_lists()

    # Initialize game state
    game_state = {'last_wall_check': time.time()}
    # Spawn the initial set of bombs
    for _ in range(NUM_BOMBS):
        spawn_bomb()

    glutSetCursor(GLUT_CURSOR_NONE)
    center_x, center_y = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
    glutWarpPointer(center_x, center_y)

    camera = Camera(position=(0, 2, 5))
    last_mouse_pos = {'x': center_x, 'y': center_y}

    print("Dynamic Battleground loaded.")
    print("Watch out for hidden bombs and sudden walls!")
    print("Controls: 1/2 for sensitivity, WASD to move, Mouse to look, Space/Shift for up/down, ESC to exit.")
    glutMainLoop()


if __name__ == "__main__":
    main()
