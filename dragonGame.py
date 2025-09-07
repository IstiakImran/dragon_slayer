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
NUM_DRAGONS = 2 # --- ADDED FOR MULTIPLE DRAGONS ---
NUM_BOMBS = 5
BOMB_TRIGGER_RADIUS = 5.0
BOMB_FUSE_TIME = 1.0
BOMB_EXPLOSION_DURATION = 1.5
BOMB_EXPLOSION_MAX_RADIUS = 15.0
# --- ADDED FOR HEARTS ---
NUM_HEARTS = 5
HEART_TRIGGER_RADIUS = 3.0
HEART_HEAL_AMOUNT = 25
# -------------------------
# --- ADDED FOR FIREBALL EXPLOSION ---
FIREBALL_EXPLOSION_DURATION = 1.0
FIREBALL_EXPLOSION_MAX_RADIUS = 10.0
FIREBALL_SPLASH_DAMAGE = 15
# ------------------------------------
WALL_SPAWN_CHANCE = 0.40
WALL_SPAWN_INTERVAL = 5.0
WALL_SPAWN_DISTANCE = 10.0
WALL_LIFETIME = 8.0

# --- Global State Variables ---
camera = None
warrior = None
dragons = [] # --- MODIFIED FOR MULTIPLE DRAGONS ---
keys = {b'w': False, b's': False, b'a': False, b'd': False,
        b' ': False, b'x': False, b'c': False, b'r': False}
lastMousePos = {'x': 0, 'y': 0}
isMouseWarping = False
isControlsLocked = False
gameOver = False

# --- World and Game Objects ---
objectPositions = {}
playerProjectiles = []
dragonFireballs = []
embers = []
bombs = []
# --- ADDED FOR HEARTS ---
hearts = []
# -------------------------
gameState = {}

# --- Display List Handles ---
LIST_IDS = {'tree': 1, 'rock': 2, 'wall': 3, 'shrub': 4}

# -----------------------------------------------------------------------------
# --- Warrior Prince Class (Player) ---
# -----------------------------------------------------------------------------


def drawWarriorCube(scaleX, scaleY, scaleZ):
    """Draws a solid color cube, scaled to the given dimensions."""
    glPushMatrix()
    glScalef(scaleX, scaleY, scaleZ)
    vertices = [[0.5,  0.5, -0.5], [0.5, -0.5, -0.5], [-0.5, -0.5, -0.5], [-0.5,  0.5, -0.5],
                [0.5,  0.5,  0.5], [0.5, -0.5,  0.5], [-0.5, -0.5,  0.5], [-0.5,  0.5,  0.5]]
    faces = [[0, 1, 2, 3], [3, 2, 6, 7], [7, 6, 5, 4],
             [4, 5, 1, 0], [0, 3, 7, 4], [1, 5, 6, 2]]
    glBegin(GL_QUADS)
    for face in faces:
        for vertexIndex in face:
            glVertex3fv(vertices[vertexIndex])
    glEnd()
    glPopMatrix()


