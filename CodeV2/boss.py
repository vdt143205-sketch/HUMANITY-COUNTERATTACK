import pygame
import math


class Boss(pygame.sprite.Sprite):

    def __init__(
        self,
        name,
        hp,
        window_width,
        game_x,
        color,
        speed,
        image=None,
        pattern='horizontal'
    ):
        super().__init__()

        self.name = name
        self.max_hp = hp
        self.hp = hp

        self.pattern = pattern

        if image is not None:
            self.image = image

        else:
            self.image = pygame.Surface((150, 85), pygame.SRCALPHA)

            pygame.draw.rect(
                self.image,
                color,
                (0, 0, 150, 85),
                border_radius=20
            )

        self.rect = self.image.get_rect(
            center=(game_x + 300, 165)
        )

        self.base_y = self.rect.y

        self.direction_x = 1
        self.direction_y = 1

        self.speed = speed
        self.timer = 0

        self.game_x = game_x
        self.window_width = window_width

    def update(self):

        self.timer += 1

        # LEVEL 1
        if self.pattern == 'horizontal':

            self.rect.x += self.speed * self.direction_x

        # LEVEL 2
        elif self.pattern == 'wave':

            self.rect.x += self.speed * self.direction_x

            self.rect.y = (
                self.base_y +
                int(math.sin(self.timer * 0.05) * 50)
            )

        # LEVEL 3
        elif self.pattern == 'aggressive':

            self.rect.x += self.speed * self.direction_x
            self.rect.y += self.direction_y * 2

            if self.rect.top <= 115:
                self.direction_y = 1

            if self.rect.bottom >= 350:
                self.direction_y = -1

        if self.rect.left <= self.game_x + 20:
            self.direction_x = 1

        if self.rect.right >= self.window_width - 20:
            self.direction_x = -1

    def take_damage(self, amount):

        self.hp -= amount

        if self.hp <= 0:
            self.kill()

    def draw_health_bar(self, screen, x, y, width):

        width = 260
        height = 14

        pygame.draw.rect(
            screen,
            (35, 35, 35),
            (x, y, width, height),
            border_radius=8
        )

        hp_ratio = max(0, self.hp / self.max_hp)

        health_width = int(hp_ratio * width)

        pygame.draw.rect(
            screen,
            (255, 70, 70),
            (x, y, health_width, height),
            border_radius=8
        )

        pygame.draw.rect(
            screen,
            (255, 255, 255),
            (x, y, width, height),
            2,
            border_radius=8
        )

        font = pygame.font.Font('../Resources/Pixeled.ttf', 6)

        text = font.render(
            f'{self.name} HP {self.hp}/{self.max_hp}',
            False,
            'white'
        )

        screen.blit(text, (x + 6, y - 14))