import pygame
import sys
import random  # 추가: 적 위치를 랜덤으로 생성하기 위해 사용

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

# Set up screen and clock
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mario-Style Platformer")
clock = pygame.time.Clock()

# Background class with seamless scrolling functionality
class Background:
    def __init__(self):
        try:
            self.image = pygame.image.load("background.png")  # Background image
            self.image = pygame.transform.scale(self.image, (SCREEN_WIDTH, SCREEN_HEIGHT))  # Scale to screen size
        except (pygame.error, FileNotFoundError):
            print("Warning: 'background.png' not found. Using fallback color.")
            self.image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.image.fill(WHITE)  # Fallback color
        self.scroll_x = 0  # Horizontal scroll position

    def draw(self, surface):
        """Draw the background with seamless scrolling."""
        surface.blit(self.image, (self.scroll_x, 0))  # Draw the first instance
        surface.blit(self.image, (self.scroll_x + SCREEN_WIDTH, 0))  # Draw the second instance for looping

    def update(self, player):
        """Scroll the background based on the player's position."""
        self.scroll_x -= player.x_velocity * 0.3  # Background scrolls slower than the player

        # Reset scroll position for seamless looping
        if self.scroll_x <= -SCREEN_WIDTH:
            self.scroll_x = 0
        elif self.scroll_x > 0:
            self.scroll_x = -SCREEN_WIDTH

# Foreground class for additional layer
class Foreground:
    def __init__(self):
        try:
            self.image = pygame.image.load("foreground.png")  # Foreground image
            self.image = pygame.transform.scale(self.image, (SCREEN_WIDTH, SCREEN_HEIGHT))  # Scale to screen size
        except (pygame.error, FileNotFoundError):
            print("Warning: 'foreground.png' not found. Using fallback color.")
            self.image = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.image.fill(BLACK)  # Fallback color
        self.scroll_x = 0  # Horizontal scroll position

    def draw(self, surface):
        """Draw the foreground with seamless scrolling."""
        surface.blit(self.image, (self.scroll_x, 0))  # Draw the first instance
        surface.blit(self.image, (self.scroll_x + SCREEN_WIDTH, 0))  # Draw the second instance for looping

    def update(self, player):
        """Scroll the foreground based on the player's position."""
        self.scroll_x -= player.x_velocity * 0.5  # Foreground scrolls faster than the background

        # Reset scroll position for seamless looping
        if self.scroll_x <= -SCREEN_WIDTH:
            self.scroll_x = 0
        elif self.scroll_x > 0:
            self.scroll_x = -SCREEN_WIDTH

