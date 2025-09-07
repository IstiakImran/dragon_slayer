from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import time
import math

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
GRID_LENGTH = 1000
GAME_TITLE = b"Dragon Slayer's Arena"

camera_angle_y = 0.0
camera_height = 250.0
camera_distance = 1800.0

is_day = True
last_time_cycle_change = time.time()
day_night_duration = 60
start_time = 0.0

last_small_stone_spawn = time.time()
small_stone_interval = 3.0

class Particle:
    def __init__(self, origin_position):
        self.origin = list(origin_position)
        self.position = list(origin_position)
        self.velocity = [random.uniform(-0.5, 0.5), random.uniform(2, 4), random.uniform(-0.5, 0.5)]
        self.life = 1.0
        self.decay_rate = random.uniform(0.01, 0.03)
        
    def update(self):
        self.position[0] += self.velocity[0]
        self.position[1] += self.velocity[1]
        self.position[2] += self.velocity[2]
        self.velocity[1] -= 0.05
        self.life -= self.decay_rate
        return self.life > 0

class FireParticleSystem:
    def __init__(self, origin_position, particle_count):
        self.origin = origin_position
        self.particles = []
        self.particle_count = particle_count

    def update(self):
        self.particles = [particle for particle in self.particles if particle.update()]
        while len(self.particles) < self.particle_count:
            self.particles.append(Particle(self.origin))

small_stones = []
stars = []
birds = []
near_hills = []
far_hills = []
boundary_objects = []
fire_systems = []
ground_clutter = []
tree_rock_bunch = []

def generate_hill_mesh(center_x, center_z, radius, max_height, segments):
    vertices = []
    for i in range(segments + 1):
        row = []
        for j in range(segments + 1):
            x_position = center_x + (i - segments / 2) * (2 * radius / segments)
            z_position = center_z + (j - segments / 2) * (2 * radius / segments)
            distance_from_center = math.sqrt((x_position - center_x)**2 + (z_position - center_z)**2)
            y_position = max_height * (1 - (distance_from_center / radius)**2) if distance_from_center < radius else 0
            row.append((x_position, y_position, z_position))
        vertices.append(row)
    return vertices

def initialize_environment():
    global stars, near_hills, far_hills, birds, boundary_objects, fire_systems, ground_clutter, tree_rock_bunch
    stars = [(random.uniform(-8000, 8000), random.uniform(1000, 4000), random.uniform(-8000, 8000)) for _ in range(300)]
    
    for _ in range(60):
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(5000, 8000)
        center_x = math.cos(angle) * distance
        center_z = math.sin(angle) * distance
        mesh = generate_hill_mesh(center_x, center_z, random.uniform(800, 1500), random.uniform(700, 1200), 20)
        far_hills.append({'mesh': mesh, 'color': (0.6, 0.6, 0.6)})

    for _ in range(30):
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(2500, 4500)
        center_x = math.cos(angle) * distance
        center_z = math.sin(angle) * distance
        mesh = generate_hill_mesh(center_x, center_z, random.uniform(500, 1000), random.uniform(400, 800), 20)
        near_hills.append({'mesh': mesh, 'color': (0.45, 0.45, 0.45)})

    birds = [[random.uniform(-3000, 3000), random.uniform(700, 900), random.uniform(-3000, -2000), random.uniform(1.0, 2.0)] for _ in range(25)]
    
    density = 80
    possible_positions = []
    for i in range(-GRID_LENGTH, GRID_LENGTH + 1, density):
        possible_positions.extend([(i, -GRID_LENGTH), (i, GRID_LENGTH)])
    for i in range(-GRID_LENGTH + density, GRID_LENGTH, density):
        possible_positions.extend([(-GRID_LENGTH, i), (GRID_LENGTH, i)])
    random.shuffle(possible_positions)
    
    for i in range(12):
        position = possible_positions.pop()
        size = 'medium' if i < 6 else 'small'
        boundary_objects.append(('stone', size, position[0], position[1]))
    for position in possible_positions:
        size = 'tall' if random.random() > 0.5 else 'short'
        boundary_objects.append(('tree', size, position[0], position[1]))

    fire_systems.append(FireParticleSystem((GRID_LENGTH - 150, 40, -GRID_LENGTH + 150), 50))
    fire_systems.append(FireParticleSystem((-GRID_LENGTH + 150, 10, -GRID_LENGTH + 150), 75))
    for _ in range(6):
        x_position = random.uniform(-GRID_LENGTH / 1.5, GRID_LENGTH / 1.5)
        z_position = random.uniform(-GRID_LENGTH / 1.5, GRID_LENGTH / 1.5)
        fire_systems.append(FireParticleSystem((x_position, 10, z_position), 30))
        
    for _ in range(50):
        x_position = random.uniform(-GRID_LENGTH, GRID_LENGTH)
        z_position = random.uniform(-GRID_LENGTH, GRID_LENGTH)
        ground_clutter.append(('flat_stone', x_position, z_position))

    for _ in range(15):
        x_position = GRID_LENGTH - 250 + random.uniform(-50, 50)
        z_position = GRID_LENGTH - 250 + random.uniform(-50, 50)
        rotation = random.uniform(0, 360)
        tree_rock_bunch.append((x_position, z_position, rotation))