class Warrior:
    def __init__(self, position=(0, 0, 0)):
        self.position = list(position)
        self.rotationY = 0.0
        self.health = PLAYER_MAX_HEALTH
        # Animation and Physics State
        self.isRunning = False
        self.isJumping = False
        self.yVelocity = 0.0
        self.yPos = 0.0
        self.animationTimer = 0.0
        self.JUMP_STRENGTH = 0.7
        # Special Abilities State
        self.isShieldActive = False
        self.shieldAlpha = 0.0
        self.shieldTimer = 0.0
        self.SHIELD_DURATION = 300
        self.PROJECTILE_SPEED = 2.5
        self.PROJECTILE_LIFESPAN = 120
        # Animation Timers for Abilities
        self.blastAnimationTimer = 0
        self.shieldPoseTimer = 0
        self.BLAST_ANIMATION_DURATION = 30
        self.SHIELD_POSE_DURATION = 40

    def jump(self):
        if not self.isJumping:
            self.isJumping = True
            self.yVelocity = self.JUMP_STRENGTH

    def activateShield(self):
        if not self.isShieldActive:
            self.isShieldActive = True
            self.shieldTimer = self.SHIELD_DURATION
            self.shieldPoseTimer = self.SHIELD_POSE_DURATION

    def fireBlast(self, startPos, directionVec):
        global playerProjectiles
        self.blastAnimationTimer = self.BLAST_ANIMATION_DURATION
        playerProjectiles.append({
            'pos': list(startPos),
            'vel': [v * self.PROJECTILE_SPEED for v in directionVec],
            'life': self.PROJECTILE_LIFESPAN
        })

    def takeDamage(self, amount):
        if not self.isShieldActive:
            self.health -= amount
            print(f"Player hit! Health: {self.health}")
            if self.health <= 0:
                global gameOver
                gameOver = True
                print("Game Over!")

    # --- ADDED FOR HEARTS ---
    def heal(self, amount):
        self.health += amount
        if self.health > PLAYER_MAX_HEALTH:
            self.health = PLAYER_MAX_HEALTH
        print(f"Player healed! Health: {self.health}")
    # -------------------------

    def update(self):
        self.isRunning = not isControlsLocked and (
            keys[b'w'] or keys[b's'] or keys[b'a'] or keys[b'd'])
        if self.isRunning:
            self.animationTimer += 0.15

        if self.isJumping:
            self.yPos += self.yVelocity
            self.yVelocity -= GRAVITY
            if self.yPos < 0.0:
                self.isJumping = False
                self.yPos = 0.0
                self.yVelocity = 0.0

        if self.blastAnimationTimer > 0:
            self.blastAnimationTimer -= 1
        if self.shieldPoseTimer > 0:
            self.shieldPoseTimer -= 1

        if self.isShieldActive:
            self.shieldTimer -= 1
            fadeSpeed = 0.05
            if self.shieldTimer > self.SHIELD_DURATION * 0.8:
                self.shieldAlpha = min(0.6, self.shieldAlpha + fadeSpeed)
            elif self.shieldTimer < self.SHIELD_DURATION * 0.3:
                self.shieldAlpha = max(0.0, self.shieldAlpha - fadeSpeed)
            else:
                self.shieldAlpha = 0.6
            if self.shieldTimer <= 0:
                self.isShieldActive = False

    def draw(self):
        glPushMatrix()
        glTranslatef(self.position[0], self.position[1] +
                     self.yPos + 2.0, self.position[2])
        glRotatef(self.rotationY, 0, 1, 0)
        glScalef(0.5, 0.5, 0.5)

        drawSwordFunc, drawShieldFunc, drawAxeFunc = self.drawWeaponsAndShield()
        runAngle = math.sin(self.animationTimer) * \
            40 if self.isRunning else 0

        # Torso and Hips
        glPushMatrix()
        glColor3f(0.25, 0.25, 0.7)
        drawWarriorCube(2.5, 3.0, 1.5)
        glPushMatrix()
        glTranslatef(0, 0.5, -0.76)
        glColor3f(1.0, 0.85, 0.1)
        drawWarriorCube(2.0, 2.0, 0.1)
        glPopMatrix()
        glTranslatef(0, -1.5, 0)
        glColor3f(0.4, 0.2, 0.1)
        drawWarriorCube(2.6, 0.4, 1.6)
        glTranslatef(0, -0.8, 0)
        glColor3f(0.3, 0.3, 0.35)
        drawWarriorCube(2.0, 1.2, 1.2)
        glPopMatrix()

        # Head and Neck
        glPushMatrix()
        glTranslatef(0, 1.85, 0)
        glColor3f(0.9, 0.7, 0.55)
        drawWarriorCube(0.7, 0.7, 0.7)
        glPopMatrix()
        self.drawHead()

        # Right Arm (Sword Arm)
        glPushMatrix()
        glTranslatef(-1.7, 1.0, 0)
        isBlastingPose = self.blastAnimationTimer > 0
        if isBlastingPose:
            glRotatef(-180, 0, 1, 0)
            glRotatef(-70, 1, 0, 0)
        elif self.isRunning:
            glRotatef(runAngle, 1, 0, 0)
        else:
            glRotatef(20, 1, 0, 0)
            glRotatef(15, 0, 0, 1)
        self.drawArm(is_left=False, sword_func=drawSwordFunc,
                     is_blasting=isBlastingPose)
        glPopMatrix()

        # Left Arm (Shield Arm)
        glPushMatrix()
        glTranslatef(1.7, 1.0, 0)
        if self.shieldPoseTimer > 0:
            glRotatef(60, 1, 0, 0)
            glRotatef(-80, 0, 1, 0)
            glRotatef(-20, 0, 0, 1)
        elif self.isRunning:
            glRotatef(-runAngle, 1, 0, 0)
        else:
            glRotatef(20, 1, 0, 0)
            glRotatef(-15, 0, 0, 1)
        self.drawArm(is_left=True, shield_func=drawShieldFunc)
        glPopMatrix()

        # Legs
        glPushMatrix()
        glTranslatef(0.7, -2.8, 0)
        if self.isRunning:
            glRotatef(-runAngle, 1, 0, 0)
        else:
            glRotatef(-10, 1, 0, 0)
            glRotatef(5, 0, 0, 1)
        self.drawLeg()
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-0.7, -2.8, 0)
        if self.isRunning:
            glRotatef(runAngle, 1, 0, 0)
        else:
            glRotatef(15, 1, 0, 0)
            glRotatef(-5, 0, 0, 1)
        self.drawLeg()
        glPopMatrix()

        # Axe on back
        glPushMatrix()
        glTranslatef(0.5, 1.0, 0.8)
        glRotatef(25, 1, 0, 0)
        glRotatef(20, 0, 1, 0)
        glRotatef(20, 0, 0, 1)
        glScalef(0.8, 0.8, 0.8)
        drawAxeFunc()
        glPopMatrix()

        self.drawEnergyShield()
        glPopMatrix()

    def drawHead(self):
        glPushMatrix()
        glTranslatef(0, 2.95, 0)
        glColor3f(0.9, 0.7, 0.55)
        drawWarriorCube(1.5, 1.5, 1.5)
        glColor3f(0.2, 0.1, 0.05)
        glPushMatrix()
        glTranslatef(0, 0.5, 0)
        drawWarriorCube(1.55, 1.0, 1.55)
        glPopMatrix()
        glColor3f(0.2, 0.5, 0.9)
        glPushMatrix()
        glTranslatef(-0.3, 0.1, -0.76)
        drawWarriorCube(0.25, 0.25, 0.05)
        glTranslatef(0.6, 0, 0)
        drawWarriorCube(0.25, 0.25, 0.05)
        glPopMatrix()
        glColor3f(1.0, 0.85, 0.1)
        glPushMatrix()
        glTranslatef(0, 0.9, 0)
        drawWarriorCube(1.6, 0.3, 1.6)
        glColor3f(0.8, 0.1, 0.1)
        glTranslatef(0, 0.25, -0.8)
        drawWarriorCube(0.2, 0.2, 0.2)
        glColor3f(1.0, 0.85, 0.1)
        glTranslatef(-0.5, 0.05, 0)
        drawWarriorCube(0.1, 0.3, 0.1)
        glTranslatef(1.0, 0, 0)
        drawWarriorCube(0.1, 0.3, 0.1)
        glPopMatrix()
        glPopMatrix()

    def drawArm(self, is_left=False, sword_func=None, shield_func=None, is_blasting=False):
        glPushMatrix()
        glColor3f(0.7, 0.7, 0.8)
        drawWarriorCube(1.1, 1.1, 1.1)
        glColor3f(0.2, 0.2, 0.6)
        glTranslatef(0, -1.25, 0)
        drawWarriorCube(0.9, 1.5, 0.9)
        glTranslatef(0, -1.25, 0)
        glRotatef(15, 1, 0, 0)
        glColor3f(0.7, 0.7, 0.8)
        drawWarriorCube(0.8, 1.5, 0.8)
        if is_left and shield_func:
            shield_func()
        glColor3f(0.9, 0.7, 0.55)
        glTranslatef(0, -0.9, 0)
        drawWarriorCube(0.7, 0.5, 0.7)
        if not is_left and sword_func:
            glPushMatrix()
            if is_blasting:
                glRotatef(75, 1, 0, 0)
            sword_func()
            glPopMatrix()
        glPopMatrix()

    def drawLeg(self):
        glPushMatrix()
        glColor3f(0.3, 0.3, 0.35)
        drawWarriorCube(1.2, 2.0, 1.2)
        glTranslatef(0, -2.0, 0)
        glRotatef(5, 1, 0, 0)
        glColor3f(0.15, 0.1, 0.05)
        drawWarriorCube(1.1, 2.0, 1.1)
        glTranslatef(0, -1.0, -0.2)
        drawWarriorCube(1.1, 0.3, 1.5)
        glPopMatrix()

    def drawWeaponsAndShield(self):
        def drawSword():
            glPushMatrix()
            glTranslatef(0.0, -0.4, 0.1)
            glRotatef(-75, 1, 0, 0)
            glRotatef(-10, 0, 1, 0)
            glColor3f(0.3, 0.15, 0.05)
            drawWarriorCube(0.2, 1.0, 0.2)
            glColor3f(0.7, 0.7, 0.8)
            glTranslatef(0, -0.5, 0)
            drawWarriorCube(0.3, 0.2, 0.3)
            glTranslatef(0, 0.7, 0)
            drawWarriorCube(0.8, 0.2, 0.2)
            glColor3f(0.85, 0.85, 0.9)
            glTranslatef(0, 2.0, 0)
            drawWarriorCube(0.15, 3.0, 0.15)
            glTranslatef(0, 1.5, 0)
            glRotatef(45, 0, 0, 1)
            drawWarriorCube(0.1, 0.4, 0.15)
            glPopMatrix()

        def drawShield():
            glPushMatrix()
            glTranslatef(-0.5, 0.2, 0)
            glRotatef(-10, 1, 0, 0)
            glRotatef(15, 0, 0, 1)
            glColor3f(0.6, 0.6, 0.7)
            drawWarriorCube(0.2, 2.2, 2.2)
            glColor3f(1.0, 0.85, 0.1)
            glTranslatef(-0.11, 0, 0)
            drawWarriorCube(0.05, 1.5, 1.8)
            glTranslatef(0, 0, -0.7)
            drawWarriorCube(0.05, 0.6, 0.3)
            glTranslatef(0, 0, 1.4)
            drawWarriorCube(0.05, 0.6, 0.3)
            glPopMatrix()

        def drawAxe():
            glPushMatrix()
            glColor3f(0.5, 0.3, 0.1)
            drawWarriorCube(0.2, 3.5, 0.2)
            glColor3f(0.6, 0.6, 0.7)
            glTranslatef(0, 1.5, 0)
            glRotatef(90, 0, 0, 1)
            drawWarriorCube(1.5, 0.3, 0.3)
            glTranslatef(0, -0.8, 0)
            drawWarriorCube(0.2, 0.2, 0.2)
            glPopMatrix()
        return drawSword, drawShield, drawAxe

    def drawEnergyShield(self):
        if not self.isShieldActive:
            return
        glPushMatrix()
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glTranslatef(0, 0.5, -4.0)
        glColor4f(0.3, 0.7, 1.0, self.shieldAlpha)
        drawWarriorCube(7, 7, 0.3)
        glDisable(GL_BLEND)
        glPopMatrix()

