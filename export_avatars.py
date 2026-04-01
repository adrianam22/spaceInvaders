# export_avatars.py
import pygame
from sprites import PLAYER_AVATARS, draw_player

pygame.init()

for index in range(len(PLAYER_AVATARS)):
    surface = pygame.Surface((200, 200), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))  # transparent

    scaled_surface = pygame.Surface((50, 50), pygame.SRCALPHA)
    scaled_surface.fill((0, 0, 0, 0))
    draw_player(scaled_surface, 0, 0, index)

    scaled = pygame.transform.scale(scaled_surface, (200, 200))

    pygame.image.save(scaled, f"avatar_{index}.png")
    print(f"Saved avatar_{index}.png")

pygame.quit()