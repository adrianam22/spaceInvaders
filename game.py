import math
import random
import sys

import pygame

from android_server import AndroidServer
from constants import BLACK, CYAN, FPS, GRAY, GREEN, LIGHT_GRAY, ORANGE, RED, SCREEN_H, SCREEN_W, TITLE, WHITE, YELLOW
from entities import Barrier, EnemyGrid, Player
from sprites import PLAYER_AVATARS, draw_player, draw_stars


class SpaceInvaders:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont("consolas", 48, bold=True)
        self.font_med = pygame.font.SysFont("consolas", 28)
        self.font_small = pygame.font.SysFont("consolas", 18)

        self.server = AndroidServer(port=5555)
        self.server.start()

        self.sounds = {}
        self.high_score = 0
        self.selected_avatar = 0
        self.menu_index = 0
        self.menu_items = ["Start Game", "Choose Avatar"]
        self._init_sounds()
        self._reset_session()

    def _init_sounds(self):
        sr = 44100
        pygame.mixer.pre_init(sr, -16, 1, 512)
        try:
            import numpy as np

            def beep(freq, duration_ms, volume=0.3):
                frames = int(sr * duration_ms / 1000)
                timeline = np.linspace(0, duration_ms / 1000, frames, False)
                wave = np.sign(np.sin(2 * np.pi * freq * timeline))
                fade = np.linspace(1, 0, frames)
                wave = (wave * fade * volume * 32767).astype(np.int16)
                return pygame.sndarray.make_sound(wave)

            self.sounds["shoot"] = beep(880, 80, 0.2)
            self.sounds["explode"] = beep(110, 200, 0.4)
            self.sounds["hit"] = beep(220, 150, 0.3)
            self.sounds["level"] = beep(440, 400, 0.3)
        except ImportError:
            pass

    def play(self, name):
        if name in self.sounds:
            self.sounds[name].play()

    def _reset_session(self):
        self.player = Player(self.selected_avatar)
        self.enemies = EnemyGrid()
        self.barriers = [Barrier(120 + index * 170, SCREEN_H - 140) for index in range(4)]
        self.wave = 1
        self.state = "menu"
        self.stars = [(random.randint(0, SCREEN_W), random.randint(0, SCREEN_H), random.randint(80, 220)) for _ in range(100)]
        self.explosion_particles = []

    def _start_game(self):
        self.player = Player(self.selected_avatar)
        self.enemies = EnemyGrid()
        self.barriers = [Barrier(120 + index * 170, SCREEN_H - 140) for index in range(4)]
        self.wave = 1
        self.explosion_particles.clear()
        self.state = "playing"

    def _next_wave(self):
        self.wave += 1
        self.enemies = EnemyGrid()
        self.barriers = [Barrier(120 + index * 170, SCREEN_H - 140) for index in range(4)]
        self.player.bullets.clear()
        self.state = "playing"
        self.play("level")

    def _add_explosion(self, x, y, color=ORANGE, count=12):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(1, 4)
            self.explosion_particles.append(
                {
                    "x": x,
                    "y": y,
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed,
                    "life": random.randint(20, 40),
                    "color": color,
                    "size": random.randint(2, 5),
                }
            )

    def _update_particles(self):
        alive = []
        for particle in self.explosion_particles:
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            particle["life"] -= 1
            if particle["life"] > 0:
                alive.append(particle)
        self.explosion_particles = alive

    def _draw_particles(self):
        for particle in self.explosion_particles:
            pygame.draw.circle(self.screen, particle["color"], (int(particle["x"]), int(particle["y"])), particle["size"])

    def _check_collisions(self):
        for bullet in self.player.bullets[:]:
            bx, by = bullet
            for enemy in self.enemies.enemies:
                if not enemy["alive"]:
                    continue
                enemy_rect = pygame.Rect(enemy["x"], enemy["y"], 44, 40)
                if enemy_rect.collidepoint(bx, by):
                    enemy["alive"] = False
                    self.player.bullets.remove(bullet)
                    self.player.score += enemy["pts"]
                    self._add_explosion(enemy["x"] + 22, enemy["y"] + 20, YELLOW if enemy["type"] == 3 else ORANGE)
                    self.play("explode")
                    break

        for bullet in self.enemies.bullets[:]:
            bx, by = bullet
            for barrier in self.barriers:
                if barrier.health > 0 and barrier.rect.collidepoint(bx, by):
                    barrier.hit()
                    self.enemies.bullets.remove(bullet)
                    break

        player_rect = self.player.get_rect()
        for bullet in self.enemies.bullets[:]:
            bx, by = bullet
            if player_rect.collidepoint(bx, by) and self.player.invincible == 0:
                self.enemies.bullets.remove(bullet)
                self.player.lives -= 1
                self.player.invincible = 90
                self._add_explosion(self.player.x + 25, self.player.y + 25, RED, 20)
                self.play("hit")
                if self.player.lives <= 0:
                    self.state = "dead"

        for bullet in self.player.bullets[:]:
            bx, by = bullet
            for barrier in self.barriers:
                if barrier.health > 0 and barrier.rect.collidepoint(bx, by):
                    barrier.hit()
                    self.player.bullets.remove(bullet)
                    break

    def _draw_hud(self):
        score_text = self.font_med.render(f"SCORE: {self.player.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        for index in range(self.player.lives):
            draw_player(self.screen, SCREEN_W - 60 - index * 55, 0, self.selected_avatar)

        wave_text = self.font_med.render(f"WAVE: {self.wave}", True, CYAN)
        self.screen.blit(wave_text, (SCREEN_W // 2 - wave_text.get_width() // 2, 10))

        pygame.draw.line(self.screen, GREEN, (0, SCREEN_H - 55), (SCREEN_W, SCREEN_H - 55), 2)

        ip_text = self.font_small.render(f"Android: {self.server.server_ip}:5555", True, GRAY)
        self.screen.blit(ip_text, (10, SCREEN_H - 22))

        high_score_text = self.font_small.render(f"Record: {self.high_score}", True, LIGHT_GRAY)
        self.screen.blit(high_score_text, (SCREEN_W - high_score_text.get_width() - 10, SCREEN_H - 22))

    def _draw_menu(self):
        title = self.font_big.render("SPACE INVADERS", True, GREEN)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 70))

        subtitle = self.font_small.render("Main Menu", True, LIGHT_GRAY)
        self.screen.blit(subtitle, (SCREEN_W // 2 - subtitle.get_width() // 2, 130))

        for index, item in enumerate(self.menu_items):
            color = CYAN if index == self.menu_index else WHITE
            suffix = ""
            if item == "Choose avatar":
                suffix = f": {PLAYER_AVATARS[self.selected_avatar]['name']}"
            text = self.font_med.render(f"{'>' if index == self.menu_index else ' '} {item}{suffix}", True, color)
            self.screen.blit(text, (SCREEN_W // 2 - text.get_width() // 2, 220 + index * 50))

        draw_player(self.screen, SCREEN_W // 2 - 25, 350, self.selected_avatar)
        avatar_text = self.font_small.render(f"Selected avatar: {PLAYER_AVATARS[self.selected_avatar]['name']}", True, LIGHT_GRAY)
        self.screen.blit(avatar_text, (SCREEN_W // 2 - avatar_text.get_width() // 2, 420))

        instructions = [
            "MENU: UP / DOWN, ENTER",
            "GAME: LEFT / RIGHT, SPACE",
        ]
        for index, line in enumerate(instructions):
            text = self.font_small.render(line, True, GRAY)
            self.screen.blit(text, (SCREEN_W // 2 - text.get_width() // 2, 490 + index * 22))

    def _draw_avatar_menu(self):
        title = self.font_big.render("CHOOSE AVATAR", True, CYAN)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 70))

        hint = self.font_small.render(" LEFT / RIGHT for selection, ENTER / ESC for back", True, LIGHT_GRAY)
        self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, 130))

        spacing = 210
        start_x = SCREEN_W // 2 - spacing
        for index, avatar in enumerate(PLAYER_AVATARS):
            x = start_x + index * spacing
            y = 260
            if index == self.selected_avatar:
                pygame.draw.rect(self.screen, CYAN, (x - 30, y - 40, 110, 140), 3, border_radius=10)
            draw_player(self.screen, x, y, index)
            label = self.font_small.render(avatar["name"], True, WHITE if index == self.selected_avatar else GRAY)
            self.screen.blit(label, (x + 25 - label.get_width() // 2, y + 70))

    def _draw_overlay(self, title, color, sub=""):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        title_text = self.font_big.render(title, True, color)
        self.screen.blit(title_text, (SCREEN_W // 2 - title_text.get_width() // 2, SCREEN_H // 2 - 60))

        if sub:
            sub_text = self.font_med.render(sub, True, WHITE)
            self.screen.blit(sub_text, (SCREEN_W // 2 - sub_text.get_width() // 2, SCREEN_H // 2 + 10))

        hint = self.font_small.render("ENTER = Continue   |   ESC = Menu ", True,  WHITE)
        self.screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H // 2 + 70))

    def run(self):
        while True:
            self.clock.tick(FPS)
            self._handle_events()
            self._update()
            self._draw()
            pygame.display.flip()

    def _handle_events(self):
        kb = pygame.key.get_pressed()
        android = self.server.get_commands()
        left = kb[pygame.K_LEFT] or android.get("left", False)
        right = kb[pygame.K_RIGHT] or android.get("right", False)
        fire = kb[pygame.K_SPACE] or android.get("fire", False)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.server.stop()
                pygame.quit()
                sys.exit()
            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                if self.state in ("avatar_menu", "dead", "win", "playing"):
                    self.state = "menu"
                continue

            if self.state == "menu":
                if event.key == pygame.K_UP:
                    self.menu_index = (self.menu_index - 1) % len(self.menu_items)
                elif event.key == pygame.K_DOWN:
                    self.menu_index = (self.menu_index + 1) % len(self.menu_items)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    if self.menu_index == 0:
                        self._start_game()
                    else:
                        self.state = "avatar_menu"
            elif self.state == "avatar_menu":
                if event.key == pygame.K_LEFT:
                    self.selected_avatar = (self.selected_avatar - 1) % len(PLAYER_AVATARS)
                elif event.key == pygame.K_RIGHT:
                    self.selected_avatar = (self.selected_avatar + 1) % len(PLAYER_AVATARS)
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.state = "menu"
            elif self.state == "dead":
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._start_game()
            elif self.state == "win":
                if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._next_wave()

        if self.state == "playing":
            self.player.move(left, right)
            if fire:
                self.player.shoot()

    def _update(self):
        self._update_particles()
        if self.state != "playing":
            return

        self.player.update()
        self.enemies.update(self.wave)
        self._check_collisions()

        if not self.enemies.alive_list():
            self.state = "win"
        if self.enemies.check_invasion():
            self.player.lives = 0
            self.state = "dead"

        self.high_score = max(self.high_score, self.player.score)

    def _draw(self):
        self.screen.fill(BLACK)
        draw_stars(self.screen, self.stars)

        if self.state == "menu":
            self._draw_menu()
            return
        if self.state == "avatar_menu":
            self._draw_avatar_menu()
            return

        for barrier in self.barriers:
            barrier.draw(self.screen)
        self.enemies.draw(self.screen)
        self.player.draw(self.screen)
        self._draw_particles()
        self._draw_hud()

        if self.state == "dead":
            sub = f"NEW HIGH SCORE: {self.player.score}!" if self.player.score >= self.high_score and self.player.score > 0 else f"Finale score: {self.player.score}"
            self._draw_overlay("GAME OVER", RED, sub)
        elif self.state == "win":
            self._draw_overlay(f"WAVE {self.wave} COMPLETED!", GREEN, f"Score: {self.player.score}  |  ENTER = Val {self.wave + 1}")