def draw_text_on_screen(x_position, y_position, text_to_draw, font_style=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1.0, 1.0, 1.0)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x_position, y_position)
    for character in text_to_draw:
        glutBitmapCharacter(font_style, ord(character))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_arena_grid():
    grid_square_size = 50
    number_of_squares = GRID_LENGTH // grid_square_size
    for i in range(-number_of_squares, number_of_squares):
        for j in range(-number_of_squares, number_of_squares):
            if (i + j) % 2 == 0:
                glColor3f(0.45, 0.42, 0.38)
            else:
                glColor3f(0.4, 0.37, 0.33)
            glBegin(GL_QUADS)
            glVertex3f(i * grid_square_size, 0, j * grid_square_size)
            glVertex3f((i + 1) * grid_square_size, 0, j * grid_square_size)
            glVertex3f((i + 1) * grid_square_size, 0, (j + 1) * grid_square_size)
            glVertex3f(i * grid_square_size, 0, (j + 1) * grid_square_size)
            glEnd()

def draw_hill_from_mesh(hill_data):
    glColor3f(*hill_data['color'])
    mesh = hill_data['mesh']
    for i in range(len(mesh) - 1):
        glBegin(GL_QUAD_STRIP)
        for j in range(len(mesh[i])): 
            glVertex3f(*mesh[i][j])
            glVertex3f(*mesh[i+1][j])
        glEnd()

def draw_environment():
    if is_day: 
        glClearColor(0.6, 0.65, 0.7, 1.0)
        glColor3f(1.0, 1.0, 0.0)
        glPushMatrix()
        glTranslatef(-4500, 2500, -6000)
        glutSolidSphere(400, 30, 30)
        glPopMatrix()
    else:
        glClearColor(0.0, 0.05, 0.15, 1.0)
        glColor3f(0.9, 0.9, 0.9)
        glPushMatrix()
        glTranslatef(4500, 2500, -6000)
        glutSolidSphere(250, 30, 30)
        glPopMatrix()
        glPointSize(2)
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_POINTS)
        for star_position in stars:
            glVertex3f(*star_position)
        glEnd()

    for hill in far_hills:
        draw_hill_from_mesh(hill)
    for hill in near_hills:
        draw_hill_from_mesh(hill)

    if is_day: 
        glColor3f(0.1, 0.1, 0.1)
        for bird in birds:
            glPushMatrix()
            glTranslatef(*bird[:3])
            glScalef(1.5, 0.2, 1)
            glutSolidSphere(10, 5, 5)
            glPopMatrix()

def draw_tree(x_position, z_position, size='tall'):
    is_tall = (size == 'tall')
    trunk_height = 120 if is_tall else 70
    trunk_radius = 15 if is_tall else 12
    leaves_y_position = 120 if is_tall else 70
    leaves_radius = 50 if is_tall else 40
    
    glColor3f(0.5, 0.35, 0.05)
    glPushMatrix()
    glTranslatef(x_position, 0, z_position)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), trunk_radius, trunk_radius * 0.7, trunk_height, 8, 2)
    glPopMatrix()
    
    glColor3f(0.0, 0.4, 0.0)
    glPushMatrix()
    glTranslatef(x_position, leaves_y_position, z_position)
    glutSolidSphere(leaves_radius, 8, 6)
    glPopMatrix()

