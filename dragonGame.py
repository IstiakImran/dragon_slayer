
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
    sys.exit(1)

# --- Constants ---
WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720
WORLD_SIZE = 100
CULLING_DISTANCE = 100.0
WALL_BLOCK_SIZE = 1.5
TREE_COLLISION_SIZE = 1.0
SHRUB_COLLISION_SIZE = 2.0
SKY_COLOR = (0.5, 0.7, 1.0, 1.0)
GRAVITY = 0.025

# --- Gameplay Constants ---
PLAYER_MAX_HEALTH = 100
DRAGON_MAX_HEALTH = 150
DRAGON_RESPAWN_TIME = 5.0
NUM_BOMBS = 5
BOMB_TRIGGER_RADIUS = 5.0
BOMB_FUSE_TIME = 1.0
BOMB_EXPLOSION_DURATION = 1.5
BOMB_EXPLOSION_MAX_RADIUS = 15.0
WALL_SPAWN_CHANCE = 0.40
WALL_SPAWN_INTERVAL = 5.0
WALL_SPAWN_DISTANCE = 10.0
WALL_LIFETIME = 8.0

# --- Global State Variables ---
camera = None
warrior = None
dragon = None
keys = {b'w': False, b's': False, b'a': False, b'd': False,
        b' ': False, b'x': False, b'c': False, b'r': False}
last_mouse_pos = {'x': 0, 'y': 0}
is_mouse_warping = False
is_controls_locked = False
game_over = False

# --- World and Game Objects ---
object_positions = {}
player_projectiles = []
dragon_fireballs = []
embers = []
bombs = []
game_state = {}

# --- Display List Handles ---
LIST_IDS = {'tree': 1, 'rock': 2, 'wall': 3, 'shrub': 4}

# -----------------------------------------------------------------------------
# --- Warrior Prince Class (Player) ---
# -----------------------------------------------------------------------------


def draw_warrior_cube(scale_x, scale_y, scale_z):
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


