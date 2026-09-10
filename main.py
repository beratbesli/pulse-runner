"""Pulse Runner, an original single-file rhythm-platformer prototype.

Özellikler:
  - Küp & Gemi modları + Yerçekimi değiştirme
  - Jump Orb, Jump Pad, Testere, Tavan Spike
  - Programatik ses efektleri (harici dosya yok)
  - Beat-senkronize nabız efektleri & ışık sütunları
  - Parallax arka plan, afterimage, shockwave ölüm
  - Pratik Modu (checkpoint), renk seçimi
  - 8 bölümlük el yapımı seviye
"""

import math
import random
import struct
import sys
from pathlib import Path

import pygame

# ═══════════════════════════════════════════════════════════════════════════════
#  SABİTLER
# ═══════════════════════════════════════════════════════════════════════════════

WIDTH, HEIGHT = 900, 500
FPS = 60
GROUND_Y = HEIGHT - 70
CEILING_Y = 50
ASSET_DIR = Path(__file__).resolve().parent


def asset_path(filename):
    """Resolve an optional user asset independently of the launch directory."""
    return ASSET_DIR / filename

# Renkler
BG_TOP = (10, 5, 40)
BG_BOTTOM = (30, 10, 60)
GROUND_COLOR = (20, 20, 80)
GROUND_LINE_COLOR = (0, 200, 255)
SPIKE_COLOR = (255, 60, 60)
BLOCK_COLOR = (60, 60, 200)
BLOCK_OUTLINE = (100, 100, 255)
PAD_COLOR = (255, 220, 0)
PAD_OUTLINE = (255, 180, 0)
ORB_COLOR = (0, 255, 120)
SAW_COLOR = (220, 80, 30)
SAW_OUTLINE = (255, 140, 60)
COIN_COLOR = (255, 215, 0)
COIN_OUTLINE = (255, 180, 50)
PORTAL_SHIP_COLOR = (0, 150, 255)
PORTAL_CUBE_COLOR = (0, 255, 100)
GRAVITY_UP_COLOR = (220, 0, 255)
GRAVITY_DOWN_COLOR = (255, 220, 0)
PROGRESS_BG = (40, 40, 80)
PROGRESS_FILL = (0, 255, 130)
TEXT_COLOR = (255, 255, 255)
STAR_COLOR = (200, 200, 255)
DEATH_COLORS = [
    (255, 220, 0), (255, 180, 0), (255, 140, 0),
    (255, 100, 0), (255, 60, 0), (255, 255, 100),
]

# Oyuncu Renk Paletleri
PLAYER_PALETTES = [
    {'name': 'Sarı',    'main': (255, 220, 0),   'outline': (255, 160, 0),
     'trail': (255, 200, 50),  'glow': (255, 220, 0)},
    {'name': 'Cyan',    'main': (0, 220, 255),   'outline': (0, 160, 200),
     'trail': (0, 200, 255),   'glow': (0, 220, 255)},
    {'name': 'Yeşil',   'main': (0, 255, 100),   'outline': (0, 200, 80),
     'trail': (0, 255, 130),   'glow': (0, 255, 100)},
    {'name': 'Pembe',   'main': (255, 100, 200),  'outline': (200, 60, 150),
     'trail': (255, 120, 220), 'glow': (255, 100, 200)},
    {'name': 'Turuncu', 'main': (255, 140, 0),    'outline': (200, 100, 0),
     'trail': (255, 160, 40),  'glow': (255, 140, 0)},
    {'name': 'Mor',     'main': (180, 80, 255),   'outline': (140, 40, 200),
     'trail': (160, 100, 255), 'glow': (180, 80, 255)},
]

# Fizik
GRAVITY = 1.2
JUMP_FORCE = -16
PAD_FORCE = -19
GAME_SPEED = 7
SHIP_GRAVITY = 0.55
SHIP_FLY_ACCEL = -0.95
SHIP_MAX_VEL = 8.5
PLAYER_SIZE = 40
PLAYER_X = 150

# Beat
BPM = 128
BEAT_FRAMES = int(60 / (BPM / 60))

# Parallax arka plan renkleri
BG_SHAPE_COLORS = [
    (100, 50, 200), (50, 100, 200), (200, 50, 150),
    (50, 200, 150), (150, 80, 220), (80, 180, 220),
]


# ═══════════════════════════════════════════════════════════════════════════════
#  SES YÖNETİCİSİ
# ═══════════════════════════════════════════════════════════════════════════════

class SoundManager:
    """Programatik ses efektleri."""

    def __init__(self):
        self.enabled = True
        try:
            self.jump_snd = self._sweep(500, 850, 0.08, 0.18)
            self.death_snd = self._sweep(450, 120, 0.22, 0.22)
            self.coin_snd = self._two_tone(880, 1320, 0.07, 0.07, 0.20)
            self.pad_snd = self._sweep(400, 1100, 0.06, 0.18)
            self.portal_snd = self._sweep(300, 800, 0.15, 0.15)
            self.orb_snd = self._sweep(700, 1200, 0.05, 0.15)
            self.gravity_snd = self._sweep(250, 650, 0.13, 0.16)
            self.milestone_snd = self._two_tone(660, 990, 0.06, 0.08, 0.18)
            self.complete_snd = self._chord([523, 659, 784, 1047], 0.6, 0.2)
            self.practice_snd = self._sweep(400, 600, 0.05, 0.12)
        except Exception:
            self.enabled = False

    def play(self, name):
        if not self.enabled:
            return
        snd = getattr(self, f'{name}_snd', None)
        if snd:
            snd.play()

    @staticmethod
    def _sweep(f1, f2, dur, vol=0.2):
        sr, n = 44100, int(44100 * dur)
        phase, samples = 0.0, []
        for i in range(n):
            t = i / sr
            r = t / dur
            freq = f1 + (f2 - f1) * r
            phase += 2 * math.pi * freq / sr
            samples.append(max(-32768, min(32767,
                int(math.sin(phase) * vol * 32767 * max(0, 1 - r)))))
        return pygame.mixer.Sound(buffer=struct.pack(f'<{n}h', *samples))

    @staticmethod
    def _two_tone(f1, f2, d1, d2, vol=0.2):
        sr, total = 44100, d1 + d2
        n = int(sr * total)
        samples = []
        for i in range(n):
            t = i / sr
            freq = f1 if t < d1 else f2
            env = max(0, 1 - (t / total) * 0.6)
            samples.append(max(-32768, min(32767,
                int(math.sin(2 * math.pi * freq * t) * vol * 32767 * env))))
        return pygame.mixer.Sound(buffer=struct.pack(f'<{n}h', *samples))

    @staticmethod
    def _chord(freqs, dur, vol=0.15):
        sr, n, nf = 44100, int(44100 * dur), len(freqs)
        samples = []
        for i in range(n):
            t = i / sr
            env = max(0, 1 - t / dur)
            v = sum(math.sin(2 * math.pi * f * t) for f in freqs) / nf
            samples.append(max(-32768, min(32767, int(v * vol * 32767 * env))))
        return pygame.mixer.Sound(buffer=struct.pack(f'<{n}h', *samples))


# ═══════════════════════════════════════════════════════════════════════════════
#  PARÇACIK
# ═══════════════════════════════════════════════════════════════════════════════

class Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'size', 'color', 'lifetime',
                 'max_lifetime', 'shrink', 'alive', 'shape', 'gravity')

    def __init__(self, x, y, vx, vy, size, color, lifetime,
                 shrink=True, shape='rect', gravity=0.0):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.size = size
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.shrink = shrink
        self.alive = True
        self.shape = shape
        self.gravity = gravity

    def update(self):
        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        ratio = self.lifetime / self.max_lifetime
        alpha = int(255 * ratio)
        cs = self.size * ratio if self.shrink else self.size
        if cs < 0.5:
            return
        s = max(1, int(cs))
        c = (*self.color[:3], alpha)
        if self.shape == 'line':
            end_x = self.x + self.vx * 4
            w = max(4, abs(int(self.vx * 4)) + 4)
            ls = pygame.Surface((w, 3), pygame.SRCALPHA)
            pygame.draw.line(ls, c, (0, 1), (w, 1), 1)
            surface.blit(ls, (min(int(self.x), int(end_x)), int(self.y)))
        elif self.shape == 'circle':
            ps = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
            pygame.draw.circle(ps, c, (s, s), s)
            surface.blit(ps, (int(self.x) - s, int(self.y) - s))
        else:
            ps = pygame.Surface((s, s), pygame.SRCALPHA)
            pygame.draw.rect(ps, c, (0, 0, s, s))
            surface.blit(ps, (int(self.x), int(self.y)))


