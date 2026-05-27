import pygame


class Alien(pygame.sprite.Sprite):

    def __init__(self, color, x, y, flipped, assets):
        super().__init__()

        self.image = assets.images[color]

        self.flipped = flipped

        if flipped:
            self.image = pygame.transform.flip(
                self.image,
                False,
                True
            )

        self.rect = self.image.get_rect(
            topleft=(x, y)
        )

        if color == 'red':
            self.value = 100

        elif color == 'green':
            self.value = 200

        else:
            self.value = 300

        self.move_timer = 0

    def update(self, direction):

        if pygame.time.get_ticks() > self.move_timer + 20:
            self.rect.x += direction
            self.move_timer = pygame.time.get_ticks()


class Extra(pygame.sprite.Sprite):

    def __init__(self, side, window_width, video_width, flipped, assets):
        super().__init__()

        self.image = assets.images['extra']

        if side == 'right':
            x = window_width - 50
            self.speed = -3
        else:
            x = video_width
            self.speed = 3

        if flipped:
            self.image = pygame.transform.flip(
                self.image,
                False,
                True
            )
            y = 670
        else:
            y = 10

        self.rect = self.image.get_rect(
            topleft=(x, y)
        )

        self.video_width = video_width

    def update(self):

        self.rect.x += self.speed

        if self.rect.x < self.video_width:
            self.kill()