class Warrior:
    def __init__(self, position=(0, 0, 0)):
        self.position = list(position)
        self.rotation_y = 0.0
        self.health = PLAYER_MAX_HEALTH
        # Animation and Physics State
        self.is_running = False
        self.is_jumping = False
        self.y_velocity = 0.0
        self.y_pos = 0.0
        self.animation_timer = 0.0
        self.JUMP_STRENGTH = 0.7
        # Special Abilities State
        self.is_shield_active = False
        self.shield_alpha = 0.0
        self.shield_timer = 0.0
        self.SHIELD_DURATION = 300
        self.PROJECTILE_SPEED = 2.5
        self.PROJECTILE_LIFESPAN = 120
        # Animation Timers for Abilities
        self.blast_animation_timer = 0
        self.shield_pose_timer = 0
        self.BLAST_ANIMATION_DURATION = 30
        self.SHIELD_POSE_DURATION = 40

    def jump(self):
        if not self.is_jumping:
            self.is_jumping = True
            self.y_velocity = self.JUMP_STRENGTH

    def activate_shield(self):
        if not self.is_shield_active:
            self.is_shield_active = True
            self.shield_timer = self.SHIELD_DURATION
            self.shield_pose_timer = self.SHIELD_POSE_DURATION

    def fire_blast(self, start_pos, direction_vec):
        global player_projectiles
        self.blast_animation_timer = self.BLAST_ANIMATION_DURATION
        player_projectiles.append({
            'pos': list(start_pos),
            'vel': [v * self.PROJECTILE_SPEED for v in direction_vec],
            'life': self.PROJECTILE_LIFESPAN
        })

    def take_damage(self, amount):
        if not self.is_shield_active:
            self.health -= amount
            print(f"Player hit! Health: {self.health}")
            if self.health <= 0:
                global game_over
                game_over = True
                print("Game Over!")

    def update(self):
        self.is_running = not is_controls_locked and (
            keys[b'w'] or keys[b's'] or keys[b'a'] or keys[b'd'])
        if self.is_running:
            self.animation_timer += 0.15

        if self.is_jumping:
            self.y_pos += self.y_velocity
            self.y_velocity -= GRAVITY
            if self.y_pos < 0.0:
                self.is_jumping = False
                self.y_pos = 0.0
                self.y_velocity = 0.0

        if self.blast_animation_timer > 0:
            self.blast_animation_timer -= 1
        if self.shield_pose_timer > 0:
            self.shield_pose_timer -= 1

        if self.is_shield_active:
            self.shield_timer -= 1
            fade_speed = 0.05
            if self.shield_timer > self.SHIELD_DURATION * 0.8:
                self.shield_alpha = min(0.6, self.shield_alpha + fade_speed)
            elif self.shield_timer < self.SHIELD_DURATION * 0.3:
                self.shield_alpha = max(0.0, self.shield_alpha - fade_speed)
            else:
                self.shield_alpha = 0.6
            if self.shield_timer <= 0:
                self.is_shield_active = False

    def draw(self):
        glPushMatrix()
        glTranslatef(self.position[0], self.position[1] +
                     self.y_pos + 2.0, self.position[2])
        glRotatef(self.rotation_y, 0, 1, 0)
        glScalef(0.5, 0.5, 0.5)

        draw_sword_func, draw_shield_func, draw_axe_func = self.draw_weapons_and_shield()
        run_angle = math.sin(self.animation_timer) * \
            40 if self.is_running else 0

        # Torso and Hips
        glPushMatrix()
        glColor3f(0.25, 0.25, 0.7)
        draw_warrior_cube(2.5, 3.0, 1.5)
        glPushMatrix()
        glTranslatef(0, 0.5, -0.76)
        glColor3f(1.0, 0.85, 0.1)
        draw_warrior_cube(2.0, 2.0, 0.1)
        glPopMatrix()
        glTranslatef(0, -1.5, 0)
        glColor3f(0.4, 0.2, 0.1)
        draw_warrior_cube(2.6, 0.4, 1.6)
        glTranslatef(0, -0.8, 0)
        glColor3f(0.3, 0.3, 0.35)
        draw_warrior_cube(2.0, 1.2, 1.2)
        glPopMatrix()

        # Head and Neck
        glPushMatrix()
        glTranslatef(0, 1.85, 0)
        glColor3f(0.9, 0.7, 0.55)
        draw_warrior_cube(0.7, 0.7, 0.7)
        glPopMatrix()
        self.draw_head()

        # Right Arm (Sword Arm)
        glPushMatrix()
        glTranslatef(-1.7, 1.0, 0)
        is_blasting_pose = self.blast_animation_timer > 0
        if is_blasting_pose:
            glRotatef(-180, 0, 1, 0)
            glRotatef(-70, 1, 0, 0)
        elif self.is_running:
            glRotatef(run_angle, 1, 0, 0)
        else:
            glRotatef(20, 1, 0, 0)
            glRotatef(15, 0, 0, 1)
        self.draw_arm(is_left=False, sword_func=draw_sword_func,
                      is_blasting=is_blasting_pose)
        glPopMatrix()

        # Left Arm (Shield Arm)
        glPushMatrix()
        glTranslatef(1.7, 1.0, 0)
        if self.shield_pose_timer > 0:
            glRotatef(60, 1, 0, 0)
            glRotatef(-80, 0, 1, 0)
            glRotatef(-20, 0, 0, 1)
        elif self.is_running:
            glRotatef(-run_angle, 1, 0, 0)
        else:
            glRotatef(20, 1, 0, 0)
            glRotatef(-15, 0, 0, 1)
        self.draw_arm(is_left=True, shield_func=draw_shield_func)
        glPopMatrix()

        # Legs
        glPushMatrix()
        glTranslatef(0.7, -2.8, 0)
        if self.is_running:
            glRotatef(-run_angle, 1, 0, 0)
        else:
            glRotatef(-10, 1, 0, 0)
            glRotatef(5, 0, 0, 1)
        self.draw_leg()
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-0.7, -2.8, 0)
        if self.is_running:
            glRotatef(run_angle, 1, 0, 0)
        else:
            glRotatef(15, 1, 0, 0)
            glRotatef(-5, 0, 0, 1)
        self.draw_leg()
        glPopMatrix()

        # Axe on back
        glPushMatrix()
        glTranslatef(0.5, 1.0, 0.8)
        glRotatef(25, 1, 0, 0)
        glRotatef(20, 0, 1, 0)
        glRotatef(20, 0, 0, 1)
        glScalef(0.8, 0.8, 0.8)
        draw_axe_func()
        glPopMatrix()

        self.draw_energy_shield()
        glPopMatrix()

    def draw_head(self):
        glPushMatrix()
        glTranslatef(0, 2.95, 0)
        glColor3f(0.9, 0.7, 0.55)
        draw_warrior_cube(1.5, 1.5, 1.5)
        glColor3f(0.2, 0.1, 0.05)
        glPushMatrix()
        glTranslatef(0, 0.5, 0)
        draw_warrior_cube(1.55, 1.0, 1.55)
        glPopMatrix()
        glColor3f(0.2, 0.5, 0.9)
        glPushMatrix()
        glTranslatef(-0.3, 0.1, -0.76)
        draw_warrior_cube(0.25, 0.25, 0.05)
        glTranslatef(0.6, 0, 0)
        draw_warrior_cube(0.25, 0.25, 0.05)
        glPopMatrix()
        glColor3f(1.0, 0.85, 0.1)
        glPushMatrix()
        glTranslatef(0, 0.9, 0)
        draw_warrior_cube(1.6, 0.3, 1.6)
        glColor3f(0.8, 0.1, 0.1)
        glTranslatef(0, 0.25, -0.8)
        draw_warrior_cube(0.2, 0.2, 0.2)
        glColor3f(1.0, 0.85, 0.1)
        glTranslatef(-0.5, 0.05, 0)
        draw_warrior_cube(0.1, 0.3, 0.1)
        glTranslatef(1.0, 0, 0)
        draw_warrior_cube(0.1, 0.3, 0.1)
        glPopMatrix()
        glPopMatrix()

    def draw_arm(self, is_left=False, sword_func=None, shield_func=None, is_blasting=False):
        glPushMatrix()
        glColor3f(0.7, 0.7, 0.8)
        draw_warrior_cube(1.1, 1.1, 1.1)
        glColor3f(0.2, 0.2, 0.6)
        glTranslatef(0, -1.25, 0)
        draw_warrior_cube(0.9, 1.5, 0.9)
        glTranslatef(0, -1.25, 0)
        glRotatef(15, 1, 0, 0)
        glColor3f(0.7, 0.7, 0.8)
        draw_warrior_cube(0.8, 1.5, 0.8)
        if is_left and shield_func:
            shield_func()
        glColor3f(0.9, 0.7, 0.55)
        glTranslatef(0, -0.9, 0)
        draw_warrior_cube(0.7, 0.5, 0.7)
        if not is_left and sword_func:
            glPushMatrix()
            if is_blasting:
                glRotatef(75, 1, 0, 0)
            sword_func()
            glPopMatrix()
        glPopMatrix()

    def draw_leg(self):
        glPushMatrix()
        glColor3f(0.3, 0.3, 0.35)
        draw_warrior_cube(1.2, 2.0, 1.2)
        glTranslatef(0, -2.0, 0)
        glRotatef(5, 1, 0, 0)
        glColor3f(0.15, 0.1, 0.05)
        draw_warrior_cube(1.1, 2.0, 1.1)
        glTranslatef(0, -1.0, -0.2)
        draw_warrior_cube(1.1, 0.3, 1.5)
        glPopMatrix()

    def draw_weapons_and_shield(self):
        def draw_sword():
            glPushMatrix()
            glTranslatef(0.0, -0.4, 0.1)
            glRotatef(-75, 1, 0, 0)
            glRotatef(-10, 0, 1, 0)
            glColor3f(0.3, 0.15, 0.05)
            draw_warrior_cube(0.2, 1.0, 0.2)
            glColor3f(0.7, 0.7, 0.8)
            glTranslatef(0, -0.5, 0)
            draw_warrior_cube(0.3, 0.2, 0.3)
            glTranslatef(0, 0.7, 0)
            draw_warrior_cube(0.8, 0.2, 0.2)
            glColor3f(0.85, 0.85, 0.9)
            glTranslatef(0, 2.0, 0)
            draw_warrior_cube(0.15, 3.0, 0.15)
            glTranslatef(0, 1.5, 0)
            glRotatef(45, 0, 0, 1)
            draw_warrior_cube(0.1, 0.4, 0.15)
            glPopMatrix()

        def draw_shield():
            glPushMatrix()
            glTranslatef(-0.5, 0.2, 0)
            glRotatef(-10, 1, 0, 0)
            glRotatef(15, 0, 0, 1)
            glColor3f(0.6, 0.6, 0.7)
            draw_warrior_cube(0.2, 2.2, 2.2)
            glColor3f(1.0, 0.85, 0.1)
            glTranslatef(-0.11, 0, 0)
            draw_warrior_cube(0.05, 1.5, 1.8)
            glTranslatef(0, 0, -0.7)
            draw_warrior_cube(0.05, 0.6, 0.3)
            glTranslatef(0, 0, 1.4)
            draw_warrior_cube(0.05, 0.6, 0.3)
            glPopMatrix()

        def draw_axe():
            glPushMatrix()
            glColor3f(0.5, 0.3, 0.1)
            draw_warrior_cube(0.2, 3.5, 0.2)
            glColor3f(0.6, 0.6, 0.7)
            glTranslatef(0, 1.5, 0)
            glRotatef(90, 0, 0, 1)
            draw_warrior_cube(1.5, 0.3, 0.3)
            glTranslatef(0, -0.8, 0)
            draw_warrior_cube(0.2, 0.2, 0.2)
            glPopMatrix()
        return draw_sword, draw_shield, draw_axe

    def draw_energy_shield(self):
        if not self.is_shield_active:
            return
        glPushMatrix()
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glTranslatef(0, 0.5, -4.0)
        glColor4f(0.3, 0.7, 1.0, self.shield_alpha)
        draw_warrior_cube(7, 7, 0.3)
        glDisable(GL_BLEND)
        glPopMatrix()