# -----------------------------------------------------------------------------
# --- Dragon Class ---
# -----------------------------------------------------------------------------


class Dragon:
    def __init__(self, position=(0, 20, -30)):
        # --- MODIFIED: Give each dragon a random starting position ---
        self.position = [random.uniform(-WORLD_SIZE/2, WORLD_SIZE/2), 
                         random.uniform(20, 35), 
                         random.uniform(-WORLD_SIZE/2, WORLD_SIZE/2)]
        self.health = DRAGON_MAX_HEALTH
        self.isAlive = True
        self.deathTimer = 0
        # Animation
        self.wingAngle = 0
        self.jawAngle = 0.0
        self.breathingOffset = 0.0
        self.tailSwayAngle = 0.0
        self.headRotX = 0.0
        self.headRotY = 0.0
        self.bodyRotY = 0.0
        # AI
        self.attackCooldown = 0
        self.targetPosition = list(self.position)
        self.moveTimer = 0
        self.isEvading = False
        self.evadeTimer = 0
        self.circlingAngle = random.uniform(0, 2 * math.pi) # Random start angle
        self.circlingDirection = random.choice([-1, 1]) # Random start direction

    def takeDamage(self, amount):
        if not self.isAlive: return
        self.health -= amount
        print(f"Dragon hit! Health: {self.health}")
        if self.health <= 0:
            self.isAlive = False
            self.deathTimer = time.time()
            print("Dragon defeated!")

    def update(self, playerPos, playerProjectiles):
        currentTime = time.time()
        if not self.isAlive:
            if currentTime - self.deathTimer > DRAGON_RESPAWN_TIME:
                self.respawn()
            return

        # Evasion AI
        if not self.isEvading:
            for proj in playerProjectiles:
                distSq = sum([(self.position[i] - proj['pos'][i])**2 for i in range(3)])
                if distSq < 100: # Evasion radius
                    self.evade(proj)
                    break
        
        if self.isEvading and currentTime > self.evadeTimer:
            self.isEvading = False

        # Movement AI (Circling the player)
        if not self.isEvading:
            self.circlingAngle += 0.01 * self.circlingDirection
            radius = 40
            targetX = playerPos[0] + radius * math.cos(self.circlingAngle)
            targetZ = playerPos[2] + radius * math.sin(self.circlingAngle)
            self.targetPosition = [targetX, 20, targetZ]
            if random.random() < 0.01:
                self.circlingDirection *= -1 # Change direction occasionally

        direction = [self.targetPosition[i] - self.position[i] for i in range(3)]
        dist = math.sqrt(sum(d*d for d in direction))
        if dist > 1:
            moveSpeed = 0.2 if self.isEvading else 0.1
            for i in range(3): self.position[i] += direction[i]/dist * moveSpeed
            targetBodyRotY = math.degrees(math.atan2(direction[0], direction[2]))
            angleDiff = (targetBodyRotY - self.bodyRotY + 180) % 360 - 180
            self.bodyRotY += angleDiff * 0.05

        # Aim at player (head rotation)
        directionToPlayer = [playerPos[i] - self.position[i] for i in range(3)]
        playerYaw = math.degrees(math.atan2(directionToPlayer[0], directionToPlayer[2]))
        self.headRotY = playerYaw - self.bodyRotY
        distXZ = math.sqrt(directionToPlayer[0]**2 + directionToPlayer[2]**2)
        self.headRotX = -math.degrees(math.atan2(directionToPlayer[1], distXZ))

        # Attack AI
        if currentTime > self.attackCooldown and not self.isEvading:
            self.shootFireball()
            self.attackCooldown = currentTime + random.uniform(2, 4)

        # Animation
        self.wingAngle = math.sin(currentTime * 5) * 40
        self.breathingOffset = math.sin(currentTime * 2.0) * 0.1
        self.tailSwayAngle = math.sin(currentTime * 1.0) * 8
        if self.jawAngle > 0: self.jawAngle = max(0, self.jawAngle - 50 * 0.016)

    def evade(self, projectile):
        self.isEvading = True
        self.evadeTimer = time.time() + 2.0 # Evade for 2 seconds

        # Simple evasion: move up and to the side
        self.targetPosition[1] += 10 # Fly up
        # Move perpendicular to projectile path
        projVel = projectile['vel']
        sideVec = [-projVel[2], 0, projVel[0]]
        mag = math.sqrt(sideVec[0]**2 + sideVec[2]**2)
        if mag > 0:
            self.targetPosition[0] += sideVec[0]/mag * 20
            self.targetPosition[2] += sideVec[2]/mag * 20
        print("Dragon evading!")

    def shootFireball(self):
        global dragonFireballs
        if not self.isAlive: return
        self.jawAngle = 25
        speed = 25.0
        finalYawRad = math.radians(self.bodyRotY + self.headRotY)
        finalPitchRad = math.radians(self.headRotX)
        velX = speed * math.cos(finalPitchRad) * math.sin(finalYawRad)
        velY = -speed * math.sin(finalPitchRad)
        velZ = speed * math.cos(finalPitchRad) * math.cos(finalYawRad)
        startPos = list(self.position)
        bodyRotRad = math.radians(self.bodyRotY)
        neckOffset = [0, 3.5, 3.0]
        startPos[0] += neckOffset[2] * math.sin(bodyRotRad)
        startPos[2] += neckOffset[2] * math.cos(bodyRotRad)
        startPos[1] += neckOffset[1]
        # --- MODIFIED LINE ---
        dragonFireballs.append({'pos': startPos, 'vel': [velX, velY, velZ], 'life': 5.0, 'max_life': 5.0, 'size': 1.0, 'state': 'flying'})

    def respawn(self):
        self.position = [random.uniform(-WORLD_SIZE/2, WORLD_SIZE/2), random.uniform(20, 35), random.uniform(-WORLD_SIZE/2, WORLD_SIZE/2)]
        self.health = DRAGON_MAX_HEALTH
        self.isAlive = True
        print("A new dragon has appeared!")

    def draw(self):
        if not self.isAlive: return
        glPushMatrix()
        glTranslatef(self.position[0], self.position[1], self.position[2])
        glRotatef(-self.bodyRotY, 0, 1, 0)  # Rotate body
        glPushMatrix()
        glTranslatef(0, self.breathingOffset, 0)
        self.drawTorso()
        self.drawNeck()
        self.drawHead(self.breathingOffset, self.headRotX, self.headRotY, self.jawAngle)
        self.drawLegs()
        self.drawTail(self.tailSwayAngle)
        glPushMatrix()
        glTranslatef(1.8, 2.5, 0.5)
        glRotatef(self.wingAngle, 0, 0, 1)
        self.drawWing(1)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(-1.8, 2.5, 0.5)
        glRotatef(-self.wingAngle, 0, 0, 1)
        self.drawWing(-1)
        glPopMatrix()
        glPopMatrix()
        glPopMatrix()

    def drawCube(self, scale=(1, 1, 1), position=(0, 0, 0)):
        glPushMatrix()
        glTranslatef(*position)
        glScalef(*scale)
        glutSolidCube(1)
        glPopMatrix()

    def drawPyramid(self, scale=(1, 1, 1), position=(0, 0, 0)):
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

    def drawSphere(self, radius=1, position=(0, 0, 0)):
        glPushMatrix()
        glTranslatef(*position)
        glutSolidSphere(radius, 20, 20)
        glPopMatrix()

    def drawSpine(self):
        glColor3f(0.8, 0.1, 0.1)
        for i in range(5):
            sizeMultiplier = 1.0 - abs(i - 2) * 0.3
            self.drawPyramid(scale=(0.8 * sizeMultiplier, 1.5 *
                             sizeMultiplier, 0.3), position=(0, 3.5, 2.0 - i * 1.2))

    def drawTorso(self):
        glColor3f(0.1, 0.6, 0.2)
        self.drawCube(scale=(3.5, 3, 5.5), position=(0, 1.5, 0))
        glColor3f(0.2, 0.7, 0.3)
        self.drawCube(scale=(4, 3.5, 2), position=(0, 1.5, 1.5))
        glColor3f(0.9, 0.9, 0.2)
        for i in range(5):
            self.drawCube(scale=(2.5, 0.4, 0.8),
                          position=(0, -0.2, 2.0 - i * 1.0))
        self.drawSpine()

    def drawHead(self, breathingOffset=0.0, headRotX=0.0, headRotY=0.0, jawAngle=0.0):
        glPushMatrix()
        glTranslatef(0, 3.5, 3.0)
        glRotatef(breathingOffset * -20, 1, 0, 0)
        glRotatef(headRotY, 0, 1, 0)
        glRotatef(headRotX, 1, 0, 0)
        glColor3f(0.1, 0.6, 0.2)
        self.drawCube(scale=(2, 1.8, 2.5), position=(0, 0, 0))
        self.drawCube(scale=(1.5, 1.2, 2.5), position=(0, -0.2, 2.0))
        glColor3f(1.0, 1.0, 0.9)
        for i in range(5):
            glPushMatrix()
            glTranslatef(-0.6 + i*0.3, -0.55, 3.0)
            glRotatef(180, 1, 0, 0)
            self.drawPyramid(scale=(0.2, 0.8, 0.2), position=(0, 0, 0))
            glPopMatrix()
        glPushMatrix()
        glTranslatef(0, -0.7, 0.85)
        glRotatef(jawAngle, 1, 0, 0)
        glTranslatef(0, -0.2, 1.15)
        glColor3f(0.2, 0.7, 0.3)
        self.drawCube(scale=(1.4, 0.5, 2.3))
        glColor3f(1.0, 1.0, 0.9)
        for i in range(4):
            self.drawPyramid(scale=(0.2, 0.7, 0.2),
                             position=(-0.5, 0.25, -0.8 + i*0.5))
            self.drawPyramid(scale=(0.2, 0.7, 0.2),
                             position=(0.5, 0.25, -0.8 + i*0.5))
        glPopMatrix()
        glColor3f(1.0, 0.0, 0.0)
        self.drawSphere(radius=0.2, position=(-0.6, 0.5, 1.5))
        self.drawSphere(radius=0.2, position=(0.6, 0.5, 1.5))
        glColor3f(0.9, 0.9, 0.2)
        self.drawPyramid(scale=(0.4, 2.0, 0.4), position=(-0.8, 0.8, -0.5))
        self.drawPyramid(scale=(0.4, 2.0, 0.4), position=(0.8, 0.8, -0.5))
        self.drawPyramid(scale=(0.3, 1.5, 0.3), position=(-0.5, 0.8, -1.2))
        self.drawPyramid(scale=(0.3, 1.5, 0.3), position=(0.5, 0.8, -1.2))
        glPopMatrix()

    def drawNeck(self):
        glColor3f(0.1, 0.6, 0.2)
        glPushMatrix()
        glTranslatef(0, 2.5, 2.5)
        self.drawCube(scale=(2, 2, 1))
        glRotatef(-15, 1, 0, 0)
        glTranslatef(0, 0.5, 0.8)
        self.drawCube(scale=(1.8, 1.8, 1))
        glPopMatrix()

    def drawLegs(self):
        self.drawLeg(position=(-2.2, 0, 1.5))
        self.drawLeg(position=(2.2, 0, 1.5))
        self.drawLeg(position=(-1.8, 0, -2.0), is_rear=True)
        self.drawLeg(position=(1.8, 0, -2.0), is_rear=True)

    def drawLeg(self, position, is_rear=False):
        glPushMatrix()
        glTranslatef(*position)
        initialLegAngle = 45 if is_rear else 55
        glRotatef(initialLegAngle, 1, 0, 0)
        glColor3f(0.1, 0.6, 0.2)
        glPushMatrix()
        glRotatef(-40, 1, 0, 0)
        self.drawCube(scale=(0.8, 2.0, 1.0), position=(0, -1.0, 0))
        glTranslatef(0, -2.0, 0)
        glRotatef(80, 1, 0, 0)
        self.drawCube(scale=(0.7, 1.8, 0.7), position=(0, -0.8, 0))
        glColor3f(0.2, 0.7, 0.3)
        footZOffset = 0.5
        glRotatef(-20, 1, 0, 0)
        self.drawCube(scale=(1.0, 0.4, 1.5),
                      position=(0, -1.8, footZOffset))
        glColor3f(0.9, 0.9, 0.2)
        clawYPos = -1.8
        clawZOffset = 0.8 + footZOffset
        self.drawPyramid(scale=(0.2, 0.5, 0.2),
                         position=(-0.3, clawYPos, clawZOffset))
        self.drawPyramid(scale=(0.2, 0.5, 0.2), position=(
            0, clawYPos, clawZOffset))
        self.drawPyramid(scale=(0.2, 0.5, 0.2), position=(
            0.3, clawYPos, clawZOffset))
        glPopMatrix()
        glPopMatrix()

    def drawTail(self, swayAngle=0.0):
        glColor3f(0.1, 0.6, 0.2)
        glPushMatrix()
        glTranslatef(0, 1.5, -2.5)
        glRotatef(swayAngle, 0, 1, 0)
        glRotatef(15, 1, 0, 0)
        currentTime = time.time()
        for i in range(8):
            scaleFactor = 1.0 - i * 0.08
            self.drawCube(scale=(1.5*scaleFactor, 1.5*scaleFactor, 1.5))
            glTranslatef(0, -0.1, -1.4)
            glRotatef(math.sin(currentTime * 3 + i * 0.8) * 4, 1, 0, 0)
            glRotatef(math.sin(currentTime * 2 + i * 0.5) * 5, 0, 1, 0)
        glColor3f(0.9, 0.9, 0.2)
        self.drawPyramid(scale=(0.5, 1.0, 0.5), position=(0, 0, 0))
        glPopMatrix()

    def drawWing(self, side):
        glPushMatrix()
        glColor3f(0.1, 0.6, 0.2)
        self.drawCube(scale=(2.0, 0.4, 0.4), position=(side * 1.0, 0, 0))
        glTranslatef(side * 2.0, 0, 0)
        glRotatef(-side * 30, 0, 1, 0)
        self.drawCube(scale=(2.5, 0.4, 0.4), position=(side * 1.25, 0, 0))
        glTranslatef(side * 2.5, 0, 0)
        sparDefinitions = [{'angle': -20, 'length': 4.0},
                           {'angle': 15, 'length': 6.0}, {'angle': 50, 'length': 5.0}]
        sparEndpoints = []
        for spar in sparDefinitions:
            angleRad = math.radians(spar['angle'])
            endPoint = (side * spar['length'] * math.sin(angleRad),
                        0, -spar['length'] * math.cos(angleRad))
            sparEndpoints.append(endPoint)
        glColor3f(0.8, 0.1, 0.1)
        glBegin(GL_TRIANGLES)
        glNormal3f(0, side, 0)
        wristPos = (0, 0, 0)
        elbowPos = (-side * 2.5, 0, 0)
        glVertex3fv(elbowPos)
        glVertex3fv(wristPos)
        glVertex3fv(sparEndpoints[0])
        for i in range(len(sparEndpoints) - 1):
            glVertex3fv(wristPos)
            glVertex3fv(sparEndpoints[i])
            glVertex3fv(sparEndpoints[i+1])
        glEnd()
        glColor3f(0.1, 0.6, 0.2)
        for i, spar in enumerate(sparDefinitions):
            glPushMatrix()
            glRotatef(spar['angle'], 0, side, 0)
            self.drawCube(scale=(0.2, 0.2, spar['length']), position=(
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
        self.playerRadius = 0.5
        self.isThirdPerson = True
        self.thirdPersonDistance = 10.0
        self.thirdPersonElevation = 15.0

    def isColliding(self, nextPos):
        collidableTypes = {'boundary_walls': WALL_BLOCK_SIZE, 'random_walls': WALL_BLOCK_SIZE, 'trees': TREE_COLLISION_SIZE, 'shrubs': SHRUB_COLLISION_SIZE, 'temp_walls': WALL_BLOCK_SIZE}
        for objKey, objSize in collidableTypes.items():
            positions = objectPositions.get(objKey, [])
            if objKey == 'temp_walls':
                positions = [item['pos'] for item in positions]
            for objPos in positions:
                if (nextPos[0] + self.playerRadius > objPos[0] - objSize / 2 and nextPos[0] - self.playerRadius < objPos[0] + objSize / 2 and
                        nextPos[2] + self.playerRadius > objPos[2] - objSize / 2 and nextPos[2] - self.playerRadius < objPos[2] + objSize / 2):
                    return True
        return False

    def update(self):
        global warrior
        if isControlsLocked or gameOver:
            return
        yawRad = math.radians(self.rotation[0])
        forwardVec = [math.sin(yawRad), 0, -math.cos(yawRad)]
        strafeVec = [math.cos(yawRad), 0, math.sin(yawRad)]
        moveVec = [0, 0, 0]
        if keys[b'w']:
            moveVec[0] += forwardVec[0]
            moveVec[2] += forwardVec[2]
        if keys[b's']:
            moveVec[0] -= forwardVec[0]
            moveVec[2] -= forwardVec[2]
        if keys[b'a']:
            moveVec[0] -= strafeVec[0]
            moveVec[2] -= strafeVec[2]
        if keys[b'd']:
            moveVec[0] += strafeVec[0]
            moveVec[2] += strafeVec[2]
        magnitude = math.sqrt(moveVec[0]**2 + moveVec[2]**2)
        if magnitude > 0:
            moveVec[0] *= self.speed / magnitude
            moveVec[2] *= self.speed / magnitude
        if keys[b'x']:
            warrior.position[1] += self.speed
        if keys[b'c']:
            warrior.position[1] -= self.speed
        if magnitude > 0:
            warrior.rotationY = - \
                math.degrees(math.atan2(-moveVec[2], -moveVec[0])) + 90
        nextPosX = [warrior.position[0] + moveVec[0],
                    warrior.position[1], warrior.position[2]]
        if not self.isColliding(nextPosX):
            warrior.position[0] += moveVec[0]
        nextPosZ = [warrior.position[0], warrior.position[1],
                    warrior.position[2] + moveVec[2]]
        if not self.isColliding(nextPosZ):
            warrior.position[2] += moveVec[2]
        if warrior.position[1] < 1.0:
            warrior.position[1] = 1.0

    def handleMouse(self, x, y):
        global isMouseWarping, lastMousePos
        if isMouseWarping:
            isMouseWarping = False
            lastMousePos['x'], lastMousePos['y'] = x, y
            return
        dx, dy = x - lastMousePos['x'], y - lastMousePos['y']
        self.rotation[0] += dx * self.sensitivity
        self.rotation[1] = max(-89.0, min(89.0,
                                           self.rotation[1] - dy * self.sensitivity))
        centerX, centerY = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
        if abs(x - centerX) > 200 or abs(y - centerY) > 200:
            isMouseWarping = True
            glutWarpPointer(centerX, centerY)
        else:
            lastMousePos['x'], lastMousePos['y'] = x, y

    def getCameraForwardVector(self):
        yawRad = math.radians(self.rotation[0])
        pitchRad = math.radians(self.rotation[1])
        x = math.sin(yawRad) * math.cos(pitchRad)
        y = math.sin(pitchRad)
        z = -math.cos(yawRad) * math.cos(pitchRad)
        mag = math.sqrt(x*x + y*y + z*z)
        return [x/mag, y/mag, z/mag]

    def look(self):
        glLoadIdentity()
        if self.isThirdPerson:
            camX = warrior.position[0] - self.thirdPersonDistance * math.sin(math.radians(
                self.rotation[0])) * math.cos(math.radians(self.thirdPersonElevation))
            camY = warrior.position[1] + self.thirdPersonDistance * \
                math.sin(math.radians(self.thirdPersonElevation)) + 2.0
            camZ = warrior.position[2] + self.thirdPersonDistance * math.cos(math.radians(
                self.rotation[0])) * math.cos(math.radians(self.thirdPersonElevation))
            self.position = [camX, camY, camZ]
            lookTargetY = warrior.position[1] + 1.5
            gluLookAt(camX, camY, camZ,
                      warrior.position[0], lookTargetY, warrior.position[2], 0, 1, 0)
        else:
            pitchRad, yawRad = math.radians(
                self.rotation[1]), math.radians(self.rotation[0])
            camPos = [warrior.position[0],
                      warrior.position[1] + 4.0, warrior.position[2]]
            self.position = camPos
            lookAtPoint = [camPos[0] + math.sin(yawRad) * math.cos(pitchRad), camPos[1] + math.sin(
                pitchRad), camPos[2] - math.cos(yawRad) * math.cos(pitchRad)]
            gluLookAt(camPos[0], camPos[1], camPos[2], lookAtPoint[0],
                      lookAtPoint[1], lookAtPoint[2], 0, 1, 0)

# -----------------------------------------------------------------------------
# --- World Generation and Drawing ---
# -----------------------------------------------------------------------------


def drawCube(size, colors):
    s = size / 2.0
    vertices = [[-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s],
                [-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s]]
    faces = [(0, 1, 2, 3), (1, 5, 6, 2), (5, 4, 7, 6),
             (4, 0, 3, 7), (3, 2, 6, 7), (4, 5, 1, 0)]
    glBegin(GL_QUADS)
    for i, face in enumerate(faces):
        glColor3fv(colors[i % len(colors)])
        for vIdx in face:
            glVertex3fv(vertices[vIdx])
    glEnd()


def drawTreeGeometry(): glPushMatrix(); trunkColor = [(0.4, 0.2, 0.0)]*6; trunkSize = 1.0; [(drawCube(trunkSize, trunkColor), glTranslatef(0, trunkSize, 0)) for _ in range(5)]; leafColors = [(0.0, 0.5, 0.0), (0.0, 0.6, 0.0)]; glTranslatef(0, 2, 0); drawCube(
    4, leafColors); glTranslatef(1.5, -1, 0); drawCube(2.5, leafColors); glTranslatef(-3.0, 0, 0); drawCube(2.5, leafColors); glTranslatef(1.5, 1, 0); glTranslatef(0, -1, 1.5); drawCube(2.5, leafColors); glTranslatef(0, 0, -3.0); drawCube(2.5, leafColors); glPopMatrix()


def drawWallGeometry(): glPushMatrix(); wallColors = [(0.6, 0.6, 0.6), (0.55, 0.55, 0.55)]; drawCube(
    WALL_BLOCK_SIZE, wallColors); glTranslatef(0, WALL_BLOCK_SIZE, 0); drawCube(WALL_BLOCK_SIZE, wallColors); glPopMatrix()


def drawShrubGeometry(): glPushMatrix(); leafColors = [(0.1, 0.4, 0.1), (0.1, 0.5, 0.1)]; drawCube(2.0, leafColors); glTranslatef(0.75, -0.5, 0); drawCube(
    1.5, leafColors); glTranslatef(-1.5, 0, 0); drawCube(1.5, leafColors); glTranslatef(0.75, 0.5, 0.75); drawCube(1.5, leafColors); glTranslatef(0, 0, -1.5); drawCube(1.5, leafColors); glPopMatrix()


# --- REPLACED HEART GEOMETRY ---
def drawHeartGeometry():
    """Draws a better, blocky 3D heart shape that fits the game's art style."""
    glPushMatrix()
    glColor3f(1.0, 0.0, 0.0) # Bright red

    # Base size for the blocks
    s = 0.5

    # Central column (3 blocks high)
    glPushMatrix()
    glTranslatef(0, s, 0)
    glScalef(s, s * 3, s)
    glutSolidCube(1.0)
    glPopMatrix()

    # Side columns (2 blocks high)
    glPushMatrix()
    glTranslatef(-s, s * 1.5, 0)
    glScalef(s, s * 2, s)
    glutSolidCube(1.0)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(s, s * 1.5, 0)
    glScalef(s, s * 2, s)
    glutSolidCube(1.0)
    glPopMatrix()

    # Topmost outer blocks (1 block high)
    glPushMatrix()
    glTranslatef(-s * 2, s * 2, 0)
    glScalef(s, s, s)
    glutSolidCube(1.0)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(s * 2, s * 2, 0)
    glScalef(s, s, s)
    glutSolidCube(1.0)
    glPopMatrix()
    
    glPopMatrix()
# -------------------------


def drawGround(): glColor3f(0.1, 0.6, 0.1); glBegin(GL_QUADS); glVertex3f(-WORLD_SIZE, 0, -WORLD_SIZE); glVertex3f(-WORLD_SIZE,
                                                                                                                   0, WORLD_SIZE); glVertex3f(WORLD_SIZE, 0, WORLD_SIZE); glVertex3f(WORLD_SIZE, 0, -WORLD_SIZE); glEnd()


def drawPlayerProjectiles():
    for p in playerProjectiles:
        glPushMatrix()
        glTranslatef(p['pos'][0], p['pos'][1], p['pos'][2])
        glColor3f(0.2, 1.0, 0.8)
        glutSolidSphere(0.2, 10, 10)
        glPopMatrix()


def drawBillboardParticles(particles, modelviewMatrix):
    camRight = [modelviewMatrix[0][0],
                modelviewMatrix[1][0], modelviewMatrix[2][0]]
    camUp = [modelviewMatrix[0][1],
             modelviewMatrix[1][1], modelviewMatrix[2][1]]
    glBegin(GL_QUADS)
    for p in particles:
        lifeRatio = p['life'] / p['max_life']
        size = p.get('size', 0.1) * lifeRatio
        pos = p['pos']
        color = p['color'] + (lifeRatio,)
        glColor4fv(color)
        p1 = [pos[i] - (camRight[i] + camUp[i]) * size for i in range(3)]
        p2 = [pos[i] + (camRight[i] - camUp[i]) * size for i in range(3)]
        p3 = [pos[i] + (camRight[i] + camUp[i]) * size for i in range(3)]
        p4 = [pos[i] - (camRight[i] - camUp[i]) * size for i in range(3)]
        glVertex3fv(p1)
        glVertex3fv(p2)
        glVertex3fv(p3)
        glVertex3fv(p4)
    glEnd()


def drawFireAndEmbers(modelviewMatrix):
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)
    glDepthMask(GL_FALSE)
    fireParticles = []
    
    # --- MODIFIED: Filter for only flying fireballs ---
    flyingFireballs = [p for p in dragonFireballs if p.get('state', 'flying') == 'flying']

    for p in flyingFireballs: # Use the filtered list now
        lifeRatio = p['life'] / p['max_life']
        for _ in range(30):
            offset = [random.uniform(-1, 1) * p['size']
                      * lifeRatio for _ in range(3)]
            distFromCenter = math.sqrt(sum(x*x for x in offset))
            gChannel = max(0, 1.0 - distFromCenter /
                           (p['size'] * lifeRatio))
            particleColor = (1.0, 0.5 + gChannel*0.5, 0.0)
            fireParticles.append({'pos': [p['pos'][i] + offset[i] for i in range(
                3)], 'life': p['life'], 'max_life': p['max_life'], 'size': 0.4, 'color': particleColor})
    
    if fireParticles:
        drawBillboardParticles(fireParticles, modelviewMatrix)
    
    emberParticles = []
    for p in embers:
        emberParticles.append(
            {'pos': p['pos'], 'life': p['life'], 'max_life': p['max_life'], 'size': 0.1, 'color': (1.0, 0.4, 0.0)})
    
    if emberParticles:
        drawBillboardParticles(emberParticles, modelviewMatrix)
    
    glDepthMask(GL_TRUE)
    glDisable(GL_BLEND)


def drawUi():
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
            
    # --- MODIFIED FOR MULTIPLE DRAGON HEALTH BARS ---
    y_offset = 0
    for dragon in dragons:
        if dragon.isAlive:
            top_y = WINDOW_HEIGHT - 10 - y_offset
            bottom_y = WINDOW_HEIGHT - 30 - y_offset
            
            # Background
            glColor3f(1, 0, 0)
            glRectf(WINDOW_WIDTH - 210, bottom_y, WINDOW_WIDTH - 10, top_y)
            
            # Health
            glColor3f(0.8, 0, 0.8)
            health_width = 200 * (dragon.health / DRAGON_MAX_HEALTH)
            glRectf(WINDOW_WIDTH - 210, bottom_y, WINDOW_WIDTH - 210 + health_width, top_y)
            
            y_offset += 25 # Gap for the next bar
    # ---------------------------------------------
    
    if gameOver:
        glColor3f(1, 0, 0)
        drawText("GAME OVER", WINDOW_WIDTH/2 - 50, WINDOW_HEIGHT/2)
        drawText("Press 'R' to restart", WINDOW_WIDTH /
                 2 - 70, WINDOW_HEIGHT/2 - 30)
    if not camera.isThirdPerson:
        drawCrosshair()
    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()


def drawText(text, x, y):
    glWindowPos2f(x, y)
    for character in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(character))


