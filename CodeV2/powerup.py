import pygame


class PowerUp(pygame.sprite.Sprite):

    def __init__(self, pos, power_type):
        super().__init__()

        self.power_type = power_type

        self.image = pygame.Surface((18, 18), pygame.SRCALPHA)

        if power_type == 'heal':
            color = (40, 255, 120)

        elif power_type == 'damage':
            color = (255, 60, 60)

        else:
            color = (255, 220, 40)

        pygame.draw.circle(self.image, color, (9, 9), 8)
        pygame.draw.circle(self.image, (255, 255, 255), (9, 9), 8, 2)

        self.rect = self.image.get_rect(center=pos)

        self.speed = 2

    def update(self):

        self.rect.y += self.speed

        if self.rect.top > 700:
            self.kill()