# -----------------------------------------------------------------------------
# --- Dragon Class ---
# -----------------------------------------------------------------------------


class Dragon:
    def __init__(self, position=(0, 30, -30)):
        self.position = list(position)
        self.health = DRAGON_MAX_HEALTH
        self.is_alive = True
        self.death_timer = 0
        # Animation
        self.wing_angle = 0
        self.jaw_angle = 0.0
        self.breathing_offset = 0.0
        self.tail_sway_angle = 0.0
        self.head_rot_x = 0.0
        self.head_rot_y = 0.0
        self.body_rot_y = 0.0
        # AI
        self.attack_cooldown = 0
        self.target_position = list(position)
        self.move_timer = 0
        self.is_evading = False
        self.evade_timer = 0
        self.circling_angle = 0
        self.circling_direction = 1

    def take_damage(self, amount):
        if not self.is_alive:
            return
        self.health -= amount
        print(f"Dragon hit! Health: {self.health}")
        if self.health <= 0:
            self.is_alive = False
            self.death_timer = time.time()
            print("Dragon defeated!")

    def update(self, player_pos, player_projectiles):
        current_time = time.time()
        if not self.is_alive:
            if current_time - self.death_timer > DRAGON_RESPAWN_TIME:
                self.respawn()
            return

        # Evasion AI
        if not self.is_evading:
            for proj in player_projectiles:
                dist_sq = sum(
                    [(self.position[i] - proj['pos'][i])**2 for i in range(3)])
                if dist_sq < 100:  # Evasion radius
                    self.evade(proj)
                    break

        if self.is_evading and current_time > self.evade_timer:
            self.is_evading = False

        # Movement AI (Circling the player)
        if not self.is_evading:
            self.circling_angle += 0.01 * self.circling_direction
            radius = 40
            target_x = player_pos[0] + radius * math.cos(self.circling_angle)
            target_z = player_pos[2] + radius * math.sin(self.circling_angle)
            self.target_position = [target_x, 30, target_z]
            if random.random() < 0.01:
                self.circling_direction *= -1  # Change direction occasionally

        direction = [self.target_position[i] - self.position[i]
                     for i in range(3)]
        dist = math.sqrt(sum(d*d for d in direction))
        if dist > 1:
            move_speed = 0.2 if self.is_evading else 0.1
            for i in range(3):
                self.position[i] += direction[i]/dist * move_speed
            target_body_rot_y = math.degrees(
                math.atan2(direction[0], direction[2]))
            angle_diff = (target_body_rot_y -
                          self.body_rot_y + 180) % 360 - 180
            self.body_rot_y += angle_diff * 0.05

        # Aim at player (head rotation)
        direction_to_player = [player_pos[i] -
                               self.position[i] for i in range(3)]
        player_yaw = math.degrees(math.atan2(
            direction_to_player[0], direction_to_player[2]))
        self.head_rot_y = player_yaw - self.body_rot_y
        dist_xz = math.sqrt(
            direction_to_player[0]**2 + direction_to_player[2]**2)
        self.head_rot_x = - \
            math.degrees(math.atan2(direction_to_player[1], dist_xz))

        # Attack AI
        if current_time > self.attack_cooldown and not self.is_evading:
            self.shoot_fireball()
            self.attack_cooldown = current_time + random.uniform(2, 4)

        # Animation
        self.wing_angle = math.sin(current_time * 5) * 40
        self.breathing_offset = math.sin(current_time * 2.0) * 0.1
        self.tail_sway_angle = math.sin(current_time * 1.0) * 8
        if self.jaw_angle > 0:
            self.jaw_angle = max(0, self.jaw_angle - 50 * 0.016)

    def evade(self, projectile):
        self.is_evading = True
        self.evade_timer = time.time() + 2.0  # Evade for 2 seconds

        # Simple evasion: move up and to the side
        self.target_position[1] += 10  # Fly up
        # Move perpendicular to projectile path
        proj_vel = projectile['vel']
        side_vec = [-proj_vel[2], 0, proj_vel[0]]
        mag = math.sqrt(side_vec[0]**2 + side_vec[2]**2)
        if mag > 0:
            self.target_position[0] += side_vec[0]/mag * 20
            self.target_position[2] += side_vec[2]/mag * 20
        print("Dragon evading!")

    def shoot_fireball(self):
        global dragon_fireballs
        if not self.is_alive:
            return
        self.jaw_angle = 25
        speed = 25.0
        final_yaw_rad = math.radians(self.body_rot_y + self.head_rot_y)
        final_pitch_rad = math.radians(self.head_rot_x)
        vel_x = speed * math.cos(final_pitch_rad) * math.sin(final_yaw_rad)
        vel_y = -speed * math.sin(final_pitch_rad)
        vel_z = speed * math.cos(final_pitch_rad) * math.cos(final_yaw_rad)
        start_pos = list(self.position)
        body_rot_rad = math.radians(self.body_rot_y)
        neck_offset = [0, 3.5, 3.0]
        start_pos[0] += neck_offset[2] * math.sin(body_rot_rad)
        start_pos[2] += neck_offset[2] * math.cos(body_rot_rad)
        start_pos[1] += neck_offset[1]
        dragon_fireballs.append({'pos': start_pos, 'vel': [
                                vel_x, vel_y, vel_z], 'life': 5.0, 'max_life': 5.0, 'size': 1.0})

    def respawn(self):
        self.position = [random.uniform(-WORLD_SIZE/2, WORLD_SIZE/2), random.uniform(
            30, 50), random.uniform(-WORLD_SIZE/2, WORLD_SIZE/2)]
        self.health = DRAGON_MAX_HEALTH
        self.is_alive = True
        print("A new dragon has appeared!")

    def draw(self):
        if not self.is_alive:
            return
        glPushMatrix()
        glTranslatef(self.position[0], self.position[1], self.position[2])
        glRotatef(-self.body_rot_y, 0, 1, 0)  # Rotate body
        glPushMatrix()
        glTranslatef(0, self.breathing_offset, 0)
        self.draw_torso()
        self.draw_neck()
        self.draw_head(self.breathing_offset, self.head_rot_x,
                       self.head_rot_y, self.jaw_angle)
        self.draw_legs()
        self.draw_tail(self.tail_sway_angle)
        glPushMatrix()
        glTranslatef(1.8, 2.5, 0.5)
        glRotatef(self.wing_angle, 0, 0, 1)
        self.draw_wing(1)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-1.8, 2.5, 0.5)
        glRotatef(-self.wing_angle, 0, 0, 1)
        self.draw_wing(-1)
        glPopMatrix()
        glPopMatrix()
        glPopMatrix()

    def draw_cube(self, scale=(1, 1, 1), position=(0, 0, 0)):
        glPushMatrix()
        glTranslatef(*position)
        glScalef(*scale)
        glutSolidCube(1)
        glPopMatrix()

    def draw_pyramid(self, scale=(1, 1, 1), position=(0, 0, 0)):
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
        glPushMatrix()
        glTranslatef(*position)
        glutSolidSphere(radius, 20, 20)
        glPopMatrix()

    def draw_spine(self):
        glColor3f(0.8, 0.1, 0.1)
        for i in range(5):
            size_multiplier = 1.0 - abs(i - 2) * 0.3
            self.draw_pyramid(scale=(0.8 * size_multiplier, 1.5 *
                              size_multiplier, 0.3), position=(0, 3.5, 2.0 - i * 1.2))

    def draw_torso(self):
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
        glPushMatrix()
        glTranslatef(0, 3.5, 3.0)
        glRotatef(breathing_offset * -20, 1, 0, 0)
        glRotatef(head_rot_y, 0, 1, 0)
        glRotatef(head_rot_x, 1, 0, 0)
        glColor3f(0.1, 0.6, 0.2)
        self.draw_cube(scale=(2, 1.8, 2.5), position=(0, 0, 0))
        self.draw_cube(scale=(1.5, 1.2, 2.5), position=(0, -0.2, 2.0))
        glColor3f(1.0, 1.0, 0.9)
        for i in range(5):
            glPushMatrix()
            glTranslatef(-0.6 + i*0.3, -0.55, 3.0)
            glRotatef(180, 1, 0, 0)
            self.draw_pyramid(scale=(0.2, 0.8, 0.2), position=(0, 0, 0))
            glPopMatrix()
        glPushMatrix()
        glTranslatef(0, -0.7, 0.85)
        glRotatef(jaw_angle, 1, 0, 0)
        glTranslatef(0, -0.2, 1.15)
        glColor3f(0.2, 0.7, 0.3)
        self.draw_cube(scale=(1.4, 0.5, 2.3))
        glColor3f(1.0, 1.0, 0.9)
        for i in range(4):
            self.draw_pyramid(scale=(0.2, 0.7, 0.2),
                              position=(-0.5, 0.25, -0.8 + i*0.5))
            self.draw_pyramid(scale=(0.2, 0.7, 0.2),
                              position=(0.5, 0.25, -0.8 + i*0.5))
        glPopMatrix()
        glColor3f(1.0, 0.0, 0.0)
        self.draw_sphere(radius=0.2, position=(-0.6, 0.5, 1.5))
        self.draw_sphere(radius=0.2, position=(0.6, 0.5, 1.5))
        glColor3f(0.9, 0.9, 0.2)
        self.draw_pyramid(scale=(0.4, 2.0, 0.4), position=(-0.8, 0.8, -0.5))
        self.draw_pyramid(scale=(0.4, 2.0, 0.4), position=(0.8, 0.8, -0.5))
        self.draw_pyramid(scale=(0.3, 1.5, 0.3), position=(-0.5, 0.8, -1.2))
        self.draw_pyramid(scale=(0.3, 1.5, 0.3), position=(0.5, 0.8, -1.2))
        glPopMatrix()

    def draw_neck(self):
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