def drawCrosshair():
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


def isPositionSafe(pos, radius):
    collidableTypes = {'boundary_walls': WALL_BLOCK_SIZE, 'random_walls': WALL_BLOCK_SIZE,
                       'trees': TREE_COLLISION_SIZE, 'shrubs': SHRUB_COLLISION_SIZE}
    for objKey, objSize in collidableTypes.items():
        for objPos in objectPositions.get(objKey, []):
            if (pos[0] - objPos[0])**2 + (pos[2] - objPos[2])**2 < (radius + objSize / 2)**2:
                return False
    return True


def findSafeSpawnPoint():
    while True:
        x = random.uniform(-WORLD_SIZE * 0.8, WORLD_SIZE * 0.8)
        z = random.uniform(-WORLD_SIZE * 0.8, WORLD_SIZE * 0.8)
        pos = [x, 1.0, z]
        if isPositionSafe(pos, 2.0):
            return pos

# --- ADDED FOR HEARTS ---
def spawnHeart():
    """Finds a safe location and spawns a new heart there."""
    pos = findSafeSpawnPoint()
    pos[1] = 2.0 # Set height for the heart to float
    hearts.append({'position': pos})
# -------------------------

def spawnBomb():
    bombs.append({'position': [random.uniform(-WORLD_SIZE, WORLD_SIZE), 0.5, random.uniform(-WORLD_SIZE, WORLD_SIZE)], 'state': 'idle', 'triggered_time': 0, 'explosion_start_time': 0})

