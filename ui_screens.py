import math

import pygame

from constants import CYAN, GRAY, GREEN, LIGHT_GRAY, RED, SCREEN_H, SCREEN_W, WHITE
from sprites import PLAYER_AVATARS, draw_player


def draw_hud(screen, font_med, font_small, player, selected_avatar, high_score, wave):
    score_text = font_med.render(f"SCORE: {player.score}", True, WHITE)
    screen.blit(score_text, (10, 10))

    for index in range(player.lives):
        draw_player(screen, SCREEN_W - 60 - index * 55, 0, selected_avatar)

    wave_text = font_med.render(f"WAVE: {wave}", True, CYAN)
    screen.blit(wave_text, (SCREEN_W // 2 - wave_text.get_width() // 2, 10))

    pygame.draw.line(screen, GREEN, (0, SCREEN_H - 55), (SCREEN_W, SCREEN_H - 55), 2)

    high_score_text = font_small.render(f"Record: {high_score}", True, LIGHT_GRAY)
    screen.blit(high_score_text, (SCREEN_W - high_score_text.get_width() - 10, SCREEN_H - 22))


def draw_menu(screen, font_big, font_med, font_small, menu_items, menu_index, selected_avatar):
    title = font_big.render("SPACE INVADERS", True, GREEN)
    screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 70))

    subtitle = font_small.render("Main Menu", True, LIGHT_GRAY)
    screen.blit(subtitle, (SCREEN_W // 2 - subtitle.get_width() // 2, 130))

    for index, item in enumerate(menu_items):
        color = CYAN if index == menu_index else WHITE
        suffix = ""
        if item == "Choose Avatar":
            suffix = f": {PLAYER_AVATARS[selected_avatar]['name']}"
        text = font_med.render(f"{'>' if index == menu_index else ' '} {item}{suffix}", True, color)
        screen.blit(text, (SCREEN_W // 2 - text.get_width() // 2, 220 + index * 50))

    draw_player(screen, SCREEN_W // 2 - 25, 350, selected_avatar)
    avatar_text = font_small.render(f"Selected avatar: {PLAYER_AVATARS[selected_avatar]['name']}", True, LIGHT_GRAY)
    screen.blit(avatar_text, (SCREEN_W // 2 - avatar_text.get_width() // 2, 420))

    instructions = [
        "MENU: UP / DOWN, ENTER",
        "GAME: LEFT / RIGHT, SPACE",
        "MOBILE: UP / DOWN / LEFT / RIGHT / FIRE / SELECT / BACK",
    ]
    for index, line in enumerate(instructions):
        text = font_small.render(line, True, GRAY)
        screen.blit(text, (SCREEN_W // 2 - text.get_width() // 2, 490 + index * 22))


def draw_avatar_menu(screen, font_big, font_small, selected_avatar):
    title = font_big.render("CHOOSE AVATAR", True, CYAN)
    screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 70))

    hint = font_small.render("LEFT / RIGHT for selection, ENTER / ESC for back", True, LIGHT_GRAY)
    screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, 130))

    spacing = 210
    start_x = SCREEN_W // 2 - spacing
    for index, avatar in enumerate(PLAYER_AVATARS):
        x = start_x + index * spacing
        y = 260
        if index == selected_avatar:
            pygame.draw.rect(screen, CYAN, (x - 30, y - 40, 110, 140), 3, border_radius=10)
        draw_player(screen, x, y, index)
        label = font_small.render(avatar["name"], True, WHITE if index == selected_avatar else GRAY)
        screen.blit(label, (x + 25 - label.get_width() // 2, y + 70))


def draw_overlay(screen, font_big, font_med, font_small, title, color, sub=""):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    title_text = font_big.render(title, True, color)
    screen.blit(title_text, (SCREEN_W // 2 - title_text.get_width() // 2, SCREEN_H // 2 - 60))

    if sub:
        sub_text = font_med.render(sub, True, WHITE)
        screen.blit(sub_text, (SCREEN_W // 2 - sub_text.get_width() // 2, SCREEN_H // 2 + 10))

    hint = font_small.render("ENTER = Continue   |   ESC = Menu", True, WHITE)
    screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H // 2 + 70))


def draw_countdown_overlay(screen, font_big, font_small, countdown_end_time):
    remaining_ms = max(0, countdown_end_time - pygame.time.get_ticks())
    remaining_seconds = max(1, math.ceil(remaining_ms / 1000))

    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))

    title = font_big.render("GET READY", True, CYAN)
    screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, SCREEN_H // 2 - 80))

    countdown = font_big.render(str(remaining_seconds), True, WHITE)
    screen.blit(countdown, (SCREEN_W // 2 - countdown.get_width() // 2, SCREEN_H // 2 - 10))

    hint = font_small.render("The phone finishes counting, then the game begins", True, LIGHT_GRAY)
    screen.blit(hint, (SCREEN_W // 2 - hint.get_width() // 2, SCREEN_H // 2 + 60))


def draw_pause(screen, font_big, font_med, pause_items, pause_index):
    overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    title = font_big.render("PAUSED", True, CYAN)
    screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 150))

    for index, item in enumerate(pause_items):
        color = GREEN if index == pause_index else WHITE
        text = font_med.render(item, True, color)
        screen.blit(text, (SCREEN_W // 2 - text.get_width() // 2, 250 + index * 50))