# -----------------------------------------------------------------------------
# --- Camera Class ---
# -----------------------------------------------------------------------------


class Camera:
    def __init__(self, position=(0, 5, 10)):
        self.position = list(position)
        self.rotation = [0, 0]
        self.speed = 0.2
        self.sensitivity = 0.15
        self.player_radius = 0.5
        self.is_third_person = True
        self.third_person_distance = 10.0
        self.third_person_elevation = 15.0

    def is_colliding(self, next_pos):
        collidable_types = {'boundary_walls': WALL_BLOCK_SIZE, 'random_walls': WALL_BLOCK_SIZE,
                            'trees': TREE_COLLISION_SIZE, 'shrubs': SHRUB_COLLISION_SIZE, 'temp_walls': WALL_BLOCK_SIZE}
        for obj_key, obj_size in collidable_types.items():
            positions = object_positions.get(obj_key, [])
            if obj_key == 'temp_walls':
                positions = [item['pos'] for item in positions]
            for obj_pos in positions:
                if (next_pos[0] + self.player_radius > obj_pos[0] - obj_size / 2 and next_pos[0] - self.player_radius < obj_pos[0] + obj_size / 2 and
                        next_pos[2] + self.player_radius > obj_pos[2] - obj_size / 2 and next_pos[2] - self.player_radius < obj_pos[2] + obj_size / 2):
                    return True
        return False

    def update(self):
        global warrior
        if is_controls_locked or game_over:
            return
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
            move_vec[0] *= self.speed / magnitude
            move_vec[2] *= self.speed / magnitude
        if keys[b'x']:
            warrior.position[1] += self.speed
        if keys[b'c']:
            warrior.position[1] -= self.speed
        if magnitude > 0:
            warrior.rotation_y = - \
                math.degrees(math.atan2(-move_vec[2], -move_vec[0])) + 90
        next_pos_x = [warrior.position[0] + move_vec[0],
                      warrior.position[1], warrior.position[2]]
        if not self.is_colliding(next_pos_x):
            warrior.position[0] += move_vec[0]
        next_pos_z = [warrior.position[0], warrior.position[1],
                      warrior.position[2] + move_vec[2]]
        if not self.is_colliding(next_pos_z):
            warrior.position[2] += move_vec[2]
        if warrior.position[1] < 1.0:
            warrior.position[1] = 1.0

    def handle_mouse(self, x, y):
        global is_mouse_warping, last_mouse_pos
        if is_mouse_warping:
            is_mouse_warping = False
            last_mouse_pos['x'], last_mouse_pos['y'] = x, y
            return
        dx, dy = x - last_mouse_pos['x'], y - last_mouse_pos['y']
        self.rotation[0] += dx * self.sensitivity
        self.rotation[1] = max(-89.0, min(89.0,
                               self.rotation[1] - dy * self.sensitivity))
        center_x, center_y = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
        if abs(x - center_x) > 200 or abs(y - center_y) > 200:
            is_mouse_warping = True
            glutWarpPointer(center_x, center_y)
        else:
            last_mouse_pos['x'], last_mouse_pos['y'] = x, y

    def get_camera_forward_vector(self):
        yaw_rad = math.radians(self.rotation[0])
        pitch_rad = math.radians(self.rotation[1])
        x = math.sin(yaw_rad) * math.cos(pitch_rad)
        y = math.sin(pitch_rad)
        z = -math.cos(yaw_rad) * math.cos(pitch_rad)
        mag = math.sqrt(x*x + y*y + z*z)
        return [x/mag, y/mag, z/mag]

    def look(self):
        glLoadIdentity()
        if self.is_third_person:
            cam_x = warrior.position[0] - self.third_person_distance * math.sin(math.radians(
                self.rotation[0])) * math.cos(math.radians(self.third_person_elevation))
            cam_y = warrior.position[1] + self.third_person_distance * \
                math.sin(math.radians(self.third_person_elevation)) + 2.0
            cam_z = warrior.position[2] + self.third_person_distance * math.cos(math.radians(
                self.rotation[0])) * math.cos(math.radians(self.third_person_elevation))
            self.position = [cam_x, cam_y, cam_z]
            look_target_y = warrior.position[1] + 1.5
            gluLookAt(cam_x, cam_y, cam_z,
                      warrior.position[0], look_target_y, warrior.position[2], 0, 1, 0)
        else:
            pitch_rad, yaw_rad = math.radians(
                self.rotation[1]), math.radians(self.rotation[0])
            cam_pos = [warrior.position[0],
                       warrior.position[1] + 4.0, warrior.position[2]]
            self.position = cam_pos
            look_at_point = [cam_pos[0] + math.sin(yaw_rad) * math.cos(pitch_rad), cam_pos[1] + math.sin(
                pitch_rad), cam_pos[2] - math.cos(yaw_rad) * math.cos(pitch_rad)]
            gluLookAt(cam_pos[0], cam_pos[1], cam_pos[2], look_at_point[0],
                      look_at_point[1], look_at_point[2], 0, 1, 0)