def spawnBlockingWall():
    yawRad = math.radians(camera.rotation[0])
    forwardVec = [math.sin(yawRad), 0, -math.cos(yawRad)]
    strafeVec = [math.cos(yawRad), 0, math.sin(yawRad)]
    centerPos = [warrior.position[0]+forwardVec[0]*WALL_SPAWN_DISTANCE, 0, warrior.position[2]+forwardVec[2]*WALL_SPAWN_DISTANCE]
    for i in range(-1, 2):
        objectPositions['temp_walls'].append({'pos': [centerPos[0]+strafeVec[0]*i*WALL_BLOCK_SIZE, centerPos[1], centerPos[2]+strafeVec[2]*i*WALL_BLOCK_SIZE], 'despawn_time': time.time()+WALL_LIFETIME})
    print("A blocking wall appears!")


def updateGameLogic():
    global playerProjectiles, dragonFireballs, embers, bombs, hearts, objectPositions, gameState
    if gameOver:
        return

    currentTime = time.time()
    
    # --- ADDED FOR HEARTS ---
    for heart in hearts[:]: # Iterate over a copy
        distSq = (heart['position'][0] - warrior.position[0])**2 + \
                 (heart['position'][1] - (warrior.position[1] + warrior.yPos))**2 + \
                 (heart['position'][2] - warrior.position[2])**2
        
        if distSq < HEART_TRIGGER_RADIUS**2:
            warrior.heal(HEART_HEAL_AMOUNT)
            hearts.remove(heart)
            spawnHeart() # Spawn a new one to replace it
    # -------------------------
            
    for bomb in bombs[:]:
        if bomb.get('state') == 'idle':
            if (bomb['position'][0]-warrior.position[0])**2 + (bomb['position'][2]-warrior.position[2])**2 < BOMB_TRIGGER_RADIUS**2:
                bomb['state'] = 'triggered'
                bomb['triggered_time'] = currentTime
                print("Bomb triggered!")
        elif bomb.get('state') == 'triggered':
            if currentTime > bomb['triggered_time']+BOMB_FUSE_TIME:
                bomb['state'] = 'exploding'
                bomb['explosion_start_time'] = currentTime
                bomb['damage_dealt'] = False  # Add a flag to ensure damage is dealt only once
                print("Boom!")
        elif bomb.get('state') == 'exploding':
            progress = (currentTime - bomb['explosion_start_time']) / BOMB_EXPLOSION_DURATION
            if progress < 1.0:
                currentRadius = progress * BOMB_EXPLOSION_MAX_RADIUS
                distToPlayerSq = (bomb['position'][0] - warrior.position[0])**2 + (bomb['position'][1] - (warrior.position[1] + warrior.yPos))**2 + (bomb['position'][2] - warrior.position[2])**2
                
                if distToPlayerSq < currentRadius**2 and not bomb.get('damage_dealt', False):
                    warrior.takeDamage(40)
                    bomb['damage_dealt'] = True
                    
            if currentTime > bomb['explosion_start_time']+BOMB_EXPLOSION_DURATION:
                bombs.remove(bomb)
                spawnBomb()
                
    objectPositions['temp_walls'] = [w for w in objectPositions['temp_walls'] if currentTime < w['despawn_time']]
    if currentTime > gameState.get('lastWallCheck', 0) + WALL_SPAWN_INTERVAL:
        gameState['lastWallCheck'] = currentTime
        if random.random() < WALL_SPAWN_CHANCE:
            spawnBlockingWall()

    # --- MODIFIED FOR MULTIPLE DRAGONS ---
    # Update player projectiles
    updatedProjectiles = []
    for proj in playerProjectiles:
        proj['pos'][0] += proj['vel'][0]
        proj['pos'][1] += proj['vel'][1]
        proj['pos'][2] += proj['vel'][2]
        proj['life'] -= 1

        hit_a_dragon = False
        if proj['life'] > 0:
            for dragon in dragons:
                if dragon.isAlive:
                    distSq = (proj['pos'][0] - dragon.position[0])**2 + \
                             (proj['pos'][1] - dragon.position[1])**2 + \
                             (proj['pos'][2] - dragon.position[2])**2
                    if distSq < 10:  # Hit radius
                        dragon.takeDamage(10)
                        hit_a_dragon = True
                        break  # Projectile is consumed, stop checking other dragons
        
        if not hit_a_dragon and proj['life'] > 0:
            updatedProjectiles.append(proj)
            
    playerProjectiles = updatedProjectiles
    # ------------------------------------

    # Update dragon fireballs
    gravity = 9.8 * 0.016
    updatedFireballs = []
    warriorPosWithJump = [warrior.position[0], warrior.position[1] + warrior.yPos, warrior.position[2]]

    for p in dragonFireballs:
        isExplodingThisFrame = False

        # --- Handle flying fireballs ---
        if p.get('state', 'flying') == 'flying':
            for i in range(3): p['pos'][i] += p['vel'][i] * 0.016
            p['vel'][1] -= gravity
            p['life'] -= 0.016

            if random.random() < 0.8:
                embers.append({'pos': p['pos'][:], 'vel': [v*0.1 + random.uniform(-0.2, 0.2) for v in p['vel']], 'life': 0.8, 'max_life': 0.8})

            distToPlayerSq = sum([(p['pos'][i] - warriorPosWithJump[i])**2 for i in range(3)])
            
            if distToPlayerSq < 4:
                warrior.takeDamage(20)
                isExplodingThisFrame = True
                p['damage_dealt'] = True
            
            elif p['pos'][1] <= 0.1 or p['life'] <= 0:
                isExplodingThisFrame = True
                p['damage_dealt'] = False

            if isExplodingThisFrame:
                p['state'] = 'exploding'
                p['explosion_start_time'] = currentTime
                p['explosion_pos'] = list(p['pos'])
                if p['pos'][1] <= 0.1: p['explosion_pos'][1] = 0.1
        
        # --- Handle exploding fireballs (Area of Effect Damage) ---
        if p.get('state') == 'exploding':
            progress = (currentTime - p['explosion_start_time']) / FIREBALL_EXPLOSION_DURATION
            
            if progress < 1.0:
                if not p.get('damage_dealt', False):
                    currentRadius = progress * FIREBALL_EXPLOSION_MAX_RADIUS
                    distToPlayerSq = sum([(p['explosion_pos'][i] - warriorPosWithJump[i])**2 for i in range(3)])
                    if distToPlayerSq < currentRadius**2:
                        warrior.takeDamage(FIREBALL_SPLASH_DAMAGE)
                        p['damage_dealt'] = True
                updatedFireballs.append(p)
        
        # --- Keep non-exploding fireballs ---
        elif p.get('state', 'flying') == 'flying':
            updatedFireballs.append(p)

    dragonFireballs = updatedFireballs

    # Update embers separately
    for p in embers:
        for i in range(3): p['pos'][i] += p['vel'][i] * 0.016
        p['vel'][1] -= gravity * 0.5
        p['life'] -= 0.016
    embers = [p for p in embers if p['life'] > 0]


