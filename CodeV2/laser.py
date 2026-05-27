import pygame


class Laser(pygame.sprite.Sprite):

    def __init__(
        self,
        pos,
        speed,
        screen_height,
        color='white',
        damage=1
    ):
        super().__init__()

        self.image = pygame.Surface((5, 22))
        self.image.fill(color)

        self.rect = self.image.get_rect(center=pos)

        self.speed = speed
        self.screen_height = screen_height

        self.damage = damage

    def destroy(self):

        if (
            self.rect.y <= -50 or
            self.rect.y >= self.screen_height + 50
        ):
            self.kill()

    def update(self):

        self.rect.y += self.speed
        self.destroy()