# -----------------------------------------------------------------------------
# --- World Generation and Drawing ---
# -----------------------------------------------------------------------------


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


def draw_tree_geometry(): glPushMatrix(); trunk_color = [(0.4, 0.2, 0.0)]*6; trunk_size = 1.0; [(draw_cube(trunk_size, trunk_color), glTranslatef(0, trunk_size, 0)) for _ in range(5)]; leaf_colors = [(0.0, 0.5, 0.0), (0.0, 0.6, 0.0)]; glTranslatef(0, 2, 0); draw_cube(
    4, leaf_colors); glTranslatef(1.5, -1, 0); draw_cube(2.5, leaf_colors); glTranslatef(-3.0, 0, 0); draw_cube(2.5, leaf_colors); glTranslatef(1.5, 1, 0); glTranslatef(0, -1, 1.5); draw_cube(2.5, leaf_colors); glTranslatef(0, 0, -3.0); draw_cube(2.5, leaf_colors); glPopMatrix()


def draw_wall_geometry(): glPushMatrix(); wall_colors = [(0.6, 0.6, 0.6), (0.55, 0.55, 0.55)]; draw_cube(
    WALL_BLOCK_SIZE, wall_colors); glTranslatef(0, WALL_BLOCK_SIZE, 0); draw_cube(WALL_BLOCK_SIZE, wall_colors); glPopMatrix()