def compileDisplayLists():
    glNewList(LIST_IDS['tree'], GL_COMPILE)
    drawTreeGeometry()
    glEndList()
    glNewList(LIST_IDS['wall'], GL_COMPILE)
    drawWallGeometry()
    glEndList()
    glNewList(LIST_IDS['rock'], GL_COMPILE)
    drawCube(1, [(0.5, 0.5, 0.5)])
    glEndList()
    glNewList(LIST_IDS['shrub'], GL_COMPILE)
    drawShrubGeometry()
    glEndList()


def generateWorld():
    global objectPositions
    wallSpacing = WALL_BLOCK_SIZE
    numWalls = int(WORLD_SIZE * 2 / wallSpacing)
    objectPositions = {'trees': [(random.uniform(-WORLD_SIZE, WORLD_SIZE), 0, random.uniform(-WORLD_SIZE, WORLD_SIZE)) for _ in range(150)], 'rocks': [(random.uniform(-WORLD_SIZE, WORLD_SIZE), 0.5, random.uniform(-WORLD_SIZE, WORLD_SIZE)) for _ in range(70)], 'shrubs': [(random.uniform(-WORLD_SIZE, WORLD_SIZE), 1, random.uniform(-WORLD_SIZE, WORLD_SIZE)) for _ in range(800)], 'random_walls': [(
        random.randint(-WORLD_SIZE, WORLD_SIZE), 0, random.randint(-WORLD_SIZE, WORLD_SIZE)) for _ in range(30)], 'boundary_walls': ([(i*wallSpacing-WORLD_SIZE, 0, -WORLD_SIZE) for i in range(numWalls+1)]+[(i*wallSpacing-WORLD_SIZE, 0, WORLD_SIZE) for i in range(numWalls+1)]+[(-WORLD_SIZE, 0, i*wallSpacing-WORLD_SIZE) for i in range(numWalls+1)]+[(WORLD_SIZE, 0, i*wallSpacing-WORLD_SIZE) for i in range(numWalls+1)]), 'temp_walls': []}


