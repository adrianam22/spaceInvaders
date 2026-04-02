import math
import random
import sys

import pygame

from constants import BLACK, FPS, GREEN, ORANGE, RED, SCREEN_H, SCREEN_W, TITLE, YELLOW
from entities import Barrier, EnemyGrid, Player
from sprites import PLAYER_AVATARS, draw_stars
from ui_screens import draw_avatar_menu, draw_countdown_overlay, draw_hud, draw_menu, draw_overlay, draw_pause


class SpaceInvaders:
    def __init__(self, server=None):
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont("consolas", 48, bold=True)
        self.font_med = pygame.font.SysFont("consolas", 28)
        self.font_small = pygame.font.SysFont("consolas", 18)

        self.sounds = {}
        self.high_score = 0
        self.selected_avatar = 0
        self.menu_index = 0
        self.menu_items = ["Start Game", "Choose Avatar"]
        self.pause_index = 0
        self.pause_items = ["Resume", "Change Avatar", "Quit Game"]
        self.previous_state = "menu"
        self.server = server
        self.remote_left_held = False
        self.remote_right_held = False
        self.remote_left_once = False
        self.remote_right_once = False
        self.remote_fire_requested = False
        self.countdown_end_time = 0
        self._init_sounds()
        self._reset_session()

    def _init_sounds(self):
        self.sounds["shoot"] = pygame.mixer.Sound("assets/sounds/laser.wav")
        self.sounds["hit"] = pygame.mixer.Sound("assets/sounds/Boom.wav")
        self.sounds["explode"] = pygame.mixer.Sound("assets/sounds/Boom.wav")
        self.sounds["win"] = pygame.mixer.Sound("assets/sounds/win.wav")
        self.sounds["fail"] = pygame.mixer.Sound("assets/sounds/fail.wav")
        self.sounds["level"] = pygame.mixer.Sound("assets/sounds/win.wav")

        self.sounds["shoot"].set_volume(0.4)
        self.sounds["hit"].set_volume(0.3)
        self.sounds["explode"].set_volume(0.3)
        self.sounds["win"].set_volume(0.5)
        self.sounds["fail"].set_volume(0.5)

    def play(self, name):
        if name in self.sounds:
            if name == "shoot":
                self.sounds[name].play(maxtime=200)
            else:
                self.sounds[name].play()

    def _reset_session(self):
        self.player = Player(self.selected_avatar)
        self.enemies = EnemyGrid()
        self.barriers = [Barrier(120 + index * 170, SCREEN_H - 140) for index in range(4)]
        self.wave = 1
        self.state = "menu"
        self.stars = [(random.randint(0, SCREEN_W), random.randint(0, SCREEN_H), random.randint(80, 220)) for _ in range(100)]
        self.explosion_particles = []
        self.last_reported_lives = self.player.lives

    def _change_state(self, new_state):
        if self.state == new_state:
            return
        old_state = self.state
        self.state = new_state
        if self.server:
            self.server.send_state_signal(new_state.upper())
            if new_state == "dead":
                self.server.send_message("GAME_OVER")
            elif new_state == "win":
                self.server.send_message("WINNER")
           # elif new_state == "pause":
            #    self.server.send_message("PAUSE")
            #elif new_state == "playing" and old_state == "pause":
             #   self.server.send_message("RESUME")
            elif new_state == "menu":
                self.server.send_message("MENU")

    def _start_game(self):
        self.player = Player(self.selected_avatar)
        self.enemies = EnemyGrid()
        self.barriers = [Barrier(120 + index * 170, SCREEN_H - 140) for index in range(4)]
        self.wave = 1
        self.explosion_particles.clear()
        self.last_reported_lives = self.player.lives
        self.countdown_end_time = pygame.time.get_ticks() + 3000
        self._change_state("countdown")
        if self.server:
            self.server.send_start_signal()

    def _next_wave(self):
        self.wave += 1
        self.enemies = EnemyGrid()
        self.barriers = [Barrier(120 + index * 170, SCREEN_H - 140) for index in range(4)]
        self.player.bullets.clear()
        self._change_state("playing")
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

    def _notify_life_lost(self):
        if self.server and self.player.lives < self.last_reported_lives:
            self.server.send_life_lost_signal()
        self.last_reported_lives = self.player.lives

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
                self._notify_life_lost()
                if self.player.lives <= 0:
                    self._change_state("dead")
                    self.play("fail")

        for bullet in self.player.bullets[:]:
            bx, by = bullet
            for barrier in self.barriers:
                if barrier.health > 0 and barrier.rect.collidepoint(bx, by):
                    barrier.hit()
                    self.player.bullets.remove(bullet)
                    break

    def _draw_hud(self):
        draw_hud(self.screen, self.font_med, self.font_small, self.player, self.selected_avatar, self.high_score, self.wave)

    def _draw_menu(self):
        draw_menu(self.screen, self.font_big, self.font_med, self.font_small, self.menu_items, self.menu_index, self.selected_avatar)

    def _draw_avatar_menu(self):
        draw_avatar_menu(self.screen, self.font_big, self.font_small, self.selected_avatar)

    def _draw_overlay(self, title, color, sub=""):
        draw_overlay(self.screen, self.font_big, self.font_med, self.font_small, title, color, sub)

    def _draw_countdown_overlay(self):
        draw_countdown_overlay(self.screen, self.font_big, self.font_small, self.countdown_end_time)

    def _handle_virtual_key(self, key):
        if key == pygame.K_ESCAPE:
            if self.state == "playing":
                self._change_state("pause")
            elif self.state == "pause":
                self._change_state("playing")
            elif self.state == "avatar_menu":
                self._change_state(self.previous_state)
            elif self.state in ("dead", "win"):
                self._change_state("menu")
            return

        if self.state == "menu":
            if key == pygame.K_UP:
                self.menu_index = (self.menu_index - 1) % len(self.menu_items)
            elif key == pygame.K_DOWN:
                self.menu_index = (self.menu_index + 1) % len(self.menu_items)
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.menu_index == 0:
                    self._start_game()
                else:
                    self.previous_state = "menu"
                    self._change_state("avatar_menu")
        elif self.state == "avatar_menu":
            if key == pygame.K_LEFT:
                self.selected_avatar = (self.selected_avatar - 1) % len(PLAYER_AVATARS)
                self.player.avatar_index = self.selected_avatar
            elif key == pygame.K_RIGHT:
                self.selected_avatar = (self.selected_avatar + 1) % len(PLAYER_AVATARS)
                self.player.avatar_index = self.selected_avatar
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._change_state(self.previous_state)
        elif self.state == "dead":
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._start_game()
        elif self.state == "win":
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._next_wave()
        elif self.state == "pause":
            if key == pygame.K_UP:
                self.pause_index = (self.pause_index - 1) % len(self.pause_items)
            elif key == pygame.K_DOWN:
                self.pause_index = (self.pause_index + 1) % len(self.pause_items)
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.pause_index == 0:
                    self._change_state("playing")
                elif self.pause_index == 1:
                    self.previous_state = "pause"
                    self._change_state("avatar_menu")
                else:
                    self._reset_session()
                    self._change_state("menu")

    def _handle_remote_command(self, command):
        command = command.upper()

        if command in {"LEFT_DOWN", "MOVE_LEFT_START", "HOLD_LEFT"}:
            self.remote_left_held = True
            return
        if command in {"LEFT_UP", "STOP_LEFT", "RELEASE_LEFT"}:
            self.remote_left_held = False
            return
        if command in {"RIGHT_DOWN", "MOVE_RIGHT_START", "HOLD_RIGHT"}:
            self.remote_right_held = True
            return
        if command in {"RIGHT_UP", "STOP_RIGHT", "RELEASE_RIGHT"}:
            self.remote_right_held = False
            return
        if command in {"STOP", "STOP_MOVE"}:
            self.remote_left_held = False
            self.remote_right_held = False
            return
        if command in {"FIRE", "SHOOT", "SPACE", "TAP"}:
            self.remote_fire_requested = True
            return
        if command == "LEFT":
            if self.state == "playing":
                self.remote_left_once = True
            elif self.state == "avatar_menu":
                self.selected_avatar = (self.selected_avatar - 1) % len(PLAYER_AVATARS)
                self.player.avatar_index = self.selected_avatar
                if self.server:
                    self.server.send_message(f"AVATAR:{self.selected_avatar}")
            else:
                self._handle_virtual_key(pygame.K_LEFT)
            return

        if command == "RIGHT":
            if self.state == "playing":
                self.remote_right_once = True
            elif self.state == "avatar_menu":
                self.selected_avatar = (self.selected_avatar + 1) % len(PLAYER_AVATARS)
                self.player.avatar_index = self.selected_avatar
                if self.server:
                    self.server.send_message(f"AVATAR:{self.selected_avatar}")
            else:
                self._handle_virtual_key(pygame.K_RIGHT)
            return
        if command == "UP":
            self._handle_virtual_key(pygame.K_UP)
            return
        if command == "DOWN":
            self._handle_virtual_key(pygame.K_DOWN)
            return
        if command in {"ENTER", "SELECT", "START"}:
            self._handle_virtual_key(pygame.K_RETURN)
            return
        if command == "AVATAR_MENU":
            if self.state == "menu":
                self.previous_state = "menu"
                self._change_state("avatar_menu")
            elif self.state == "playing":
                self.previous_state = "playing"
                self._change_state("avatar_menu")
            return
        if command in {"BACK", "ESC", "ESCAPE"}:
            self._handle_virtual_key(pygame.K_ESCAPE)

    def _consume_server_commands(self):
        if not self.server:
            return

        for command in self.server.pop_commands():
            self._handle_remote_command(command)

    def _apply_playing_input(self):
        kb = pygame.key.get_pressed()
        left = kb[pygame.K_LEFT] or self.remote_left_held or self.remote_left_once
        right = kb[pygame.K_RIGHT] or self.remote_right_held or self.remote_right_once
        fire = kb[pygame.K_SPACE] or self.remote_fire_requested

        if self.state == "playing":
            self.player.move(left, right)
            if fire and self.player.shoot():
                self.play("shoot")

        self.remote_left_once = False
        self.remote_right_once = False
        self.remote_fire_requested = False

    def run(self):
        while True:
            self.clock.tick(FPS)
            self._handle_events()
            self._update()
            self._draw()
            pygame.display.flip()

    def _handle_events(self):
        self._consume_server_commands()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.server:
                    self.server.stop()
                pygame.quit()
                sys.exit()
            if event.type != pygame.KEYDOWN:
                continue

            self._handle_virtual_key(event.key)

        self._apply_playing_input()

    def _update(self):
        self._update_particles()
        if self.state == "countdown":
            if pygame.time.get_ticks() >= self.countdown_end_time:
                self._change_state("playing")
            return
        if self.state != "playing":
            return

        self.player.update()
        self.enemies.update(self.wave)
        self._check_collisions()

        if not self.enemies.alive_list():
            self._change_state("win")
            self.play("win")
        if self.enemies.check_invasion():
            self.player.lives = 0
            self._notify_life_lost()
            self._change_state("dead")
            self.play("fail")

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
        if self.state == "pause":
            self._draw_pause()
            return

        for barrier in self.barriers:
            barrier.draw(self.screen)
        self.enemies.draw(self.screen)
        self.player.draw(self.screen)
        self._draw_particles()
        self._draw_hud()

        if self.state == "countdown":
            self._draw_countdown_overlay()
        elif self.state == "dead":
            if self.player.score >= self.high_score and self.player.score > 0:
                sub = f"NEW HIGH SCORE: {self.player.score}!"
            else:
                sub = f"Final score: {self.player.score}"
            self._draw_overlay("GAME OVER", RED, sub)
        elif self.state == "win":
            self._draw_overlay(f"WAVE {self.wave} COMPLETED!", GREEN, f"Score: {self.player.score}  |  ENTER = Wave {self.wave + 1}")

    def _draw_pause(self):
        draw_pause(self.screen, self.font_big, self.font_med, self.pause_items, self.pause_index)