def draw_shrub_geometry(): glPushMatrix(); leaf_colors = [(0.1, 0.4, 0.1), (0.1, 0.5, 0.1)]; draw_cube(2.0, leaf_colors); glTranslatef(0.75, -0.5, 0); draw_cube(
    1.5, leaf_colors); glTranslatef(-1.5, 0, 0); draw_cube(1.5, leaf_colors); glTranslatef(0.75, 0.5, 0.75); draw_cube(1.5, leaf_colors); glTranslatef(0, 0, -1.5); draw_cube(1.5, leaf_colors); glPopMatrix()


def draw_ground(): glColor3f(0.1, 0.6, 0.1); glBegin(GL_QUADS); glVertex3f(-WORLD_SIZE, 0, -WORLD_SIZE); glVertex3f(-WORLD_SIZE,
                                                                                                                    0, WORLD_SIZE); glVertex3f(WORLD_SIZE, 0, WORLD_SIZE); glVertex3f(WORLD_SIZE, 0, -WORLD_SIZE); glEnd()


def draw_player_projectiles():
    for p in player_projectiles:
        glPushMatrix()
        glTranslatef(p['pos'][0], p['pos'][1], p['pos'][2])
        glColor3f(0.2, 1.0, 0.8)
        glutSolidSphere(0.2, 10, 10)
        glPopMatrix()


def draw_billboard_particles(particles, modelview_matrix):
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
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glDepthMask(GL_FALSE)
    fire_particles = []
    for p in dragon_fireballs:
        life_ratio = p['life'] / p['max_life']
        for _ in range(30):
            offset = [random.uniform(-1, 1) * p['size']
                      * life_ratio for _ in range(3)]
            dist_from_center = math.sqrt(sum(x*x for x in offset))
            g_channel = max(0, 1.0 - dist_from_center /
                            (p['size'] * life_ratio))
            particle_color = (1.0, 0.5 + g_channel*0.5, 0.0)
            fire_particles.append({'pos': [p['pos'][i] + offset[i] for i in range(
                3)], 'life': p['life'], 'max_life': p['max_life'], 'size': 0.4, 'color': particle_color})
    if fire_particles:
        draw_billboard_particles(fire_particles, modelview_matrix)
    ember_particles = []
    for p in embers:
        ember_particles.append(
            {'pos': p['pos'], 'life': p['life'], 'max_life': p['max_life'], 'size': 0.1, 'color': (1.0, 0.4, 0.0)})
    if ember_particles:
        draw_billboard_particles(ember_particles, modelview_matrix)
    glDepthMask(GL_TRUE)
    glDisable(GL_BLEND)


def draw_ui():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glDisable(GL_DEPTH_TEST)
    # Health bars
    glColor3f(1, 0, 0)
    glRectf(10, WINDOW_HEIGHT - 30, 10 + 200, WINDOW_HEIGHT - 10)
    glColor3f(0, 1, 0)
    glRectf(10, WINDOW_HEIGHT - 30, 10 + 200 *
            (warrior.health/PLAYER_MAX_HEALTH), WINDOW_HEIGHT - 10)
    if dragon and dragon.is_alive:
        glColor3f(1, 0, 0)
        glRectf(WINDOW_WIDTH - 210, WINDOW_HEIGHT - 30,
                WINDOW_WIDTH - 10, WINDOW_HEIGHT - 10)
        glColor3f(0.8, 0, 0.8)
        glRectf(WINDOW_WIDTH - 210, WINDOW_HEIGHT - 30, WINDOW_WIDTH -
                210 + 200 * (dragon.health/DRAGON_MAX_HEALTH), WINDOW_HEIGHT - 10)
    if game_over:
        glColor3f(1, 0, 0)
        draw_text("GAME OVER", WINDOW_WIDTH/2 - 50, WINDOW_HEIGHT/2)
        draw_text("Press 'R' to restart", WINDOW_WIDTH /
                  2 - 70, WINDOW_HEIGHT/2 - 30)
    if not camera.is_third_person:
        draw_crosshair()
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()


def draw_text(text, x, y):
    glWindowPos2f(x, y)
    for character in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(character))


def draw_crosshair():
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(2.0)
    glBegin(GL_LINES)
    glVertex2f(WINDOW_WIDTH/2-10, WINDOW_HEIGHT/2)
    glVertex2f(WINDOW_WIDTH/2+10, WINDOW_HEIGHT/2)
    glVertex2f(WINDOW_WIDTH/2, WINDOW_HEIGHT/2-10)
    glVertex2f(WINDOW_WIDTH/2, WINDOW_HEIGHT/2+10)
    glEnd()

# -----------------------------------------------------------------------------
# --- Game Logic and World Setup ---
# -----------------------------------------------------------------------------


def is_position_safe(pos, radius):
    collidable_types = {'boundary_walls': WALL_BLOCK_SIZE, 'random_walls': WALL_BLOCK_SIZE,
                        'trees': TREE_COLLISION_SIZE, 'shrubs': SHRUB_COLLISION_SIZE}
    for obj_key, obj_size in collidable_types.items():
        for obj_pos in object_positions.get(obj_key, []):
            if (pos[0] - obj_pos[0])**2 + (pos[2] - obj_pos[2])**2 < (radius + obj_size / 2)**2:
                return False
    return True


