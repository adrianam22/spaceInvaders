import random
import pygame

from constants import CYAN, ORANGE, PURPLE, RED, SCREEN_H, SCREEN_W, YELLOW
from sprites import draw_barrier, draw_bullet, draw_enemy_type1, draw_enemy_type2, draw_enemy_type3, draw_player


class Player:
    def __init__(self, avatar_index=0):
        self.w, self.h = 50, 50
        self.x = SCREEN_W // 2 - self.w // 2
        self.y = SCREEN_H - 80
        self.speed = 5
        self.bullets = []
        self.shoot_cooldown = 0
        self.lives = 3
        self.score = 0
        self.invincible = 0
        self.avatar_index = avatar_index

    def move(self, left, right):
        if left:
            self.x = max(0, self.x - self.speed)
        if right:
            self.x = min(SCREEN_W - self.w, self.x + self.speed)

    def shoot(self):
        if self.shoot_cooldown <= 0:
            center_x = self.x + self.w // 2
            self.bullets.append([center_x, self.y])
            self.shoot_cooldown = 20

    def update(self):
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.invincible > 0:
            self.invincible -= 1
        self.bullets = [[bx, by - 12] for bx, by in self.bullets if by > -10]

    def get_rect(self):
        return pygame.Rect(self.x + 6, self.y + 8, self.w - 12, self.h - 8)

    def draw(self, surface):
        if self.invincible % 6 < 3:
            draw_player(surface, self.x, self.y, self.avatar_index)
        for bx, by in self.bullets:
            draw_bullet(surface, bx, by, CYAN)


class EnemyGrid:
    ROWS = 5
    COLS = 11
    X_GAP = 60
    Y_GAP = 50

    def __init__(self):
        self.enemies = []
        self.direction = 1
        self.drop_y = 20
        self.move_timer = 0
        self.move_interval = 45
        self.bullets = []
        self.shoot_timer = 0
        self.shoot_interval = 90
        self._create()

    def _create(self):
        types = [3, 2, 2, 1, 1]
        points = [30, 20, 20, 10, 10]
        for row in range(self.ROWS):
            for col in range(self.COLS):
                self.enemies.append(
                    {
                        "x": 60 + col * self.X_GAP,
                        "y": 60 + row * self.Y_GAP,
                        "type": types[row],
                        "pts": points[row],
                        "alive": True,
                        "anim": col % 2,
                    }
                )

    def alive_list(self):
        return [enemy for enemy in self.enemies if enemy["alive"]]

    def update(self, wave=1):
        self.move_timer += 1
        interval = max(8, self.move_interval - wave * 4)
        if self.move_timer >= interval:
            self.move_timer = 0
            alive = self.alive_list()
            if not alive:
                return

            min_x = min(enemy["x"] for enemy in alive)
            max_x = max(enemy["x"] for enemy in alive) + 44

            drop = False
            if max_x >= SCREEN_W - 5 and self.direction == 1:
                self.direction = -1
                drop = True
            elif min_x <= 5 and self.direction == -1:
                self.direction = 1
                drop = True

            step = 18 + wave * 2
            for enemy in self.enemies:
                if enemy["alive"]:
                    enemy["x"] += self.direction * step
                    if drop:
                        enemy["y"] += self.drop_y

            for enemy in self.enemies:
                enemy["anim"] = 1 - enemy["anim"]

        self.shoot_timer += 1
        shoot_interval = max(30, self.shoot_interval - wave * 8)
        if self.shoot_timer >= shoot_interval:
            self.shoot_timer = 0
            alive = self.alive_list()
            if alive:
                shooter = random.choice(alive)
                self.bullets.append([shooter["x"] + 22, shooter["y"] + 40])

        self.bullets = [[bx, by + 7] for bx, by in self.bullets if by < SCREEN_H + 10]

    def draw(self, surface):
        draw_funcs = {1: draw_enemy_type1, 2: draw_enemy_type2, 3: draw_enemy_type3}
        colors_by_type = {1: [RED, ORANGE], 2: [PURPLE, (220, 50, 220)], 3: [YELLOW, (200, 200, 0)]}
        for enemy in self.enemies:
            if enemy["alive"]:
                draw_func = draw_funcs[enemy["type"]]
                draw_func(surface, enemy["x"], enemy["y"], colors_by_type[enemy["type"]][enemy["anim"]])
        for bx, by in self.bullets:
            draw_bullet(surface, bx, by, RED)

    def check_invasion(self):
        return any(enemy["y"] + 40 >= SCREEN_H - 80 for enemy in self.alive_list())


class Barrier:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 4
        self.rect = pygame.Rect(x, y, 48, 40)

    def draw(self, surface):
        if self.health > 0:
            draw_barrier(surface, self.x, self.y, self.health)

    def hit(self):
        self.health -= 1