# Player class with attack functionality and scrolling support
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        try:
            self.walking_right = [
                pygame.transform.scale(pygame.image.load("right1.png"), (150, 150)),  # Reduced size
                pygame.transform.scale(pygame.image.load("right2.png"), (150, 150))   # Reduced size
            ]
            self.standing = pygame.transform.scale(pygame.image.load("standing.png"), (150, 150))  # Reduced size
            self.attacking = pygame.transform.scale(pygame.image.load("attack.png"), (150, 150))  # Reduced size
        except (pygame.error, FileNotFoundError):
            print("Warning: Player images not found. Using fallback colors.")
            self.walking_right = [pygame.Surface((150, 150)), pygame.Surface((150, 150))]  # Reduced size
            self.standing = pygame.Surface((150, 150))  # Reduced size
            self.attacking = pygame.Surface((150, 150))  # Reduced size
            for surface in self.walking_right:
                surface.fill(BLUE)
            self.standing.fill(GREEN)
            self.attacking.fill(RED)

        self.image = self.standing
        self.rect = self.image.get_rect()
        self.rect.bottom = SCREEN_HEIGHT - 20  # Align player bottom with ground

        self.x_velocity = 0
        self.y_velocity = 0
        self.direction = "right"
        self.walk_index = 0
        self.score = 0
        self.is_attacking = False
        self.attack_cooldown = 0
        self.attack_duration = 10  # Attack animation duration in frames
        self.initial_position_restriction = True  # Restrict backward movement initially
        self.is_jumping = False  # Add a flag to track jumping state
        self.screen_margin = 200  # Margin to keep the player near the center of the screen
        self.health = 100  # Add health attribute for the player
        self.damage_cooldown = 0  # Cooldown timer for taking damage

    def update(self, coins, enemies, background, foreground):
        keys = pygame.key.get_pressed()

        # Horizontal movement
        if keys[pygame.K_LEFT]:
            if not self.initial_position_restriction and self.rect.left > 0:
                self.x_velocity = -5
                self.direction = "left"
            else:
                self.x_velocity = 0  # Prevent moving left initially
        elif keys[pygame.K_RIGHT]:
            self.x_velocity = 5
            self.direction = "right"
            self.initial_position_restriction = False  # Allow backward movement after moving right
        else:
            self.x_velocity = 0

        # Update position within screen margin
        if self.rect.centerx < self.screen_margin and self.x_velocity < 0:
            self.x_velocity = 0  # Prevent moving left beyond margin
        elif self.rect.centerx > SCREEN_WIDTH - self.screen_margin and self.x_velocity > 0:
            self.x_velocity = 0  # Prevent moving right beyond margin

        self.rect.x += self.x_velocity  # Update horizontal position

        # Jump
        if keys[pygame.K_SPACE] and not self.is_jumping and self.is_on_ground():
            self.y_velocity = -10  # Set upward velocity for jump
            self.is_jumping = True  # Set jumping state to True

        # Apply gravity
        self.y_velocity += 0.5  # Simulate gravity
        if self.y_velocity > 10:
            self.y_velocity = 10  # Cap downward velocity

        # Update vertical position
        self.rect.y += self.y_velocity

        # Reset jumping state when on the ground
        if self.is_on_ground():
            self.is_jumping = False

        # Attack
        if keys[pygame.K_f] and self.attack_cooldown == 0:
            self.is_attacking = True
            self.attack_cooldown = 20  # Cooldown for 20 frames
            self.attack_duration = 10  # Attack animation lasts for 10 frames

        # Handle attack
        if self.is_attacking:
            self.handle_attack(enemies, coins)  # Pass coins to handle_attack
            self.attack_duration -= 1
            if self.attack_duration <= 0:
                self.is_attacking = False  # End attack animation

        # Reduce attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        # Reduce damage cooldown
        if self.damage_cooldown > 0:
            self.damage_cooldown -= 1

        # Animate player
        self.animate()

        # Collect coins
        for coin in coins:
            coin.update(self)

        # Update background and foreground scrolling
        background.update(self)
        foreground.update(self)

        # Prevent player from going off screen vertically
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

        # Check for game over condition
        if self.score >= 100:  # Game over condition updated to 100 points
            print("Game Over! You reached the target score.")
            game_over_screen()

        # Check for collisions with enemies
        for enemy in enemies:
            if self.rect.colliderect(enemy.rect) and self.damage_cooldown == 0:
                self.take_damage(10)  # Reduce health by 10 on collision
                self.damage_cooldown = 30  # Set cooldown to 30 frames (0.5 seconds at 60 FPS)

    def is_on_ground(self):
        """Check if the player is standing on the ground."""
        return self.rect.bottom >= SCREEN_HEIGHT - 20

    def handle_attack(self, enemies, coins):
        """Handle attack collisions with enemies."""
        for enemy in enemies:
            if self.rect.colliderect(enemy.rect):
                enemy.health -= 50  # Reduced damage per attack
                if enemy.health <= 0:
                    enemy.drop_coin(coins)  # Drop a coin when the enemy is killed
                    enemy.kill()
                    self.score += 10  # Increase score only when an enemy is killed
                    # Add a new enemy at a random position
                    new_enemy = Enemy(random.randint(200, SCREEN_WIDTH - 200), SCREEN_HEIGHT - 150)
                    enemies.add(new_enemy)

    def take_damage(self, amount):
        """Reduce player's health by the specified amount."""
        self.health -= amount
        if self.health <= 0:
            print("Game Over! Player has no health left.")
            game_over_screen()

    def animate(self):
        """Animate the player."""
        if self.is_attacking:
            self.image = self.attacking
        elif self.x_velocity != 0:
            self.walk_index = (self.walk_index + 1) % len(self.walking_right)
            self.image = self.walking_right[self.walk_index]
        else:
            self.image = self.standing

    def draw_health_bar(self, surface):
        """Draw the health bar above the player."""
        bar_width = 100
        bar_height = 10
        health_ratio = self.health / 100  # Adjusted for max health
        health_bar_width = int(bar_width * health_ratio)

        # Draw the health bar background
        pygame.draw.rect(surface, RED, (self.rect.centerx - bar_width // 2, self.rect.top - 20, bar_width, bar_height))
        # Draw the current health
        pygame.draw.rect(surface, GREEN, (self.rect.centerx - bar_width // 2, self.rect.top - 20, health_bar_width, bar_height))

# Coin class
class Coin(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            self.image = pygame.transform.scale(pygame.image.load("coin.png"), (40, 40))
        except (pygame.error, FileNotFoundError):
            print("Warning: 'coin.png' not found. Using fallback color.")
            self.image = pygame.Surface((40, 40))
            self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self, player):
        if pygame.sprite.collide_rect(self, player):
            self.kill()
            player.score += 10

# Enemy class with running and attacking animations
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            # Load enemy running and attacking frames
            self.run_frames = [
                pygame.transform.scale(pygame.image.load("enemy_run1.png"), (200, 200)),
                pygame.transform.scale(pygame.image.load("enemy_run2.png"), (200, 200))
            ]
            self.attack_frames = [
                pygame.transform.scale(pygame.image.load("enemy_attack1.png"), (200, 200)),
                pygame.transform.scale(pygame.image.load("enemy_attack2.png"), (200, 200))
            ]
        except (pygame.error, FileNotFoundError):
            print("Warning: Enemy animation frames not found. Using fallback color.")
            self.run_frames = [pygame.Surface((200, 200)) for _ in range(2)]
            self.attack_frames = [pygame.Surface((200, 200)) for _ in range(2)]
            for frame in self.run_frames:
                frame.fill(RED)
            for frame in self.attack_frames:
                frame.fill(BLUE)

        self.image = self.run_frames[0]  # Start with the first running frame
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.bottom = SCREEN_HEIGHT - 20  # Align enemy with the ground

        self.x_velocity = 0  # Initial horizontal movement speed
        self.health = 200  # Health for enemy
        self.animation_index = 0  # Current animation frame index
        self.animation_timer = 0  # Timer to control animation speed
        self.state = "run"  # Initial state: "run" or "attack"
        self.facing_left = True  # Track the direction the enemy is facing
        self.attack_range = 150  # Increase the attack range to 150 pixels

    def update(self, player):
        """Move the enemy towards the player and update its animation."""
        # Calculate distance to the player
        distance_to_player = abs(self.rect.centerx - player.rect.centerx)

        # Determine movement direction
        if distance_to_player > self.attack_range:
            if self.rect.centerx < player.rect.centerx:
                self.x_velocity = 2  # Move right towards the player
                self.facing_left = False  # Facing right
            elif self.rect.centerx > player.rect.centerx:
                self.x_velocity = -2  # Move left towards the player
                self.facing_left = True  # Facing left
        else:
            self.x_velocity = 0
            self.state = "attack"  # Switch to attack state when within range

        # Update position
        self.rect.x += self.x_velocity

        # Update state
        if self.x_velocity != 0:
            self.state = "run"  # Switch to running state when moving

        # Update animation
        self.animation_timer += 1
        if self.animation_timer >= 10:  # Change frame every 10 updates
            self.animation_index = (self.animation_index + 1) % 2  # Toggle between 0 and 1
            if self.state == "run":
                self.image = self.run_frames[self.animation_index]
            elif self.state == "attack":
                self.image = self.attack_frames[self.animation_index]
            self.animation_timer = 0

        # Remove flipping logic
        # No image flipping is applied here

    def draw_health_bar(self, surface):
        """Draw the health bar above the enemy."""
        bar_width = 100
        bar_height = 10
        health_ratio = self.health / 200  # Adjusted for health
        health_bar_width = int(bar_width * health_ratio)

        # Draw the health bar background
        pygame.draw.rect(surface, RED, (self.rect.centerx - bar_width // 2, self.rect.top - 20, bar_width, bar_height))
        # Draw the current health
        pygame.draw.rect(surface, GREEN, (self.rect.centerx - bar_width // 2, self.rect.top - 20, health_bar_width, bar_height))

    def drop_coin(self, coins):
        """Drop a coin at the enemy's center position."""
        coin = Coin(self.rect.centerx, self.rect.centery)  # Coin appears at the enemy's center
        coins.add(coin)

# Game over screen function
def game_over_screen():
    """Display 'Game Over' message and exit the game."""
    screen.fill(BLACK)
    font = pygame.font.SysFont(None, 72)
    game_over_text = font.render("Game Over", True, WHITE)
    screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2,
                                 SCREEN_HEIGHT // 2 - game_over_text.get_height() // 2))
    pygame.display.update()
    pygame.time.wait(3000)  # Wait for 3 seconds
    pygame.quit()
    sys.exit()

# Main game loop
def game_loop():
    background = Background()
    foreground = Foreground()  # Add foreground layer

    # Create objects
    player = Player()
    coins = pygame.sprite.Group()
    # Spawn enemy on the opposite side of the player (right side of the screen)
    enemies = pygame.sprite.Group(Enemy(SCREEN_WIDTH - 200, SCREEN_HEIGHT - 20 - 300))  # Enemy starts from the right

    all_sprites = pygame.sprite.Group(player)

    while True:
        screen.fill(WHITE)

        # Draw and update background
        background.draw(screen)

        # Draw and update foreground
        foreground.draw(screen)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Update sprites
        player.update(coins, enemies, background, foreground)  # Pass background and foreground to player update
        for enemy in enemies:
            enemy.update(player)  # Pass player to enemy update

        # Draw everything
        all_sprites.draw(screen)
        coins.draw(screen)
        for enemy in enemies:
            screen.blit(enemy.image, enemy.rect)
            enemy.draw_health_bar(screen)  # Draw health bar for each enemy

        # Draw player's health bar
        player.draw_health_bar(screen)

        # Display score
        font = pygame.font.SysFont(None, 36)
        score_text = font.render(f"Score: {player.score}", True, (0, 0, 0))
        screen.blit(score_text, (10, 10))

        pygame.display.update()
        clock.tick(FPS)

# Run the game loop
game_loop()