def find_safe_spawn_point():
    while True:
        x = random.uniform(-WORLD_SIZE * 0.8, WORLD_SIZE * 0.8)
        z = random.uniform(-WORLD_SIZE * 0.8, WORLD_SIZE * 0.8)
        pos = [x, 1.0, z]
        if is_position_safe(pos, 2.0):
            return pos


def spawn_bomb():
    bombs.append({'position': [random.uniform(-WORLD_SIZE, WORLD_SIZE), 0.5, random.uniform(-WORLD_SIZE,
                 WORLD_SIZE)], 'state': 'idle', 'triggered_time': 0, 'explosion_start_time': 0})


def spawn_blocking_wall():
    yaw_rad = math.radians(camera.rotation[0])
    forward_vec = [math.sin(yaw_rad), 0, -math.cos(yaw_rad)]
    strafe_vec = [math.cos(yaw_rad), 0, math.sin(yaw_rad)]
    center_pos = [warrior.position[0]+forward_vec[0]*WALL_SPAWN_DISTANCE,
                  0, warrior.position[2]+forward_vec[2]*WALL_SPAWN_DISTANCE]
    for i in range(-1, 2):
        object_positions['temp_walls'].append({'pos': [center_pos[0]+strafe_vec[0]*i*WALL_BLOCK_SIZE, center_pos[1],
                                              center_pos[2]+strafe_vec[2]*i*WALL_BLOCK_SIZE], 'despawn_time': time.time()+WALL_LIFETIME})
    print("A blocking wall appears!")


def update_game_logic():
    global player_projectiles, dragon_fireballs, embers, bombs, object_positions, game_state
    if game_over:
        return

    current_time = time.time()
    for bomb in bombs[:]:
        if bomb.get('state') == 'idle':
            if (bomb['position'][0]-warrior.position[0])**2 + (bomb['position'][2]-warrior.position[2])**2 < BOMB_TRIGGER_RADIUS**2:
                bomb['state'] = 'triggered'
                bomb['triggered_time'] = current_time
                print("Bomb triggered!")
        elif bomb.get('state') == 'triggered':
            if current_time > bomb['triggered_time']+BOMB_FUSE_TIME:
                bomb['state'] = 'exploding'
                bomb['explosion_start_time'] = current_time
                print("Boom!")
        elif bomb.get('state') == 'exploding':
            if current_time > bomb['explosion_start_time']+BOMB_EXPLOSION_DURATION:
                bombs.remove(bomb)
                spawn_bomb()
    object_positions['temp_walls'] = [
        w for w in object_positions['temp_walls'] if current_time < w['despawn_time']]
    if current_time > game_state.get('last_wall_check', 0) + WALL_SPAWN_INTERVAL:
        game_state['last_wall_check'] = current_time
        if random.random() < WALL_SPAWN_CHANCE:
            spawn_blocking_wall()

    # Update player projectiles
    updated_projectiles = []
    for proj in player_projectiles:
        proj['pos'][0] += proj['vel'][0]
        proj['pos'][1] += proj['vel'][1]
        proj['pos'][2] += proj['vel'][2]
        proj['life'] -= 1
        if proj['life'] > 0:
            if dragon and dragon.is_alive and (proj['pos'][0]-dragon.position[0])**2 + (proj['pos'][1]-dragon.position[1])**2 + (proj['pos'][2]-dragon.position[2])**2 < 10:
                dragon.take_damage(10)
            else:
                updated_projectiles.append(proj)
    player_projectiles = updated_projectiles

    # Update dragon fireballs
    gravity = 9.8 * 0.016
    for p in dragon_fireballs:
        for i in range(3):
            p['pos'][i] += p['vel'][i] * 0.016
        p['vel'][1] -= gravity
        p['life'] -= 0.016
        if (p['pos'][0]-warrior.position[0])**2 + (p['pos'][1]-warrior.position[1])**2 + (p['pos'][2]-warrior.position[2])**2 < 4:
            warrior.take_damage(20)
            p['life'] = 0  # remove fireball
        if random.random() < 0.8:
            embers.append({'pos': p['pos'][:], 'vel': [
                          p['vel'][i]*0.1 + random.uniform(-0.2, 0.2) for i in range(3)], 'life': 0.8, 'max_life': 0.8})
    dragon_fireballs = [p for p in dragon_fireballs if p['life'] > 0]
    for p in embers:
        for i in range(3):
            p['pos'][i] += p['vel'][i] * 0.016
        p['vel'][1] -= gravity * 0.5
        p['life'] -= 0.016
    embers = [p for p in embers if p['life'] > 0]


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


def generate_world():
    global object_positions
    wall_spacing = WALL_BLOCK_SIZE
    num_walls = int(WORLD_SIZE * 2 / wall_spacing)
    object_positions = {'trees': [(random.uniform(-WORLD_SIZE, WORLD_SIZE), 0, random.uniform(-WORLD_SIZE, WORLD_SIZE)) for _ in range(150)], 'rocks': [(random.uniform(-WORLD_SIZE, WORLD_SIZE), 0.5, random.uniform(-WORLD_SIZE, WORLD_SIZE)) for _ in range(70)], 'shrubs': [(random.uniform(-WORLD_SIZE, WORLD_SIZE), 1, random.uniform(-WORLD_SIZE, WORLD_SIZE)) for _ in range(800)], 'random_walls': [(
        random.randint(-WORLD_SIZE, WORLD_SIZE), 0, random.randint(-WORLD_SIZE, WORLD_SIZE)) for _ in range(30)], 'boundary_walls': ([(i*wall_spacing-WORLD_SIZE, 0, -WORLD_SIZE) for i in range(num_walls+1)]+[(i*wall_spacing-WORLD_SIZE, 0, WORLD_SIZE) for i in range(num_walls+1)]+[(-WORLD_SIZE, 0, i*wall_spacing-WORLD_SIZE) for i in range(num_walls+1)]+[(WORLD_SIZE, 0, i*wall_spacing-WORLD_SIZE) for i in range(num_walls+1)]), 'temp_walls': []}


