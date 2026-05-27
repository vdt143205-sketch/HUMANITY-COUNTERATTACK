import pygame
import cv2
import numpy as np
from cvzone.HandTrackingModule import HandDetector

from laser import Laser


class Player(pygame.sprite.Sprite):

    def __init__(self, pos, cwidth, speed, vwidth, screen, height, assets):
        super().__init__()

        self.assets = assets
        self.image = assets.images['player']
        self.rect = self.image.get_rect(midtop=pos)

        self.speed = speed
        self.max_x_constraint = cwidth + vwidth
        self.vwidth = vwidth
        self.screen = screen
        self.window_height = height

        self.ready_to_shoot = True
        self.ready_to_flip = True
        self.ready_to_nuke = True

        self.laser_time = 0
        self.laser_cooldown = 280
        self.default_laser_cooldown = 280

        self.flip_time = 0
        self.flip_cooldown = 450

        self.nuke_time = 0
        self.nuke_cooldown = 3000
        self.nuke_action_available = False

        self.damage = 1
        self.damage_boost_time = 0
        self.fire_boost_time = 0

        # =========================
        # ENERGY CHARGE SYSTEM
        # =========================
        self.is_charging = False
        self.energy_full = False
        self.energy_charge_start = 0
        self.energy_charge_time = 3000
        self.energy_progress = 0

        self.energy_blast_action_available = False
        self.energy_blast_cooldown = 700
        self.energy_blast_time = 0
        self.ready_to_energy_blast = True

        # Âm thanh nạp năng lượng
        self.charge_sound_playing = False
        self.charge_full_sound_played = False

        self.lasers = pygame.sprite.Group()

        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        self.detector = HandDetector(
            detectionCon=0.75,
            maxHands=1
        )

        self.fingers = [0, 0, 0, 0, 0]
        self.img = None
        self.in_scope = False

        self.flipped = False
        self.last_gesture = 'NONE'
        self.flip_action_available = False

    def reset_position(self, pos):
        self.rect = self.image.get_rect(midtop=pos)

        self.damage = 1
        self.laser_cooldown = self.default_laser_cooldown

        self.ready_to_nuke = True
        self.nuke_action_available = False

        self.is_charging = False
        self.energy_full = False
        self.energy_progress = 0
        self.energy_blast_action_available = False
        self.ready_to_energy_blast = True

        self.charge_sound_playing = False
        self.charge_full_sound_played = False

        try:
            self.assets.sounds['charge'].stop()
        except:
            pass

    def release_camera(self):
        if self.cap:
            self.cap.release()

    def constraint(self):
        if self.rect.left <= self.vwidth:
            self.rect.left = self.vwidth

        if self.rect.right >= self.max_x_constraint:
            self.rect.right = self.max_x_constraint

    def shoot_laser(self):
        speed = 25 if self.flipped else -25

        if self.damage > 1:
            color = (255, 80, 80)
        elif self.laser_cooldown < self.default_laser_cooldown:
            color = (255, 220, 40)
        else:
            color = (80, 255, 210)

        self.lasers.add(
            Laser(
                self.rect.center,
                speed,
                700,
                color=color,
                damage=self.damage
            )
        )

    def flip(self):
        self.flipped = not self.flipped

    def detect_gesture(self):
        up_count = sum(self.fingers)

        # Mở lòng bàn tay: nhận 4 hoặc 5 ngón để tránh lỗi nhận sai ngón cái
        if up_count >= 4:
            return 'CHARGE'

        # Nắm tay: dùng năng lượng nếu đã đầy
        if self.fingers == [0, 0, 0, 0, 0]:
            return 'FIST'

        # Dơ duy nhất ngón giữa: ultimate
        if self.fingers == [0, 0, 1, 0, 0]:
            return 'NUKE'

        # Dơ ngón út: flip
        if self.fingers == [0, 0, 0, 0, 1]:
            return 'FLIP'

        # Dơ ngón trỏ: bắn
        if self.fingers[1] == 1:
            return 'SHOOT'

        return 'MOVE'

    def draw_hand_box(self, img, hand, gesture):
        x, y, w, h = hand['bbox']

        if gesture == 'SHOOT':
            color = (0, 0, 220)
            text = 'SHOOT'
        elif gesture == 'FLIP':
            color = (0, 200, 0)
            text = 'FLIP'
        elif gesture == 'NUKE':
            color = (180, 0, 255)
            text = 'ULTIMATE'
        elif gesture == 'CHARGE':
            color = (0, 220, 255)
            text = 'CHARGE'
        elif gesture == 'FIST':
            color = (255, 160, 0)
            text = 'BLAST'
        else:
            color = (220, 80, 0)
            text = 'MOVE'

        cv2.rectangle(
            img,
            (x - 20, y - 20),
            (x + w + 20, y + h + 20),
            color,
            8
        )

        cv2.putText(
            img,
            text,
            (x - 25, y - 30),
            cv2.FONT_HERSHEY_PLAIN,
            5,
            color,
            7
        )

        cv2.putText(
            img,
            str(self.fingers),
            (x - 25, y + h + 45),
            cv2.FONT_HERSHEY_PLAIN,
            3,
            color,
            4
        )

    def read_fingers(self):
        success, img = self.cap.read()

        if not success or img is None:
            self.in_scope = False
            self.last_gesture = 'NONE'
            self.is_charging = False
            return False

        img = cv2.flip(img, 1)

        hands, img = self.detector.findHands(
            img,
            draw=False,
            flipType=False
        )

        self.img = img

        if hands:
            hand = hands[0]

            x, y, w, h = hand['bbox']
            self.fingers = self.detector.fingersUp(hand)
            self.last_gesture = self.detect_gesture()

            # Khi đang tích năng lượng thì nhân vật đứng im
            if self.last_gesture != 'CHARGE':
                center_x = x + w // 2
                center_x = np.clip(center_x, 100, 1150)

                mapped_x = center_x - 100
                mapped_x = mapped_x * (
                    self.max_x_constraint - self.vwidth
                )
                mapped_x = mapped_x // 1050

                self.rect.x = int(mapped_x + self.vwidth)

            self.draw_hand_box(img, hand, self.last_gesture)

            self.img = img
            return True

        self.fingers = [0, 0, 0, 0, 0]
        self.last_gesture = 'NONE'
        self.is_charging = False
        self.img = img

        return False

    def update_energy_charge(self, allow_actions=True):
        if not allow_actions:
            self.is_charging = False

            if self.charge_sound_playing:
                self.assets.sounds['charge'].stop()
                self.charge_sound_playing = False

            return

        current_time = pygame.time.get_ticks()

        # =========================
        # XÒE LÒNG BÀN TAY ĐỂ NẠP
        # =========================
        if self.last_gesture == 'CHARGE':

            if not self.is_charging and not self.energy_full:
                self.is_charging = True
                self.energy_charge_start = current_time

                if not self.charge_sound_playing:
                    self.assets.sounds['charge'].play(-1)
                    self.charge_sound_playing = True

            if self.is_charging and not self.energy_full:
                elapsed = current_time - self.energy_charge_start
                self.energy_progress = min(1, elapsed / self.energy_charge_time)

                if elapsed >= self.energy_charge_time:
                    self.energy_full = True
                    self.energy_progress = 1
                    self.is_charging = False

                    if self.charge_sound_playing:
                        self.assets.sounds['charge'].stop()
                        self.charge_sound_playing = False

                    if not self.charge_full_sound_played:
                        self.assets.sounds['charge_full'].play()
                        self.charge_full_sound_played = True

        else:
            if not self.energy_full:
                self.is_charging = False
                self.energy_progress = 0
                self.charge_full_sound_played = False

            if self.charge_sound_playing:
                self.assets.sounds['charge'].stop()
                self.charge_sound_playing = False

        # =========================
        # NẮM TAY KHI ĐẦY NĂNG LƯỢNG
        # =========================
        if (
            self.last_gesture == 'FIST'
            and self.energy_full
            and self.ready_to_energy_blast
        ):
            self.energy_blast_action_available = True
            self.energy_full = False
            self.energy_progress = 0
            self.is_charging = False
            self.charge_full_sound_played = False

            if self.charge_sound_playing:
                self.assets.sounds['charge'].stop()
                self.charge_sound_playing = False

            self.ready_to_energy_blast = False
            self.energy_blast_time = current_time

        if not self.ready_to_energy_blast:
            if current_time - self.energy_blast_time >= self.energy_blast_cooldown:
                self.ready_to_energy_blast = True

    def consume_energy_blast_action(self):
        if self.energy_blast_action_available:
            self.energy_blast_action_available = False
            return True

        return False

    def get_input(self, allow_actions=True):
        if not allow_actions:
            return

        # Đang tích năng lượng thì không bắn, không flip
        if self.last_gesture == 'CHARGE':
            return

        if self.last_gesture == 'SHOOT' and self.ready_to_shoot:
            self.assets.sounds['laser'].play()
            self.shoot_laser()

            self.ready_to_shoot = False
            self.laser_time = pygame.time.get_ticks()

        if self.last_gesture == 'FLIP' and self.ready_to_flip:
            self.flip()

            self.ready_to_flip = False
            self.flip_action_available = True
            self.flip_time = pygame.time.get_ticks()

        if self.last_gesture == 'NUKE' and self.ready_to_nuke:
            self.nuke_action_available = True
            self.ready_to_nuke = False
            self.nuke_time = pygame.time.get_ticks()

    def consume_flip_action(self):
        if self.flip_action_available:
            self.flip_action_available = False
            return True

        return False

    def consume_nuke_action(self):
        if self.nuke_action_available:
            self.nuke_action_available = False
            return True

        return False

    def apply_powerup(self, power_type):
        if power_type == 'damage':
            self.damage = 2
            self.damage_boost_time = pygame.time.get_ticks()

        elif power_type == 'fire':
            self.laser_cooldown = 120
            self.fire_boost_time = pygame.time.get_ticks()

    def update_powerup_timers(self):
        current_time = pygame.time.get_ticks()

        if (
            self.damage == 2
            and current_time - self.damage_boost_time > 6000
        ):
            self.damage = 1

        if (
            self.laser_cooldown == 120
            and current_time - self.fire_boost_time > 6000
        ):
            self.laser_cooldown = self.default_laser_cooldown

    def recharge_shoot(self):
        if not self.ready_to_shoot:
            current_time = pygame.time.get_ticks()

            if (
                current_time - self.laser_time >= self.laser_cooldown
                and self.last_gesture != 'SHOOT'
            ):
                self.ready_to_shoot = True

    def recharge_flip(self):
        if not self.ready_to_flip:
            current_time = pygame.time.get_ticks()

            if (
                current_time - self.flip_time >= self.flip_cooldown
                and self.last_gesture != 'FLIP'
            ):
                self.ready_to_flip = True

    def recharge_nuke(self):
        if not self.ready_to_nuke:
            current_time = pygame.time.get_ticks()

            if (
                current_time - self.nuke_time >= self.nuke_cooldown
                and self.last_gesture != 'NUKE'
            ):
                self.ready_to_nuke = True

    def update(self, allow_actions=True):
        if self.read_fingers():
            self.in_scope = True
        else:
            self.in_scope = False

        self.constraint()
        self.lasers.update()

        self.update_energy_charge(allow_actions)
        self.get_input(allow_actions)

        self.recharge_flip()
        self.recharge_shoot()
        self.recharge_nuke()

        self.update_powerup_timers()

    def draw_energy_bar(self):
        if self.energy_progress <= 0 and not self.energy_full:
            return

        bar_width = 70
        bar_height = 8

        x = self.rect.centerx - bar_width // 2
        y = self.rect.top - 22

        pygame.draw.rect(
            self.screen,
            (30, 30, 30),
            (x, y, bar_width, bar_height),
            border_radius=5
        )

        if self.energy_full:
            color = (0, 255, 255)
            fill_width = bar_width
        else:
            color = (80, 220, 255)
            fill_width = int(bar_width * self.energy_progress)

        pygame.draw.rect(
            self.screen,
            color,
            (x, y, fill_width, bar_height),
            border_radius=5
        )

        pygame.draw.rect(
            self.screen,
            (255, 255, 255),
            (x, y, bar_width, bar_height),
            1,
            border_radius=5
        )

    def draw_aura(self):
        if not self.is_charging and not self.energy_full:
            return

        current_time = pygame.time.get_ticks()

        if self.energy_full:
            radius = 38 + int((current_time // 120) % 8)
            color = (0, 255, 255)
        else:
            radius = 30 + int(self.energy_progress * 16)
            color = (80, 220, 255)

        pygame.draw.circle(
            self.screen,
            color,
            self.rect.center,
            radius,
            2
        )

        pygame.draw.circle(
            self.screen,
            color,
            self.rect.center,
            max(8, radius - 12),
            1
        )

    def draw_player(self):
        self.draw_aura()

        if self.flipped:
            image = pygame.transform.flip(
                self.image,
                False,
                True
            )
        else:
            image = self.image

        self.screen.blit(image, self.rect)
        self.draw_energy_bar()