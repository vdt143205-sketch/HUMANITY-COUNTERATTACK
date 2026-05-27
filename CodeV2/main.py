import pygame
import sys
import cv2
from random import choice, randint

from player import Player
from alien import Alien, Extra
from laser import Laser
from obstacle import Block, shape, shape_flipped
from levels import LEVELS
from boss import Boss
from powerup import PowerUp


# =========================
# WINDOW SIZE
# =========================

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 850

VIDEO_WIDTH = 430
VIDEO_HEIGHT = 260

WINDOW_WIDTH = SCREEN_WIDTH + VIDEO_WIDTH
WINDOW_HEIGHT = SCREEN_HEIGHT

VIDEO_POS_X = 0
VIDEO_POS_Y = SCREEN_HEIGHT - VIDEO_HEIGHT

GAME_X = VIDEO_WIDTH

FPS = 60


class NullSound:
    def play(self, loops=0):
        pass

    def stop(self):
        pass

    def set_volume(self, volume):
        pass


class AssetManager:

    def __init__(self):
        self.font = pygame.font.Font('../Resources/Pixeled.ttf', 14)
        self.small_font = pygame.font.Font('../Resources/Pixeled.ttf', 7)
        self.tiny_font = pygame.font.Font('../Resources/Pixeled.ttf', 6)

        self.images = {}

        self.load_image('logo', '../Resources/logo.png', (400, 100))

        self.load_image('move0', '../Resources/move0.png', (390, 88))
        self.load_image('move1', '../Resources/move1.png', (390, 88))
        self.load_image('shoot0', '../Resources/shoot0.png', (390, 88))
        self.load_image('shoot1', '../Resources/shoot1.png', (390, 88))
        self.load_image('flip0', '../Resources/flip0.png', (390, 88))
        self.load_image('flip1', '../Resources/flip1.png', (390, 88))

        self.load_image('player', '../Resources/player.png', (54, 27))
        self.load_image('red', '../Resources/red.png', (24, 18))
        self.load_image('green', '../Resources/green.png', (24, 18))
        self.load_image('yellow', '../Resources/yellow.png', (24, 18))
        self.load_image('extra', '../Resources/extra.png', (24, 14))

        self.load_optional_image('boss_city', '../Resources/boss_city.png', (190, 110))
        self.load_optional_image('boss_forest', '../Resources/boss_forest.png', (200, 120))
        self.load_optional_image('boss_ai', '../Resources/boss_ai.png', (210, 125))

        # =========================
        # SOUND EFFECTS
        # =========================
        self.sounds = {
            'laser': self.load_sound('../Resources/laser.wav'),
            'explosion': self.load_sound('../Resources/explosion.wav'),

            # Âm thanh mới
            'charge': self.load_sound('../Resources/charge.wav'),
            'charge_full': self.load_sound('../Resources/charge_full.wav')
        }

        self.sounds['laser'].set_volume(0.04)
        self.sounds['explosion'].set_volume(0.05)
        self.sounds['charge'].set_volume(0.18)
        self.sounds['charge_full'].set_volume(0.22)

    def load_image(self, name, path, size=None):
        image = pygame.image.load(path).convert_alpha()

        if size is not None:
            image = pygame.transform.scale(image, size)

        self.images[name] = image

    def load_optional_image(self, name, path, size=None):
        try:
            image = pygame.image.load(path).convert_alpha()

            if size is not None:
                image = pygame.transform.scale(image, size)

            self.images[name] = image

        except:
            self.images[name] = None

    def load_sound(self, path):
        try:
            return pygame.mixer.Sound(path)

        except:
            print('Không tìm thấy âm thanh:', path)
            return NullSound()

    def play_background_music(self):
        try:
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.load('../Resources/bg_music.mp3')
                pygame.mixer.music.set_volume(0.25)
                pygame.mixer.music.play(-1)

        except:
            print('Không tìm thấy file nhạc nền: ../Resources/bg_music.mp3')

    def stop_background_music(self):
        try:
            pygame.mixer.music.stop()
        except:
            pass

    def update_background_music_by_state(self, state):
        # Chỉ bật nhạc nền ở màn giới thiệu, menu và màn kết thúc
        if state in ['INTRO', 'MENU', 'DEAD', 'VICTORY']:
            if not pygame.mixer.music.get_busy():
                self.play_background_music()

        # Khi đang chơi hoặc đang chuyển màn thì tắt nhạc nền
        elif state in ['PLAYING', 'LEVEL_CLEAR']:
            if pygame.mixer.music.get_busy():
                self.stop_background_music()


class Particle:

    def __init__(self, x, y, vx, vy, life, size):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.size = size

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw(self, screen, color):
        if self.life > 0:
            pygame.draw.circle(
                screen,
                color,
                (int(self.x), int(self.y)),
                self.size
            )