def draw_stone(x_position, z_position, size='medium', shape='sphere'):
    radius = 35 if size == 'medium' else 25
    glColor3f(0.45, 0.45, 0.45)
    glPushMatrix()
    glTranslatef(x_position, radius * 0.5, z_position)
    if shape == 'oval':
        glScalef(1.0, 1.5, 1.0)
    else:
        glScalef(1.5, 1.0, 1.2)
    glutSolidSphere(radius, 8, 8)
    glPopMatrix()

def draw_arena_boundaries():
    for object_type, size, x_position, z_position in boundary_objects:
        random_x = x_position + (hash(str((x_position, z_position))) % 20 - 10)
        random_z = z_position + (hash(str((z_position, x_position))) % 20 - 10)
        if object_type == 'tree':
            draw_tree(random_x, random_z, size=size)
        else:
            draw_stone(random_x, random_z, size=size)

def draw_fence():
    post_height = 80
    post_radius = 8
    rail_radius = 5
    glColor3f(0.35, 0.2, 0.1)
    
    for i in range(-GRID_LENGTH, GRID_LENGTH + 1, 100):
        glPushMatrix(); glTranslatef(i, 0, -GRID_LENGTH); glRotatef(-90, 1, 0, 0); gluCylinder(gluNewQuadric(), post_radius, post_radius, post_height, 8, 2); glPopMatrix()
        glPushMatrix(); glTranslatef(i, 0, GRID_LENGTH); glRotatef(-90, 1, 0, 0); gluCylinder(gluNewQuadric(), post_radius, post_radius, post_height, 8, 2); glPopMatrix()
        if i > -GRID_LENGTH and i < GRID_LENGTH:
             glPushMatrix(); glTranslatef(-GRID_LENGTH, 0, i); glRotatef(-90, 1, 0, 0); gluCylinder(gluNewQuadric(), post_radius, post_radius, post_height, 8, 2); glPopMatrix()
             glPushMatrix(); glTranslatef(GRID_LENGTH, 0, i); glRotatef(-90, 1, 0, 0); gluCylinder(gluNewQuadric(), post_radius, post_radius, post_height, 8, 2); glPopMatrix()

    for y_offset in [post_height * 0.4, post_height * 0.7]:
        glPushMatrix(); glTranslatef(-GRID_LENGTH, y_offset, -GRID_LENGTH); glRotatef(90, 0, 1, 0); gluCylinder(gluNewQuadric(), rail_radius, rail_radius, GRID_LENGTH * 2, 8, 2); glPopMatrix()
        glPushMatrix(); glTranslatef(-GRID_LENGTH, y_offset, GRID_LENGTH); glRotatef(90, 0, 1, 0); gluCylinder(gluNewQuadric(), rail_radius, rail_radius, GRID_LENGTH * 2, 8, 2); glPopMatrix()
        glPushMatrix(); glTranslatef(-GRID_LENGTH, y_offset, -GRID_LENGTH); gluCylinder(gluNewQuadric(), rail_radius, rail_radius, GRID_LENGTH * 2, 8, 2); glPopMatrix()
        glPushMatrix(); glTranslatef(GRID_LENGTH, y_offset, -GRID_LENGTH); gluCylinder(gluNewQuadric(), rail_radius, rail_radius, GRID_LENGTH * 2, 8, 2); glPopMatrix()

def draw_fire_pit(x_position, z_position, style='rocks'):
    if style == 'rocks':
        for i in range(4):
            angle = i * math.pi / 2 + 0.5
            draw_stone(x_position + math.cos(angle) * 20, z_position + math.sin(angle) * 20, 'small')
    elif style == 'oval_stone':
        draw_stone(x_position, z_position, 'medium', shape='oval')
        for i in range(3):
            angle = i * 2 * math.pi / 3
            draw_stone(x_position + math.cos(angle) * 30, z_position + math.sin(angle) * 30, 'small')
    elif style == 'wood':
        glColor3f(0.4, 0.2, 0.0)
        for angle in [45, -45]:
            glPushMatrix(); glTranslatef(x_position, 5, z_position); glRotatef(angle, 0, 1, 0); glScalef(60, 10, 10); glutSolidCube(1); glPopMatrix()