def setupOpengl():
    glClearColor(*SKY_COLOR)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)
    glShadeModel(GL_SMOOTH)


def restartGame():
    global warrior, dragons, gameOver, playerProjectiles, dragonFireballs, embers, bombs, hearts, gameState
    gameOver = False
    safeSpawnPos = findSafeSpawnPoint()
    warrior = Warrior(position=safeSpawnPos)
    
    # --- MODIFIED FOR MULTIPLE DRAGONS ---
    dragons = []
    for _ in range(NUM_DRAGONS):
        dragons.append(Dragon())
    # ------------------------------------

    playerProjectiles = []
    dragonFireballs = []
    embers = []
    bombs = []
    # --- ADDED FOR HEARTS ---
    hearts = []
    for _ in range(NUM_HEARTS):
        spawnHeart()
    # -------------------------
    gameState = {'lastWallCheck': time.time()}
    for _ in range(NUM_BOMBS):
        spawnBomb()
    print("Game Restarted!")

# -----------------------------------------------------------------------------
# --- GLUT Callbacks and Main Loop ---
# -----------------------------------------------------------------------------


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    camera.look()
    modelviewMatrix = glGetFloatv(GL_MODELVIEW_MATRIX)
    drawGround()
    drawPlayerProjectiles()
    if dragonFireballs or embers:
        drawFireAndEmbers(modelviewMatrix)

    cullingDistSq = CULLING_DISTANCE**2
    camPos = warrior.position
    objectMap = [('trees', LIST_IDS['tree']), ('rocks', LIST_IDS['rock']), ('shrubs',
                                                                            LIST_IDS['shrub']), ('random_walls', LIST_IDS['wall']), ('boundary_walls', LIST_IDS['wall'])]
    for key, listId in objectMap:
        for pos in objectPositions[key]:
            if (pos[0]-camPos[0])**2+(pos[2]-camPos[2])**2 < cullingDistSq:
                glPushMatrix()
                glTranslatef(pos[0], pos[1], pos[2])
                glCallList(listId)
                glPopMatrix()
    for wall in objectPositions.get('temp_walls', []):
        pos = wall['pos']
        if (pos[0]-camPos[0])**2+(pos[2]-camPos[2])**2 < cullingDistSq:
            glPushMatrix()
            glTranslatef(pos[0], pos[1], pos[2])
            glCallList(LIST_IDS['wall'])
            glPopMatrix()
    for bomb in bombs:
        if bomb.get('state') in ['idle', 'triggered']:
            glPushMatrix()
            glTranslatef(*bomb['position'])
            glColor3f(1, 0, 0) if bomb['state'] == 'triggered' and int(time.time()*10) % 2 == 0 else glColor3f(0.8, 0.8, 0)
            glutSolidSphere(0.5, 16, 16)
            glPopMatrix()
        elif bomb.get('state') == 'exploding':
            progress = (time.time()-bomb['explosion_start_time'])/BOMB_EXPLOSION_DURATION
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

    # --- ADDED FOR HEARTS ---
    for heart in hearts:
        glPushMatrix()
        # Bobbing and rotating animation
        bobbing_offset = math.sin(time.time() * 2.0 + heart['position'][0]) * 0.25
        pos = heart['position']
        glTranslatef(pos[0], pos[1] + bobbing_offset, pos[2])
        glRotatef(time.time() * 30, 0, 1, 0) # Slow rotation on Y axis
        glScalef(1.5, 1.5, 1.5) # Scale it up to be more visible
        drawHeartGeometry()
        glPopMatrix()
    # -------------------------

    for fireball in dragonFireballs:
        if fireball.get('state') == 'exploding':
            progress = (time.time() - fireball['explosion_start_time']) / FIREBALL_EXPLOSION_DURATION
            if 0 < progress < 1.0:
                radius = progress * FIREBALL_EXPLOSION_MAX_RADIUS
                alpha = 0.8 * (1.0 - progress)
                glPushMatrix()
                glTranslatef(*fireball['explosion_pos'])
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                glColor4f(1.0, 0.6, 0.1, alpha)
                glutSolidSphere(radius, 32, 32)
                glDisable(GL_BLEND)
                glPopMatrix()

    if camera.isThirdPerson:
        warrior.draw()
    
    # --- MODIFIED FOR MULTIPLE DRAGONS ---
    for dragon in dragons:
        dragon.draw()
    # ------------------------------------

    if not camera.isThirdPerson and warrior.isShieldActive:
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
        glColor4f(0.3, 0.7, 1.0, warrior.shieldAlpha * 0.7)
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

    drawUi()
    glutSwapBuffers()


