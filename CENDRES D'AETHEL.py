#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CENDRES D'AETHEL - un action-RPG en pygame (fichier unique, aucun asset externe)

Installation :  pip install pygame
Lancement    :  python cendres_d_aethel.py

COMMANDES
  ZQSD / WASD / Flèches : se déplacer         Souris : viser
  Clic gauche / Espace  : coup d'épée (pare les projectiles !)
  Clic droit / E        : boule de braise (12 mana)
  Maj                   : roulade (invulnérable un court instant)
  R                     : potion de braise     F / Entrée : interagir / dialogue
  Échap : pause / menu / sauvegarde   F11 : plein écran <-> fenêtre
"""
import math
import random
import io
import json
import os
import sys
import time
from collections import deque

import pygame

pygame.init()
W, H = 960, 640
TILE = 32
MW, MH = 90, 70
FPS = 60
try:
    screen = pygame.display.set_mode((W, H), pygame.FULLSCREEN | pygame.SCALED)
except pygame.error:
    screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Cendres d'Aethel")
clock = pygame.time.Clock()


def font(size, bold=False):
    return pygame.font.SysFont("georgia,garamond,palatino,serif", size, bold=bold)


F_S, F_M, F_B, F_L, F_XL = font(15), font(19), font(24), font(30, True), font(58, True)


# --------------------------------------------------------------------------
#  LORE ET DONNÉES
# --------------------------------------------------------------------------
LORE_PAGES = [
    "Au commencement, il n'y avait que le Froid. Puis le Premier Souffle tomba sur la pierre nue et y alluma la Flamme Éternelle. "
    "Autour d'elle naquit Aethelgard, la Cité-Phare, et avec elle, le monde.",
    "Cinq Veilleurs jurèrent de ne jamais la laisser mourir. Quatre reçurent une Braise et un Cercle à garder : "
    "Sylvaine la Forêt, Vaelith les Eaux, Karn la Pierre, Ignis le Feu. La cinquième, Maëlys, ne reçut aucune Braise : elle reçut la Mémoire.",
    "Mais Karn, le roi-bâtisseur, avait aimé une mortelle. Quand elle mourut, la Flamme refusa de la rappeler : elle ne rend pas ce qui est parti. "
    "Alors la peur de la mort le rongea, jusqu'à lui faire croire qu'il suffisait de posséder la Flamme pour la plier.",
    "Ce fut la Nuit du Silence. Karn arracha la Flamme à son autel. Elle ne se laisse pas prendre : elle s'éteignit entre ses mains. "
    "Le froid revint, les morts se levèrent, la Cendre se mit à tomber, et les quatre Braises, orphelines, rendirent fous leurs gardiens.",
    "On raconte qu'à l'instant où la Flamme mourait, une dernière étincelle tomba dans le berceau d'un enfant de Port-Cendre, "
    "le dernier village d'Aethel. Cet enfant, c'est toi. Le Porte-Braise : le seul coeur encore chaud dans un monde de cendre.",
    "La Cendre approche des murs de Port-Cendre. Maëlys t'a vu grandir et t'a tu bien des choses. "
    "Il est temps de partir, de rendre aux Gardiens ce qu'ils ont perdu... et de découvrir ce que la Flamme attendait vraiment de toi.",
]

CREDITS = [
    ("title", "CENDRES D'AETHEL"),
    ("space", ""),
    ("small", "Un jeu de"),
    ("big", "WILOOPE"),
    ("space", ""),
    ("role", "Concept & game design", "WILOOPE"),
    ("role", "Univers, lore & écriture", "WILOOPE"),
    ("role", "Programmation", "WILOOPE"),
    ("role", "Direction artistique", "WILOOPE"),
    ("role", "Level design & équilibrage", "WILOOPE"),
    ("space", ""),
    ("small", "Réalisé avec Python & pygame"),
    ("space", ""),
    ("small", "Merci d'avoir joué."),
    ("big", "WILOOPE"),
]

TIPS = [
    "Un coup d'épée bien placé détruit les projectiles ennemis (et te rend un peu de mana).",
    "La roulade (Maj) te rend invulnérable un bref instant : traverse les anneaux de projectiles.",
    "Les stèles donnent de l'expérience... et des réponses. La Flamme garde une fin secrète pour les curieux.",
    "Les monstres ne te poursuivent pas dans Port-Cendre : c'est ton refuge.",
    "Les Gardiens se réveillent quand tu t'approches de leur arène. Prépare-toi avant d'entrer.",
    "Sauvegarde auprès de Maëlys, ou depuis le menu pause (Échap).",
    "Chaque Gardien vaincu t'offre une Braise, et son histoire s'ajoute à ton Journal.",
]

SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sauvegardes")
SLOTS = ["auto", "1", "2", "3"]
SLOT_NAMES = {"auto": "Sauvegarde automatique", "1": "Emplacement 1", "2": "Emplacement 2", "3": "Emplacement 3"}


def slot_path(slot):
    return os.path.join(SAVE_DIR, "slot_%s.json" % slot)


def read_slot(slot):
    try:
        with io.open(slot_path(slot), "r", encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and d.get("version") == 1:
            return d
    except (OSError, ValueError):
        pass
    return None


def write_slot(slot, data):
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        tmp = slot_path(slot) + ".tmp"
        with io.open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp, slot_path(slot))
        return True
    except OSError:
        return False


def delete_slot(slot):
    try:
        os.remove(slot_path(slot))
    except OSError:
        pass


BIOMES = {
    0: dict(name="Port-Cendre, le dernier refuge", ground=(112, 98, 74), tint=(0, 0, 0, 0)),
    1: dict(name="Forêt des Murmures", ground=(34, 72, 42), tint=(0, 30, 10, 38)),
    2: dict(name="Marais de Vaelith", ground=(52, 66, 54), tint=(10, 40, 40, 48)),
    3: dict(name="Ruines de Karn-la-Haute", ground=(84, 82, 92), tint=(20, 20, 50, 42)),
    4: dict(name="Cime de Cendre", ground=(66, 52, 50), tint=(70, 15, 0, 52)),
}

KINDS = {
    "loup":     dict(name="Loup-Cendre", hp=22, spd=120, dmg=7, r=9, xp=8, col=(125, 125, 132), ranged=False, shards=(1, 3)),
    "errant":   dict(name="Cendreux", hp=32, spd=70, dmg=9, r=10, xp=10, col=(165, 165, 175), ranged=False, shards=(1, 4)),
    "noye":     dict(name="Noyé", hp=44, spd=58, dmg=12, r=11, xp=14, col=(70, 125, 135), ranged=False, shards=(2, 5)),
    "follet":   dict(name="Feu-follet", hp=20, spd=70, dmg=8, r=8, xp=12, col=(120, 235, 175), ranged=True, shards=(2, 4)),
    "creux":    dict(name="Soldat Creux", hp=55, spd=80, dmg=13, r=11, xp=16, col=(145, 140, 165), ranged=False, shards=(3, 6)),
    "archer":   dict(name="Archer Creux", hp=30, spd=64, dmg=10, r=10, xp=15, col=(175, 155, 195), ranged=True, shards=(3, 6)),
    "braise":   dict(name="Cendre-Vive", hp=62, spd=94, dmg=15, r=11, xp=20, col=(235, 115, 50), ranged=False, shards=(4, 8)),
    "cracheur": dict(name="Cracheur de braise", hp=38, spd=62, dmg=12, r=10, xp=20, col=(245, 165, 60), ranged=True, shards=(4, 8)),
}
BIOME_KINDS = {
    1: ["loup", "loup", "errant"],
    2: ["noye", "noye", "follet"],
    3: ["creux", "creux", "archer"],
    4: ["braise", "braise", "cracheur"],
}

BOSSES = {
    1: dict(name="Sylvaine, l'Arbre-Mère", hp=380, r=26, spd=48, col=(70, 150, 80), bcol=(112, 220, 110),
            pats=["ring", "summon", "aimed", "ring"], braise="Braise Verte",
            last="« Merci... Enfin, je sens la pluie. Porte ma Braise, enfant, et n'oublie pas la forêt. »"),
    2: dict(name="Vaelith la Noyée", hp=460, r=24, spd=62, col=(80, 140, 185), bcol=(110, 190, 255),
            pats=["aimed", "charge", "ring", "aimed"], braise="Braise Bleue",
            last="« Les eaux se retirent... Dis-leur, quand ils reviendront, que j'ai gardé le gué jusqu'au bout. »"),
    3: dict(name="Karn, le Roi Creux", hp=560, r=26, spd=72, col=(150, 142, 175), bcol=(190, 150, 255),
            pats=["charge", "shock", "summon", "aimed"], braise="Braise Violette",
            last="« Ces yeux... elle avait ces mêmes yeux. Je voulais ne jamais mourir, et je n'ai jamais vécu. Prends la Braise, enfant. »"),
    4: dict(name="Ignis, Dernier Dragon de Cendre", hp=700, r=30, spd=56, col=(215, 85, 40), bcol=(255, 140, 50),
            pats=["spiral", "aimed", "ring", "charge", "shock"], braise="Braise Ardente",
            last="« Je me souviens... d'avoir été chaude. Rallume-nous. Ou ne le fais pas... mais choisis. »"),
}

BOSS_CODEX = {
    1: ("Sylvaine, la Veilleuse Verte",
        "Gardienne du Cercle Vert, elle plantait un arbre pour chaque âme apaisée. La Nuit du Silence, elle s'est enracinée pour ne pas voir "
        "tomber sa forêt, et la Cendre l'a changée en Arbre-Mère. Sa Braise est verte comme la première pluie."),
    2: ("Vaelith, la Veilleuse des Eaux",
        "Passeuse des morts, elle guidait les défunts à travers le gué des Marais. Quand la Flamme s'est éteinte, plus personne n'a pu traverser : "
        "elle s'est noyée dans sa propre attente. Sa Braise est bleue comme un adieu."),
    3: ("Karn, le Roi Creux",
        "Roi-bâtisseur d'Aethelgard, il aima une mortelle que la Flamme refusa de rappeler. Sa peur de la mort lui fit voler la Flamme, "
        "et la Flamme s'éteignit entre ses mains. Ses derniers mots parlaient d'yeux que tu semblais lui rappeler."),
    4: ("Ignis, la Veilleuse du Feu",
        "Quand la Flamme est morte, elle a continué de brûler seule, jusqu'à devenir une cendre vivante que les légendes appellent dragon. "
        "Sa Braise est la dernière : elle brûle encore comme un reproche."),
}

STELES = {
    0: [("Les Cinq Serments",
         "« Cinq Veilleurs, cinq serments : Sylvaine jura de garder les vivants, Vaelith de guider les morts, Ignis de garder la chaleur, "
         "Karn de garder la loi, Maëlys de garder le souvenir. Qu'aucun serment ne s'éteigne. »"),
        ("Port-Cendre",
         "« Port-Cendre fut fondé par les derniers pèlerins d'Aethelgard. On y garde les feux de cuisine allumés par habitude, "
         "comme on parle aux morts. »")],
    1: [("Sylvaine la Première",
         "« Sylvaine plantait un arbre pour chaque âme apaisée. Aujourd'hui, la forêt murmure leurs noms, sans fin, et ne sait plus les taire. »"),
        ("Les Loups-Cendre",
         "« Les loups-cendre ne sont pas nés ainsi. Ce sont les chiens des bergers d'Aethel, restés fidèles à des maîtres morts. »"),
        ("L'Arbre-Mère",
         "« Au coeur du Cercle Vert se dresse l'arbre-mère. Sylvaine s'y est enracinée la Nuit du Silence pour ne pas voir tomber sa forêt. "
         "Ses racines boivent la Cendre. »")],
    2: [("Le Gué des Morts",
         "« Vaelith veillait sur le gué où les défunts traversent vers leur dernier sommeil. Depuis la Nuit du Silence, plus personne ne traverse. "
         "Les noyés attendent. »"),
        ("Les Feux-Follets",
         "« Les feux-follets sont les prières que personne n'a exaucées. Ne les suis pas. »"),
        ("Lettres à Karn",
         "« Vaelith écrivit à Karn chaque soir de l'hiver du Silence, le suppliant de reposer la Flamme. "
         "Les lettres dorment au fond de l'eau, sans réponse. »")],
    3: [("Karn-la-Haute",
         "« Ici s'élevait Karn-la-Haute. Le roi bâtit mille tours pour monter vers la Flamme. Il ne comprit jamais qu'elle était déjà en bas, "
         "parmi les gens. »"),
        ("Le Coeur offert",
         "« Le Roi Creux n'a plus de coeur. Il l'a offert à la Flamme, et la Flamme l'a refusé. Depuis, il le cherche dans les pierres. »"),
        ("La tisserande",
         "« On dit que Karn aima une tisserande de Port-Cendre. Elle mourut en hiver, alors qu'elle attendait un enfant. La Flamme refusa de la "
         "rappeler. Les chroniques s'arrêtent là : l'Archiviste a arraché la page suivante. »")],
    4: [("Ignis",
         "« Ignis ne fut jamais un dragon. C'était la Veilleuse du Feu. Quand la Flamme s'est éteinte, elle a continué de brûler seule, "
         "et s'est changée en cendre vivante. »"),
        ("Le Choix",
         "« Gravé dans la roche : quand les quatre Braises seront réunies, le Porte-Braise devra choisir. Rendre la Flamme, ou la garder. »"),
        ("Ce que la Flamme demande",
         "« La Flamme ne se prend pas. Elle ne se vole pas. Elle se donne, d'un coeur qui bat à un coeur qui bat. "
         "Karn l'avait su, autrefois. Il l'avait oublié. »")],
}
LORE_TOTAL = sum(len(v) for v in STELES.values())

ASH_COL = {0: (190, 185, 180), 1: (240, 225, 130), 2: (140, 230, 180), 3: (200, 200, 225), 4: (255, 140, 60)}
ASH_VY = {0: 1.0, 1: 0.3, 2: 0.3, 3: 0.9, 4: -0.8}


def clamp(v, a, b):
    return max(a, min(b, v))


def dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def wrap(text, fnt, width):
    lines, cur = [], ""
    for w in text.split(" "):
        t = (cur + " " + w).strip()
        if fnt.size(t)[0] <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_text(text, fnt, col, pos, center=False, alpha=255, shadow=True, surf=None):
    surf = surf or screen
    img = fnt.render(text, True, col)
    r = img.get_rect()
    if center:
        r.center = pos
    else:
        r.topleft = pos
    if shadow:
        sh = fnt.render(text, True, (0, 0, 0))
        if alpha < 255:
            sh.set_alpha(alpha)
        surf.blit(sh, r.move(2, 2))
    if alpha < 255:
        img.set_alpha(alpha)
    surf.blit(img, r)
    return r


def draw_bar(x, y, w, h, frac, col, back=(30, 20, 22)):
    pygame.draw.rect(screen, back, (x, y, w, h), border_radius=3)
    if frac > 0:
        pygame.draw.rect(screen, col, (x, y, max(2, int(w * clamp(frac, 0, 1))), h), border_radius=3)
    pygame.draw.rect(screen, (225, 205, 165), (x, y, w, h), 1, border_radius=3)


# --------------------------------------------------------------------------
#  TUILES (dessinées par code)
# --------------------------------------------------------------------------
def build_tiles():
    r = random.Random(3)
    cache = {}
    for b, info in BIOMES.items():
        g = info["ground"]
        grounds = []
        for _ in range(4):
            s = pygame.Surface((TILE, TILE))
            k = r.randint(-7, 7)
            s.fill(tuple(clamp(c + k, 0, 255) for c in g))
            for _ in range(6):
                c = tuple(clamp(v + r.randint(-16, 12), 0, 255) for v in g)
                pygame.draw.rect(s, c, (r.randrange(TILE - 3), r.randrange(TILE - 3), r.randint(2, 5), r.randint(1, 3)))
            grounds.append(s)
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        if b == 1:      # arbre
            pygame.draw.rect(s, (60, 40, 25), (13, 18, 6, 13))
            pygame.draw.circle(s, (16, 52, 28), (16, 14), 14)
            pygame.draw.circle(s, (26, 78, 40), (12, 11), 8)
            pygame.draw.circle(s, (20, 64, 34), (21, 15), 7)
        elif b == 2:    # eau noire
            s.fill((36, 80, 108))
            for (x1, y1, x2) in ((4, 9, 14), (16, 20, 28), (6, 26, 12)):
                pygame.draw.line(s, (88, 150, 182), (x1, y1), (x2, y1), 2)
        elif b == 3:    # mur en ruine
            s.fill((50, 48, 60))
            pygame.draw.rect(s, (72, 70, 86), (1, 1, TILE - 2, TILE - 2), 2)
            pygame.draw.line(s, (36, 34, 44), (0, 16), (TILE, 16), 2)
            pygame.draw.line(s, (36, 34, 44), (10, 0), (10, 16), 2)
            pygame.draw.line(s, (36, 34, 44), (22, 16), (22, TILE), 2)
        elif b == 4:    # roche volcanique
            s.fill((34, 26, 28))
            pygame.draw.polygon(s, (52, 40, 42), [(2, 28), (8, 6), (20, 2), (30, 14), (28, 29)])
            pygame.draw.line(s, (225, 85, 25), (10, 12), (18, 20), 2)
            pygame.draw.line(s, (225, 85, 25), (18, 20), (16, 27), 1)
        cache[b] = (grounds, s)
    return cache


TILES = build_tiles()


# --------------------------------------------------------------------------
#  MONDE
# --------------------------------------------------------------------------
class World:
    def __init__(self, seed):
        rnd = random.Random(seed)
        self.cx, self.cy = MW // 2, MH // 2
        cx, cy = self.cx, self.cy
        self.arenas = {1: (14, 11), 2: (MW - 15, 11), 3: (14, MH - 12), 4: (MW - 15, MH - 12)}
        self.biome = [[0] * MW for _ in range(MH)]
        for y in range(MH):
            for x in range(MW):
                dx = x - cx + 4 * math.sin(y * 0.23)
                dy = y - cy + 4 * math.sin(x * 0.19)
                if abs(x - cx) <= 9 and abs(y - cy) <= 7:
                    b = 0
                elif dx < 0 and dy < 0:
                    b = 1
                elif dx >= 0 and dy < 0:
                    b = 2
                elif dx < 0:
                    b = 3
                else:
                    b = 4
                self.biome[y][x] = b
        dens = {0: 0.0, 1: 0.43, 2: 0.41, 3: 0.38, 4: 0.40}
        g = [[rnd.random() < dens[self.biome[y][x]] for x in range(MW)] for y in range(MH)]
        for _ in range(3):  # lissage (automate cellulaire)
            ng = [[False] * MW for _ in range(MH)]
            for y in range(MH):
                for x in range(MW):
                    n = 0
                    for yy in range(y - 1, y + 2):
                        for xx in range(x - 1, x + 2):
                            if (xx, yy) != (x, y):
                                if xx < 0 or yy < 0 or xx >= MW or yy >= MH or g[yy][xx]:
                                    n += 1
                    ng[y][x] = n >= 5 or (g[y][x] and n == 4)
            g = ng
        self.solid = g
        for x in range(MW):
            self.solid[0][x] = self.solid[MH - 1][x] = True
        for y in range(MH):
            self.solid[y][0] = self.solid[y][MW - 1] = True
        for y in range(MH):
            for x in range(MW):
                if self.biome[y][x] == 0:
                    self.solid[y][x] = False
        for b, (ax, ay) in self.arenas.items():
            for y in range(ay - 7, ay + 8):
                for x in range(ax - 7, ax + 8):
                    if (x - ax) ** 2 + (y - ay) ** 2 <= 49 and 0 < x < MW - 1 and 0 < y < MH - 1:
                        self.solid[y][x] = False

        def clear(x, y, r):
            for yy in range(y - r, y + r + 1):
                for xx in range(x - r, x + r + 1):
                    if 1 <= xx < MW - 1 and 1 <= yy < MH - 1:
                        self.solid[yy][xx] = False

        def walk(x, y, tx, ty, horiz_first):
            for o in (("h", "v") if horiz_first else ("v", "h")):
                if o == "h":
                    while x != tx:
                        x += 1 if tx > x else -1
                        clear(x, y, rnd.choice((1, 1, 2)))
                else:
                    while y != ty:
                        y += 1 if ty > y else -1
                        clear(x, y, rnd.choice((1, 1, 2)))

        walk(cx, cy, *self.arenas[1], True)
        walk(cx, cy, *self.arenas[2], False)
        walk(cx, cy, *self.arenas[3], False)
        walk(cx, cy, *self.arenas[4], True)
        # zones accessibles depuis le hub ; le reste est comblé
        seen = {(cx, cy)}
        dq = deque([(cx, cy)])
        while dq:
            x, y = dq.popleft()
            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if 0 <= nx < MW and 0 <= ny < MH and not self.solid[ny][nx] and (nx, ny) not in seen:
                    seen.add((nx, ny))
                    dq.append((nx, ny))
        for y in range(MH):
            for x in range(MW):
                if not self.solid[y][x] and (x, y) not in seen:
                    self.solid[y][x] = True
        self.by_biome = {b: [] for b in BIOMES}
        for (x, y) in seen:
            self.by_biome[self.biome[y][x]].append((x, y))

    def draw(self, surf, camx, camy):
        x0, y0 = camx // TILE, camy // TILE
        for ty in range(max(0, y0), min(MH, y0 + H // TILE + 2)):
            for tx in range(max(0, x0), min(MW, x0 + W // TILE + 2)):
                b = self.biome[ty][tx]
                grounds, sol = TILES[b]
                pos = (tx * TILE - camx, ty * TILE - camy)
                surf.blit(grounds[((tx * 73856093) ^ (ty * 19349663)) % 4], pos)
                if self.solid[ty][tx]:
                    surf.blit(sol, pos)


def blocked(world, x, y, r):
    for ty in range(int((y - r) // TILE), int((y + r) // TILE) + 1):
        for tx in range(int((x - r) // TILE), int((x + r) // TILE) + 1):
            if tx < 0 or ty < 0 or tx >= MW or ty >= MH or world.solid[ty][tx]:
                return True
    return False


def move_entity(world, e, dx, dy):
    if not blocked(world, e.x + dx, e.y, e.r):
        e.x += dx
    if not blocked(world, e.x, e.y + dy, e.r):
        e.y += dy


# --------------------------------------------------------------------------
#  ENTITÉS
# --------------------------------------------------------------------------
class Player:
    def __init__(self, x, y):
        self.x, self.y, self.r = x, y, 10
        self.maxhp = self.hp = 100
        self.maxmp = 50
        self.mp = 50.0
        self.dmg = 14
        self.lvl, self.xp = 1, 0
        self.speed = 168
        self.shards = 0
        self.potions = 2
        self.braises = set()
        self.lore = 0
        self.forge = 0
        self.atk_cd = self.atk_t = self.spell_cd = 0.0
        self.roll_t = self.roll_cd = self.inv = 0.0
        self.roll_dir = (1.0, 0.0)
        self.face = 0.0

    def xp_need(self):
        return 40 + 30 * (self.lvl - 1)


class Enemy:
    boss = False

    def __init__(self, kind, x, y):
        d = KINDS[kind]
        self.kind, self.name = kind, d["name"]
        self.x, self.y, self.r = x, y, d["r"]
        self.maxhp = self.hp = d["hp"]
        self.spd, self.dmg, self.xp = d["spd"], d["dmg"], d["xp"]
        self.col, self.ranged, self.shards = d["col"], d["ranged"], d["shards"]
        self.cd = random.uniform(0.3, 1.5)
        self.hurt = 0.0
        self.kx = self.ky = 0.0
        self.ang = random.uniform(0, 6.28)
        self.wt = random.uniform(0, 2)
        self.moving = False


class Boss:
    boss = True

    def __init__(self, biome, x, y):
        d = BOSSES[biome]
        self.biome, self.kind, self.name = biome, "boss", d["name"]
        self.x, self.y, self.home = x, y, (x, y)
        self.r, self.maxhp, self.spd = d["r"], d["hp"], d["spd"]
        self.hp = self.maxhp
        self.col, self.bcol, self.pats = d["col"], d["bcol"], d["pats"]
        self.dmg, self.xp, self.shards, self.ranged = 16, 150, (50, 70), False
        self.active = False
        self.cd, self.pat_i = 1.5, 0
        self.wind = self.dash = self.dir = 0.0
        self.spiral_t = self.spiral_cd = self.spiral_a = 0.0
        self.touch = self.hurt = 0.0
        self.kx = self.ky = 0.0

    def reset(self):
        self.hp, self.active = self.maxhp, False
        self.x, self.y = self.home
        self.wind = self.dash = self.spiral_t = 0.0
        self.cd = 1.5


# --------------------------------------------------------------------------
#  LE JEU
# --------------------------------------------------------------------------
class Game:
    def __init__(self):
        self.state = "loading"
        self.page, self.chars, self.t = 1, 0.0, 0.0
        self.ash = [[random.uniform(0, W), random.uniform(0, H), random.uniform(-12, 12),
                     random.uniform(18, 50), random.choice((1, 1, 2, 2, 3))] for _ in range(110)]
        self.vignette = self.make_vignette()
        self.world = self.p = None
        self.sel = 0
        self.hits = []
        self.saves = {}
        self.toast_text, self.toast_t = "", 0.0
        self.cred_t = 0.0
        self.slot_mode, self.slot_from, self.slot_msg, self.slot_del = "load", "main", "", -1
        self.journal_sel = 0
        self.load_ok = True
        self.begin_loading(self.new_game, lambda: self.set_state("main"), 5.5)

    # ---------- création ----------
    def make_vignette(self):
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        steps = 36
        for i in range(steps):
            t = i / steps
            w, h = int(W * (1.6 - 1.05 * t)), int(H * (1.6 - 1.05 * t))
            pygame.draw.ellipse(s, (0, 0, 0, int(150 * (1 - t))), (W // 2 - w // 2, H // 2 - h // 2, w, h))
        return s

    def begin_loading(self, job, then, min_time=3.5):
        self.state = "loading"
        self.load_job, self.load_then = job, then
        self.load_t, self.load_frames, self.load_min, self.load_done = 0.0, 0, min_time, False
        self.load_tip = random.choice(TIPS)
        self.hits = []

    def set_state(self, s):
        self.state, self.sel, self.hits = s, 0, []
        if s in ("main", "pause", "slots"):
            self.refresh_saves()

    def new_game(self, seed=None):
        self.seed = seed if seed is not None else random.randrange(10 ** 9)
        random.seed(self.seed)  # monde, stèles et ennemis reproductibles pour les sauvegardes
        self.world = w = World(self.seed)
        self.p = Player((w.cx + 0.5) * TILE, (w.cy + 2.5) * TILE)
        self.cam = [clamp(self.p.x - W / 2, 0, MW * TILE - W), clamp(self.p.y - H / 2, 0, MH * TILE - H)]
        self.projs, self.parts, self.floats, self.enemies = [], [], [], []
        self.bosses = {}
        for b, (ax, ay) in w.arenas.items():
            bo = Boss(b, (ax + 0.5) * TILE, (ay + 0.5) * TILE)
            self.bosses[b] = bo
            self.enemies.append(bo)
        for b in (1, 2, 3, 4):
            for _ in range(20):
                s = self.random_spot(b, 250)
                if s:
                    self.enemies.append(Enemy(random.choice(BIOME_KINDS[b]), *s))
        self.build_items()
        self.minimap = self.make_minimap()
        self.fog = pygame.Surface((MW * 2, MH * 2), pygame.SRCALPHA)
        self.fog.fill((0, 0, 0, 255))
        self.explored = set()
        self.shake = 0.0
        self.banner_text, self.banner_t = "", 0.0
        self.zone = -1
        self.play_time = 0.0
        self.spawn_t = 6.0
        self.dlg = None
        self.ending = 0
        self.end_t = self.dead_t = 0.0
        self.near = None
        random.seed()

    # ---------- sauvegarde / chargement ----------
    def toast(self, text):
        self.toast_text, self.toast_t = text, 2.8

    def refresh_saves(self):
        self.saves = {s: read_slot(s) for s in SLOTS}

    def has_save(self):
        return any(self.saves.values())

    def snapshot(self):
        p = self.p
        return dict(
            version=1, seed=self.seed, ts=time.time(), saved=time.strftime("%d/%m/%Y %H:%M"),
            lvl=p.lvl, nb=len(p.braises), lore=p.lore, play_time=self.play_time,
            zone=BIOMES[self.tile_biome(p.x, p.y)]["name"],
            player=dict(x=p.x, y=p.y, hp=p.hp, mp=p.mp, maxhp=p.maxhp, maxmp=p.maxmp, dmg=p.dmg, lvl=p.lvl, xp=p.xp,
                        shards=p.shards, potions=p.potions, braises=sorted(p.braises), lore=p.lore, forge=p.forge),
            items=[dict(r=it.get("read"), s=it.get("seen"), t=it.get("truth")) for it in self.items],
            explored=[list(c) for c in self.explored])

    def save_to(self, slot, auto=False):
        ok = write_slot(slot, self.snapshot())
        self.refresh_saves()
        self.toast(("Sauvegarde automatique." if auto else "Partie sauvegardée.") if ok else "Échec de la sauvegarde.")
        return ok

    def autosave(self):
        if self.world is not None and self.p is not None:
            self.save_to("auto", True)

    def load_from(self, d):
        self.new_game(d["seed"])
        pl, p = d["player"], self.p
        p.x, p.y = pl["x"], pl["y"]
        for k in ("hp", "maxhp", "maxmp", "dmg", "lvl", "xp", "shards", "potions", "lore", "forge"):
            setattr(p, k, pl[k])
        p.mp = float(pl["mp"])
        p.braises = set(pl["braises"])
        for it, st in zip(self.items, d["items"]):
            if "read" in it:
                it["read"] = bool(st.get("r"))
            if "seen" in it:
                it["seen"] = bool(st.get("s"))
            if st.get("t"):
                it["truth"] = True
        for b in p.braises:
            self.bosses[b].hp = 0
        self.enemies = [e for e in self.enemies if e.hp > 0]
        self.explored = set(tuple(c) for c in d.get("explored", []))
        for ex, ey in self.explored:
            pygame.draw.circle(self.fog, (0, 0, 0, 0), ((ex * 4 + 2) * 2, (ey * 4 + 2) * 2), 14)
        self.play_time = float(d.get("play_time", 0.0))
        self.cam = [clamp(p.x - W / 2, 0, MW * TILE - W), clamp(p.y - H / 2, 0, MH * TILE - H)]

    def start_new(self):
        self.begin_loading(self.new_game, self.start_prologue, 3.5)

    def start_prologue(self):
        self.set_state("intro")
        self.page, self.chars = 1, 0.0

    def start_load(self, slot):
        d = read_slot(slot)
        if not d:
            self.toast("Sauvegarde illisible.")
            return

        def job():
            try:
                self.load_from(d)
                self.load_ok = True
            except (KeyError, TypeError, ValueError, IndexError):
                self.new_game()
                self.load_ok = False

        self.begin_loading(job, self.after_load, 3.5)

    def after_load(self):
        if self.load_ok:
            self.set_state("play")
        else:
            self.set_state("main")
            self.toast("Sauvegarde corrompue.")

    def continue_game(self):
        best = max((s for s in SLOTS if self.saves.get(s)), key=lambda s: self.saves[s].get("ts", 0), default=None)
        if best:
            self.start_load(best)

    def random_spot(self, b, min_player=0):
        w = self.world
        ax, ay = w.arenas[b]
        for _ in range(60):
            tx, ty = random.choice(w.by_biome[b])
            if (tx - ax) ** 2 + (ty - ay) ** 2 < 100:
                continue
            x, y = (tx + 0.5) * TILE, (ty + 0.5) * TILE
            if min_player and dist(x, y, self.p.x, self.p.y) < min_player:
                continue
            return x, y
        return None

    def build_items(self):
        w = self.world
        cx, cy = w.cx, w.cy

        def T(dx, dy):
            return (cx + dx + 0.5) * TILE, (cy + dy + 0.5) * TILE

        self.items = []
        x, y = T(0, -1)
        self.items.append(dict(type="altar", name="Autel de la Flamme", x=x, y=y))
        x, y = T(-5, -3)
        self.items.append(dict(
            type="npc", name="Maëlys l'Archiviste", x=x, y=y, col=(175, 140, 205), seen=False, service="rest",
            lines=["Un Porte-Braise... Alors la prophétie n'était pas qu'une berceuse. Approche, que je regarde ton coeur : il est tiède, c'est bon signe.",
                   "Je suis Maëlys, la dernière Veilleuse. Pas la plus puissante : la plus ancienne. Je garde la Mémoire d'Aethel, et je te dois un peu de cette mémoire.",
                   "Quatre Gardiens détiennent chacun une Braise : Sylvaine au nord-ouest, Vaelith au nord-est, Karn au sud-ouest, Ignis au sud-est. "
                   "Ils furent mes frères et soeurs d'ordre. Ne les hais pas : ils sont en deuil.",
                   "Lis les stèles sur ta route : la mémoire d'Aethel s'y est réfugiée. Et reviens te reposer ici quand tu en auras besoin. Je veillerai sur ton feu."],
            lines2=["Que la Braise te garde. Veux-tu te reposer près du feu ? Je noterai où tu en es."],
            lines3=["Tu les as toutes... Alors je ne peux plus me taire.",
                    "Ta mère était la tisserande de Port-Cendre dont parlent les stèles. Ton père était Karn. "
                    "Je t'ai caché la vérité : j'avais peur que tu lui ressembles.",
                    "C'est pour toi que la Flamme a gardé une étincelle, la nuit où elle est morte. Karn voulait posséder la Flamme. "
                    "Toi, tu en es la dernière braise vivante.",
                    "Rends-la, garde-la... ou fais ce que Karn n'a jamais osé faire. Lis les stèles, enfant : elles disent ce que je n'ai jamais eu le courage d'écrire."]))
        x, y = T(5, -3)
        self.items.append(dict(
            type="npc", name="Torvald le Forgeron", x=x, y=y, col=(190, 110, 70), seen=False, service="forge",
            lines=["Hmpf. Encore un gamin avec une lame émoussée. Je suis Torvald, forgeron. Je forgeais pour les Veilleurs, avant.",
                   "C'est moi qui ai forgé la couronne de Karn. Il m'avait juré qu'elle servirait à bâtir. Je n'ai jamais su me pardonner ma naïveté.",
                   "Apporte-moi des éclats, et je rendrai ta lame digne de ceux qui t'ont précédé. Les Gardiens ne sont pas des monstres... "
                   "mais ils ne te feront aucun cadeau."],
            lines2=["Des éclats ? Je t'écoute. Et ne meurs pas, ça fait mauvais genre pour mon métier."]))
        x, y = T(3, 4)
        self.items.append(dict(
            type="npc", name="Orin le Colporteur", x=x, y=y, col=(90, 170, 130), seen=False, service="shop",
            lines=["Psst ! Orin, colporteur, pour vous servir. Je vends des potions de braise, distillées à partir de tout ce qui brille encore.",
                   "Un tuyau gratuit : les Gardiens attaquent en motifs. Roule à travers leurs anneaux, pare leurs tirs avec ton épée... et ne reste jamais immobile.",
                   "Et ne me demandez pas où je trouve la matière première."],
            lines2=["Une potion ? Toujours en stock. Et toujours un peu tiède."]))
        for (title, text), (dx, dy) in zip(STELES[0], ((-7, 5), (8, -1))):
            x, y = T(dx, dy)
            self.items.append(dict(type="stele", title=title, x=x, y=y, text=text, read=False))
        for b in (1, 2, 3, 4):
            for title, text in STELES[b]:
                s = self.random_spot(b)
                if s:
                    self.items.append(dict(type="stele", title=title, x=s[0], y=s[1], text=text, read=False))
        self.fires = [T(-4, 3), T(7, 1), T(-8, -5), T(8, 5)]

    def make_minimap(self):
        w = self.world
        s = pygame.Surface((MW * 2, MH * 2))
        for y in range(MH):
            for x in range(MW):
                c = BIOMES[w.biome[y][x]]["ground"]
                if w.solid[y][x]:
                    c = tuple(int(v * 0.4) for v in c)
                s.fill(c, (x * 2, y * 2, 2, 2))
        return s

    # ---------- utilitaires ----------
    def in_hub(self, e):
        return self.tile_biome(e.x, e.y) == 0

    def tile_biome(self, x, y):
        tx, ty = clamp(int(x // TILE), 0, MW - 1), clamp(int(y // TILE), 0, MH - 1)
        return self.world.biome[ty][tx]

    def set_banner(self, text, t=3.0):
        self.banner_text, self.banner_t = text, t

    def float(self, x, y, text, col=(255, 255, 255)):
        self.floats.append(dict(x=x, y=y, t=text, col=col, life=0.9))

    def burst(self, x, y, col, n):
        for _ in range(n):
            a, s = random.uniform(0, 6.283), random.uniform(40, 200)
            self.parts.append(dict(x=x, y=y, vx=math.cos(a) * s, vy=math.sin(a) * s,
                                   life=random.uniform(0.25, 0.7), max=0.7, col=col, size=random.randint(2, 4)))

    def shoot(self, x, y, ang, spd, dmg, friendly, col, r=6, life=3.0):
        self.projs.append(dict(x=x, y=y, vx=math.cos(ang) * spd, vy=math.sin(ang) * spd,
                               dmg=dmg, fr=friendly, col=col, r=r, life=life))

    def gain_xp(self, n):
        p = self.p
        p.xp += n
        while p.xp >= p.xp_need():
            p.xp -= p.xp_need()
            p.lvl += 1
            p.maxhp += 15
            p.maxmp += 5
            p.dmg += 2
            p.hp, p.mp = p.maxhp, float(p.maxmp)
            self.set_banner("Niveau %d !" % p.lvl, 2.5)
            self.burst(p.x, p.y, (255, 220, 120), 30)

    # ---------- dialogues ----------
    def start_dialog(self, name, lines, service=None):
        if self.state == "dead":
            return
        self.dlg = dict(name=name, lines=lines, i=0, c=0.0, service=service, menu=False, sel=0, opts=[], msg="")
        self.state = "dialogue"

    def close_dialog(self):
        self.dlg = None
        if self.state == "dialogue":
            self.state = "play"

    def menu_for(self, svc):
        p = self.p
        if svc == "rest":
            return [(lambda: "Se reposer près du feu (soins complets + sauvegarde)", self.svc_rest)]
        if svc == "forge":
            return [(lambda: "Aiguiser la lame (+3 dégâts) - %d éclats" % (25 + 20 * p.forge), self.svc_forge)]
        if svc == "shop":
            return [(lambda: "Acheter une potion de braise - 20 éclats", self.svc_potion)]
        if svc == "altar":
            opts = [(lambda: "Rallumer la Flamme (lui donner ton coeur)", lambda: self.finish(1)),
                    (lambda: "Garder les Braises pour toi", lambda: self.finish(2))]
            if p.lore >= LORE_TOTAL:
                opts.append((lambda: "Partager la Flamme avec tous  [fin véritable]", lambda: self.finish(3)))
            return opts
        return []

    def svc_rest(self):
        self.p.hp, self.p.mp = self.p.maxhp, float(self.p.maxmp)
        self.autosave()
        return "Le feu te réchauffe. Tes forces reviennent. (Partie sauvegardée)"

    def svc_forge(self):
        p = self.p
        c = 25 + 20 * p.forge
        if p.shards < c:
            return "Pas assez d'éclats."
        p.shards -= c
        p.forge += 1
        p.dmg += 3
        return "Torvald aiguise ta lame. Dégâts : %d." % p.dmg

    def svc_potion(self):
        p = self.p
        if p.shards < 20:
            return "Pas assez d'éclats."
        p.shards -= 20
        p.potions += 1
        return "Tu as maintenant %d potion(s)." % p.potions

    def finish(self, n):
        self.ending = n
        self.state = "ending"
        self.end_t = 0.0
        self.dlg = None
        return ""

    def interact(self):
        it, p = self.near, self.p
        if not it:
            return
        if it["type"] == "stele":
            lines = [it["text"]]
            if not it["read"]:
                it["read"] = True
                p.lore += 1
                self.gain_xp(15)
                lines.append("(Fragment de mémoire %d/%d - ajouté à ton Journal.)" % (p.lore, LORE_TOTAL))
            self.start_dialog("Stèle : " + it["title"], lines)
        elif it["type"] == "npc":
            if it.get("lines3") and len(p.braises) == 4 and not it.get("truth"):
                lines = it["lines3"]
                it["truth"] = True
            else:
                lines = it["lines2"] if it["seen"] else it["lines"]
            it["seen"] = True
            self.start_dialog(it["name"], lines, it["service"])
        elif it["type"] == "altar":
            if len(p.braises) < 4:
                self.start_dialog("Autel de la Flamme",
                                  ["Un cratère de pierre noire, froid comme une tombe. Quatre creux y attendent chacun une Braise.",
                                   "Braises rapportées : %d/4." % len(p.braises)])
            else:
                lines = ["Les quatre Braises vibrent dans ta poitrine. L'autel s'éclaire faiblement, comme s'il te reconnaissait.",
                         "Tu sais ce que tu dois faire... ou ce que tu pourrais faire à la place."]
                if p.lore >= LORE_TOTAL:
                    lines.append("Les %d fragments de mémoire résonnent en toi : une troisième voie, que Karn n'a jamais vue, s'ouvre devant toi." % LORE_TOTAL)
                self.start_dialog("Autel de la Flamme", lines, "altar")

    # ---------- entrées ----------
    def handle(self, ev):
        if ev.type == pygame.QUIT:
            self.quit_game()
        if ev.type == pygame.KEYDOWN:
            self.on_key(ev.key)
        elif ev.type == pygame.MOUSEMOTION:
            self.mouse_motion(ev.pos)
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.state in ("main", "pause", "slots"):
                self.mouse_click(ev.pos)
            elif self.state in ("intro", "dead", "ending", "loading", "credits") or \
                    (self.state == "dialogue" and not self.dlg["menu"]):
                self.on_key(pygame.K_RETURN)

    def quit_game(self):
        pygame.quit()
        sys.exit()

    def toggle_fullscreen(self):
        try:
            pygame.display.toggle_fullscreen()
        except pygame.error:
            pass

    def mouse_motion(self, pos):
        if self.state in ("main", "pause", "slots"):
            for x, y, w, h, i in self.hits:
                if x <= pos[0] < x + w and y <= pos[1] < y + h:
                    if self.sel != i:
                        self.sel, self.slot_del = i, -1
                    return

    def mouse_click(self, pos):
        for x, y, w, h, i in self.hits:
            if x <= pos[0] < x + w and y <= pos[1] < y + h:
                self.sel = i
                self.on_key(pygame.K_RETURN)
                return

    def menu_items(self):
        if self.state == "main":
            return [("Nouvelle partie", self.start_new, True),
                    ("Continuer", self.continue_game, self.has_save()),
                    ("Charger une partie", lambda: self.open_slots("load", "main"), self.has_save()),
                    ("Crédits", self.open_credits, True),
                    ("Quitter", self.quit_game, True)]
        if self.state == "pause":
            return [("Reprendre", lambda: self.set_state("play"), True),
                    ("Sauvegarder", lambda: self.open_slots("save", "pause"), True),
                    ("Charger une partie", lambda: self.open_slots("load", "pause"), self.has_save()),
                    ("Journal", self.open_journal, True),
                    ("Plein écran / fenêtre  (F11)", self.toggle_fullscreen, True),
                    ("Retour au menu principal", lambda: self.set_state("main"), True)]
        return []

    def open_credits(self):
        self.set_state("credits")
        self.cred_t = 0.0

    def open_journal(self):
        self.set_state("journal")
        self.journal_sel = 0

    def open_slots(self, mode, back):
        self.set_state("slots")
        self.slot_mode, self.slot_from, self.slot_msg, self.slot_del = mode, back, "", -1

    def slot_list(self):
        return SLOTS if self.slot_mode == "load" else SLOTS[1:]

    def journal_entries(self):
        out = [BOSS_CODEX[b] for b in sorted(self.p.braises)]
        out += [(it["title"], it["text"]) for it in self.items if it["type"] == "stele" and it["read"]]
        return out

    def on_key(self, key):
        K = pygame
        if key == K.K_F11:
            self.toggle_fullscreen()
            return
        confirm = key in (K.K_RETURN, K.K_KP_ENTER, K.K_SPACE, K.K_f)
        up = key in (K.K_UP, K.K_z, K.K_w)
        down = key in (K.K_DOWN, K.K_s)
        s = self.state
        if s == "loading":
            if confirm and self.load_done:
                self.load_t = max(self.load_t, self.load_min)
        elif s in ("main", "pause"):
            items = self.menu_items()
            n = len(items)
            if up or down:
                step = -1 if up else 1
                for _ in range(n):
                    self.sel = (self.sel + step) % n
                    if items[self.sel][2]:
                        break
            elif confirm:
                if items[self.sel][2]:
                    items[self.sel][1]()
            elif key == K.K_ESCAPE and s == "pause":
                self.set_state("play")
        elif s == "slots":
            slots = self.slot_list()
            n = len(slots) + 1
            if up or down:
                self.sel = (self.sel + (-1 if up else 1)) % n
                self.slot_del = -1
            elif key == K.K_ESCAPE:
                self.set_state(self.slot_from)
            elif key == K.K_DELETE and self.sel < len(slots) and self.saves.get(slots[self.sel]):
                if self.slot_del == self.sel:
                    delete_slot(slots[self.sel])
                    self.refresh_saves()
                    self.slot_msg, self.slot_del = "Sauvegarde supprimée.", -1
                else:
                    self.slot_del = self.sel
                    self.slot_msg = "Appuie encore sur Suppr pour confirmer la suppression."
            elif confirm:
                if self.sel >= len(slots):
                    self.set_state(self.slot_from)
                else:
                    slot = slots[self.sel]
                    if self.slot_mode == "save":
                        if self.save_to(slot):
                            self.slot_msg = "Sauvegardé dans : %s." % SLOT_NAMES[slot]
                        else:
                            self.slot_msg = "Impossible d'écrire la sauvegarde."
                    elif self.saves.get(slot):
                        self.start_load(slot)
                    else:
                        self.slot_msg = "Cet emplacement est vide."
        elif s == "credits":
            if confirm or key == K.K_ESCAPE:
                self.set_state("main")
        elif s == "journal":
            n = len(self.journal_entries())
            if key == K.K_ESCAPE:
                self.set_state("pause")
            elif n and up:
                self.journal_sel = (self.journal_sel - 1) % n
            elif n and down:
                self.journal_sel = (self.journal_sel + 1) % n
        elif s == "intro":
            if key == K.K_ESCAPE:
                self.set_state("play")
            elif confirm:
                text = LORE_PAGES[self.page - 1]
                if self.chars < len(text):
                    self.chars = len(text)
                else:
                    self.page, self.chars = self.page + 1, 0.0
                    if self.page > len(LORE_PAGES):
                        self.set_state("play")
        elif s == "play":
            if key == K.K_ESCAPE:
                self.set_state("pause")
            elif key in (K.K_f, K.K_RETURN, K.K_KP_ENTER):
                self.interact()
            elif key in (K.K_LSHIFT, K.K_RSHIFT):
                self.roll()
            elif key == K.K_r:
                self.use_potion()
        elif s == "dead":
            if confirm and self.dead_t > 1.0:
                self.respawn()
        elif s == "ending":
            if confirm and self.end_t > 2.0:
                self.set_state("main")
        elif s == "dialogue":
            d = self.dlg
            if key == K.K_ESCAPE:
                self.close_dialog()
            elif not d["menu"]:
                if confirm:
                    text = d["lines"][d["i"]]
                    if d["c"] < len(text):
                        d["c"] = len(text)
                    else:
                        d["i"] += 1
                        d["c"] = 0.0
                        if d["i"] >= len(d["lines"]):
                            if d["service"]:
                                d["menu"] = True
                                d["i"] = len(d["lines"]) - 1
                                d["c"] = 9999
                                d["opts"] = self.menu_for(d["service"])
                            else:
                                self.close_dialog()
            else:
                n = len(d["opts"]) + 1
                if up:
                    d["sel"] = (d["sel"] - 1) % n
                elif down:
                    d["sel"] = (d["sel"] + 1) % n
                elif confirm:
                    if d["sel"] == len(d["opts"]):
                        self.close_dialog()
                    else:
                        d["msg"] = d["opts"][d["sel"]][1]()

    def move_vec(self):
        k = pygame.key.get_pressed()
        ax = (k[pygame.K_d] or k[pygame.K_RIGHT]) - (k[pygame.K_q] or k[pygame.K_a] or k[pygame.K_LEFT])
        ay = (k[pygame.K_s] or k[pygame.K_DOWN]) - (k[pygame.K_z] or k[pygame.K_w] or k[pygame.K_UP])
        n = math.hypot(ax, ay)
        return (ax / n, ay / n) if n else (0.0, 0.0)

    def roll(self):
        p = self.p
        if p.roll_cd > 0 or p.roll_t > 0:
            return
        ax, ay = self.move_vec()
        if ax == 0 and ay == 0:
            ax, ay = math.cos(p.face), math.sin(p.face)
        p.roll_dir = (ax, ay)
        p.roll_t, p.roll_cd = 0.26, 0.8
        p.inv = max(p.inv, 0.3)
        self.burst(p.x, p.y, (200, 190, 170), 6)

    def use_potion(self):
        p = self.p
        if p.potions > 0 and p.hp < p.maxhp:
            p.potions -= 1
            p.hp = min(p.maxhp, p.hp + 45)
            self.float(p.x, p.y - 24, "+45 PV", (120, 255, 140))
            self.burst(p.x, p.y, (255, 140, 140), 12)

    # ---------- combat ----------
    def hurt_player(self, dmg):
        p = self.p
        if p.inv > 0 or self.state != "play":
            return False
        dmg = int(round(dmg))
        p.hp -= dmg
        p.inv = 0.7
        self.shake = max(self.shake, 7)
        self.float(p.x, p.y - 24, "-%d" % dmg, (255, 90, 80))
        self.burst(p.x, p.y, (200, 40, 40), 10)
        if p.hp <= 0:
            p.hp = 0
            self.state = "dead"
            self.dead_t = 0.0
        return True

    def damage_enemy(self, e, dmg, kx=0.0, ky=0.0, crit=False):
        dmg = int(round(dmg))
        e.hp -= dmg
        e.hurt = 0.12
        if e.boss:
            e.active = True
        else:
            e.kx += kx
            e.ky += ky
        self.float(e.x, e.y - e.r - 6, str(dmg) + ("!" if crit else ""), (255, 240, 120) if crit else (255, 255, 255))
        self.burst(e.x, e.y, e.col, 4)

    def attack(self):
        p = self.p
        p.atk_cd, p.atk_t = 0.36, 0.16
        move_entity(self.world, p, math.cos(p.face) * 7, math.sin(p.face) * 7)
        hit = False
        for e in self.enemies:
            dx, dy = e.x - p.x, e.y - p.y
            d = math.hypot(dx, dy)
            if d < 66 + e.r:
                a = math.atan2(dy, dx)
                diff = abs((a - p.face + math.pi) % (2 * math.pi) - math.pi)
                if diff < 1.1 or d < e.r + 18:
                    crit = random.random() < 0.12
                    dmg = p.dmg * random.uniform(0.9, 1.15) * (2 if crit else 1)
                    self.damage_enemy(e, dmg, math.cos(a) * 230, math.sin(a) * 230, crit)
                    hit = True
        for pr in self.projs:
            if not pr["fr"] and dist(pr["x"], pr["y"], p.x, p.y) < 66:
                a = math.atan2(pr["y"] - p.y, pr["x"] - p.x)
                if abs((a - p.face + math.pi) % (2 * math.pi) - math.pi) < 1.2:
                    pr["life"] = 0
                    p.mp = min(p.maxmp, p.mp + 4)
                    self.float(pr["x"], pr["y"], "Parade !", (180, 220, 255))
                    self.burst(pr["x"], pr["y"], (180, 220, 255), 8)
        if hit:
            p.mp = min(p.maxmp, p.mp + 3)
            self.shake = max(self.shake, 3)

    def cast(self):
        p = self.p
        if p.spell_cd > 0 or p.mp < 12:
            return
        p.mp -= 12
        p.spell_cd = 0.45
        self.shoot(p.x + math.cos(p.face) * 14, p.y + math.sin(p.face) * 14, p.face, 400,
                   p.dmg * 1.7, True, (255, 150, 50), 7, 1.1)

    def kill(self, e):
        p = self.p
        self.burst(e.x, e.y, e.col, 60 if e.boss else 14)
        sh = random.randint(*e.shards)
        p.shards += sh
        self.float(e.x, e.y - 20, "+%d éclats" % sh, (240, 210, 100))
        self.gain_xp(e.xp)
        if e.boss:
            d = BOSSES[e.biome]
            p.braises.add(e.biome)
            self.shake = 12
            lines = [d["last"], "Tu obtiens la %s ! (%d/4)" % (d["braise"], len(p.braises))]
            if len(p.braises) == 4:
                lines.append("Les quatre Braises vibrent dans ta poitrine. Retourne à l'autel de Port-Cendre.")
            self.start_dialog(d["name"], lines)
            self.autosave()
        elif random.random() < 0.10:
            p.potions += 1
            self.float(e.x, e.y - 34, "Potion !", (255, 150, 150))

    def respawn(self):
        p, w = self.p, self.world
        p.hp, p.mp = p.maxhp, float(p.maxmp)
        p.shards //= 2
        p.x, p.y = (w.cx + 0.5) * TILE, (w.cy + 2.5) * TILE
        p.inv = 1.5
        self.projs.clear()
        for bo in self.bosses.values():
            if bo.hp > 0:
                bo.reset()
        self.state = "play"
        self.set_banner("Ta Braise bat encore...", 2.5)

    # ---------- mise à jour ----------
    def update_ash(self, dt):
        b = 0
        if self.p is not None and self.state in ("play", "dialogue", "pause", "dead"):
            b = self.tile_biome(self.p.x, self.p.y)
        m = ASH_VY[b]
        for a in self.ash:
            a[0] = (a[0] + a[2] * dt + math.sin(self.t + a[1] * 0.02) * 6 * dt) % W
            a[1] = (a[1] + a[3] * m * dt) % H

    def update(self, dt):
        self.t += dt
        self.update_ash(dt)
        self.toast_t = max(0.0, self.toast_t - dt)
        pygame.mouse.set_visible(self.state != "play")
        s = self.state
        if s == "loading":
            self.load_t += dt
            self.load_frames += 1
            if not self.load_done and self.load_frames >= 3:
                self.load_job()
                self.load_done = True
            if self.load_done and self.load_t >= self.load_min:
                self.load_then()
            return
        if s == "credits":
            self.cred_t += dt
            return
        if s == "intro":
            self.chars += dt * 45
            return
        if s == "ending":
            self.end_t += dt
            return
        if s == "dialogue":
            self.dlg["c"] += dt * 60
            return
        if s == "dead":
            self.dead_t += dt
            return
        if s != "play":
            return

        p, w = self.p, self.world
        self.play_time += dt
        mx, my = pygame.mouse.get_pos()
        p.face = math.atan2(my + self.cam[1] - p.y, mx + self.cam[0] - p.x)
        for name in ("atk_cd", "atk_t", "spell_cd", "roll_cd", "inv"):
            setattr(p, name, max(0.0, getattr(p, name) - dt))
        p.mp = min(p.maxmp, p.mp + 5 * dt)
        self.shake = max(0.0, self.shake - 30 * dt)
        self.banner_t = max(0.0, self.banner_t - dt)

        # déplacement
        if p.roll_t > 0:
            p.roll_t -= dt
            move_entity(w, p, p.roll_dir[0] * 390 * dt, p.roll_dir[1] * 390 * dt)
        else:
            ax, ay = self.move_vec()
            move_entity(w, p, ax * p.speed * dt, ay * p.speed * dt)
        k, mb = pygame.key.get_pressed(), pygame.mouse.get_pressed()
        if (mb[0] or k[pygame.K_SPACE]) and p.atk_cd <= 0 and p.roll_t <= 0:
            self.attack()
        if (mb[2] or k[pygame.K_e]) and p.roll_t <= 0:
            self.cast()

        # zone
        z = self.tile_biome(p.x, p.y)
        if z != self.zone:
            self.zone = z
            self.set_banner(BIOMES[z]["name"], 3.0)
        # brouillard de la minicarte
        pygame.draw.circle(self.fog, (0, 0, 0, 0), (int(p.x / TILE * 2), int(p.y / TILE * 2)), 14)
        self.explored.add((int(p.x // TILE) // 4, int(p.y // TILE) // 4))

        # ennemis
        near = [e for e in self.enemies if not e.boss and abs(e.x - p.x) < 700 and abs(e.y - p.y) < 560]
        for e in self.enemies:
            if e.boss:
                self.update_boss(e, dt)
            elif e in near:
                self.update_enemy(e, dt)
        for i, a in enumerate(near):  # séparation douce
            for b in near[i + 1:]:
                dx, dy = b.x - a.x, b.y - a.y
                d = math.hypot(dx, dy)
                if 0 < d < a.r + b.r:
                    push = (a.r + b.r - d) * 0.5
                    move_entity(w, a, -dx / d * push, -dy / d * push)
                    move_entity(w, b, dx / d * push, dy / d * push)
        # projectiles
        for pr in self.projs:
            pr["x"] += pr["vx"] * dt
            pr["y"] += pr["vy"] * dt
            pr["life"] -= dt
            tx, ty = int(pr["x"] // TILE), int(pr["y"] // TILE)
            if tx < 0 or ty < 0 or tx >= MW or ty >= MH or w.solid[ty][tx]:
                pr["life"] = 0
                self.burst(pr["x"], pr["y"], pr["col"], 4)
                continue
            if pr["fr"]:
                for e in self.enemies:
                    if dist(pr["x"], pr["y"], e.x, e.y) < e.r + pr["r"]:
                        a = math.atan2(pr["vy"], pr["vx"])
                        self.damage_enemy(e, pr["dmg"], math.cos(a) * 160, math.sin(a) * 160)
                        self.burst(pr["x"], pr["y"], (255, 170, 60), 8)
                        pr["life"] = 0
                        break
            elif dist(pr["x"], pr["y"], p.x, p.y) < p.r + pr["r"]:
                if self.hurt_player(pr["dmg"]):
                    pr["life"] = 0
        self.projs = [pr for pr in self.projs if pr["life"] > 0]
        # morts
        for e in [e for e in self.enemies if e.hp <= 0]:
            self.kill(e)
        self.enemies = [e for e in self.enemies if e.hp > 0]
        # réapparitions
        self.spawn_t -= dt
        if self.spawn_t <= 0:
            self.spawn_t = 5.0
            if sum(1 for e in self.enemies if not e.boss) < 70:
                b = random.choice((1, 2, 3, 4))
                s = self.random_spot(b, 420)
                if s:
                    self.enemies.append(Enemy(random.choice(BIOME_KINDS[b]), *s))
        # particules / textes
        for q in self.parts:
            q["x"] += q["vx"] * dt
            q["y"] += q["vy"] * dt
            q["vx"] *= 0.93
            q["vy"] *= 0.93
            q["life"] -= dt
        self.parts = [q for q in self.parts if q["life"] > 0]
        for f in self.floats:
            f["y"] -= 32 * dt
            f["life"] -= dt
        self.floats = [f for f in self.floats if f["life"] > 0]
        # interaction proche
        self.near, best = None, 64
        for it in self.items:
            d = dist(it["x"], it["y"], p.x, p.y)
            if d < best:
                best, self.near = d, it
        # caméra
        tx, ty = clamp(p.x - W / 2, 0, MW * TILE - W), clamp(p.y - H / 2, 0, MH * TILE - H)
        s = 1 - math.exp(-10 * dt)
        self.cam[0] += (tx - self.cam[0]) * s
        self.cam[1] += (ty - self.cam[1]) * s

    def update_enemy(self, e, dt):
        p, w = self.p, self.world
        e.hurt = max(0.0, e.hurt - dt)
        e.cd -= dt
        if abs(e.kx) + abs(e.ky) > 5:
            move_entity(w, e, e.kx * dt, e.ky * dt)
            f = max(0.0, 1 - 9 * dt)
            e.kx *= f
            e.ky *= f
        d = dist(e.x, e.y, p.x, p.y)
        if not self.in_hub(p) and d < (330 if e.ranged else 280):
            a = math.atan2(p.y - e.y, p.x - e.x)
            if e.ranged:
                mv = -1 if d < 150 else (1 if d > 230 else 0)
                if mv:
                    move_entity(w, e, math.cos(a) * e.spd * mv * dt, math.sin(a) * e.spd * mv * dt)
                if e.cd <= 0:
                    e.cd = random.uniform(1.4, 2.2)
                    self.shoot(e.x, e.y, a + random.uniform(-0.08, 0.08), 190, e.dmg, False, e.col, 5, 2.5)
            else:
                move_entity(w, e, math.cos(a) * e.spd * dt, math.sin(a) * e.spd * dt)
                if d < e.r + p.r + 3 and e.cd <= 0:
                    e.cd = 0.9 if self.hurt_player(e.dmg) else 0.3
        else:
            e.wt -= dt
            if e.wt <= 0:
                e.wt = random.uniform(1, 3)
                e.ang = random.uniform(0, 6.283)
                e.moving = random.random() < 0.6
            if e.moving:
                move_entity(w, e, math.cos(e.ang) * e.spd * 0.35 * dt, math.sin(e.ang) * e.spd * 0.35 * dt)

    def update_boss(self, b, dt):
        p, w = self.p, self.world
        b.hurt = max(0.0, b.hurt - dt)
        d = dist(b.x, b.y, p.x, p.y)
        if not b.active:
            if d < 330 and not self.in_hub(p):
                b.active = True
                self.set_banner(b.name, 3.0)
            return
        rage = b.hp < b.maxhp * 0.5
        ang = math.atan2(p.y - b.y, p.x - b.x)
        b.touch -= dt
        dashing = b.dash > 0
        if b.wind > 0:
            b.wind -= dt
            if b.wind <= 0:
                b.dash = 0.55
        elif b.dash > 0:
            b.dash -= dt
            move_entity(w, b, math.cos(b.dir) * 440 * dt, math.sin(b.dir) * 440 * dt)
        else:
            if d > 130:
                s = b.spd * (1.4 if rage else 1.0)
                move_entity(w, b, math.cos(ang) * s * dt, math.sin(ang) * s * dt)
            b.cd -= dt
            if b.cd <= 0:
                self.boss_attack(b, ang, rage)
                b.cd = 1.5 if rage else 2.2
        if b.spiral_t > 0:
            b.spiral_t -= dt
            b.spiral_cd -= dt
            if b.spiral_cd <= 0:
                b.spiral_cd = 0.07 if rage else 0.09
                b.spiral_a += 0.45
                for k in range(2):
                    self.shoot(b.x, b.y, b.spiral_a + k * math.pi, 175, 11, False, b.bcol, 6, 4)
        if d < b.r + p.r and b.touch <= 0:
            if self.hurt_player(b.dmg * (1.6 if dashing else 1)):
                b.touch = 0.8

    def boss_attack(self, b, ang, rage):
        pat = b.pats[b.pat_i % len(b.pats)]
        b.pat_i += 1
        if pat == "ring":
            n, off = (22 if rage else 16), random.uniform(0, 6.28)
            for i in range(n):
                self.shoot(b.x, b.y, off + 6.2832 * i / n, 140, 12, False, b.bcol, 6, 4)
        elif pat == "aimed":
            n = 5 if rage else 3
            for i in range(n):
                self.shoot(b.x, b.y, ang + (i - (n - 1) / 2) * 0.22, 230, 13, False, b.bcol, 6, 3)
        elif pat == "spiral":
            b.spiral_t, b.spiral_a = 2.4, ang
        elif pat == "charge":
            b.wind, b.dir = 0.7, ang
        elif pat == "shock":
            for spd, off in ((95, 0.0), (170, 0.13)):
                for i in range(20):
                    self.shoot(b.x, b.y, off + 6.2832 * i / 20, spd, 12, False, b.bcol, 6, 4)
        elif pat == "summon":
            if sum(1 for e in self.enemies if not e.boss and dist(e.x, e.y, b.x, b.y) < 400) < 6:
                for i in range(3):
                    a = random.uniform(0, 6.28)
                    x, y = b.x + math.cos(a) * 70, b.y + math.sin(a) * 70
                    if not blocked(self.world, x, y, 10):
                        self.enemies.append(Enemy(BIOME_KINDS[b.biome][0], x, y))
                        self.burst(x, y, b.bcol, 8)

    # ---------- affichage ----------
    def draw(self):
        s = self.state
        if s == "loading":
            self.draw_loading()
        elif s == "main":
            self.draw_main()
        elif s == "slots":
            self.draw_slots()
        elif s == "credits":
            self.draw_credits_screen()
        elif s == "journal":
            self.draw_journal()
        elif s == "intro":
            self.draw_intro()
        elif s == "ending":
            self.draw_ending()
        else:
            self.draw_world()
            self.draw_hud()
            if s == "dialogue":
                self.draw_dialog()
            elif s == "pause":
                self.draw_pause()
            elif s == "dead":
                self.draw_overlay()
        if self.toast_t > 0:
            draw_text(self.toast_text, F_M, (170, 235, 180), (W // 2, H - 40), center=True,
                      alpha=int(255 * clamp(self.toast_t, 0, 1)))

    def draw_ash(self, col):
        for x, y, _, _, s in self.ash:
            pygame.draw.circle(screen, col, (int(x), int(y)), max(1, s // 2 + 1) if s > 1 else 1)

    def draw_world(self):
        p, t = self.p, self.t
        sh = self.shake if self.state == "play" else 0
        ox = int(self.cam[0] + (random.uniform(-sh, sh) if sh > 0.5 else 0))
        oy = int(self.cam[1] + (random.uniform(-sh, sh) if sh > 0.5 else 0))
        self.world.draw(screen, ox, oy)

        # feux de camp
        for fx, fy in self.fires:
            sx, sy = int(fx - ox), int(fy - oy)
            if -40 < sx < W + 40 and -40 < sy < H + 40:
                pygame.draw.line(screen, (70, 45, 30), (sx - 9, sy + 5), (sx + 9, sy - 3), 4)
                pygame.draw.line(screen, (70, 45, 30), (sx - 9, sy - 3), (sx + 9, sy + 5), 4)
                fl = 7 + math.sin(t * 9 + fx) * 2
                pygame.draw.circle(screen, (230, 100, 30), (sx, sy - 2), int(fl))
                pygame.draw.circle(screen, (255, 210, 90), (sx, sy - 3), int(fl * 0.55))

        # éléments interactifs
        for it in self.items:
            sx, sy = int(it["x"] - ox), int(it["y"] - oy)
            if not (-60 < sx < W + 60 and -60 < sy < H + 60):
                continue
            if it["type"] == "altar":
                self.draw_altar(sx, sy)
            elif it["type"] == "stele":
                pygame.draw.rect(screen, (96, 96, 108), (sx - 9, sy - 15, 18, 28), border_radius=5)
                pygame.draw.rect(screen, (60, 60, 70), (sx - 9, sy - 15, 18, 28), 2, border_radius=5)
                rune = (110, 120, 130) if it["read"] else (120, 230, 255)
                glow = 2 + int(math.sin(t * 3 + sx) + 1) if not it["read"] else 2
                pygame.draw.circle(screen, rune, (sx, sy - 4), glow)
                pygame.draw.line(screen, rune, (sx - 4, sy + 4), (sx + 4, sy + 4), 1)
            else:
                pygame.draw.circle(screen, it["col"], (sx, sy), 12)
                pygame.draw.circle(screen, (30, 20, 30), (sx, sy), 12, 2)
                pygame.draw.circle(screen, (235, 215, 190), (sx, sy - 3), 5)
                draw_text(it["name"], F_S, (235, 225, 200), (sx, sy - 28), center=True)

        # ennemis
        for e in self.enemies:
            sx, sy = int(e.x - ox), int(e.y - oy)
            if -80 < sx < W + 80 and -80 < sy < H + 80:
                (self.draw_boss if e.boss else self.draw_enemy)(e, sx, sy)

        # joueur
        self.draw_player(int(p.x - ox), int(p.y - oy))

        # projectiles
        for pr in self.projs:
            sx, sy = int(pr["x"] - ox), int(pr["y"] - oy)
            pygame.draw.circle(screen, pr["col"], (sx, sy), pr["r"] + 2)
            pygame.draw.circle(screen, (255, 250, 235), (sx, sy), max(2, pr["r"] - 2))
        for q in self.parts:
            f = q["life"] / q["max"]
            pygame.draw.circle(screen, q["col"], (int(q["x"] - ox), int(q["y"] - oy)), max(1, int(q["size"] * f)))
        for f in self.floats:
            draw_text(f["t"], F_S, f["col"], (int(f["x"] - ox), int(f["y"] - oy)), center=True,
                      alpha=int(255 * clamp(f["life"] / 0.5, 0, 1)))

        # invite d'interaction
        if self.near and self.state == "play":
            it = self.near
            draw_text("F : interagir", F_S, (255, 230, 150), (int(it["x"] - ox), int(it["y"] - oy) - 46), center=True)

        # ambiance
        z = self.tile_biome(p.x, p.y)
        tint = BIOMES[z]["tint"]
        if tint[3]:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill(tint)
            screen.blit(ov, (0, 0))
        self.draw_ash(ASH_COL[z])
        screen.blit(self.vignette, (0, 0))

        # réticule
        if self.state == "play":
            mx, my = pygame.mouse.get_pos()
            pygame.draw.circle(screen, (255, 230, 170), (mx, my), 8, 1)
            pygame.draw.circle(screen, (255, 230, 170), (mx, my), 1)

    def draw_altar(self, sx, sy):
        pygame.draw.circle(screen, (46, 42, 50), (sx, sy), 36)
        pygame.draw.circle(screen, (24, 22, 28), (sx, sy), 27)
        for i, b in enumerate((1, 2, 3, 4)):
            a = i * math.pi / 2 + math.pi / 4
            lit = b in self.p.braises
            col = BOSSES[b]["bcol"] if lit else (70, 64, 76)
            rad = 5 + (int(math.sin(self.t * 4 + i) * 1.5) if lit else 0)
            pygame.draw.circle(screen, col, (int(sx + math.cos(a) * 21), int(sy + math.sin(a) * 21)), rad)
        if len(self.p.braises) == 4:
            f = 9 + math.sin(self.t * 8) * 2
            pygame.draw.circle(screen, (240, 110, 40), (sx, sy), int(f))
            pygame.draw.circle(screen, (255, 230, 150), (sx, sy), int(f * 0.5))
        else:
            pygame.draw.circle(screen, (88, 88, 94), (sx, sy), 6)

    def draw_player(self, sx, sy):
        p = self.p
        if p.inv > 0 and p.roll_t <= 0 and int(self.t * 20) % 2:
            return
        pygame.draw.ellipse(screen, (20, 18, 16), (sx - 11, sy + 6, 22, 9))
        rr = p.r - (3 if p.roll_t > 0 else 0)
        pygame.draw.circle(screen, (128, 42, 38), (sx, sy), rr)
        pygame.draw.circle(screen, (60, 18, 18), (sx, sy), rr, 2)
        core = 3 + min(4, len(p.braises)) + int(math.sin(self.t * 6))
        pygame.draw.circle(screen, (255, 150, 50), (sx, sy), core + 2)
        pygame.draw.circle(screen, (255, 235, 160), (sx, sy), max(1, core - 1))
        wa = p.face
        if p.atk_t > 0:
            wa = p.face - 1.1 + 2.2 * (1 - p.atk_t / 0.16)
        x1, y1 = sx + math.cos(wa) * 9, sy + math.sin(wa) * 9
        x2, y2 = sx + math.cos(wa) * 27, sy + math.sin(wa) * 27
        pygame.draw.line(screen, (225, 225, 235), (x1, y1), (x2, y2), 3)
        pygame.draw.circle(screen, (235, 200, 160), (int(x1), int(y1)), 3)
        if p.atk_t > 0:
            s = pygame.Surface((170, 170), pygame.SRCALPHA)
            pts = [(85 + math.cos(p.face - 1.1 + 2.2 * i / 12) * 64, 85 + math.sin(p.face - 1.1 + 2.2 * i / 12) * 64) for i in range(13)]
            pts += [(85 + math.cos(p.face - 1.1 + 2.2 * i / 12) * 36, 85 + math.sin(p.face - 1.1 + 2.2 * i / 12) * 36) for i in range(12, -1, -1)]
            pygame.draw.polygon(s, (255, 240, 200, int(190 * p.atk_t / 0.16)), pts)
            screen.blit(s, (sx - 85, sy - 85))

    def draw_enemy(self, e, sx, sy):
        col = (255, 255, 255) if e.hurt > 0 else e.col
        pygame.draw.ellipse(screen, (18, 16, 16), (sx - e.r, sy + e.r - 5, e.r * 2, 8))
        pygame.draw.circle(screen, col, (sx, sy), e.r)
        pygame.draw.circle(screen, tuple(int(c * 0.45) for c in e.col), (sx, sy), e.r, 2)
        a = math.atan2(self.p.y - e.y, self.p.x - e.x)
        for s in (-0.55, 0.55):
            pygame.draw.circle(screen, (255, 70, 50), (int(sx + math.cos(a + s) * e.r * 0.55), int(sy + math.sin(a + s) * e.r * 0.55)), 2)
        if e.ranged:
            pygame.draw.circle(screen, e.col, (sx, sy), e.r + 4, 1)
        if e.hp < e.maxhp:
            pygame.draw.rect(screen, (40, 10, 10), (sx - 13, sy - e.r - 9, 26, 4))
            pygame.draw.rect(screen, (220, 60, 50), (sx - 13, sy - e.r - 9, int(26 * e.hp / e.maxhp), 4))

    def draw_boss(self, b, sx, sy):
        t = self.t
        if b.wind > 0:
            ex, ey = sx + math.cos(b.dir) * 320, sy + math.sin(b.dir) * 320
            pygame.draw.line(screen, (255, 70, 60), (sx, sy), (ex, ey), 4 + int(b.wind * 6))
        if b.active:
            pygame.draw.circle(screen, b.bcol, (sx, sy), int((b.r + 9) * (1 + 0.06 * math.sin(t * 5))), 2)
        for i in range(6):
            a = t * 1.3 + i * math.pi / 3
            pygame.draw.circle(screen, b.bcol, (int(sx + math.cos(a) * (b.r + 16)), int(sy + math.sin(a) * (b.r + 16))), 4)
        if b.biome == 4:
            pygame.draw.polygon(screen, (150, 50, 25), [(sx - b.r + 4, sy - 4), (sx - b.r - 30, sy - 30), (sx - b.r - 8, sy + 16)])
            pygame.draw.polygon(screen, (150, 50, 25), [(sx + b.r - 4, sy - 4), (sx + b.r + 30, sy - 30), (sx + b.r + 8, sy + 16)])
        col = (255, 255, 255) if b.hurt > 0 else b.col
        pygame.draw.circle(screen, col, (sx, sy), b.r)
        pygame.draw.circle(screen, tuple(int(c * 0.45) for c in b.col), (sx, sy), b.r, 3)
        pygame.draw.circle(screen, tuple(min(255, int(c * 1.25)) for c in b.col), (sx, sy), int(b.r * 0.55))
        if b.biome == 3:
            r = b.r
            pygame.draw.polygon(screen, (230, 200, 90), [(sx - 14, sy - r + 2), (sx - 14, sy - r - 12), (sx - 7, sy - r - 3),
                                                         (sx, sy - r - 16), (sx + 7, sy - r - 3), (sx + 14, sy - r - 12), (sx + 14, sy - r + 2)])
        a = math.atan2(self.p.y - b.y, self.p.x - b.x)
        for s in (-0.5, 0.5):
            pygame.draw.circle(screen, (255, 240, 200), (int(sx + math.cos(a + s) * b.r * 0.5), int(sy + math.sin(a + s) * b.r * 0.5)), 4)
            pygame.draw.circle(screen, b.bcol, (int(sx + math.cos(a + s) * b.r * 0.5), int(sy + math.sin(a + s) * b.r * 0.5)), 2)

    def draw_hud(self):
        p = self.p
        draw_bar(14, 12, 230, 18, p.hp / p.maxhp, (200, 50, 50))
        draw_text("PV %d/%d" % (p.hp, p.maxhp), F_S, (255, 240, 230), (22, 12), shadow=True)
        draw_bar(14, 34, 190, 12, p.mp / p.maxmp, (70, 120, 230))
        draw_bar(14, 50, 230, 6, p.xp / p.xp_need(), (230, 200, 80))
        draw_text("Niv. %d" % p.lvl, F_M, (255, 220, 140), (14, 60))
        draw_text("Éclats : %d" % p.shards, F_S, (240, 210, 100), (14, 86))
        draw_text("Potions (R) : %d" % p.potions, F_S, (255, 160, 160), (14, 104))
        draw_text("Dégâts : %d" % p.dmg, F_S, (220, 220, 230), (14, 122))
        for i, b in enumerate((1, 2, 3, 4)):
            c = BOSSES[b]["bcol"] if b in p.braises else (60, 56, 66)
            pygame.draw.circle(screen, c, (24 + i * 24, 156), 8)
            pygame.draw.circle(screen, (225, 205, 165), (24 + i * 24, 156), 8, 1)
        # boss
        for b in self.bosses.values():
            if b.active and b.hp > 0:
                draw_text(b.name, F_M, (255, 220, 170), (W // 2, 16), center=True)
                draw_bar(W // 2 - 220, 30, 440, 14, b.hp / b.maxhp, tuple(b.bcol))
                break
        # minicarte
        mm = self.minimap.copy()
        mm.blit(self.fog, (0, 0))
        mx0, my0 = W - MW * 2 - 12, 12
        screen.blit(mm, (mx0, my0))
        for b in self.bosses.values():
            if b.hp > 0:
                px, py = int(b.home[0] / TILE * 2), int(b.home[1] / TILE * 2)
                if self.fog.get_at((clamp(px, 0, MW * 2 - 1), clamp(py, 0, MH * 2 - 1)))[3] == 0:
                    pygame.draw.circle(screen, (255, 60, 50), (mx0 + px, my0 + py), 3)
        pygame.draw.circle(screen, (255, 215, 90), (mx0 + MW, my0 + MH), 3, 1)
        pygame.draw.circle(screen, (255, 255, 255), (mx0 + int(p.x / TILE * 2), my0 + int(p.y / TILE * 2)), 3)
        pygame.draw.rect(screen, (225, 205, 165), (mx0, my0, MW * 2, MH * 2), 1)
        # bandeau de zone
        if self.banner_t > 0:
            draw_text(self.banner_text, F_L, (255, 225, 160), (W // 2, 110), center=True,
                      alpha=int(255 * clamp(self.banner_t, 0, 1)))
        if self.play_time < 14 and self.state == "play":
            draw_text("ZQSD : bouger | Souris : viser | Clic G/Espace : frapper | Clic D/E : braise | Maj : roulade | R : potion | F : parler | F11 : plein écran",
                      F_S, (220, 215, 200), (W // 2, H - 18), center=True,
                      alpha=int(255 * clamp((14 - self.play_time) / 2, 0, 1)))

    def draw_dialog(self):
        d = self.dlg
        box = pygame.Rect(40, H - 272, W - 80, 252)
        s = pygame.Surface(box.size, pygame.SRCALPHA)
        s.fill((14, 10, 18, 230))
        screen.blit(s, box.topleft)
        pygame.draw.rect(screen, (200, 170, 110), box, 2, border_radius=6)
        draw_text(d["name"], F_M, (255, 215, 130), (box.x + 18, box.y + 10))
        remaining = int(d["c"])
        y = box.y + 44
        for ln in wrap(d["lines"][d["i"]], F_M, box.w - 36):
            if remaining > 0:
                draw_text(ln[:remaining], F_M, (240, 232, 215), (box.x + 18, y))
            remaining -= len(ln) + 1
            y += 24
        if d["menu"]:
            y = box.y + 44 + 3 * 24 + 4
            labels = [o[0]() for o in d["opts"]] + ["Partir"]
            for i, lab in enumerate(labels):
                sel = i == d["sel"]
                draw_text(("> " if sel else "   ") + lab, F_M, (255, 225, 130) if sel else (190, 185, 170), (box.x + 30, y))
                y += 26
            if d["msg"]:
                draw_text(d["msg"], F_S, (150, 230, 160), (box.x + 30, box.bottom - 28))
            draw_text("Haut/Bas : choisir | Entrée : valider", F_S, (150, 145, 135), (box.right - 330, box.y + 12), shadow=False)
        else:
            draw_text("F / Entrée : continuer", F_S, (150, 145, 135), (box.right - 190, box.bottom - 26), shadow=False)

    def draw_overlay(self):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((60, 0, 0, int(clamp(self.dead_t * 200, 0, 190))))
        screen.blit(ov, (0, 0))
        if self.dead_t > 0.4:
            draw_text("TU T'ÉTEINS...", F_XL, (230, 70, 60), (W // 2, H // 2 - 50), center=True)
            draw_text("La Cendre te recouvre. Mais ta Braise bat encore.", F_M, (230, 215, 200), (W // 2, H // 2 + 10), center=True)
        if self.dead_t > 1.0:
            draw_text("Entrée : renaître à Port-Cendre (la moitié de tes éclats est perdue)", F_S, (200, 195, 185),
                      (W // 2, H // 2 + 50), center=True)

    def draw_list(self, labels, enabled, y0, sel, w=460, step=46):
        self.hits = []
        x = W // 2 - w // 2
        for i, lab in enumerate(labels):
            y = y0 + i * step
            if i == sel:
                pygame.draw.rect(screen, (60, 34, 24), (x, y - 6, w, 38), border_radius=8)
                pygame.draw.rect(screen, (230, 170, 80), (x, y - 6, w, 38), 2, border_radius=8)
            col = (255, 225, 150) if i == sel else ((215, 205, 190) if enabled[i] else (100, 94, 90))
            draw_text(lab, F_B, col, (W // 2, y + 12), center=True)
            self.hits.append((x, y - 6, w, 38, i))

    def draw_credit_lines(self, top, bottom, t, speed=50):
        hts = {"title": 56, "big": 80, "small": 32, "role": 58, "space": 26}
        total = sum(hts[c[0]] for c in CREDITS)
        y = bottom - (t * speed) % (total + (bottom - top))
        for c in CREDITS:
            k = c[0]
            if k != "space" and top - 60 < y < bottom + 10:
                a = int(255 * clamp(min(y - top, bottom - y) / 50.0, 0, 1))
                if a > 0:
                    if k == "title":
                        draw_text(c[1], F_L, (225, 150, 60), (W // 2, y), center=True, alpha=a)
                    elif k == "big":
                        f = 215 + int(math.sin(self.t * 5) * 25)
                        draw_text(c[1], F_XL, (f, int(f * 0.66), 60), (W // 2, y + 20), center=True, alpha=a)
                    elif k == "small":
                        draw_text(c[1], F_M, (200, 192, 178), (W // 2, y), center=True, alpha=a)
                    elif k == "role":
                        draw_text(c[1], F_S, (150, 145, 135), (W // 2, y), center=True, alpha=a)
                        draw_text(c[2], F_B, (255, 225, 150), (W // 2, y + 24), center=True, alpha=a)
            y += hts[k]

    def draw_loading(self):
        screen.fill((8, 6, 10))
        self.draw_ash((150, 140, 130))
        draw_text("CENDRES D'AETHEL", F_L, (225, 150, 60), (W // 2, 46), center=True)
        self.draw_credit_lines(96, 430, self.load_t, 52)
        prog = clamp(self.load_t / self.load_min, 0, 1) * (1.0 if self.load_done else 0.85)
        draw_text("Chargement...  %d %%" % int(prog * 100), F_S, (210, 200, 185), (W // 2, 462), center=True)
        draw_bar(W // 2 - 260, 480, 520, 14, prog, (230, 120, 40))
        for i, ln in enumerate(wrap(self.load_tip, F_S, 700)):
            draw_text(ln, F_S, (160, 154, 142), (W // 2, 524 + i * 20), center=True)
        draw_text("WILOOPE", F_S, (120, 112, 100), (W - 70, H - 20), center=True, shadow=False)

    def draw_main(self):
        screen.fill((8, 6, 10))
        for rad, col in ((330, (22, 10, 8)), (250, (30, 13, 9)), (180, (40, 17, 10)), (110, (54, 22, 11))):
            pygame.draw.circle(screen, col, (W // 2, 210), rad)
        self.draw_ash((150, 140, 130))
        f = 215 + int(math.sin(self.t * 5) * 25)
        draw_text("CENDRES D'AETHEL", F_XL, (f, int(f * 0.62), 50), (W // 2, 150), center=True)
        draw_text("Un conte de feu, de cendre et de choix", F_M, (190, 180, 165), (W // 2, 205), center=True)
        draw_text("par WILOOPE", F_B, (255, 215, 140), (W // 2, 240), center=True)
        items = self.menu_items()
        self.draw_list([i[0] for i in items], [i[2] for i in items], 300, self.sel)
        draw_text("Flèches / ZQSD + Entrée, ou souris   |   F11 : plein écran", F_S, (130, 125, 115),
                  (W // 2, H - 28), center=True)

    def draw_pause(self):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 175))
        screen.blit(ov, (0, 0))
        draw_text("PAUSE", F_XL, (255, 225, 160), (W // 2, 110), center=True)
        items = self.menu_items()
        self.draw_list([i[0] for i in items], [i[2] for i in items], 190, self.sel)

    def draw_slots(self):
        screen.fill((10, 8, 12))
        self.draw_ash((150, 140, 130))
        title = "Charger une partie" if self.slot_mode == "load" else "Sauvegarder la partie"
        draw_text(title, F_L, (255, 225, 160), (W // 2, 60), center=True)
        slots = self.slot_list()
        self.hits = []
        for i, sl in enumerate(slots):
            y = 110 + i * 92
            sel = i == self.sel
            pygame.draw.rect(screen, (60, 34, 24) if sel else (24, 18, 22), (120, y, W - 240, 80), border_radius=8)
            pygame.draw.rect(screen, (230, 170, 80) if sel else (90, 76, 66), (120, y, W - 240, 80), 2, border_radius=8)
            draw_text(SLOT_NAMES[sl], F_B, (255, 225, 150) if sel else (215, 205, 190), (144, y + 8))
            d = self.saves.get(sl)
            if d:
                mins = int(d.get("play_time", 0)) // 60
                draw_text("Niv. %d   |   Braises %d/4   |   Fragments %d/%d   |   %d min" % (
                    d.get("lvl", 1), d.get("nb", 0), d.get("lore", 0), LORE_TOTAL, mins), F_S, (200, 192, 178), (144, y + 40))
                draw_text("%s   -   %s" % (d.get("zone", ""), d.get("saved", "")), F_S, (150, 145, 135), (144, y + 58))
            else:
                draw_text("- vide -", F_S, (110, 104, 98), (144, y + 44))
            self.hits.append((120, y, W - 240, 80, i))
        i = len(slots)
        y = 110 + i * 92
        sel = i == self.sel
        pygame.draw.rect(screen, (60, 34, 24) if sel else (24, 18, 22), (W // 2 - 110, y, 220, 40), border_radius=8)
        pygame.draw.rect(screen, (230, 170, 80) if sel else (90, 76, 66), (W // 2 - 110, y, 220, 40), 2, border_radius=8)
        draw_text("Retour", F_B, (255, 225, 150) if sel else (215, 205, 190), (W // 2, y + 20), center=True)
        self.hits.append((W // 2 - 110, y, 220, 40, i))
        if self.slot_msg:
            draw_text(self.slot_msg, F_M, (170, 235, 180), (W // 2, H - 56), center=True)
        draw_text("Entrée : valider   |   Échap : retour   |   Suppr : supprimer une sauvegarde", F_S, (130, 125, 115),
                  (W // 2, H - 24), center=True)

    def draw_credits_screen(self):
        screen.fill((8, 6, 10))
        self.draw_ash((150, 140, 130))
        self.draw_credit_lines(70, H - 60, self.cred_t, 48)
        draw_text("Échap : retour", F_S, (130, 125, 115), (W // 2, H - 24), center=True)

    def draw_journal(self):
        screen.fill((10, 8, 12))
        self.draw_ash((150, 140, 130))
        draw_text("Journal", F_L, (255, 225, 160), (W // 2, 40), center=True)
        ents = self.journal_entries()
        if not ents:
            draw_text("Rien pour l'instant. Lis les stèles et vaincs les Gardiens.", F_M, (190, 185, 170),
                      (W // 2, H // 2), center=True)
        else:
            self.journal_sel = clamp(self.journal_sel, 0, len(ents) - 1)
            first = max(0, min(self.journal_sel - 8, len(ents) - 10))
            for i in range(first, min(len(ents), first + 10)):
                yy = 90 + (i - first) * 42
                sel = i == self.journal_sel
                if sel:
                    pygame.draw.rect(screen, (60, 34, 24), (30, yy - 4, 330, 34), border_radius=6)
                draw_text(ents[i][0], F_S, (255, 225, 150) if sel else (200, 192, 178), (42, yy + 3))
            title, text = ents[self.journal_sel]
            draw_text(title, F_B, (255, 215, 130), (400, 92))
            y = 140
            for ln in wrap(text, F_M, 520):
                draw_text(ln, F_M, (235, 226, 210), (400, y))
                y += 28
        draw_text("Haut/Bas : parcourir   |   Échap : retour", F_S, (130, 125, 115), (W // 2, H - 24), center=True)

    def draw_intro(self):
        screen.fill((8, 6, 10))
        self.draw_ash((150, 145, 140))
        text = LORE_PAGES[self.page - 1]
        rem, y = int(self.chars), 150
        for ln in wrap(text, F_B, 720):
            if rem > 0:
                draw_text(ln[:rem], F_B, (225, 215, 195), (W // 2, y), center=True)
            rem -= len(ln) + 1
            y += 38
        draw_text("%d / %d" % (self.page, len(LORE_PAGES)), F_S, (120, 115, 105), (W // 2, H - 60), center=True)
        draw_text("Entrée : continuer   |   Échap : passer le prologue", F_S, (150, 145, 135), (W // 2, H - 36), center=True)

    def draw_ending(self):
        p, n = self.p, self.ending
        for y in range(0, H, 4):
            f = y / H
            if n == 1:
                c = (int(30 + 90 * (1 - f)), int(18 + 60 * (1 - f)), int(14 + 14 * (1 - f)))
            elif n == 2:
                c = (int(24 + 36 * f), int(8 + 6 * f), int(34 + 26 * (1 - f)))
            else:
                c = (int(40 + 120 * (1 - f)), int(34 + 100 * (1 - f)), int(30 + 60 * (1 - f)))
            pygame.draw.rect(screen, c, (0, y, W, 4))
        self.draw_ash((255, 210, 120) if n != 2 else (150, 120, 170))
        if n == 1:
            title = "FIN : L'ÉTINCELLE"
            txt = ("Tu poses les quatre Braises dans les creux de l'autel, puis ta propre main. La Flamme jaillit, et pour la rallumer "
                   "tu lui donnes ton coeur. Tu ne t'éteins pas : tu deviens la lumière. Les morts retrouvent le repos, la Cendre se change "
                   "en pluie, et mille ans plus tard, un enfant de Port-Cendre allume encore une lanterne à ton nom.")
        elif n == 2:
            title = "FIN : LA COURONNE DE CENDRE"
            txt = ("Tu refermes la main sur les quatre Braises. Leur puissance t'envahit, et la Flamme, elle, reste morte. Les ombres "
                   "s'agenouillent devant toi. Tu règnes sur un monde froid que plus rien ne menace... sauf ce qui a rongé Karn avant toi : "
                   "la peur de mourir. Elle finit toujours par frapper à la porte des rois.")
        else:
            title = "FIN VÉRITABLE : LE FOYER"
            txt = ("Tu n'offres pas la Flamme, tu ne la gardes pas : tu la partages. Maëlys, Torvald, Orin, les enfants de Port-Cendre, "
                   "chacun pose une main sur l'autel. La Flamme se divise en mille braises, une dans chaque foyer d'Aethel. Plus de Veilleur "
                   "unique, plus de trône, plus de peur. Dans les cendres, Sylvaine, Vaelith, Ignis et Karn trouvent enfin le sommeil : "
                   "ils avaient seulement oublié qu'on ne garde pas seul un feu.")
        draw_text(title, F_L, (255, 225, 150), (W // 2, 120), center=True)
        y = 190
        for ln in wrap(txt, F_M, 740):
            draw_text(ln, F_M, (240, 230, 210), (W // 2, y), center=True)
            y += 30
        mins, secs = divmod(int(self.play_time), 60)
        draw_text("Niveau %d  |  Fragments de mémoire : %d/%d  |  Temps : %d min %02d s" % (p.lvl, p.lore, LORE_TOTAL, mins, secs),
                  F_S, (200, 190, 170), (W // 2, 450), center=True)
        draw_text("Un jeu de WILOOPE", F_B, (255, 215, 140), (W // 2, 500), center=True)
        if self.end_t > 2.0 and int(self.t * 1.6) % 2 == 0:
            draw_text("Entrée : retour au menu", F_M, (240, 225, 190), (W // 2, 560), center=True)
        fade = pygame.Surface((W, H))
        fade.set_alpha(int(clamp(255 - self.end_t * 120, 0, 255)))
        screen.blit(fade, (0, 0))


def main():
    g = Game()
    while True:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)
        for ev in pygame.event.get():
            g.handle(ev)
        g.update(dt)
        g.draw()
        pygame.display.flip()


if __name__ == "__main__":
    main()