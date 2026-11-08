import pygame
import random
import sys
import math
import urllib.request
import io

# ----------------- INITIALIZATION & AUDIO -----------------
pygame.init()
pygame.mixer.init()

# Setup sound: Pygame cannot load directly from a web page HTML URL,
# so we attempt to download the underlying MP3 file into memory, 
# falling back to an auto-synthesized hit sound if offline.
SOUND_URL = "https://www.myinstants.com/media/sounds/faaah.mp3"
crash_sound = None

try:
    req = urllib.request.Request(
        SOUND_URL, 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    with urllib.request.urlopen(req, timeout=3) as response:
        sound_data = io.BytesIO(response.read())
        crash_sound = pygame.mixer.Sound(sound_data)
except Exception:
    # Fallback procedural crash tone if internet is disconnected/blocked
    try:
        sample_rate = 22050
        duration = 0.3
        n_samples = int(sample_rate * duration)
        buf = bytearray()
        for i in range(n_samples):
            val = int(32767 * math.sin(2.0 * math.pi * 180.0 * (i / sample_rate)) * (1 - i / n_samples))
            buf += val.to_bytes(2, byteorder='little', signed=True)
        crash_sound = pygame.mixer.Sound(buffer=bytes(buf))
    except Exception:
        crash_sound = None

# ----------------- DISPLAY SETUP -----------------
# Optimized for Pydroid 3 and Primebook screens
WIDTH, HEIGHT = 450, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird - Bamboo Edition")
clock = pygame.time.Clock()

# ----------------- COLOR PALETTE -----------------
COLOR_SKY_BLUE    = (112, 197, 206)
COLOR_DEEP_BLUE   = (45, 115, 185)
COLOR_WHITE       = (255, 255, 255)
COLOR_CLOUD_SHADE = (225, 238, 245)
COLOR_BAMBOO_BASE = (76, 175, 80)
COLOR_BAMBOO_DARK = (46, 125, 50)
COLOR_BAMBOO_RING = (139, 195, 74)
COLOR_BIRD_BODY   = (255, 215, 0)
COLOR_BIRD_BEAK   = (255, 100, 0)
COLOR_TREE_TRUNK  = (101, 67, 33)
COLOR_TREE_LEAF   = (34, 139, 34)
COLOR_GROUND      = (222, 216, 149)
COLOR_GROUND_LINE = (180, 170, 100)

# ----------------- GAME ASSET GENERATORS -----------------
def create_bird_surfaces():
    """Generates flap animation frames procedurally."""
    frames = []
    wing_offsets = [0, -3, 2]  # neutral, up, down
    for offset in wing_offsets:
        surf = pygame.Surface((38, 28), pygame.SRCALPHA)
        # Main body (Yellow)
        pygame.draw.ellipse(surf, COLOR_BIRD_BODY, (4, 4, 26, 20))
        pygame.draw.ellipse(surf, (200, 160, 0), (4, 4, 26, 20), 2)
        
        # Wing (Yellow with white highlight)
        pygame.draw.ellipse(surf, (245, 245, 245), (6, 10 + offset, 14, 8))
        pygame.draw.ellipse(surf, (230, 190, 0), (6, 10 + offset, 14, 8), 1)

        # Eye (White + pupil)
        pygame.draw.circle(surf, COLOR_WHITE, (22, 9), 4)
        pygame.draw.circle(surf, (20, 20, 20), (24, 9), 2)
        
        # Beak (Orange/Yellow)
        pygame.draw.polygon(surf, COLOR_BIRD_BEAK, [(27, 10), (36, 13), (27, 17)])
        frames.append(surf)
    return frames

def draw_bamboo_segment(surface, rect, is_top=False):
    """Draws realistic bamboo nodes with green ridges and vertical grain."""
    pygame.draw.rect(surface, COLOR_BAMBOO_BASE, rect)
    
    # Bamboo stalk shadow strip
    shadow_rect = pygame.Rect(rect.x + rect.width - 8, rect.y, 8, rect.height)
    pygame.draw.rect(surface, COLOR_BAMBOO_DARK, shadow_rect)
    
    # Highlight stripe
    highlight_rect = pygame.Rect(rect.x + 4, rect.y, 4, rect.height)
    pygame.draw.rect(surface, (160, 220, 120), highlight_rect)

    # Bamboo horizontal joint rings every 45 pixels
    node_spacing = 45
    start_y = rect.y if not is_top else rect.bottom
    step = node_spacing if not is_top else -node_spacing
    
    for y in range(rect.top, rect.bottom, node_spacing):
        # Ring joint
        pygame.draw.rect(surface, COLOR_BAMBOO_RING, (rect.x - 3, y - 2, rect.width + 6, 5), border_radius=2)
        pygame.draw.line(surface, COLOR_BAMBOO_DARK, (rect.x - 3, y + 3), (rect.right + 3, y + 3), 1)

    # Bamboo end ring cap
    cap_y = rect.bottom - 12 if is_top else rect.top
    pygame.draw.rect(surface, COLOR_BAMBOO_RING, (rect.x - 4, cap_y, rect.width + 8, 12), border_radius=3)
    pygame.draw.rect(surface, COLOR_BAMBOO_DARK, (rect.x - 4, cap_y, rect.width + 8, 12), 2, border_radius=3)

# ----------------- ENVIRONMENT CLASSES -----------------
class Cloud:
    def __init__(self, x, y, speed):
        self.x = x
        self.y = y
        self.speed = speed

    def update(self):
        self.x -= self.speed
        if self.x < -120:
            self.x = WIDTH + random.randint(20, 80)
            self.y = random.randint(30, 160)

    def draw(self, surface):
        # Fluffy layered cloud
        pygame.draw.circle(surface, COLOR_WHITE, (int(self.x + 20), int(self.y + 10)), 18)
        pygame.draw.circle(surface, COLOR_WHITE, (int(self.x + 40), int(self.y)), 24)
        pygame.draw.circle(surface, COLOR_WHITE, (int(self.x + 60), int(self.y + 8)), 20)
        pygame.draw.ellipse(surface, COLOR_WHITE, (int(self.x), int(self.y + 10), 80, 24))

class Tree:
    def __init__(self, x, y, scale=1.0):
        self.x = x
        self.y = y
        self.scale = scale

    def update(self, speed):
        self.x -= speed
        if self.x < -60:
            self.x = WIDTH + random.randint(20, 100)

    def draw(self, surface):
        w = int(14 * self.scale)
        h = int(35 * self.scale)
        # Trunk
        pygame.draw.rect(surface, COLOR_TREE_TRUNK, (self.x, self.y - h, w, h))
        # Foliage puffs
        radius = int(22 * self.scale)
        pygame.draw.circle(surface, COLOR_TREE_LEAF, (int(self.x + w / 2), int(self.y - h - 5)), radius)
        pygame.draw.circle(surface, (46, 160, 46), (int(self.x + w / 2 - 8), int(self.y - h - 2)), radius - 6)

# ----------------- GAME OBJECT CLASSES -----------------
class Bird:
    def __init__(self):
        self.x = 80
        self.y = HEIGHT // 2
        self.velocity = 0.0
        self.gravity = 0.38
        self.lift = -7.5
        self.frames = create_bird_surfaces()
        self.frame_index = 0
        self.anim_timer = 0
        self.angle = 0.0

    def flap(self):
        self.velocity = self.lift

    def update(self):
        self.velocity += self.gravity
        self.y += self.velocity
        
        # Flap animation cycle
        self.anim_timer += 1
        if self.anim_timer % 5 == 0:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            
        # Realistic tilt dynamics
        target_angle = max(-35.0, min(70.0, -self.velocity * 4.5))
        self.angle += (target_angle - self.angle) * 0.25

    def draw(self, surface):
        curr_frame = self.frames[self.frame_index]
        rotated = pygame.transform.rotate(curr_frame, self.angle)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect.topleft)

    def get_hitbox(self):
        return pygame.Rect(self.x - 12, self.y - 10, 24, 20)

