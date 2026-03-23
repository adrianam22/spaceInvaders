import random

import pygame

from constants import BLACK, CYAN, DARK_GREEN, GRAY, GREEN, LIGHT_GRAY, ORANGE, PURPLE, RED, WHITE, YELLOW


def draw_player_classic(surface, x, y):
    cx = x + 25
    pygame.draw.polygon(surface, GREEN, [(cx, y), (cx - 22, y + 45), (cx + 22, y + 45)])
    pygame.draw.rect(surface, DARK_GREEN, (cx - 22, y + 35, 10, 12))
    pygame.draw.rect(surface, DARK_GREEN, (cx + 12, y + 35, 10, 12))
    pygame.draw.ellipse(surface, CYAN, (cx - 8, y + 12, 16, 18))
    flame_h = random.randint(6, 14)
    pygame.draw.polygon(surface, ORANGE, [(cx - 4, y + 47), (cx + 4, y + 47), (cx, y + 47 + flame_h)])


def draw_player_arrow(surface, x, y):
    cx = x + 25
    pygame.draw.polygon(surface, CYAN, [(cx, y), (cx - 20, y + 18), (cx - 12, y + 45), (cx + 12, y + 45), (cx + 20, y + 18)])
    pygame.draw.polygon(surface, WHITE, [(cx, y + 8), (cx - 7, y + 24), (cx + 7, y + 24)])
    pygame.draw.rect(surface, (0, 170, 200), (cx - 18, y + 30, 8, 12))
    pygame.draw.rect(surface, (0, 170, 200), (cx + 10, y + 30, 8, 12))
    flame_h = random.randint(8, 16)
    pygame.draw.polygon(surface, YELLOW, [(cx - 5, y + 45), (cx + 5, y + 45), (cx, y + 45 + flame_h)])


def draw_player_tank(surface, x, y):
    cx = x + 25
    pygame.draw.rect(surface, PURPLE, (cx - 18, y + 12, 36, 24), border_radius=8)
    pygame.draw.polygon(surface, PURPLE, [(cx, y), (cx - 10, y + 15), (cx + 10, y + 15)])
    pygame.draw.rect(surface, LIGHT_GRAY, (cx - 12, y + 18, 24, 10), border_radius=4)
    pygame.draw.rect(surface, YELLOW, (cx - 6, y + 20, 12, 6), border_radius=3)
    pygame.draw.rect(surface, (120, 0, 180), (cx - 22, y + 28, 8, 14))
    pygame.draw.rect(surface, (120, 0, 180), (cx + 14, y + 28, 8, 14))
    flame_h = random.randint(6, 12)
    pygame.draw.polygon(surface, RED, [(cx - 4, y + 36), (cx + 4, y + 36), (cx, y + 36 + flame_h)])


PLAYER_AVATARS = [
    {"id": "classic", "name": "Classic", "draw": draw_player_classic},
    {"id": "arrow", "name": "Arrow", "draw": draw_player_arrow},
    {"id": "nova", "name": "Nova", "draw": draw_player_tank},
]


def draw_player(surface, x, y, avatar_index=0):
    PLAYER_AVATARS[avatar_index]["draw"](surface, x, y)


def draw_enemy_type1(surface, x, y, color=RED):
    cx = x + 22
    pygame.draw.ellipse(surface, color, (cx - 14, y + 8, 28, 22))
    pygame.draw.polygon(surface, color, [(cx - 14, y + 14), (cx - 32, y + 5), (cx - 32, y + 28), (cx - 14, y + 25)])
    pygame.draw.polygon(surface, color, [(cx + 14, y + 14), (cx + 32, y + 5), (cx + 32, y + 28), (cx + 14, y + 25)])
    pygame.draw.circle(surface, WHITE, (cx - 5, y + 16), 4)
    pygame.draw.circle(surface, WHITE, (cx + 5, y + 16), 4)
    pygame.draw.circle(surface, BLACK, (cx - 5, y + 16), 2)
    pygame.draw.circle(surface, BLACK, (cx + 5, y + 16), 2)
    for i, ox in enumerate([-10, -3, 4, 11]):
        pygame.draw.line(surface, color, (cx + ox, y + 30), (cx + ox - 2 + i, y + 40), 2)


def draw_enemy_type2(surface, x, y, color=PURPLE):
    cx = x + 22
    pygame.draw.rect(surface, color, (cx - 16, y + 6, 32, 24), border_radius=6)
    pygame.draw.polygon(surface, color, [(cx - 16, y + 8), (cx - 30, y + 2), (cx - 30, y + 18), (cx - 16, y + 20)])
    pygame.draw.polygon(surface, color, [(cx + 16, y + 8), (cx + 30, y + 2), (cx + 30, y + 18), (cx + 16, y + 20)])
    pygame.draw.rect(surface, YELLOW, (cx - 10, y + 10, 7, 7))
    pygame.draw.rect(surface, YELLOW, (cx + 3, y + 10, 7, 7))
    for ox in [-12, -5, 5, 12]:
        pygame.draw.line(surface, color, (cx + ox, y + 30), (cx + ox, y + 40), 2)


def draw_enemy_type3(surface, x, y, color=YELLOW):
    cx = x + 22
    pygame.draw.ellipse(surface, color, (cx - 20, y + 12, 40, 18))
    pygame.draw.ellipse(surface, LIGHT_GRAY, (cx - 10, y + 4, 20, 16))
    for i, ox in enumerate([-14, -6, 2, 10]):
        light_color = [RED, GREEN, CYAN, YELLOW][i]
        pygame.draw.circle(surface, light_color, (cx + ox, y + 21), 3)


def draw_bullet(surface, x, y, color=GREEN):
    pygame.draw.rect(surface, color, (x - 2, y, 4, 12), border_radius=2)
    pygame.draw.circle(surface, WHITE, (x, y + 2), 2)


def draw_barrier(surface, x, y, health):
    colors = [GREEN, DARK_GREEN, GRAY, (50, 50, 50)]
    color_index = min(3 - (health - 1), 3)
    color = colors[color_index]
    blocks = [
        (0, 1), (0, 2), (0, 3), (0, 4),
        (1, 0), (1, 1), (1, 2), (1, 3), (1, 4), (1, 5),
        (2, 0), (2, 1), (2, 2), (2, 3), (2, 4), (2, 5),
        (3, 0), (3, 1), (3, 4), (3, 5),
        (4, 0), (4, 1), (4, 4), (4, 5),
    ]
    block_size = 8
    for row, col in blocks:
        if random.random() > 0.15 * (4 - health):
            pygame.draw.rect(surface, color, (x + col * block_size, y + row * block_size, block_size - 1, block_size - 1))


def draw_stars(surface, stars):
    for sx, sy, brightness in stars:
        color = (brightness, brightness, brightness)
        pygame.draw.circle(surface, color, (sx, sy), 1)