def setup_opengl():
    glClearColor(*SKY_COLOR)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)
    glShadeModel(GL_SMOOTH)


def restart_game():
    global warrior, dragon, game_over, player_projectiles, dragon_fireballs, embers, bombs, game_state
    game_over = False
    safe_spawn_pos = find_safe_spawn_point()
    warrior = Warrior(position=safe_spawn_pos)
    dragon = Dragon()
    player_projectiles = []
    dragon_fireballs = []
    embers = []
    bombs = []
    game_state = {'last_wall_check': time.time()}
    for _ in range(NUM_BOMBS):
        spawn_bomb()
    print("Game Restarted!")

# -----------------------------------------------------------------------------
# --- GLUT Callbacks and Main Loop ---
# -----------------------------------------------------------------------------


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    camera.look()
    modelview_matrix = glGetFloatv(GL_MODELVIEW_MATRIX)
    draw_ground()
    draw_player_projectiles()
    if dragon_fireballs or embers:
        draw_fire_and_embers(modelview_matrix)

    culling_dist_sq = CULLING_DISTANCE**2
    cam_pos = warrior.position
    object_map = [('trees', LIST_IDS['tree']), ('rocks', LIST_IDS['rock']), ('shrubs',
                                                                             LIST_IDS['shrub']), ('random_walls', LIST_IDS['wall']), ('boundary_walls', LIST_IDS['wall'])]
    for key, list_id in object_map:
        for pos in object_positions[key]:
            if (pos[0]-cam_pos[0])**2+(pos[2]-cam_pos[2])**2 < culling_dist_sq:
                glPushMatrix()
                glTranslatef(pos[0], pos[1], pos[2])
                glCallList(list_id)
                glPopMatrix()
    for wall in object_positions.get('temp_walls', []):
        pos = wall['pos']
        if (pos[0]-cam_pos[0])**2+(pos[2]-cam_pos[2])**2 < culling_dist_sq:
            glPushMatrix()
            glTranslatef(pos[0], pos[1], pos[2])
            glCallList(LIST_IDS['wall'])
            glPopMatrix()
    for bomb in bombs:
        if bomb.get('state') in ['idle', 'triggered']:
            glPushMatrix()
            glTranslatef(*bomb['position'])
            glColor3f(1, 0, 0) if bomb['state'] == 'triggered' and int(
                time.time()*10) % 2 == 0 else glColor3f(0.8, 0.8, 0)
            glutSolidSphere(0.5, 16, 16)
            glPopMatrix()
        elif bomb.get('state') == 'exploding':
            progress = (
                time.time()-bomb['explosion_start_time'])/BOMB_EXPLOSION_DURATION
            radius = progress*BOMB_EXPLOSION_MAX_RADIUS
            alpha = 0.8*(1.0-progress)
            glPushMatrix()
            glTranslatef(*bomb['position'])
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            glColor4f(1.0, 0.5, 0.0, alpha)
            glutSolidSphere(radius, 32, 32)
            glDisable(GL_BLEND)
            glPopMatrix()

    if camera.is_third_person:
        warrior.draw()
    if dragon:
        dragon.draw()

    if not camera.is_third_person and warrior.is_shield_active:
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.3, 0.7, 1.0, warrior.shield_alpha * 0.7)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(WINDOW_WIDTH, 0)
        glVertex2f(WINDOW_WIDTH, WINDOW_HEIGHT)
        glVertex2f(0, WINDOW_HEIGHT)
        glEnd()
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    draw_ui()
    glutSwapBuffers()


def keyboard(key, x, y):
    global keys, is_controls_locked, game_over
    if key == b'':
        sys.exit()
    if key.lower() in keys:
        keys[key.lower()] = True
    if game_over:
        if key.lower() == b'r':
            restart_game()
        return
    if not is_controls_locked:
        if key == b' ':
            warrior.jump()
        if key == b'e':
            warrior.activate_shield()
    if key == b'l':
        is_controls_locked = not is_controls_locked
        print(f"Controls {'LOCKED' if is_controls_locked else 'UNLOCKED'}")


def keyboard_up(key, x, y):
    if key.lower() in keys:
        keys[key.lower()] = False


def mouse(button, state, x, y):
    global camera
    if game_over:
        return
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        camera.is_third_person = not camera.is_third_person
    elif button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not is_controls_locked:
        if camera.is_third_person:
            camera.is_third_person = False
        fwd_vec = camera.get_camera_forward_vector()
        start_pos = [camera.position[i] + fwd_vec[i] * 1.5 for i in range(3)]
        warrior.fire_blast(start_pos, fwd_vec)


def mouse_motion(x, y): camera.handle_mouse(x, y)


def idle():
    if not game_over:
        update_game_logic()
        camera.update()
        warrior.update()
        if dragon:
            dragon.update(warrior.position, player_projectiles)
    glutPostRedisplay()


def reshape(w, h):
    global WINDOW_WIDTH, WINDOW_HEIGHT
    WINDOW_WIDTH, WINDOW_HEIGHT = w, h
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(55, (w/max(1, h)), 0.1, 500.0)
    glMatrixMode(GL_MODELVIEW)


def main():
    global camera, warrior, dragon, last_mouse_pos
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutCreateWindow(b"Final Game: Warrior vs Dragon")
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboard_up)
    glutPassiveMotionFunc(mouse_motion)
    glutMouseFunc(mouse)
    glutIdleFunc(idle)
    setup_opengl()
    generate_world()
    compile_display_lists()
    glutSetCursor(GLUT_CURSOR_NONE)
    center_x, center_y = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
    glutWarpPointer(center_x, center_y)
    camera = Camera()
    last_mouse_pos = {'x': center_x, 'y': center_y}
    restart_game()
    print("Game Loaded. Controls: W,A,S,D, Mouse, Space, E, L, R")
    glutMainLoop()


if __name__ == "__main__":
    main()