def keyboard(key, x, y):
    global keys, isControlsLocked, gameOver
    if key == b'\x1b':
        sys.exit()
    if key.lower() in keys:
        keys[key.lower()] = True
    if gameOver:
        if key.lower() == b'r':
            restartGame()
        return
    if not isControlsLocked:
        if key == b' ':
            warrior.jump()
        if key == b'e':
            warrior.activateShield()
    if key == b'l':
        isControlsLocked = not isControlsLocked
        print(f"Controls {'LOCKED' if isControlsLocked else 'UNLOCKED'}")


def keyboardUp(key, x, y):
    if key.lower() in keys:
        keys[key.lower()] = False


def mouse(button, state, x, y):
    global camera
    if gameOver:
        return
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        camera.isThirdPerson = not camera.isThirdPerson
    elif button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not isControlsLocked:
        if camera.isThirdPerson:
            camera.isThirdPerson = False
        fwdVec = camera.getCameraForwardVector()
        startPos = [camera.position[i] + fwdVec[i] * 1.5 for i in range(3)]
        warrior.fireBlast(startPos, fwdVec)


def mouseMotion(x, y): camera.handleMouse(x, y)


def idle():
    if not gameOver:
        updateGameLogic()
        camera.update()
        warrior.update()
        # --- MODIFIED FOR MULTIPLE DRAGONS ---
        for dragon in dragons:
            dragon.update(warrior.position, playerProjectiles)
        # ------------------------------------
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
    global camera, warrior, dragons, lastMousePos
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutCreateWindow(b"Final Game: Warrior vs Dragons")
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutKeyboardUpFunc(keyboardUp)
    glutPassiveMotionFunc(mouseMotion)
    glutMouseFunc(mouse)
    glutIdleFunc(idle)
    setupOpengl()
    generateWorld()
    compileDisplayLists()
    glutSetCursor(GLUT_CURSOR_NONE)
    centerX, centerY = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
    glutWarpPointer(centerX, centerY)
    camera = Camera()
    lastMousePos = {'x': centerX, 'y': centerY}
    restartGame()
    print("Game Loaded. Controls: W,A,S,D, Mouse, Space, E, L, R")
    glutMainLoop()


if __name__ == "__main__":
    main()