def draw_particle_system(system):
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glPointSize(5)
    glBegin(GL_POINTS)
    for particle in system.particles:
        life_ratio = particle.life
        glColor4f(1.0, 1.0 * life_ratio, 0.0, life_ratio)
        glVertex3fv(particle.position)
    glEnd()
    glDisable(GL_BLEND)

def draw_flat_stone(x_position, z_position):
    glColor3f(0.2, 0.2, 0.2)
    glPushMatrix()
    glTranslatef(x_position, 5, z_position)
    glScalef(1.0, 0.3, 1.0)
    glutSolidSphere(20, 10, 10)
    glPopMatrix()

def draw_log(x_position, z_position, rotation):
    glColor3f(0.4, 0.25, 0.15)
    glPushMatrix()
    glTranslatef(x_position, 5, z_position)
    glRotatef(rotation, 0, 1, 0)
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 8, 8, 45, 8, 2)
    glPopMatrix()

def draw_obstacles():
    glColor3f(0.6, 0.6, 0.6)
    for stone_position in small_stones: 
        glPushMatrix()
        glTranslatef(*stone_position)
        glutSolidSphere(15, 10, 10)
        glPopMatrix()
    for clutter_type, x_position, z_position in ground_clutter:
        if clutter_type == 'flat_stone':
            draw_flat_stone(x_position, z_position)

def special_key_listener(key, x, y):
    global camera_angle_y, camera_height
    if key == GLUT_KEY_LEFT:
        camera_angle_y -= 0.05
    if key == GLUT_KEY_RIGHT:
        camera_angle_y += 0.05
    if key == GLUT_KEY_UP:
        camera_height += 20.0
    if key == GLUT_KEY_DOWN:
        camera_height = max(20.0, camera_height - 20.0)

def setup_camera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, (WINDOW_WIDTH / WINDOW_HEIGHT), 1.0, 15000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    camera_x = camera_distance * math.sin(camera_angle_y)
    camera_z = camera_distance * math.cos(camera_angle_y)
    gluLookAt(camera_x, camera_height, camera_z, 0, 50, 0, 0, 1, 0)

def idle_function():
    global last_time_cycle_change, is_day, last_small_stone_spawn
    current_time = time.time()
    if current_time - last_time_cycle_change > day_night_duration:
        is_day = not is_day
        last_time_cycle_change = current_time
    if current_time - last_small_stone_spawn > small_stone_interval:
        small_stones.append((random.uniform(-GRID_LENGTH / 2, GRID_LENGTH / 2), 7.5, random.uniform(-GRID_LENGTH / 2, GRID_LENGTH / 2)))
        last_small_stone_spawn = current_time
        if len(small_stones) > 10:
            small_stones.pop(0)
    for bird in birds:
        bird[0] += bird[3]
        if bird[0] > 3000:
            bird[0] = -3000
    for fire_system in fire_systems:
        fire_system.update()
    glutPostRedisplay()

def display_scene():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    setup_camera()
    
    draw_environment()
    draw_arena_grid()
    draw_arena_boundaries()
    draw_fence()
    
    draw_fire_pit(GRID_LENGTH - 150, -GRID_LENGTH + 150, 'oval_stone')
    draw_particle_system(fire_systems[0])
    draw_fire_pit(-GRID_LENGTH + 150, -GRID_LENGTH + 150, 'wood')
    draw_particle_system(fire_systems[1])
    
    for i in range(2, 8):
        origin = fire_systems[i].origin
        style = 'rocks' if i % 2 == 0 else 'wood'
        draw_fire_pit(origin[0], origin[2], style)
        draw_particle_system(fire_systems[i])
        
    draw_obstacles()
    for x_pos, z_pos, rotation in tree_rock_bunch:
        draw_log(x_pos, z_pos, rotation)
        
    time_mode_text = "Time: Day" if is_day else "Time: Night"
    draw_text_on_screen(10, WINDOW_HEIGHT - 30, time_mode_text)
    draw_text_on_screen(10, WINDOW_HEIGHT - 60, f"Camera Height: {camera_height:.1f}")
    
    glutSwapBuffers()

def main():
    global start_time
    glutInit()
    start_time = time.time()
    initialize_environment()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(GAME_TITLE)
    glutDisplayFunc(display_scene)
    glutSpecialFunc(special_key_listener)
    glutIdleFunc(idle_function)
    glEnable(GL_DEPTH_TEST)
    glutMainLoop()

if __name__ == "__main__":
    main()