class BambooObstacle:
    def __init__(self, x):
        self.x = x
        self.width = 54
        self.gap = 145  # Path clearance gap
        self.passed = False
        
        ground_top = HEIGHT - 70
        min_top = 80
        max_top = ground_top - self.gap - 80
        self.top_height = random.randint(min_top, max_top)
        self.bottom_y = self.top_height + self.gap
        self.bottom_height = ground_top - self.bottom_y

    def update(self, speed):
        self.x -= speed

    def draw(self, surface):
        top_rect = pygame.Rect(self.x, 0, self.width, self.top_height)
        bottom_rect = pygame.Rect(self.x, self.bottom_y, self.width, self.bottom_height)
        
        draw_bamboo_segment(surface, top_rect, is_top=True)
        draw_bamboo_segment(surface, bottom_rect, is_top=False)

    def collides_with(self, rect):
        top_rect = pygame.Rect(self.x, 0, self.width, self.top_height)
        bottom_rect = pygame.Rect(self.x, self.bottom_y, self.width, self.bottom_height)
        return rect.colliderect(top_rect) or rect.colliderect(bottom_rect)

# ----------------- MAIN LOOP -----------------
def main():
    bird = Bird()
    obstacles = [BambooObstacle(WIDTH + 100)]
    clouds = [Cloud(50, 60, 0.5), Cloud(220, 110, 0.8), Cloud(360, 40, 0.4)]
    ground_y = HEIGHT - 70
    trees = [Tree(i * 90 + random.randint(0, 30), ground_y, random.uniform(0.8, 1.2)) for i in range(6)]
    
    score = 0
    font = pygame.font.SysFont('Arial', 32, bold=True)
    small_font = pygame.font.SysFont('Arial', 18, bold=True)
    
    game_state = "READY"  # READY, RUNNING, GAMEOVER
    speed = 2.8

    while True:
        clock.tick(60)

        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            trigger_action = False
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_UP):
                trigger_action = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                trigger_action = True

            if trigger_action:
                if game_state == "READY":
                    game_state = "RUNNING"
                    bird.flap()
                elif game_state == "RUNNING":
                    bird.flap()
                elif game_state == "GAMEOVER":
                    # Reset game
                    bird = Bird()
                    obstacles = [BambooObstacle(WIDTH + 100)]
                    score = 0
                    game_state = "READY"

        # 2. Logic Update
        if game_state == "RUNNING":
            bird.update()
            
            # Ground and sky border collisions
            if bird.y + 12 >= ground_y or bird.y - 12 <= 0:
                if crash_sound:
                    crash_sound.play()
                game_state = "GAMEOVER"

            # Parallax Background Updates
            for cloud in clouds:
                cloud.update()
            for tree in trees:
                tree.update(speed * 0.4)

            # Bamboo Obstacle Handling
            for obs in obstacles:
                obs.update(speed)
                
                # Check collision with bamboo
                if obs.collides_with(bird.get_hitbox()):
                    if crash_sound:
                        crash_sound.play()
                    game_state = "GAMEOVER"
                
                # Score increment
                if not obs.passed and obs.x + obs.width < bird.x:
                    obs.passed = True
                    score += 1

            # Remove offscreen pipes & spawn new ones
            if obstacles and obstacles[0].x < -obstacles[0].width:
                obstacles.pop(0)

            if obstacles[-1].x < WIDTH - 220:
                obstacles.append(BambooObstacle(WIDTH + 20))

        # 3. Render Canvas
        # Sky background
        screen.fill(COLOR_SKY_BLUE)

        # Draw Clouds
        for cloud in clouds:
            cloud.draw(screen)

        # Draw Distant Horizon Trees
        for tree in trees:
            tree.draw(screen)

        # Draw Bamboo Pipes
        for obs in obstacles:
            obs.draw(screen)

        # Draw Ground
        pygame.draw.rect(screen, COLOR_GROUND, (0, ground_y, WIDTH, 70))
        pygame.draw.line(screen, COLOR_BAMBOO_BASE, (0, ground_y), (WIDTH, ground_y), 4)
        pygame.draw.line(screen, COLOR_GROUND_LINE, (0, ground_y + 4), (WIDTH, ground_y + 4), 2)

        # Draw Bird
        bird.draw(screen)

        # UI & HUD
        score_surface = font.render(str(score), True, COLOR_WHITE)
        score_shadow = font.render(str(score), True, (50, 50, 50))
        screen.blit(score_shadow, (WIDTH // 2 - score_surface.get_width() // 2 + 2, 32))
        screen.blit(score_surface, (WIDTH // 2 - score_surface.get_width() // 2, 30))

        if game_state == "READY":
            hint = small_font.render("TAP OR PRESS SPACE TO FLY", True, COLOR_WHITE)
            screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 60))
        elif game_state == "GAMEOVER":
            over_text = font.render("GAME OVER", True, (220, 50, 50))
            retry_text = small_font.render("TAP TO TRY AGAIN", True, COLOR_WHITE)
            screen.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 2 - 40))
            screen.blit(retry_text, (WIDTH // 2 - retry_text.get_width() // 2, HEIGHT // 2 + 10))

        pygame.display.flip()

if __name__ == "__main__":
    main()