class Game:

    def __init__(self, screen, clock, assets):
        self.screen = screen
        self.clock = clock
        self.assets = assets

        # Mở game sẽ vào màn cốt truyện trước
        self.state = 'INTRO'
        self.selected_level = 1
        self.level_id = 1
        self.level = LEVELS[self.level_id]

        # =========================
        # INTRO TYPEWRITER STORY
        # =========================
        self.intro_start_time = pygame.time.get_ticks()

        # Tốc độ hiện chữ.
        # 25 = nhanh, 35 = vừa đọc, 45 = chậm hơn.
        self.intro_char_delay = 35

        self.intro_finished = False

        self.story_full_text = (
            "Year 2147.\n\n"
            "Earth is under attack by an alien AI system.\n"
            "Cities have collapsed. Forests are poisoned.\n"
            "The central machine core controls the invasion.\n\n"
            "You are the last pilot of the human resistance.\n"
            "Your spaceship is controlled by hand gestures\n"
            "using computer vision through the camera.\n\n"
            "Defeat each boss.\n"
            "Destroy the Central AI.\n"
            "Lead humanity into the final counterattack."
        )

        self.level_clear_time = 0
        self.level_clear_delay = 2500

        self.player_sprite = None
        self.player = None

        self.lives = 3
        self.score = 0

        self.blocks = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self.alien_lasers = pygame.sprite.Group()
        self.extra = pygame.sprite.GroupSingle()
        self.boss_group = pygame.sprite.GroupSingle()
        self.powerups = pygame.sprite.Group()

        self.alien_direction = 1
        self.extra_spawn_time = randint(300, 600)

        self.particles = []
        self.stars = []

        self.create_player()
        self.create_stars()
        self.load_level(1)

        self.ALIENLASER = pygame.USEREVENT + 1
        pygame.time.set_timer(self.ALIENLASER, 800)

    def create_player(self):
        self.player_sprite = Player(
            pos=(GAME_X + SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2),
            cwidth=SCREEN_WIDTH,
            speed=5,
            vwidth=VIDEO_WIDTH,
            screen=self.screen,
            height=WINDOW_HEIGHT,
            assets=self.assets
        )

        self.player = pygame.sprite.GroupSingle(self.player_sprite)

    def create_stars(self):
        self.stars.clear()

        for i in range(130):
            x = randint(GAME_X + 5, WINDOW_WIDTH - 5)
            y = randint(5, SCREEN_HEIGHT - 5)
            speed = choice([1, 1, 1, 2])
            size = choice([1, 1, 2])

            self.stars.append([x, y, speed, size])

    def reset_runtime_groups(self):
        self.blocks.empty()
        self.aliens.empty()
        self.alien_lasers.empty()
        self.extra.empty()
        self.boss_group.empty()
        self.powerups.empty()
        self.particles.clear()
        self.player_sprite.lasers.empty()

    def load_level(self, level_id):
        self.level_id = level_id
        self.level = LEVELS[level_id]

        self.lives = 3
        self.score = 0
        self.level_clear_time = 0

        self.alien_direction = self.level['alien_speed']

        self.reset_runtime_groups()

        self.player_sprite.reset_position(
            (GAME_X + SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        )

        self.player_sprite.flipped = False

        self.create_level_obstacles()
        self.create_level_aliens()

        boss_image = self.assets.images.get(self.level['boss_image'])

        self.boss_group.add(
            Boss(
                self.level['boss_name'],
                self.level['boss_hp'],
                WINDOW_WIDTH,
                GAME_X,
                self.level['boss_color'],
                self.level['boss_speed'],
                boss_image,
                self.level['boss_pattern']
            )
        )

    def create_level_obstacles(self):
        layout = self.level['layout']

        if layout == 'city':
            self.create_custom_obstacles(
                [80, 250, 420, 590, 760],
                390,
                False
            )

            self.create_custom_obstacles(
                [160, 330, 500, 670],
                550,
                True
            )

        elif layout == 'forest':
            self.create_custom_obstacles(
                [60, 260, 520, 780],
                350,
                False
            )

            self.create_custom_obstacles(
                [160, 400, 640, 840],
                600,
                True
            )

        elif layout == 'ai_core':
            self.create_custom_obstacles(
                [150, 430, 710],
                460,
                False
            )

    def create_custom_obstacles(self, offsets, y_start, flipped):
        for offset_x in offsets:
            self.create_obstacle(
                GAME_X + 35,
                y_start,
                offset_x,
                flipped
            )

    def create_obstacle(self, x_start, y_start, offset_x, flipped):
        selected_shape = shape_flipped if flipped else shape
        block_size = 4

        for row_index, row in enumerate(selected_shape):
            for col_index, col in enumerate(row):
                if col == 'x':
                    x = x_start + col_index * block_size + offset_x
                    y = y_start + row_index * block_size

                    block = Block(
                        block_size,
                        self.level['block_color'],
                        x,
                        y
                    )

                    self.blocks.add(block)

    def create_level_aliens(self):
        layout = self.level['layout']

        if layout == 'city':
            self.alien_setup(4, 10, 80, 30, 100, 180, False)
            self.alien_setup(4, 10, 80, 30, 100, 690, True)

        elif layout == 'forest':
            self.alien_setup(5, 9, 90, 32, 100, 190, False)
            self.alien_setup(5, 9, 90, 32, 100, 670, True)

        elif layout == 'ai_core':
            self.alien_setup(4, 12, 72, 32, 60, 245, False)
            self.alien_setup(4, 12, 72, 32, 60, 590, True)

    def alien_setup(
        self,
        rows,
        cols,
        x_distance=50,
        y_distance=20,
        x_offset=70,
        y_offset=50,
        flipped=False
    ):
        x_offset = x_offset + GAME_X
        colors = self.level['alien_colors']

        for row_index in range(rows):
            for col_index in range(cols):
                x = col_index * x_distance + x_offset
                y = row_index * y_distance + y_offset

                if self.level['layout'] == 'forest':
                    if col_index % 2 == 0:
                        y += 18

                if self.level['layout'] == 'ai_core':
                    if row_index % 2 == 0:
                        x += 14

                if row_index == 0:
                    color = colors[2]
                elif row_index <= 2:
                    color = colors[1]
                else:
                    color = colors[0]

                alien = Alien(
                    color,
                    x,
                    y,
                    flipped,
                    self.assets
                )

                self.aliens.add(alien)

    def alien_position_checker(self):
        for alien in self.aliens.sprites():
            if alien.rect.right >= WINDOW_WIDTH:
                self.alien_direction = -abs(self.level['alien_speed'])
                self.alien_move_down(7)
                break

            if alien.rect.left <= GAME_X:
                self.alien_direction = abs(self.level['alien_speed'])
                self.alien_move_down(7)
                break

    def alien_move_down(self, distance):
        for alien in self.aliens.sprites():
            if alien.flipped:
                alien.rect.y -= distance
            else:
                alien.rect.y += distance

    def alien_shoot(self):
        if self.state != 'PLAYING':
            return

        enemies = self.aliens.sprites()

        if enemies:
            random_alien = choice(enemies)
            speed = -6 if random_alien.flipped else 6

            self.alien_lasers.add(
                Laser(
                    random_alien.rect.center,
                    speed,
                    SCREEN_HEIGHT,
                    color=self.level['enemy_laser_color']
                )
            )

    def extra_alien_timer(self):
        self.extra_spawn_time -= 1

        if self.extra_spawn_time <= 0:
            self.extra.add(
                Extra(
                    choice(['right', 'left']),
                    WINDOW_WIDTH,
                    GAME_X,
                    choice([False, True]),
                    self.assets
                )
            )

            self.extra_spawn_time = randint(400, 800)

    def add_explosion(self, x, y, amount=14):
        for i in range(amount):
            self.particles.append(
                Particle(
                    x,
                    y,
                    randint(-5, 5),
                    randint(-5, 5),
                    randint(22, 42),
                    randint(2, 5)
                )
            )

    def drop_powerup(self, pos):
        drop = randint(1, 100)

        if drop <= 18:
            self.powerups.add(PowerUp(pos, 'heal'))

        elif drop <= 30:
            self.powerups.add(PowerUp(pos, 'damage'))

        elif drop <= 42:
            self.powerups.add(PowerUp(pos, 'fire'))

    def start_level_clear(self):
        if self.state != 'LEVEL_CLEAR':
            self.level_clear_time = pygame.time.get_ticks()
            self.state = 'LEVEL_CLEAR'

    def update_level_clear(self):
         current_time = pygame.time.get_ticks()

         if current_time - self.level_clear_time < self.level_clear_delay:
             return

        # Sau khi hiện YOU WIN xong thì quay lại menu chọn màn
         self.state = 'MENU'

    def ultimate_blast(self):
        for alien in self.aliens.sprites():
            self.add_explosion(
                alien.rect.centerx,
                alien.rect.centery,
                35
            )

        self.aliens.empty()

        boss = self.boss_group.sprite

        if boss and boss.alive():
            self.add_explosion(
                boss.rect.centerx,
                boss.rect.centery,
                100
            )

            boss.take_damage(boss.hp)

        self.alien_lasers.empty()
        self.extra.empty()
        self.powerups.empty()

        self.score += 3000
        self.assets.sounds['explosion'].play()

        self.start_level_clear()

    def energy_blast(self):
        blast_radius = 180

        center_x = self.player_sprite.rect.centerx
        center_y = self.player_sprite.rect.centery

        self.add_explosion(
            center_x,
            center_y,
            90
        )

        for alien in self.aliens.sprites():
            dx = alien.rect.centerx - center_x
            dy = alien.rect.centery - center_y
            distance = (dx * dx + dy * dy) ** 0.5

            if distance <= blast_radius:
                self.add_explosion(
                    alien.rect.centerx,
                    alien.rect.centery,
                    30
                )

                self.score += alien.value
                alien.kill()

        if self.extra.sprite:
            extra = self.extra.sprite
            dx = extra.rect.centerx - center_x
            dy = extra.rect.centery - center_y
            distance = (dx * dx + dy * dy) ** 0.5

            if distance <= blast_radius:
                self.add_explosion(
                    extra.rect.centerx,
                    extra.rect.centery,
                    35
                )

                self.score += 500
                extra.kill()

        for laser in self.alien_lasers.sprites():
            dx = laser.rect.centerx - center_x
            dy = laser.rect.centery - center_y
            distance = (dx * dx + dy * dy) ** 0.5

            if distance <= blast_radius:
                laser.kill()

        self.assets.sounds['explosion'].play()

    def collision_checks(self):
        for laser in self.player_sprite.lasers.sprites():

            if pygame.sprite.spritecollide(laser, self.blocks, True):
                laser.kill()
                continue

            aliens_hit = pygame.sprite.spritecollide(
                laser,
                self.aliens,
                True
            )

            if aliens_hit:
                for alien in aliens_hit:
                    self.score += alien.value
                    self.add_explosion(
                        alien.rect.centerx,
                        alien.rect.centery
                    )
                    self.drop_powerup(alien.rect.center)

                laser.kill()
                self.assets.sounds['explosion'].play()
                continue

            if pygame.sprite.spritecollide(laser, self.extra, True):
                self.score += 500
                self.add_explosion(
                    laser.rect.centerx,
                    laser.rect.centery,
                    22
                )
                self.drop_powerup(laser.rect.center)

                laser.kill()
                self.assets.sounds['explosion'].play()
                continue

            boss = self.boss_group.sprite

            if boss and boss.alive() and laser.rect.colliderect(boss.rect):
                boss.take_damage(laser.damage)

                self.score += 30
                self.add_explosion(
                    laser.rect.centerx,
                    laser.rect.centery,
                    8
                )
                laser.kill()

                if boss.hp <= 0:
                    self.score += 1000
                    self.add_explosion(
                        boss.rect.centerx,
                        boss.rect.centery,
                        70
                    )
                    self.assets.sounds['explosion'].play()

        for laser in self.alien_lasers.sprites():

            if pygame.sprite.spritecollide(laser, self.blocks, True):
                laser.kill()
                continue

            if pygame.sprite.spritecollide(laser, self.player, False):
                laser.kill()
                self.lives -= 1

                self.add_explosion(
                    self.player_sprite.rect.centerx,
                    self.player_sprite.rect.centery,
                    18
                )

                self.assets.sounds['explosion'].play()

                if self.lives <= 0:
                    self.state = 'DEAD'

        powerups_hit = pygame.sprite.spritecollide(
            self.player_sprite,
            self.powerups,
            True
        )

        for powerup in powerups_hit:
            if powerup.power_type == 'heal':
                if self.lives < 5:
                    self.lives += 1

            elif powerup.power_type == 'damage':
                self.player_sprite.apply_powerup('damage')

            elif powerup.power_type == 'fire':
                self.player_sprite.apply_powerup('fire')

        for alien in self.aliens.sprites():
            pygame.sprite.spritecollide(alien, self.blocks, True)

            if pygame.sprite.spritecollide(alien, self.player, False):
                self.state = 'DEAD'

    def handle_events(self):
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.close()

            if event.type == self.ALIENLASER:
                self.alien_shoot()

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_ESCAPE:
                    self.close()

                if self.state == 'INTRO':

                    # Chỉ được vào menu khi cốt truyện đã chạy hết
                    if event.key == pygame.K_RETURN and self.intro_finished:
                        self.state = 'MENU'

                elif self.state == 'MENU':

                    if event.key == pygame.K_1:
                        self.selected_level = 1

                    elif event.key == pygame.K_2:
                        self.selected_level = 2

                    elif event.key == pygame.K_3:
                        self.selected_level = 3

                    elif event.key == pygame.K_RETURN:
                        self.load_level(self.selected_level)
                        self.state = 'PLAYING'

                elif self.state in ['DEAD', 'VICTORY']:

                    if event.key == pygame.K_RETURN:
                        self.state = 'MENU'

                elif self.state == 'PLAYING':

                    if event.key == pygame.K_m:
                        self.state = 'MENU'

    def update_hand_menu_control(self):
        if (
            self.player_sprite.last_gesture == 'FLIP'
            and self.player_sprite.consume_flip_action()
        ):

            if self.state == 'INTRO':
                # FLIP chỉ có tác dụng sau khi cốt truyện đã hiện hết
                if self.intro_finished:
                    self.state = 'MENU'

            elif self.state == 'MENU':
                self.load_level(self.selected_level)
                self.state = 'PLAYING'

            elif self.state in ['DEAD', 'VICTORY']:
                self.state = 'MENU'

    def draw_left_panel_box(self, x, y, w, h, border_color=(80, 255, 210)):
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((10, 12, 18, 210))

        self.screen.blit(panel, (x, y))

        pygame.draw.rect(
            self.screen,
            border_color,
            (x, y, w, h),
            2,
            border_radius=14
        )

    def draw_camera_panel(self):
        self.screen.fill(
            (12, 14, 20),
            (0, 0, VIDEO_WIDTH, SCREEN_HEIGHT)
        )

        pygame.draw.line(
            self.screen,
            (80, 255, 210),
            (GAME_X, 0),
            (GAME_X, SCREEN_HEIGHT),
            3
        )

        logo = self.assets.images['logo']
        logo_rect = logo.get_rect(center=(VIDEO_WIDTH // 2, 92))
        self.screen.blit(logo, logo_rect)

        status_y = 185

        if self.player_sprite.last_gesture == 'NUKE':
            status_text = 'ULTIMATE'
            status_color = (180, 0, 255)

        elif self.player_sprite.last_gesture == 'CHARGE':
            status_text = 'CHARGING'
            status_color = (0, 220, 255)

        elif self.player_sprite.last_gesture == 'FIST':
            status_text = 'BLAST'
            status_color = (255, 160, 0)

        elif self.player_sprite.last_gesture == 'SHOOT':
            status_text = 'SHOOT'
            status_color = (255, 80, 80)

        elif self.player_sprite.last_gesture == 'FLIP':
            status_text = 'FLIP'
            status_color = (80, 255, 120)

        elif self.player_sprite.last_gesture == 'MOVE':
            status_text = 'MOVE'
            status_color = (80, 160, 255)

        else:
            status_text = 'NO HAND'
            status_color = (160, 160, 160)

        status_surf = self.assets.font.render(
            status_text,
            False,
            status_color
        )

        self.screen.blit(
            status_surf,
            status_surf.get_rect(
                center=(VIDEO_WIDTH // 2, status_y)
            )
        )

        # Panel hướng dẫn cử chỉ
        guide_x = 16
        guide_y = 235
        guide_w = VIDEO_WIDTH - 32
        guide_h = 300

        self.draw_left_panel_box(
            guide_x,
            guide_y,
            guide_w,
            guide_h
        )

        move_pos = (guide_x + 10, guide_y + 14)
        shoot_pos = (guide_x + 10, guide_y + 106)
        flip_pos = (guide_x + 10, guide_y + 198)

        self.screen.blit(self.assets.images['move0'], move_pos)
        self.screen.blit(self.assets.images['shoot0'], shoot_pos)
        self.screen.blit(self.assets.images['flip0'], flip_pos)

        if self.player_sprite.last_gesture == 'MOVE':
            self.screen.blit(self.assets.images['move1'], move_pos)

        elif self.player_sprite.last_gesture == 'SHOOT':
            self.screen.blit(self.assets.images['shoot1'], shoot_pos)

        elif self.player_sprite.last_gesture == 'FLIP':
            self.screen.blit(self.assets.images['flip1'], flip_pos)

        # Panel camera nằm riêng bên dưới, không đè ảnh hướng dẫn
        cam_x = 16
        cam_y = guide_y + guide_h + 28
        cam_w = VIDEO_WIDTH - 32

        max_cam_h = SCREEN_HEIGHT - cam_y - 20

        if max_cam_h < 180:
            max_cam_h = 180

        cam_display_h = min(VIDEO_HEIGHT, max_cam_h - 12)
        cam_h = cam_display_h + 12

        self.draw_left_panel_box(
            cam_x,
            cam_y,
            cam_w,
            cam_h
        )

        img = self.player_sprite.img

        if img is not None:
            try:
                frame_rgb = cv2.cvtColor(
                    img,
                    cv2.COLOR_BGR2RGB
                )

                frame_rgb = cv2.rotate(
                    frame_rgb,
                    cv2.ROTATE_90_COUNTERCLOCKWISE
                )

                frame_rgb = pygame.surfarray.make_surface(frame_rgb)

                frame_scaled = pygame.transform.scale(
                    frame_rgb,
                    (cam_w - 12, cam_display_h)
                )

                self.screen.blit(
                    frame_scaled,
                    (cam_x + 6, cam_y + 6)
                )

            except:
                pass

        if not self.player_sprite.in_scope:
            warning = self.assets.tiny_font.render(
                'Hands out of camera scope!',
                False,
                'red'
            )

            self.screen.blit(
                warning,
                warning.get_rect(
                    center=(VIDEO_WIDTH // 2, cam_y - 12)
                )
            )

    def draw_background(self):
        color_top = self.level['bg_top']
        color_bottom = self.level['bg_bottom']

        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT

            r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
            g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
            b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)

            pygame.draw.line(
                self.screen,
                (r, g, b),
                (GAME_X, y),
                (WINDOW_WIDTH, y)
            )

        for star in self.stars:
            star[1] += star[2]

            if star[1] > SCREEN_HEIGHT:
                star[0] = randint(GAME_X + 5, WINDOW_WIDTH - 5)
                star[1] = 0

            pygame.draw.circle(
                self.screen,
                self.level['star_color'],
                (star[0], star[1]),
                star[3]
            )

        pygame.draw.line(
            self.screen,
            (80, 255, 210),
            (GAME_X, 0),
            (GAME_X, SCREEN_HEIGHT),
            2
        )

    def draw_hud(self):
        level_text = self.assets.font.render(
            f"LEVEL {self.level_id}: {self.level['name']}",
            False,
            'white'
        )

        score_text = self.assets.font.render(
            f'SCORE: {self.score}',
            False,
            'white'
        )

        lives_text = self.assets.font.render(
            f'LIVES: {self.lives}',
            False,
            'white'
        )

        self.screen.blit(level_text, (GAME_X + 25, 20))
        self.screen.blit(score_text, (GAME_X + 25, 55))
        self.screen.blit(lives_text, (GAME_X + 25, 90))

        if self.player_sprite.ready_to_nuke:
            nuke_text = self.assets.small_font.render(
                'ULTIMATE READY',
                False,
                (180, 0, 255)
            )
        else:
            nuke_text = self.assets.small_font.render(
                'ULTIMATE COOLDOWN',
                False,
                (120, 120, 120)
            )

        self.screen.blit(nuke_text, (GAME_X + 25, 125))

        if self.player_sprite.energy_full:
            energy_text = self.assets.small_font.render(
                'ENERGY FULL - MAKE FIST',
                False,
                (0, 255, 255)
            )
        elif self.player_sprite.is_charging:
            energy_text = self.assets.small_font.render(
                'CHARGING ENERGY',
                False,
                (0, 220, 255)
            )
        else:
            energy_text = self.assets.small_font.render(
                'OPEN HAND = CHARGE',
                False,
                (170, 170, 170)
            )

        self.screen.blit(energy_text, (GAME_X + 25, 150))

        if self.player_sprite.damage > 1:
            dmg = self.assets.small_font.render(
                'POWER: DAMAGE x2',
                False,
                (255, 80, 80)
            )

            self.screen.blit(dmg, (GAME_X + 25, 175))

        if (
            self.player_sprite.laser_cooldown
            < self.player_sprite.default_laser_cooldown
        ):
            fire = self.assets.small_font.render(
                'POWER: RAPID FIRE',
                False,
                (255, 220, 40)
            )

            self.screen.blit(fire, (GAME_X + 25, 195))

        boss = self.boss_group.sprite

        if boss and boss.alive():
            boss.draw_health_bar(
                self.screen,
                GAME_X + 520,
                85,
                260
            )

    def draw_powerup_guide(self):
        x = WINDOW_WIDTH - 230
        y = SCREEN_HEIGHT - 85

        font = self.assets.tiny_font

        guide = [
            ((40, 255, 120), 'GREEN = HEAL'),
            ((255, 60, 60), 'RED = DAMAGE'),
            ((255, 220, 40), 'YELLOW = FIRE')
        ]

        for color, text in guide:
            pygame.draw.circle(
                self.screen,
                color,
                (x, y + 6),
                6
            )

            surf = font.render(text, False, 'white')
            self.screen.blit(surf, (x + 14, y))

            y += 20

    def draw_particles(self):
        for p in self.particles[:]:
            p.update()
            p.draw(
                self.screen,
                self.level['particle_color']
            )

            if p.life <= 0:
                self.particles.remove(p)

    def draw_energy_blast_range(self):
        if (
            self.player_sprite.energy_full
            or self.player_sprite.is_charging
        ):
            pygame.draw.circle(
                self.screen,
                (0, 255, 255),
                self.player_sprite.rect.center,
                180,
                1
            )

    def draw_level_clear_screen(self):
        self.draw_playing()

        overlay = pygame.Surface(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (GAME_X, 0))

        center_x = GAME_X + SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2

        card_w = 520
        card_h = 220
        card_x = center_x - card_w // 2
        card_y = center_y - card_h // 2

        card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card.fill((5, 10, 20, 220))

        self.screen.blit(card, (card_x, card_y))

        pygame.draw.rect(
            self.screen,
            (80, 255, 210),
            (card_x, card_y, card_w, card_h),
            3,
            border_radius=22
        )

        win_text = self.assets.font.render(
            'YOU WIN',
            False,
         (80, 255, 210)
        )

        self.screen.blit(
            win_text,
            win_text.get_rect(
                center=(center_x, card_y + 65)
            )
        )

        back_text = self.assets.small_font.render(
            'RETURNING TO MENU...',
            False,
            'white'
        )

        score_text = self.assets.small_font.render(
            f'SCORE: {self.score}',
            False,
            (255, 255, 255)
        )

        self.screen.blit(
            back_text,
            back_text.get_rect(
                center=(center_x, card_y + 125)
            )
        )

        self.screen.blit(
            score_text,
            score_text.get_rect(
                center=(center_x, card_y + 165)
            )
        )
    def draw_intro_screen(self):
        self.draw_background()

        center_x = GAME_X + SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2

        card_w = 820
        card_h = 580
        card_x = center_x - card_w // 2
        card_y = center_y - card_h // 2

        card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card.fill((5, 10, 22, 235))

        self.screen.blit(card, (card_x, card_y))

        pygame.draw.rect(
            self.screen,
            (80, 255, 210),
            (card_x, card_y, card_w, card_h),
            3,
            border_radius=24
        )

        title = self.assets.font.render(
            'HUMANITY COUNTERATTACK',
            False,
            (80, 255, 210)
        )

        self.screen.blit(
            title,
            title.get_rect(
                center=(center_x, card_y + 55)
            )
        )

        subtitle = self.assets.small_font.render(
            'A Gesture-Controlled Computer Vision Game',
            False,
            (220, 220, 220)
        )

        self.screen.blit(
            subtitle,
            subtitle.get_rect(
                center=(center_x, card_y + 95)
            )
        )

        # =========================
        # TYPEWRITER TEXT EFFECT
        # =========================
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.intro_start_time

        visible_chars = elapsed // self.intro_char_delay

        if visible_chars >= len(self.story_full_text):
            visible_chars = len(self.story_full_text)
            self.intro_finished = True

        visible_text = self.story_full_text[:visible_chars]
        lines = visible_text.split('\n')

        y = card_y + 145

        for line in lines:
            if line.strip() == '':
                y += 22
                continue

            text = self.assets.small_font.render(
                line,
                False,
                (235, 235, 235)
            )

            self.screen.blit(
                text,
                text.get_rect(
                    center=(center_x, y)
                )
            )

            y += 32

        # Con trỏ nhấp nháy khi chữ đang chạy
        if not self.intro_finished:
            if (current_time // 400) % 2 == 0:
                cursor = self.assets.small_font.render(
                    '_',
                    False,
                    (80, 255, 210)
                )

                self.screen.blit(
                    cursor,
                    (center_x + 245, y - 30)
                )

        # Khi chạy hết cốt truyện mới hiện hướng dẫn tiếp tục
        if self.intro_finished:
            guide_box_w = 560
            guide_box_h = 54
            guide_box_x = center_x - guide_box_w // 2
            guide_box_y = card_y + card_h - 78

            pygame.draw.rect(
                self.screen,
                (20, 30, 45),
                (guide_box_x, guide_box_y, guide_box_w, guide_box_h),
                border_radius=16
            )

            pygame.draw.rect(
                self.screen,
                (80, 255, 210),
                (guide_box_x, guide_box_y, guide_box_w, guide_box_h),
                2,
                border_radius=16
            )

            guide = self.assets.small_font.render(
                'Press ENTER or use FLIP gesture to continue',
                False,
                (255, 255, 255)
            )

            self.screen.blit(
                guide,
                guide.get_rect(
                    center=(center_x, guide_box_y + guide_box_h // 2)
                )
            )

        else:
            skip_text = self.assets.tiny_font.render(
                'Story is playing...',
                False,
                (160, 160, 160)
            )

            self.screen.blit(
                skip_text,
                skip_text.get_rect(
                    center=(center_x, card_y + card_h - 45)
                )
            )

    def draw_menu(self):
        self.draw_background()

        center_x = GAME_X + SCREEN_WIDTH // 2

        # =========================
        # TITLE AREA
        # =========================
        title_y = 105

        title = self.assets.font.render(
            'HUMANITY COUNTERATTACK',
            False,
            (80, 255, 210)
        )

        subtitle = self.assets.small_font.render(
            'Gesture-Controlled Computer Vision Game',
            False,
            (220, 220, 220)
        )

        self.screen.blit(
            title,
            title.get_rect(
                center=(center_x, title_y)
            )
        )

        self.screen.blit(
            subtitle,
            subtitle.get_rect(
                center=(center_x, title_y + 42)
            )
        )

        # Gạch trang trí dưới subtitle
        pygame.draw.line(
            self.screen,
            (80, 255, 210),
            (center_x - 210, title_y + 68),
            (center_x - 55, title_y + 68),
            2
        )

        pygame.draw.line(
            self.screen,
            (80, 255, 210),
            (center_x + 55, title_y + 68),
            (center_x + 210, title_y + 68),
            2
        )

        # =========================
        # LEVEL CARDS
        # =========================
        card_w = 660
        card_h = 95
        card_gap = 34

        total_cards_h = card_h * 3 + card_gap * 2
        start_y = SCREEN_HEIGHT // 2 - total_cards_h // 2 + 25

        for index, level_id in enumerate(LEVELS.keys()):
            data = LEVELS[level_id]
            selected = level_id == self.selected_level

            card_x = center_x - card_w // 2
            card_y = start_y + index * (card_h + card_gap)

            rect = pygame.Rect(
                card_x,
                card_y,
                card_w,
                card_h
            )

            if selected:
                box_color = data['menu_color']
                border_color = (255, 255, 255)
                text_color = (255, 255, 255)
                boss_color = (235, 235, 235)
                border_width = 4
            else:
                box_color = (28, 34, 46)
                border_color = (80, 92, 115)
                text_color = (235, 235, 235)
                boss_color = (185, 190, 205)
                border_width = 3

            shadow_rect = pygame.Rect(
                card_x + 6,
                card_y + 8,
                card_w,
                card_h
            )

            shadow = pygame.Surface(
                (card_w, card_h),
                pygame.SRCALPHA
            )

            shadow.fill((0, 0, 0, 85))

            self.screen.blit(
                shadow,
                shadow_rect
            )

            pygame.draw.rect(
                self.screen,
                box_color,
                rect,
                border_radius=18
            )

            pygame.draw.rect(
                self.screen,
                border_color,
                rect,
                border_width,
                border_radius=18
            )

            # Số màn nhỏ bên trái
            level_no = self.assets.small_font.render(
                f'LEVEL {level_id}',
                False,
                boss_color
            )

            self.screen.blit(
                level_no,
                (card_x + 32, card_y + 18)
            )

            # Tên màn
            name = self.assets.font.render(
                data['name'],
                False,
                text_color
            )

            self.screen.blit(
                name,
                (card_x + 32, card_y + 42)
            )

            # Boss nằm bên phải cho cân đối
            boss = self.assets.small_font.render(
                f'BOSS: {data["boss_name"]}',
                False,
                boss_color
            )

            self.screen.blit(
                boss,
                boss.get_rect(
                    midright=(card_x + card_w - 32, card_y + card_h // 2)
                )
            )

            # Dấu chọn màn
            if selected:
                marker = self.assets.small_font.render(
                    'SELECTED',
                    False,
                    (80, 255, 210)
                )

                self.screen.blit(
                    marker,
                    marker.get_rect(
                        midright=(card_x + card_w - 32, card_y + card_h - 20)
                    )
                )

        # =========================
        # GUIDE AREA
        # =========================
        guide_y = start_y + total_cards_h + 75

        guide_box_w = 620
        guide_box_h = 86
        guide_box_x = center_x - guide_box_w // 2
        guide_box_y = guide_y - guide_box_h // 2

        guide_panel = pygame.Surface(
            (guide_box_w, guide_box_h),
            pygame.SRCALPHA
        )

        guide_panel.fill((8, 12, 24, 160))

        self.screen.blit(
            guide_panel,
            (guide_box_x, guide_box_y)
        )

        pygame.draw.rect(
            self.screen,
            (80, 255, 210),
            (guide_box_x, guide_box_y, guide_box_w, guide_box_h),
            2,
            border_radius=18
        )

        guide1 = self.assets.small_font.render(
            'Press 1 / 2 / 3 to choose level',
            False,
            (235, 235, 235)
        )

        guide2 = self.assets.small_font.render(
            'Press ENTER or use FLIP gesture to start',
            False,
            (80, 255, 210)
        )

        self.screen.blit(
            guide1,
            guide1.get_rect(
                center=(center_x, guide_box_y + 28)
            )
        )

        self.screen.blit(
            guide2,
            guide2.get_rect(
                center=(center_x, guide_box_y + 58)
            )
        )

    def draw_end_screen(self, title, subtitle):
        self.draw_background()

        center_x = GAME_X + SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2

        card_w = 560
        card_h = 260
        card_x = center_x - card_w // 2
        card_y = center_y - card_h // 2

        card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card.fill((5, 8, 18, 210))

        self.screen.blit(card, (card_x, card_y))

        pygame.draw.rect(
            self.screen,
            (80, 255, 210),
            (card_x, card_y, card_w, card_h),
            3,
            border_radius=20
        )

        title_surf = self.assets.font.render(
            title,
            False,
            (255, 255, 255)
        )

        score_surf = self.assets.font.render(
            f'FINAL SCORE: {self.score}',
            False,
            (80, 255, 210)
        )

        sub_surf = self.assets.small_font.render(
            subtitle,
            False,
            (220, 220, 220)
        )

        self.screen.blit(
            title_surf,
            title_surf.get_rect(
                center=(center_x, card_y + 70)
            )
        )

        self.screen.blit(
            score_surf,
            score_surf.get_rect(
                center=(center_x, card_y + 135)
            )
        )

        self.screen.blit(
            sub_surf,
            sub_surf.get_rect(
                center=(center_x, card_y + 200)
            )
        )

    def update_playing(self):
        self.aliens.update(self.alien_direction)
        self.alien_position_checker()

        self.alien_lasers.update()
        self.extra_alien_timer()
        self.extra.update()
        self.boss_group.update()
        self.powerups.update()

        self.collision_checks()

        boss_dead = (
            not self.boss_group.sprite
            or self.boss_group.sprite.hp <= 0
        )

        if boss_dead:
            for alien in self.aliens.sprites():
                self.add_explosion(
                    alien.rect.centerx,
                    alien.rect.centery,
                    25
                )

            self.aliens.empty()
            self.alien_lasers.empty()
            self.extra.empty()
            self.powerups.empty()

            self.start_level_clear()

    def draw_playing(self):
        self.draw_background()

        self.blocks.draw(self.screen)
        self.aliens.draw(self.screen)
        self.alien_lasers.draw(self.screen)
        self.extra.draw(self.screen)
        self.boss_group.draw(self.screen)
        self.player_sprite.lasers.draw(self.screen)
        self.powerups.draw(self.screen)

        self.draw_energy_blast_range()
        self.draw_particles()
        self.draw_hud()
        self.draw_powerup_guide()

    def run(self):
        while True:
            self.handle_events()

            # Tự bật/tắt nhạc nền theo trạng thái game
            self.assets.update_background_music_by_state(self.state)

            self.screen.fill((0, 0, 0))

            self.player_sprite.update(
                allow_actions=(self.state == 'PLAYING')
            )

            if self.state == 'PLAYING':
                if (
                    self.player_sprite.last_gesture == 'NUKE'
                    and self.player_sprite.consume_nuke_action()
                ):
                    self.ultimate_blast()

                if self.player_sprite.consume_energy_blast_action():
                    self.energy_blast()

            self.update_hand_menu_control()
            self.draw_camera_panel()

            if self.state == 'INTRO':
                self.draw_intro_screen()

            elif self.state == 'MENU':
                self.draw_menu()

            elif self.state == 'PLAYING':
                self.update_playing()
                self.draw_playing()
                self.player_sprite.draw_player()

            elif self.state == 'LEVEL_CLEAR':
                self.draw_level_clear_screen()
                self.player_sprite.draw_player()
                self.update_level_clear()

            elif self.state == 'DEAD':
                self.draw_end_screen(
                    'YOU DIED!',
                    'Press ENTER or FLIP to return menu'
                )

            elif self.state == 'VICTORY':
                self.draw_end_screen(
                    'MISSION COMPLETE!',
                    'Press ENTER or FLIP to return menu'
                )

            pygame.display.flip()
            self.clock.tick(FPS)

    def close(self):
        self.player_sprite.release_camera()
        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.init()

    screen = pygame.display.set_mode(
        (WINDOW_WIDTH, WINDOW_HEIGHT),
        pygame.RESIZABLE
    )

    pygame.display.set_caption(
        'Humanity Counterattack - Gesture Controlled Game'
    )

    clock = pygame.time.Clock()
assets = AssetManager()

# Không cần gọi play_background_music ở đây nữa
# Game sẽ tự bật/tắt nhạc theo state
game = Game(screen, clock, assets)
game.run()