# ═══════════════════════════════════════════════════════════════════════════════
#  OYUNCU
# ═══════════════════════════════════════════════════════════════════════════════

class Player:
    """Küp & Gemi modları, yerçekimi değiştirme, afterimage."""

    def __init__(self, color_index=0):
        self.size = PLAYER_SIZE
        self.x = PLAYER_X
        self.y = GROUND_Y - self.size
        self.vel_y = 0.0
        self.on_ground = True
        self.alive = True
        self.mode = 'cube'
        self.gravity_dir = 1        # 1 = normal, -1 = ters
        self.angle = 0.0
        self.squash_timer = 0
        self.was_on_ground = True
        self.color_index = color_index

        # Renk
        pal = PLAYER_PALETTES[color_index]
        self.main_color = pal['main']
        self.outline_color = pal['outline']
        self.trail_color = pal['trail']
        self.glow_color = pal['glow']

        # Afterimage
        self.afterimages = []
        self.frame_count = 0

        self._build_surfaces()

    def _build_surfaces(self):
        s = self.size

        # Küp
        player_image = asset_path('player.png')
        if player_image.is_file():
            try:
                img = pygame.image.load(player_image).convert_alpha()
                self.cube_surf = pygame.transform.scale(img, (s, s))
            except Exception:
                self._draw_default_cube(s)
        else:
            self._draw_default_cube(s)

        # Gemi
        ship_image = asset_path('ship.png')
        if ship_image.is_file():
            try:
                img = pygame.image.load(ship_image).convert_alpha()
                self.ship_surf = pygame.transform.scale(img, (s + 10, s))
            except Exception:
                self._draw_default_ship(s)
        else:
            self._draw_default_ship(s)

    def _draw_default_cube(self, s):
        self.cube_surf = pygame.Surface((s, s), pygame.SRCALPHA)
        pygame.draw.rect(self.cube_surf, self.main_color, (0, 0, s, s))
        pygame.draw.rect(self.cube_surf, self.outline_color, (0, 0, s, s), 3)
        eye = s // 5
        ex, ey = s // 2 - eye // 2 + 4, s // 2 - eye // 2
        pygame.draw.rect(self.cube_surf, (255, 255, 220, 200),
                         (ex, ey, eye, eye))
        pygame.draw.rect(self.cube_surf, self.outline_color,
                         (ex, ey, eye, eye), 1)

    def _draw_default_ship(self, s):
        self.ship_surf = pygame.Surface((s + 10, s), pygame.SRCALPHA)
        pts = [(s + 5, s // 2), (3, 3), (8, s // 2), (3, s - 3)]
        ship_c = (0, 220, 255)
        pygame.draw.polygon(self.ship_surf, ship_c, pts)
        pygame.draw.polygon(self.ship_surf, (180, 240, 255), pts, 2)
        pygame.draw.circle(self.ship_surf, (200, 240, 255, 180),
                           (s // 2 + 2, s // 2), 5)

    def jump(self):
        if not self.alive:
            return False
        if self.mode == 'cube' and self.on_ground:
            self.vel_y = JUMP_FORCE * self.gravity_dir
            self.on_ground = False
            return True
        return False

    def orb_jump(self):
        """Orb ile havada zıplama."""
        self.vel_y = JUMP_FORCE * self.gravity_dir
        self.on_ground = False

    def pad_launch(self):
        self.vel_y = PAD_FORCE * self.gravity_dir
        self.on_ground = False

    def set_mode(self, m):
        if self.mode != m:
            self.mode = m
            if m == 'cube':
                self.angle = 0

    def set_gravity(self, d):
        """Yerçekimi yönü: 1=normal, -1=ters."""
        self.gravity_dir = d

    def update(self, holding):
        if not self.alive:
            return
        self.was_on_ground = self.on_ground
        self.frame_count += 1

        if self.mode == 'cube':
            self._update_cube()
        else:
            self._update_ship(holding)

        if self.squash_timer > 0:
            self.squash_timer -= 1

        # Afterimage
        if self.frame_count % 3 == 0:
            self.afterimages.append({
                'x': self.x, 'y': self.y,
                'angle': self.angle, 'alpha': 90,
                'grav': self.gravity_dir, 'mode': self.mode
            })
        self.afterimages = [a for a in self.afterimages if a['alpha'] > 0]
        for a in self.afterimages:
            a['alpha'] -= 6

    def _update_cube(self):
        self.vel_y += GRAVITY * self.gravity_dir
        self.y += self.vel_y

        if self.gravity_dir == 1:
            if self.y >= GROUND_Y - self.size:
                self.y = GROUND_Y - self.size
                if not self.was_on_ground and abs(self.vel_y) > 2:
                    self.squash_timer = 6
                self.vel_y = 0
                self.on_ground = True
            else:
                self.on_ground = False
        else:
            if self.y <= CEILING_Y:
                self.y = CEILING_Y
                if not self.was_on_ground and abs(self.vel_y) > 2:
                    self.squash_timer = 6
                self.vel_y = 0
                self.on_ground = True
            else:
                self.on_ground = False

        if not self.on_ground:
            self.angle -= 7.5 * self.gravity_dir
        else:
            self._snap_angle()

    def _update_ship(self, holding):
        if holding:
            self.vel_y += SHIP_FLY_ACCEL * self.gravity_dir
        self.vel_y += SHIP_GRAVITY * self.gravity_dir
        self.vel_y = max(-SHIP_MAX_VEL, min(SHIP_MAX_VEL, self.vel_y))
        self.y += self.vel_y

        if self.y < CEILING_Y:
            self.y = CEILING_Y
            self.vel_y = 0
        if self.y > GROUND_Y - self.size:
            self.y = GROUND_Y - self.size
            self.vel_y = 0

        if self.gravity_dir == 1:
            self.on_ground = self.y >= GROUND_Y - self.size - 1
        else:
            self.on_ground = self.y <= CEILING_Y + 1

        self.angle = -self.vel_y * 3
        self.angle = max(-35, min(35, self.angle))

    def _snap_angle(self):
        norm = self.angle % 360
        snapped = round(norm / 90) * 90
        diff = snapped - norm
        if abs(diff) > 180:
            diff -= 360 * (1 if diff > 0 else -1)
        if abs(diff) < 2:
            self.angle = snapped
        else:
            self.angle += diff * 0.4

    def get_rect(self):
        shrink = 6
        return pygame.Rect(self.x + shrink, self.y + shrink,
                           self.size - 2 * shrink, self.size - 2 * shrink)

    def draw(self, surface):
        if not self.alive:
            return
        # Afterimage
        self._draw_afterimages(surface)
        # Ana çizim
        if self.mode == 'cube':
            self._draw_cube(surface)
        else:
            self._draw_ship(surface)

    def _draw_afterimages(self, surface):
        for img in self.afterimages:
            if img['alpha'] <= 5:
                continue
            src = self.cube_surf if img['mode'] == 'cube' else self.ship_surf
            src = src.copy()
            src.set_alpha(img['alpha'])
            rot = pygame.transform.rotate(src, img['angle'])
            if img['grav'] == -1:
                rot = pygame.transform.flip(rot, False, True)
            r = rot.get_rect(center=(img['x'] + self.size // 2,
                                     img['y'] + self.size // 2))
            surface.blit(rot, r.topleft)

    def _draw_cube(self, surface):
        src = self.cube_surf
        if self.squash_timer > 0:
            ratio = self.squash_timer / 6
            sw = int(self.size * (1 + ratio * 0.25))
            sh = int(self.size * (1 - ratio * 0.2))
            src = pygame.transform.scale(src, (sw, sh))
        else:
            sh = self.size

        rot = pygame.transform.rotate(src, self.angle)
        if self.gravity_dir == -1:
            rot = pygame.transform.flip(rot, False, True)
        r = rot.get_rect(center=(
            self.x + self.size // 2,
            self.y + self.size - sh // 2 if self.squash_timer > 0
            else self.y + self.size // 2))
        surface.blit(rot, r.topleft)

        # Glow
        gs = pygame.Surface((self.size + 24, self.size + 24), pygame.SRCALPHA)
        pygame.draw.rect(gs, (*self.glow_color, 22),
                         (0, 0, self.size + 24, self.size + 24), border_radius=10)
        surface.blit(gs, (self.x - 12, self.y - 12))

    def _draw_ship(self, surface):
        rot = pygame.transform.rotate(self.ship_surf, self.angle)
        if self.gravity_dir == -1:
            rot = pygame.transform.flip(rot, False, True)
        r = rot.get_rect(center=(self.x + self.size // 2,
                                 self.y + self.size // 2))
        surface.blit(rot, r.topleft)
        gs = pygame.Surface((self.size + 24, self.size + 24), pygame.SRCALPHA)
        pygame.draw.rect(gs, (0, 220, 255, 18),
                         (0, 0, self.size + 24, self.size + 24), border_radius=12)
        surface.blit(gs, (self.x - 12, self.y - 12))


# ═══════════════════════════════════════════════════════════════════════════════
#  ENGEL
# ═══════════════════════════════════════════════════════════════════════════════

class Obstacle:
    """spike, block, pad, orb, saw, ceiling_spike,
       portal_ship, portal_cube, gravity_up, gravity_down, coin."""

    def __init__(self, x, y, obs_type, size=40):
        self.x, self.y = x, y
        self.type = obs_type
        self.size = size
        self.active = True
        self.triggered = False
        self.anim_timer = random.uniform(0, math.pi * 2)

    def update(self, speed):
        self.x -= speed
        self.anim_timer += 0.08
        if self.x < -self.size * 3:
            self.active = False

    def get_rect(self):
        s = self.size
        if self.type == 'spike':
            return pygame.Rect(self.x + 10, self.y + 10, s - 20, s - 10)
        elif self.type == 'ceiling_spike':
            return pygame.Rect(self.x + 10, self.y, s - 20, s - 10)
        elif self.type == 'block':
            return pygame.Rect(self.x + 3, self.y + 3, s - 6, s - 6)
        elif self.type == 'pad':
            return pygame.Rect(self.x + 4, self.y + s // 2, s - 8, s // 2)
        elif self.type == 'orb':
            r = s // 3
            return pygame.Rect(self.x + s // 2 - r, self.y + s // 2 - r,
                               r * 2, r * 2)
        elif self.type == 'saw':
            shrink = 5
            return pygame.Rect(self.x + shrink, self.y + shrink,
                               s - 2 * shrink, s - 2 * shrink)
        elif self.type in ('portal_ship', 'portal_cube',
                           'gravity_up', 'gravity_down'):
            return pygame.Rect(self.x + 5, self.y, s - 10, s * 2)
        elif self.type == 'coin':
            r = s // 3
            return pygame.Rect(self.x + s // 2 - r, self.y + s // 2 - r,
                               r * 2, r * 2)
        return pygame.Rect(self.x, self.y, s, s)

    def is_deadly(self):
        return self.type in ('spike', 'ceiling_spike', 'block', 'saw')

    def draw(self, surface):
        if not self.active or self.triggered:
            return
        fn = {'spike': self._draw_spike, 'ceiling_spike': self._draw_ceiling_spike,
              'block': self._draw_block, 'pad': self._draw_pad,
              'orb': self._draw_orb, 'saw': self._draw_saw,
              'coin': self._draw_coin,
              'portal_ship': self._draw_portal, 'portal_cube': self._draw_portal,
              'gravity_up': self._draw_gravity_portal,
              'gravity_down': self._draw_gravity_portal}.get(self.type)
        if fn:
            fn(surface)

    def _draw_spike(self, surface):
        s = self.size
        pts = [(self.x + s // 2, self.y), (self.x, self.y + s),
               (self.x + s, self.y + s)]
        gs = pygame.Surface((s + 16, s + 16), pygame.SRCALPHA)
        gp = [(p[0] - self.x + 8, p[1] - self.y + 8) for p in pts]
        pygame.draw.polygon(gs, (*SPIKE_COLOR, 35), gp)
        surface.blit(gs, (self.x - 8, self.y - 8))
        pygame.draw.polygon(surface, SPIKE_COLOR, pts)
        pygame.draw.polygon(surface, (255, 120, 120), pts, 2)
        inner = [(self.x + s // 2, self.y + 10),
                 (self.x + 10, self.y + s * 0.65),
                 (self.x + s - 10, self.y + s * 0.65)]
        pygame.draw.polygon(surface, (255, 100, 100), inner, 1)

    def _draw_ceiling_spike(self, surface):
        """Tavandan sarkan ters spike."""
        s = self.size
        pts = [(self.x + s // 2, self.y + s), (self.x, self.y),
               (self.x + s, self.y)]
        gs = pygame.Surface((s + 16, s + 16), pygame.SRCALPHA)
        gp = [(p[0] - self.x + 8, p[1] - self.y + 8) for p in pts]
        pygame.draw.polygon(gs, (*SPIKE_COLOR, 35), gp)
        surface.blit(gs, (self.x - 8, self.y - 8))
        pygame.draw.polygon(surface, SPIKE_COLOR, pts)
        pygame.draw.polygon(surface, (255, 120, 120), pts, 2)

    def _draw_block(self, surface):
        s = self.size
        rect = pygame.Rect(self.x, self.y, s, s)
        gs = pygame.Surface((s + 12, s + 12), pygame.SRCALPHA)
        pygame.draw.rect(gs, (*BLOCK_COLOR, 30), (0, 0, s + 12, s + 12),
                         border_radius=3)
        surface.blit(gs, (self.x - 6, self.y - 6))
        pygame.draw.rect(surface, BLOCK_COLOR, rect)
        pygame.draw.rect(surface, BLOCK_OUTLINE, rect, 2)
        pygame.draw.line(surface, (80, 80, 220),
                         (self.x + 4, self.y + 4),
                         (self.x + s - 4, self.y + s - 4), 1)
        pygame.draw.line(surface, (80, 80, 220),
                         (self.x + s - 4, self.y + 4),
                         (self.x + 4, self.y + s - 4), 1)

    def _draw_pad(self, surface):
        s = self.size
        pts = [(self.x + 4, self.y + s), (self.x + s - 4, self.y + s),
               (self.x + s - 8, self.y + s // 2 + 2),
               (self.x + s // 2, self.y + s // 3),
               (self.x + 8, self.y + s // 2 + 2)]
        pulse = 0.8 + 0.2 * math.sin(self.anim_timer * 3)
        pc = tuple(int(c * pulse) for c in PAD_COLOR)
        gs = pygame.Surface((s + 12, s + 12), pygame.SRCALPHA)
        gp = [(p[0] - self.x + 6, p[1] - self.y + 6) for p in pts]
        pygame.draw.polygon(gs, (*PAD_COLOR, 40), gp)
        surface.blit(gs, (self.x - 6, self.y - 6))
        pygame.draw.polygon(surface, pc, pts)
        pygame.draw.polygon(surface, PAD_OUTLINE, pts, 2)
        # Ok işareti
        pygame.draw.polygon(surface, (255, 255, 200), [
            (self.x + s // 2, self.y + s // 3 + 2),
            (self.x + s // 2 - 6, self.y + s // 3 + 11),
            (self.x + s // 2 + 6, self.y + s // 3 + 11)])

    def _draw_orb(self, surface):
        """Yeşil jump orb – havada tıkla."""
        s = self.size
        cx, cy = int(self.x + s // 2), int(self.y + s // 2)
        r = s // 3 + 2
        # Dış glow
        gs = pygame.Surface((r * 5, r * 5), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*ORB_COLOR, 20), (r * 5 // 2, r * 5 // 2),
                           r * 5 // 2)
        surface.blit(gs, (cx - r * 5 // 2, cy - r * 5 // 2))
        # Halka
        pygame.draw.circle(surface, ORB_COLOR, (cx, cy), r, 3)
        # İç nabız
        pulse = 0.5 + 0.5 * math.sin(self.anim_timer * 3)
        ir = max(2, int(r * 0.5 * pulse))
        inner_s = pygame.Surface((ir * 2, ir * 2), pygame.SRCALPHA)
        pygame.draw.circle(inner_s, (*ORB_COLOR, int(120 * pulse)),
                           (ir, ir), ir)
        surface.blit(inner_s, (cx - ir, cy - ir))
        # Parlama
        pygame.draw.circle(surface, (200, 255, 220), (cx - 3, cy - 3), 2)

    def _draw_saw(self, surface):
        """Dönen testere bıçağı."""
        s = self.size
        cx, cy = int(self.x + s // 2), int(self.y + s // 2)
        r = s // 2 - 2
        # Glow
        gs = pygame.Surface((s + 16, s + 16), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*SAW_COLOR, 25), (s // 2 + 8, s // 2 + 8),
                           r + 8)
        surface.blit(gs, (self.x - 8, self.y - 8))
        # Ana daire
        pygame.draw.circle(surface, SAW_COLOR, (cx, cy), r)
        # Dönen dişler
        for i in range(8):
            a = self.anim_timer * 4 + i * math.pi / 4
            x1 = cx + int(math.cos(a) * (r - 3))
            y1 = cy + int(math.sin(a) * (r - 3))
            x2 = cx + int(math.cos(a) * (r + 4))
            y2 = cy + int(math.sin(a) * (r + 4))
            pygame.draw.line(surface, SAW_OUTLINE, (x1, y1), (x2, y2), 3)
        # İç merkez
        pygame.draw.circle(surface, (100, 30, 15), (cx, cy), r // 3)
        pygame.draw.circle(surface, SAW_OUTLINE, (cx, cy), 3)
        pygame.draw.circle(surface, SAW_OUTLINE, (cx, cy), r, 2)

    def _draw_coin(self, surface):
        s = self.size
        cx, cy = int(self.x + s // 2), int(self.y + s // 2)
        r = s // 3
        bob = math.sin(self.anim_timer * 2) * 4
        cy += int(bob)
        gs = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*COIN_COLOR, 30), (r * 2, r * 2), r * 2)
        surface.blit(gs, (cx - r * 2, cy - r * 2))
        pygame.draw.circle(surface, COIN_COLOR, (cx, cy), r)
        pygame.draw.circle(surface, COIN_OUTLINE, (cx, cy), r, 2)
        for i in range(4):
            a = self.anim_timer + i * math.pi / 2
            pygame.draw.circle(surface, (255, 255, 220),
                (cx + int(math.cos(a) * r * 0.4),
                 cy + int(math.sin(a) * r * 0.4)), 2)
        pygame.draw.circle(surface, (255, 255, 255, 180),
                           (cx - r // 3, cy - r // 3), 2)

    def _draw_portal(self, surface):
        s, h = self.size, self.size * 2
        color = PORTAL_SHIP_COLOR if self.type == 'portal_ship' else PORTAL_CUBE_COLOR
        outer = pygame.Rect(self.x, self.y, s, h)
        gs = pygame.Surface((s + 20, h + 20), pygame.SRCALPHA)
        pygame.draw.ellipse(gs, (*color, 25), (0, 0, s + 20, h + 20))
        surface.blit(gs, (self.x - 10, self.y - 10))
        pygame.draw.ellipse(surface, (*color, 60),
                            (self.x + 2, self.y + 2, s - 4, h - 4))
        pygame.draw.ellipse(surface, color, outer, 3)
        cx, cy = self.x + s // 2, self.y + h // 2
        for i in range(4):
            a = self.anim_timer * 2 + i * math.pi / 2
            dx = int(math.cos(a) * s // 4)
            dy = int(math.sin(a) * h // 4)
            pygame.draw.circle(surface, (255, 255, 255, 180),
                               (cx + dx, cy + dy), 3)

    def _draw_gravity_portal(self, surface):
        """Yerçekimi portali (mor veya sarı)."""
        s, h = self.size, self.size * 2
        color = GRAVITY_UP_COLOR if self.type == 'gravity_up' else GRAVITY_DOWN_COLOR
        outer = pygame.Rect(self.x, self.y, s, h)
        # Glow
        gs = pygame.Surface((s + 24, h + 24), pygame.SRCALPHA)
        pygame.draw.ellipse(gs, (*color, 30), (0, 0, s + 24, h + 24))
        surface.blit(gs, (self.x - 12, self.y - 12))
        # Gövde
        pygame.draw.ellipse(surface, (*color, 50),
                            (self.x + 2, self.y + 2, s - 4, h - 4))
        pygame.draw.ellipse(surface, color, outer, 3)
        # Ok işareti
        cx, cy = self.x + s // 2, self.y + h // 2
        arrow_dir = -1 if self.type == 'gravity_up' else 1
        ay = cy + arrow_dir * 10
        pygame.draw.polygon(surface, (255, 255, 255), [
            (cx, ay - arrow_dir * 14),
            (cx - 8, ay), (cx + 8, ay)])
        # Dönen noktalar
        for i in range(4):
            a = self.anim_timer * 2.5 + i * math.pi / 2
            dx = int(math.cos(a) * s // 4)
            dy = int(math.sin(a) * h // 4)
            pygame.draw.circle(surface, (255, 255, 255, 150),
                               (cx + dx, cy + dy), 2)


# ═══════════════════════════════════════════════════════════════════════════════
#  ARKA PLAN ŞEKLİ & NABIZ SÜTUNU
# ═══════════════════════════════════════════════════════════════════════════════

class BgShape:
    __slots__ = ('x', 'y', 'size', 'speed', 'rot', 'rot_speed',
                 'color', 'alpha', 'vertices')

    def __init__(self):
        self.reset(random.randint(0, WIDTH))

    def reset(self, sx=None):
        self.x = sx if sx is not None else WIDTH + random.randint(20, 200)
        self.y = random.randint(20, GROUND_Y - 30)
        self.size = random.randint(15, 50)
        self.speed = random.uniform(0.4, 1.8)
        self.rot = random.uniform(0, 360)
        self.rot_speed = random.uniform(-0.8, 0.8)
        self.alpha = random.randint(12, 35)
        self.color = random.choice(BG_SHAPE_COLORS)
        self.vertices = random.choice([3, 4, 5, 6])

    def update(self):
        self.x -= self.speed
        self.rot += self.rot_speed
        if self.x < -self.size * 2:
            self.reset()

    def draw(self, surface):
        cx, cy = int(self.x), int(self.y)
        pts = []
        for i in range(self.vertices):
            a = math.radians(self.rot + i * (360 / self.vertices))
            pts.append((cx + int(math.cos(a) * self.size),
                        cy + int(math.sin(a) * self.size)))
        s = self.size * 3
        ss = pygame.Surface((s, s), pygame.SRCALPHA)
        sp = [(p[0] - cx + s // 2, p[1] - cy + s // 2) for p in pts]
        if len(sp) >= 3:
            pygame.draw.polygon(ss, (*self.color, self.alpha), sp)
            pygame.draw.polygon(ss, (*self.color, self.alpha + 10), sp, 1)
        surface.blit(ss, (cx - s // 2, cy - s // 2))


class PulseColumn:
    """Beat-senkronize dikey ışık sütunu."""

    __slots__ = ('x', 'width', 'alpha', 'max_alpha', 'color')

    def __init__(self, x):
        self.x = x
        self.width = random.randint(25, 55)
        self.alpha = 0.0
        self.max_alpha = random.randint(18, 38)
        self.color = random.choice([
            (50, 0, 200), (0, 80, 200), (150, 0, 180),
            (0, 150, 200), (100, 0, 220),
        ])

    def pulse(self):
        self.alpha = self.max_alpha

    def update(self):
        self.alpha = max(0, self.alpha - 0.7)

    def draw(self, surface):
        if self.alpha < 1:
            return
        cs = pygame.Surface((self.width, GROUND_Y), pygame.SRCALPHA)
        hw = self.width // 2
        for dx in range(self.width):
            dist = abs(dx - hw) / max(1, hw)
            a = int(self.alpha * (1 - dist * 0.7))
            pygame.draw.line(cs, (*self.color, a), (dx, 0), (dx, GROUND_Y))
        surface.blit(cs, (self.x - hw, 0))


# ═══════════════════════════════════════════════════════════════════════════════
#  SEVİYE YÖNETİCİSİ
# ═══════════════════════════════════════════════════════════════════════════════

class LevelManager:
    """8 bölümlük genişletilmiş seviye. Tüm engel tiplerini barındırır."""

    def __init__(self):
        self.obstacle_size = 40
        self.level_data = [
            # ═══ BÖLÜM 1: GİRİŞ ═══
            ('spike', 0, 350),
            ('spike', 0, 300),
            ('spike', 0, 300),
            ('coin', 2, 300),
            ('spike', 0, 280),
            ('spike', 0, 50),       # İkili (tek zıplama)

            # ═══ BÖLÜM 2: PAD & BLOK ═══
            ('pad', 0, 400),
            ('spike', 0, 280),
            ('block', 0, 320),
            ('spike', 1, 0),
            ('spike', 0, 280),
            ('spike', 0, 50),

            # ═══ BÖLÜM 3: ORB TANITIMI ═══
            ('spike', 0, 380),
            ('spike', 0, 50),
            ('spike', 0, 50),       # Üçlü (tek zıplama)
            ('orb', 1, 280),        # İlk orb!
            ('spike', 0, 140),      # Orb ile geçilecek
            ('saw', 1, 350),        # İlk testere!
            ('spike', 0, 300),

            # ═══ BÖLÜM 4: GEMİ BÖLÜMÜ ═══
            ('portal_ship', 0, 420),
            ('block', 4, 380),
            ('block', 0, 0),
            ('block', 5, 350),
            ('block', 1, 0),
            ('coin', 3, 300),
            ('block', 4, 350),
            ('block', 0, 0),
            ('portal_cube', 0, 420),

            # ═══ BÖLÜM 5: YERÇEKİMİ DEĞİŞİMİ ═══
            ('gravity_up', 0, 450),
            ('ceiling_spike', 0, 350),
            ('ceiling_spike', 0, 300),
            ('ceiling_spike', 0, 50),
            ('gravity_down', 0, 450),

            # ═══ BÖLÜM 6: TESTERE BÖLÜMÜ ═══
            ('saw', 1, 400),
            ('spike', 0, 300),
            ('saw', 2, 300),
            ('spike', 0, 50),
            ('spike', 0, 50),
            ('pad', 0, 300),
            ('coin', 3, 60),

            # ═══ BÖLÜM 7: KARMA MEYDAN OKUMA ═══
            ('spike', 0, 380),
            ('orb', 1, 280),
            ('spike', 0, 140),
            ('block', 0, 300),
            ('spike', 1, 0),
            ('pad', 0, 300),
            ('saw', 2, 250),
            ('spike', 0, 300),
            ('spike', 0, 50),

            # ═══ BÖLÜM 8: FİNAL ═══
            ('block', 0, 400),
            ('spike', 1, 0),
            ('spike', 0, 280),
            ('spike', 0, 50),
            ('spike', 0, 50),
            ('pad', 0, 300),
            ('orb', 1, 220),
            ('spike', 0, 150),
            ('spike', 0, 300),
            ('spike', 0, 50),
            ('spike', 0, 50),
            ('spike', 0, 50),       # Dörtlü (pad sonrası)
        ]
        self.total_obstacles = len(self.level_data)
        self.reset()

    def reset(self):
        self.current_index = 0
        self.obstacles = []
        self.next_spawn_x = WIDTH + 250
        self.finished = False
        self.total_distance = self._calc_total()
        self.distance_traveled = 0.0
        self.coins_collected = 0
        self.total_coins = sum(1 for t, _, _ in self.level_data if t == 'coin')

    def _calc_total(self):
        t = WIDTH + 250
        for _, _, d in self.level_data:
            t += d
        return t + WIDTH

    def get_progress(self):
        return min(1.0, self.distance_traveled / self.total_distance) \
            if self.total_distance else 0

    def update(self, speed):
        self.distance_traveled += speed
        while (self.current_index < len(self.level_data)
               and self.next_spawn_x <= WIDTH + 150):
            otype, yoff, dist = self.level_data[self.current_index]
            sx = self.next_spawn_x
            os = self.obstacle_size

            if otype in ('portal_ship', 'portal_cube',
                         'gravity_up', 'gravity_down'):
                y = GROUND_Y - os * 2
            elif otype == 'ceiling_spike':
                y = CEILING_Y + os * yoff
            else:
                y = GROUND_Y - os * (1 + yoff)

            self.obstacles.append(Obstacle(sx, y, otype, os))
            self.current_index += 1
            if self.current_index < len(self.level_data):
                self.next_spawn_x = sx + self.level_data[self.current_index][2]
            else:
                self.finished = True

        for o in self.obstacles:
            o.update(speed)
        self.obstacles = [o for o in self.obstacles if o.active]
        self.next_spawn_x -= speed

    def is_level_complete(self):
        return self.finished and len(self.obstacles) == 0

    def draw(self, surface):
        for o in self.obstacles:
            o.draw(surface)


# ═══════════════════════════════════════════════════════════════════════════════
#  OYUN
# ═══════════════════════════════════════════════════════════════════════════════

class Game:
    """Menü → Oynama → Ölüm/Tamamlama döngüsü."""

    def __init__(self):
        pygame.mixer.pre_init(44100, -16, 1, 512)
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Pulse Runner")
        self.clock = pygame.time.Clock()

        self.font_title = pygame.font.SysFont("Arial", 56, bold=True)
        self.font_big = pygame.font.SysFont("Arial", 44, bold=True)
        self.font_med = pygame.font.SysFont("Arial", 26, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 18)

        self.sounds = SoundManager()
        self.bg_surface = self._prerender_bg()
        self.stars = [(random.randint(0, WIDTH), random.randint(0, GROUND_Y - 20),
                       random.uniform(0.5, 2.0), random.uniform(0.3, 1.0))
                      for _ in range(55)]
        self.bg_shapes = [BgShape() for _ in range(18)]
        self.pulse_columns = [PulseColumn(80 + i * 110) for i in range(8)]

        self.state = 'menu'
        self.attempt = 0
        self.best_progress = 0.0
        self.player_color_index = 0
        self.ground_offset = 0.0
        self.pulse_timer = 0
        self.beat_pulse = 0.0
        self.flash_alpha = 0
        self.screen_shake = 0
        self.touching_orb = None
        self.shockwave = None

        # Pratik modu
        self.practice_mode = False
        self.checkpoint = None
        self.last_cp_pct = -1

        # Milestones
        self.milestones_shown = set()
        self.milestone_text = ""
        self.milestone_timer = 0

        self.player = None
        self.level = None
        self.particles = []
        self.death_particles = []

    def _prerender_bg(self):
        bg = pygame.Surface((WIDTH, HEIGHT))
        for y in range(HEIGHT):
            r = y / HEIGHT
            bg_r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * r)
            bg_g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * r)
            bg_b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * r)
            pygame.draw.line(bg, (bg_r, bg_g, bg_b), (0, y), (WIDTH, y))
        return bg

    def reset(self):
        self.player = Player(self.player_color_index)
        self.level = LevelManager()
        self.particles = []
        self.death_particles = []
        self.state = 'playing'
        self.attempt += 1
        self.screen_shake = 0
        self.flash_alpha = 0
        self.touching_orb = None
        self.shockwave = None
        self.milestones_shown = set()
        self.milestone_timer = 0
        self.last_cp_pct = -1
        self.checkpoint = None

    def run(self):
        running = True
        while running:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == 'playing':
                            self.state = 'menu'
                        else:
                            running = False
                    elif event.key == pygame.K_SPACE:
                        self._handle_action()
                    elif event.key == pygame.K_p and self.state == 'playing':
                        self._toggle_practice()
                    elif event.key == pygame.K_LEFT and self.state == 'menu':
                        self.player_color_index = (self.player_color_index - 1) % len(PLAYER_PALETTES)
                    elif event.key == pygame.K_RIGHT and self.state == 'menu':
                        self.player_color_index = (self.player_color_index + 1) % len(PLAYER_PALETTES)
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state == 'menu':
                        if not self._check_color_click(event.pos):
                            self._handle_action()
                    else:
                        self._handle_action()
            if not running:
                break
            self._update()
            self._draw()
            pygame.display.flip()
        pygame.quit()
        sys.exit()

    def _handle_action(self):
        if self.state == 'menu':
            self.reset()
        elif self.state == 'playing':
            if self.touching_orb:
                self.touching_orb.triggered = True
                self.player.orb_jump()
                self.sounds.play('orb')
                self._spawn_orb_particles(self.touching_orb)
                self.touching_orb = None
            elif self.player.mode == 'cube':
                if self.player.jump():
                    self.sounds.play('jump')
        elif self.state in ('dead', 'complete'):
            self.reset()

    def _check_color_click(self, pos):
        mx, my = pos
        n = len(PLAYER_PALETTES)
        total_w = n * 30 + (n - 1) * 15
        sx = (WIDTH - total_w) // 2
        y = HEIGHT - 70
        for i in range(n):
            cx = sx + i * 45
            if cx <= mx <= cx + 30 and y <= my <= y + 30:
                self.player_color_index = i
                return True
        return False

    def _toggle_practice(self):
        self.practice_mode = not self.practice_mode
        self.sounds.play('practice')
        if self.practice_mode:
            self._save_checkpoint()

    def _save_checkpoint(self):
        if not self.level or not self.player:
            return
        self.checkpoint = {
            'index': self.level.current_index,
            'distance': self.level.distance_traveled,
            'coins': self.level.coins_collected,
            'mode': self.player.mode,
            'gravity': self.player.gravity_dir,
        }

    def _practice_respawn(self):
        cp = self.checkpoint
        if not cp:
            self.reset()
            return
        self.player = Player(self.player_color_index)
        self.player.set_mode(cp['mode'])
        self.player.set_gravity(cp['gravity'])
        if cp['gravity'] == -1:
            self.player.y = CEILING_Y
        self.level.obstacles = []
        self.level.current_index = cp['index']
        self.level.distance_traveled = cp['distance']
        self.level.coins_collected = cp['coins']
        self.level.next_spawn_x = WIDTH + 100
        self.level.finished = (cp['index'] >= len(self.level.level_data))
        self.particles = []
        self.death_particles = []
        self.shockwave = None
        self.flash_alpha = 0
        self.screen_shake = 0
        self.touching_orb = None
        self.state = 'playing'

    # ─── GÜNCELLEME ───────────────────────────────────────────────────────

    def _update(self):
        self.pulse_timer += 1
        if self.pulse_timer % BEAT_FRAMES == 0:
            self.beat_pulse = 1.0
            for col in self.pulse_columns:
                col.pulse()
        self.beat_pulse = max(0, self.beat_pulse - 0.06)
        for s in self.bg_shapes:
            s.update()
        for col in self.pulse_columns:
            col.update()
        if self.flash_alpha > 0:
            self.flash_alpha = max(0, self.flash_alpha - 12)
        if self.milestone_timer > 0:
            self.milestone_timer -= 1
        # Shockwave
        if self.shockwave:
            self.shockwave['radius'] += 7
            self.shockwave['alpha'] -= 5
            if self.shockwave['alpha'] <= 0:
                self.shockwave = None

        if self.state == 'playing':
            self._update_playing()
        elif self.state == 'dead':
            self._update_dead()

    def _update_playing(self):
        keys = pygame.key.get_pressed()
        mouse = pygame.mouse.get_pressed()
        holding = keys[pygame.K_SPACE] or mouse[0]

        self.player.update(holding)
        self.level.update(GAME_SPEED)
        self.ground_offset = (self.ground_offset + GAME_SPEED) % 40

        # Orb temas kontrolü
        self.touching_orb = None
        pr = self.player.get_rect()
        for obs in self.level.obstacles:
            if obs.type == 'orb' and obs.active and not obs.triggered:
                if pr.colliderect(obs.get_rect()):
                    self.touching_orb = obs
                    break

        self._spawn_trail()
        self._spawn_speed_lines()
        self.particles = [p for p in self.particles if p.alive]
        for p in self.particles:
            p.update()

        self._check_interactions()

        # Milestones
        pct = int(self.level.get_progress() * 100)
        for ms in [25, 50, 75]:
            if pct >= ms and ms not in self.milestones_shown:
                self.milestones_shown.add(ms)
                self.milestone_text = f"%{ms}"
                self.milestone_timer = 70
                self.flash_alpha = 50
                self.sounds.play('milestone')

        # Practice checkpoint
        if self.practice_mode:
            cp_id = pct // 12
            if cp_id > self.last_cp_pct:
                self.last_cp_pct = cp_id
                self._save_checkpoint()

        if self.level.is_level_complete():
            self.state = 'complete'
            self.sounds.play('complete')
            self.best_progress = 1.0

    def _update_dead(self):
        self.death_particles = [p for p in self.death_particles if p.alive]
        for p in self.death_particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]
        for p in self.particles:
            p.update()
        if self.screen_shake > 0:
            self.screen_shake -= 1

        # Pratik mod: otomatik yeniden başlama
        if self.practice_mode and self.screen_shake <= 0:
            self._practice_respawn()

    def _spawn_trail(self):
        if not self.player.alive:
            return
        tc = self.player.trail_color
        if self.player.mode == 'cube':
            if self.player.on_ground and random.random() < 0.6:
                self.particles.append(Particle(
                    self.player.x - random.randint(2, 10),
                    self.player.y + self.player.size - random.randint(0, 12),
                    random.uniform(-1.5, -0.3), random.uniform(-0.8, 0.3),
                    random.randint(4, 8), tc, random.randint(15, 28)))
        else:
            if random.random() < 0.8:
                self.particles.append(Particle(
                    self.player.x - random.randint(0, 8),
                    self.player.y + self.player.size // 2 + random.randint(-5, 5),
                    random.uniform(-2.5, -0.8), random.uniform(-0.5, 0.5),
                    random.randint(3, 7), (0, 255, 200),
                    random.randint(12, 22), shape='circle'))

    def _spawn_speed_lines(self):
        if random.random() < 0.2:
            self.particles.append(Particle(
                WIDTH + 10, random.randint(30, GROUND_Y - 10),
                random.uniform(-18, -10), 0, 1, (255, 255, 255),
                random.randint(8, 18), shrink=False, shape='line'))

    def _spawn_death(self):
        cx = self.player.x + self.player.size // 2
        cy = self.player.y + self.player.size // 2
        for _ in range(45):
            a = random.uniform(0, 2 * math.pi)
            sp = random.uniform(3, 14)
            self.death_particles.append(Particle(
                cx, cy, math.cos(a) * sp, math.sin(a) * sp - 3,
                random.randint(4, 14), random.choice(DEATH_COLORS),
                random.randint(30, 70), gravity=0.4))
        # Shockwave
        self.shockwave = {'x': cx, 'y': cy, 'radius': 10, 'alpha': 200}

    def _spawn_orb_particles(self, orb):
        cx = orb.x + orb.size // 2
        cy = orb.y + orb.size // 2
        for _ in range(10):
            a = random.uniform(0, 2 * math.pi)
            sp = random.uniform(2, 6)
            self.particles.append(Particle(
                cx, cy, math.cos(a) * sp, math.sin(a) * sp,
                random.randint(3, 6), ORB_COLOR,
                random.randint(12, 25), shape='circle'))

    def _check_interactions(self):
        pr = self.player.get_rect()
        for obs in self.level.obstacles:
            if not obs.active or obs.triggered:
                continue
            if not pr.colliderect(obs.get_rect()):
                continue

            if obs.type in ('spike', 'ceiling_spike', 'block', 'saw'):
                self._die()
                return
            elif obs.type == 'pad':
                obs.triggered = True
                self.player.pad_launch()
                self.sounds.play('pad')
            elif obs.type == 'coin':
                obs.triggered = True
                self.level.coins_collected += 1
                self.sounds.play('coin')
                self._spawn_coin_fx(obs)
                self.flash_alpha = 25
            elif obs.type in ('portal_ship', 'portal_cube'):
                obs.triggered = True
                self.player.set_mode(
                    'ship' if obs.type == 'portal_ship' else 'cube')
                self.sounds.play('portal')
                self.flash_alpha = 70
                self._spawn_portal_fx(obs)
            elif obs.type in ('gravity_up', 'gravity_down'):
                obs.triggered = True
                self.player.set_gravity(
                    -1 if obs.type == 'gravity_up' else 1)
                self.sounds.play('gravity')
                self.flash_alpha = 80
                self._spawn_portal_fx(obs)
            # orb handled in _handle_action

    def _spawn_coin_fx(self, obs):
        cx, cy = obs.x + obs.size // 2, obs.y + obs.size // 2
        for _ in range(12):
            a = random.uniform(0, 2 * math.pi)
            sp = random.uniform(1, 5)
            self.particles.append(Particle(
                cx, cy, math.cos(a) * sp, math.sin(a) * sp,
                random.randint(2, 6), COIN_COLOR,
                random.randint(15, 30), shape='circle'))

    def _spawn_portal_fx(self, obs):
        cx, cy = obs.x + obs.size // 2, obs.y + obs.size
        for _ in range(20):
            self.particles.append(Particle(
                cx + random.randint(-10, 10), cy + random.randint(-30, 30),
                random.uniform(-3, 3), random.uniform(-3, 3),
                random.randint(3, 8), (180, 220, 255),
                random.randint(20, 40), shape='circle'))

    def _die(self):
        self.player.alive = False
        self.state = 'dead'
        self.screen_shake = 14
        self.flash_alpha = 150
        self.sounds.play('death')
        self._spawn_death()
        p = self.level.get_progress()
        if p > self.best_progress:
            self.best_progress = p

    # ─── ÇİZİM ───────────────────────────────────────────────────────────

    def _draw(self):
        sx = random.randint(-self.screen_shake, self.screen_shake) \
            if self.screen_shake > 0 else 0
        sy = random.randint(-self.screen_shake, self.screen_shake) \
            if self.screen_shake > 0 else 0

        self.screen.blit(self.bg_surface, (sx, sy))

        # Gemi/yerçekimi tonu
        if self.player and self.state != 'menu':
            if self.player.mode == 'ship':
                t = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                t.fill((0, 20, 50, 35))
                self.screen.blit(t, (0, 0))
            if self.player.gravity_dir == -1:
                t = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                t.fill((40, 0, 60, 30))
                self.screen.blit(t, (0, 0))

        # Nabız sütunları
        for col in self.pulse_columns:
            col.draw(self.screen)

        for s in self.bg_shapes:
            s.draw(self.screen)
        self._draw_stars(sx, sy)

        if self.state == 'menu':
            self._draw_ground(sx, sy)
            self._draw_menu()
        elif self.state in ('playing', 'dead', 'complete'):
            if self.player and (self.player.mode == 'ship'
                                or self.player.gravity_dir == -1):
                self._draw_ceiling(sx, sy)
            self._draw_ground(sx, sy)
            for p in self.particles:
                p.draw(self.screen)
            if self.level:
                self.level.draw(self.screen)
            if self.player:
                self.player.draw(self.screen)
            for p in self.death_particles:
                p.draw(self.screen)
            # Shockwave
            if self.shockwave:
                sw = self.shockwave
                r2 = sw['radius'] * 2 + 6
                ws = pygame.Surface((r2, r2), pygame.SRCALPHA)
                pygame.draw.circle(ws, (255, 255, 255, sw['alpha']),
                                   (r2 // 2, r2 // 2), sw['radius'], 3)
                self.screen.blit(ws, (sw['x'] - r2 // 2, sw['y'] - r2 // 2))
            self._draw_ui()
            # Milestone
            if self.milestone_timer > 0:
                self._draw_milestone()
            if self.state == 'dead':
                self._draw_death_screen()
            elif self.state == 'complete':
                self._draw_complete_screen()

        # Flash
        if self.flash_alpha > 0:
            fs = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            fs.fill((255, 255, 255, min(255, self.flash_alpha)))
            self.screen.blit(fs, (0, 0))

    def _draw_stars(self, ox, oy):
        for i, (sx, sy, size, br) in enumerate(self.stars):
            fl = 0.6 + 0.4 * math.sin(self.pulse_timer * 0.05 + i)
            fl += self.beat_pulse * 0.3
            a = int(min(255, 255 * br * fl))
            s = max(1, int(size * min(2.5, fl)))
            ss = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
            pygame.draw.circle(ss, (*STAR_COLOR, a), (s, s), s)
            self.screen.blit(ss, (int(sx) + ox, int(sy) + oy))

    def _draw_ceiling(self, ox, oy):
        cs = pygame.Surface((WIDTH, CEILING_Y), pygame.SRCALPHA)
        cs.fill((15, 15, 60, 180))
        self.screen.blit(cs, (ox, oy))
        pb = 1 + self.beat_pulse * 0.5
        wc = tuple(min(255, int(c * pb)) for c in GROUND_LINE_COLOR)
        pygame.draw.line(self.screen, wc, (ox, CEILING_Y + oy),
                         (WIDTH + ox, CEILING_Y + oy), 2)

    def _draw_ground(self, ox, oy):
        pygame.draw.rect(self.screen, GROUND_COLOR,
                         (ox, GROUND_Y + oy, WIDTH, HEIGHT - GROUND_Y))
        pb = 1 + self.beat_pulse * 0.6
        gc = tuple(min(255, int(c * pb)) for c in GROUND_LINE_COLOR)
        pygame.draw.line(self.screen, gc, (ox, GROUND_Y + oy),
                         (WIDTH + ox, GROUND_Y + oy), 2)
        # Dalga
        for wx in range(0, WIDTH, 4):
            wy = GROUND_Y + math.sin((wx + self.pulse_timer * 2) * 0.04) * 2
            ws = pygame.Surface((4, 2), pygame.SRCALPHA)
            ws.fill((0, 200, 255, int(60 + 40 * self.beat_pulse)))
            self.screen.blit(ws, (wx + ox, int(wy) + oy - 1))
        for gx in range(0, WIDTH + 40, 40):
            sh = (gx - int(self.ground_offset)) % (WIDTH + 40) - 20
            pygame.draw.line(self.screen, (30, 30, 100),
                             (sh + ox, GROUND_Y + 2 + oy),
                             (sh + ox, HEIGHT + oy), 1)
        for gy in range(20, HEIGHT - GROUND_Y, 20):
            pygame.draw.line(self.screen, (25, 25, 90),
                             (ox, GROUND_Y + gy + oy),
                             (WIDTH + ox, GROUND_Y + gy + oy), 1)

    def _draw_ui(self):
        prog = self.level.get_progress() if self.level else 0
        bx, by, bw, bh = 200, 15, 500, 14
        pygame.draw.rect(self.screen, PROGRESS_BG,
                         (bx, by, bw, bh), border_radius=7)
        fw = int(bw * prog)
        if fw > 0:
            pygame.draw.rect(self.screen, PROGRESS_FILL,
                             (bx, by, fw, bh), border_radius=7)
            if fw > 6:
                hl = pygame.Surface((fw - 4, bh // 3), pygame.SRCALPHA)
                hl.fill((255, 255, 255, 50))
                self.screen.blit(hl, (bx + 2, by + 2))
        pygame.draw.rect(self.screen, (80, 80, 120),
                         (bx, by, bw, bh), 2, border_radius=7)

        # Milestone işaretleri
        for ms in [25, 50, 75]:
            mx = bx + int(bw * ms / 100)
            mc = PROGRESS_FILL if ms in self.milestones_shown else (80, 80, 120)
            pygame.draw.line(self.screen, mc, (mx, by - 2), (mx, by + bh + 2), 2)

        self.screen.blit(
            self.font_small.render(f"%{int(prog * 100)}", True, TEXT_COLOR),
            (bx + bw + 12, by - 1))
        self.screen.blit(
            self.font_small.render(f"Deneme #{self.attempt}", True,
                                   (150, 150, 200)), (15, 12))

        # Coin
        ct = f"★ {self.level.coins_collected}/{self.level.total_coins}" \
            if self.level else ""
        self.screen.blit(self.font_small.render(ct, True, COIN_COLOR), (15, 34))

        # Mod göstergesi
        if self.player:
            if self.player.mode == 'ship':
                self.screen.blit(
                    self.font_small.render("✈ GEMİ", True, (0, 220, 255)),
                    (WIDTH - 100, 12))
            if self.player.gravity_dir == -1:
                self.screen.blit(
                    self.font_small.render("⇅ TERS", True, GRAVITY_UP_COLOR),
                    (WIDTH - 100, 32))

        # Pratik modu
        if self.practice_mode:
            ps = self.font_small.render("🔧 PRATİK MOD", True, (0, 255, 130))
            self.screen.blit(ps, (WIDTH // 2 - ps.get_width() // 2, 38))

    def _draw_milestone(self):
        """Yüzde milestone animasyonu."""
        ratio = self.milestone_timer / 70
        scale = 1.0 + (1 - ratio) * 0.5
        alpha = int(255 * min(1, ratio * 2))
        fs = int(48 * scale)
        try:
            f = pygame.font.SysFont("Arial", fs, bold=True)
        except Exception:
            f = self.font_big
        ts = f.render(self.milestone_text, True, PROGRESS_FILL)
        ts.set_alpha(alpha)
        r = ts.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        self.screen.blit(ts, r)

    # ─── MENÜ ────────────────────────────────────────────────────────────

    def _draw_menu(self):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 80))
        self.screen.blit(ov, (0, 0))

        # Başlık
        pulse = 0.85 + 0.15 * math.sin(self.pulse_timer * 0.06)
        tc = (int(255 * pulse), int(220 * pulse),
              int(50 + 100 * (1 - pulse)))
        title = self.font_title.render("GEOMETRY DASH", True, tc)
        tr = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 100))
        # Glow
        gs = pygame.Surface((title.get_width() + 30, title.get_height() + 20),
                            pygame.SRCALPHA)
        gs.fill((*tc, 15))
        self.screen.blit(gs, (tr.x - 15, tr.y - 10))
        self.screen.blit(title, tr)

        # Alt başlık
        sub = self.font_med.render("Ultimate Pygame Edition", True,
                                    (150, 150, 220))
        self.screen.blit(sub, sub.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50)))

        # Başla
        blink = 0.5 + 0.5 * math.sin(self.pulse_timer * 0.1)
        st = self.font_med.render("Başlamak için SPACE'e bas", True, TEXT_COLOR)
        ss = pygame.Surface(st.get_size(), pygame.SRCALPHA)
        ss.blit(st, (0, 0))
        ss.set_alpha(int(255 * blink))
        self.screen.blit(ss, ss.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10)))

        # Kontroller
        c1 = self.font_small.render(
            "SPACE/Tık = Zıpla  |  P = Pratik Mod  |  ESC = Çık", True,
            (120, 120, 170))
        self.screen.blit(c1, c1.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))

        # Best
        if self.best_progress > 0:
            bt = self.font_small.render(
                f"En İyi: %{int(self.best_progress * 100)}", True, PROGRESS_FILL)
            self.screen.blit(bt, bt.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 78)))

        # Renk seçici
        n = len(PLAYER_PALETTES)
        tw = n * 30 + (n - 1) * 15
        start_x = (WIDTH - tw) // 2
        y = HEIGHT - 70
        label = self.font_small.render("Renk Seç (← →):", True, (150, 150, 200))
        self.screen.blit(label, (start_x, y - 22))
        for i, pal in enumerate(PLAYER_PALETTES):
            cx = start_x + i * 45
            r = pygame.Rect(cx, y, 30, 30)
            cube_s = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.rect(cube_s, pal['main'], (0, 0, 30, 30))
            pygame.draw.rect(cube_s, pal['outline'], (0, 0, 30, 30), 2)
            rot_a = self.pulse_timer * (0.6 + i * 0.15)
            rotated = pygame.transform.rotate(cube_s, rot_a)
            rr = rotated.get_rect(center=r.center)
            self.screen.blit(rotated, rr.topleft)
            if i == self.player_color_index:
                pygame.draw.rect(self.screen, (255, 255, 255),
                                 r.inflate(8, 8), 2, border_radius=4)
                # İsim
                nt = self.font_small.render(pal['name'], True, pal['main'])
                self.screen.blit(nt,
                    nt.get_rect(center=(WIDTH // 2, y + 42)))

        # Dönen dekoratif küpler
        for i in range(5):
            bx = 80 + i * 190
            by = HEIGHT // 2 + 115 + math.sin(self.pulse_timer * 0.04 + i) * 6
            bs = 14
            c = PLAYER_PALETTES[i % len(PLAYER_PALETTES)]['main']
            cs = pygame.Surface((bs, bs), pygame.SRCALPHA)
            pygame.draw.rect(cs, (*c, 60), (0, 0, bs, bs))
            rot = pygame.transform.rotate(cs, self.pulse_timer * (0.5 + i * 0.3))
            rr = rot.get_rect(center=(int(bx), int(by)))
            self.screen.blit(rot, rr.topleft)

    # ─── ÖLÜM & TAMAMLAMA ────────────────────────────────────────────────

    def _draw_death_screen(self):
        if self.practice_mode:
            return  # Pratik modda overlay yok, otomatik respawn
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 130))
        self.screen.blit(ov, (0, 0))

        self.screen.blit(
            self.font_big.render("ÖLDÜN!", True, (255, 60, 60)),
            self.font_big.render("ÖLDÜN!", True, (255, 60, 60))
                .get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))

        pulse = 0.6 + 0.4 * math.sin(self.pulse_timer * 0.08)
        st = self.font_med.render("Yeniden denemek için SPACE'e bas",
                                   True, TEXT_COLOR)
        ss = pygame.Surface(st.get_size(), pygame.SRCALPHA)
        ss.blit(st, (0, 0))
        ss.set_alpha(int(255 * pulse))
        self.screen.blit(ss, ss.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))

        pct = int(self.level.get_progress() * 100) if self.level else 0
        best = int(self.best_progress * 100)
        info = self.font_small.render(
            f"İlerleme: %{pct}  |  En İyi: %{best}", True, (180, 180, 220))
        self.screen.blit(info, info.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 65)))

        if self.level and self.level.coins_collected > 0:
            ci = self.font_small.render(
                f"★ {self.level.coins_collected}/{self.level.total_coins}",
                True, COIN_COLOR)
            self.screen.blit(ci, ci.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 90)))

    def _draw_complete_screen(self):
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 130))
        self.screen.blit(ov, (0, 0))

        hue = (self.pulse_timer * 2) % 360
        r = int(128 + 127 * math.sin(math.radians(hue)))
        g = int(128 + 127 * math.sin(math.radians(hue + 120)))
        b = int(128 + 127 * math.sin(math.radians(hue + 240)))
        title = self.font_big.render("SEVİYE TAMAMLANDI!", True, (r, g, b))
        self.screen.blit(title,
                         title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))

        self.screen.blit(
            self.font_med.render("Tekrar için SPACE'e bas", True, TEXT_COLOR),
            self.font_med.render("Tekrar için SPACE'e bas", True, TEXT_COLOR)
                .get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))

        info = self.font_small.render(
            f"Deneme #{self.attempt}  |  "
            f"★ {self.level.coins_collected}/{self.level.total_coins}",
            True, (180, 220, 180))
        self.screen.blit(info, info.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60)))

        # Kutlama parçacıkları
        if random.random() < 0.4:
            self.particles.append(Particle(
                random.randint(50, WIDTH - 50), random.randint(50, HEIGHT - 50),
                random.uniform(-1, 1), random.uniform(-2, 0),
                random.randint(3, 8),
                random.choice([COIN_COLOR, PROGRESS_FILL, (255, 100, 255)]),
                random.randint(20, 40), shape='circle'))


# ═══════════════════════════════════════════════════════════════════════════════
#  GİRİŞ NOKTASI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Run the interactive game."""
    game = Game()
    game.run()


if __name__ == '__main__':
    main()
