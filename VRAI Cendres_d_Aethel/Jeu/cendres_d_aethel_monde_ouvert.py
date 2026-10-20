#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CENDRES D'AETHEL - un action-RPG en monde ouvert (pygame, fichier unique, aucun asset externe)

Installation :  pip install pygame
Lancement    :  python cendres_d_aethel.py

COMMANDES
  ZQSD / WASD / Flèches : se déplacer         Souris : viser
  Clic gauche / Espace  : coup d'épée (pare les projectiles !)
  Clic droit / E        : boule de braise (12 mana)
  Maj                   : roulade (invulnérable un court instant)
  R                     : potion de braise     F / Entrée : interagir / dialogue
  M                     : carte du monde
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
MW, MH = 170, 130
DAY_LEN = 360.0
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
    "Il y avait un phare au sommet d'Aethel, un grand feu qu'on appelait le Brasier. Personne ne savait qui l'avait allumé. "
    "Tant qu'il brûlait, l'hiver restait de l'autre côté des montagnes et les morts restaient où on les avait mis.",
    "Quatre gardiens s'en occupaient : Sylvaine pour les forêts, Vaelith pour les marais, Karn le roi pour la pierre, Ignis pour le feu lui-même. "
    "Chacun portait un morceau du Brasier dans la poitrine, une braise. Maëlys, elle, tenait les registres. On ne l'a jamais comptée parmi les gardiens, "
    "ce qui l'a toujours un peu vexée.",
    "Karn avait aimé une tisserande de Port-Cendre, en secret, parce qu'un roi ne fait pas ça. Elle est morte en couches, un soir d'hiver. "
    "Il a demandé au Brasier de la lui rendre. Le Brasier a dit non. Karn est monté au phare avec trente hommes et une charrette de chaînes, pour discuter autrement.",
    "Personne n'a bien vu ce qui s'est passé là-haut. Le Brasier s'est éteint, voilà tout. Les gens appellent ça la Panne, comme on dirait d'une mauvaise récolte. "
    "Depuis, il neige de la cendre, les morts rentrent chez eux sans prévenir, et les quatre gardiens ne sont plus très fréquentables.",
    "Ce soir-là, à Port-Cendre, une étincelle est sortie de la cheminée et s'est posée sur un nouveau-né. La sage-femme n'a rien dit, "
    "elle a juste mis un linge dessus. L'enfant a grandi, a appris à tenir une épée à peu près droite. C'est toi.",
    "Ce matin, la cendre est arrivée jusqu'au puits du village. Maëlys t'a donné un sac, une épée et deux ou trois mensonges sur ton passé. "
    "Tu pars chercher les quatre braises. Si quelqu'un sait rallumer un phare, ça ne se trouve pas à Port-Cendre.",
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
    "Un coup d'épée au bon moment arrête les projectiles. Ça redonne même un peu de mana.",
    "Roule à travers les anneaux de projectiles : c'est fait pour ça.",
    "Les stèles rapportent de l'expérience et racontent ce qui s'est passé. Il existe une autre fin pour ceux qui les lisent toutes.",
    "Les monstres n'entrent pas dans Port-Cendre.",
    "Un gardien se réveille quand tu entres dans son arène. Fais le plein avant.",
    "Allume les foyers sur ta route : tu pourras voyager de l'un à l'autre.",
    "La nuit, il y a plus de monstres. Les coffres des camps de pillards sont les mieux garnis.",
    "Touche M pour ouvrir la carte. Les quêtes des villageois paient mieux que les sangliers.",
    "Chaque gardien vaincu te laisse une braise, et la braise te laisse un pouvoir.",
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
        if isinstance(d, dict) and d.get("version") == 2:
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
    0: dict(name="Port-Cendre", ground=(112, 98, 74), tint=(0, 0, 0, 0)),
    1: dict(name="Forêt de Sylvaine", ground=(34, 72, 42), tint=(0, 30, 10, 38)),
    2: dict(name="Marais du Gué", ground=(52, 66, 54), tint=(10, 40, 40, 48)),
    3: dict(name="Karn-la-Haute (ruines)", ground=(84, 82, 92), tint=(20, 20, 50, 42)),
    4: dict(name="Les Cendres Hautes", ground=(66, 52, 50), tint=(70, 15, 0, 52)),
    5: dict(name="Plaines de Vent-Maigre", ground=(104, 118, 64), tint=(30, 25, 0, 14)),
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
    "sanglier": dict(name="Sanglier teigneux", hp=34, spd=108, dmg=10, r=11, xp=9, col=(135, 94, 66), ranged=False, shards=(1, 3)),
    "bandit":   dict(name="Pillard", hp=36, spd=82, dmg=9, r=10, xp=11, col=(170, 125, 95), ranged=False, shards=(2, 5)),
    "frondeur": dict(name="Frondeur", hp=24, spd=66, dmg=8, r=9, xp=11, col=(195, 175, 125), ranged=True, shards=(2, 5)),
}
BIOME_KINDS = {
    1: ["loup", "loup", "errant"],
    2: ["noye", "noye", "follet"],
    3: ["creux", "creux", "archer"],
    4: ["braise", "braise", "cracheur"],
    5: ["sanglier", "bandit", "bandit", "frondeur"],
}

BOSSES = {
    1: dict(name="Sylvaine, l'Arbre-Mère", hp=380, r=26, spd=48, col=(70, 150, 80), bcol=(112, 220, 110),
            pats=["ring", "summon", "aimed", "ring"], braise="Braise Verte",
            perk="Tu récupères lentement des PV, même en plein combat.",
            last="« Ah. Il pleut. Ça faisait longtemps. Prends ma braise, gamin, et dis à quelqu'un de... non, laisse, ça ira. »"),
    2: dict(name="Vaelith la Noyée", hp=460, r=24, spd=62, col=(80, 140, 185), bcol=(110, 190, 255),
            pats=["aimed", "charge", "ring", "aimed"], braise="Braise Bleue",
            perk="Ton mana revient 50 % plus vite.",
            last="« J'ai gardé le gué jusqu'au bout. Tu peux le dire à ceux qui demanderont. Personne ne demandera, mais dis-le quand même. »"),
    3: dict(name="Karn, le Roi Creux", hp=560, r=26, spd=72, col=(150, 142, 175), bcol=(190, 150, 255),
            pats=["charge", "shock", "summon", "aimed"], braise="Braise Violette",
            perk="Tes coups font 12 % de dégâts en plus.",
            last="« Elle avait ces yeux-là. Les tiens. Je me demande si tu le sais. Prends la braise, je n'en ai plus l'usage. »"),
    4: dict(name="Ignis, Dernier Dragon de Cendre", hp=700, r=30, spd=56, col=(215, 85, 40), bcol=(255, 140, 50),
            pats=["spiral", "aimed", "ring", "charge", "shock"], braise="Braise Ardente",
            perk="Ta boule de braise frappe 35 % plus fort.",
            last="« J'ai eu chaud, longtemps. Après, il n'est resté que la rage. Fais ce que tu veux de la dernière braise, mais décide quelque chose. »"),
}

BOSS_CODEX = {
    1: ("Sylvaine, garde-forestière",
        "Avant la Panne, Sylvaine plantait un arbre par défunt qu'elle avait accompagné. Elle s'est enracinée dans sa forêt au lieu de la quitter, "
        "et la cendre a fait le reste. Les bûcherons du coin jurent qu'on l'entend encore compter."),
    2: ("Vaelith, passeuse",
        "Elle conduisait les morts de l'autre côté du marais, à la barque, sans rien demander. Quand la Panne a fermé le gué, "
        "personne n'est venu la relever. Elle a attendu dans l'eau. Les noyés, eux, font la queue."),
    3: ("Karn, roi de Karn-la-Haute",
        "Il a bâti des tours pour toucher le Brasier, et pas une fois réparé le toit de sa propre maison. Il a voulu rendre la vie à quelqu'un, "
        "ça s'est mal fini pour tout le monde. Sa couronne a été forgée par Torvald, ce qui explique le caractère de Torvald."),
    4: ("Ignis, sentinelle du phare",
        "La seule qui n'a pas quitté son poste. Quand le Brasier est mort, elle a continué à brûler à sa place, sans personne pour lui dire d'arrêter. "
        "Les gens disent dragon, parce que c'est plus facile à raconter que « une femme qui n'arrive plus à s'éteindre »."),
}

STELES = {
    0: [("Registre de Port-Cendre",
         "« Fondé par ceux qui ne voulaient pas monter au phare et ne voulaient pas rester en bas non plus. On garde un feu allumé dans chaque cuisine, "
         "par habitude. Ça ne sert à rien, mais personne ne l'éteint. »"),
        ("Mur des noms",
         "« Les gardiens, gravés par Maëlys : Sylvaine, Vaelith, Karn, Ignis. Un cinquième nom a été gratté, puis regravé en plus petit. On devine un M. »")],
    1: [("Les arbres",
         "« Un arbre par mort. C'était sa règle. Il y en a trop maintenant, et plus personne pour les compter. »"),
        ("Chiens",
         "« Les loups-cendre étaient des chiens de berger. Ils gardent encore des troupeaux qui n'existent plus. Ne les caresse pas. »"),
        ("Au pied de l'Arbre-Mère",
         "« Elle s'est plantée là le soir de la Panne, pieds nus, pour ne pas voir partir sa forêt. Elle a toujours détesté les adieux. "
         "Les racines boivent la cendre depuis. »")],
    2: [("Le gué",
         "« Avant, on laissait une pièce sur le ponton pour la passeuse. Il reste une pile de pièces et personne pour les prendre. »"),
        ("Feux-follets",
         "« Ce sont des prières. Les gens les ont dites au Brasier, il n'a pas répondu, alors elles traînent. Ne les suis pas, elles cherchent quelqu'un à qui parler. »"),
        ("Lettres",
         "« Vaelith écrivait à Karn chaque soir pour lui demander de laisser le Brasier tranquille. Les lettres sont au fond de l'eau, dans une caisse. "
         "Aucune réponse. L'encre a tenu. »")],
    3: [("Karn-la-Haute",
         "« Mille tours pour monter vers le Brasier. Le Brasier n'a jamais été en haut. Les gens de Port-Cendre le savaient, "
         "mais personne n'a demandé leur avis. »"),
        ("Le coeur du roi",
         "« Karn a offert son coeur au Brasier contre sa tisserande. Le Brasier a gardé le coeur et refusé le marché. "
         "Depuis, le roi fouille les ruines pour le retrouver. »"),
        ("La tisserande",
         "« Elle s'appelait Ysolde, elle tissait pour la cour, et elle est morte en mettant un enfant au monde, le soir même de la Panne. "
         "La page suivante du registre a été arrachée à la règle. Je reconnais l'écriture. »")],
    4: [("Ignis",
         "« Elle n'a jamais été un dragon : c'était la sentinelle du phare. Elle est restée à son poste. "
         "Personne n'est jamais venu lui dire qu'elle pouvait partir. »"),
        ("Gravé dans la roche",
         "« Quand les quatre braises seront réunies, quelqu'un devra décider si on rallume le Brasier ou si on le garde. "
         "Je ne sais pas qui a écrit ça. C'est très mal gravé. »"),
        ("Mot laissé à la forge",
         "« Le Brasier ne se prend pas. Il se donne, comme on tend une lanterne à quelqu'un qui n'y voit plus. Karn le savait, un temps. Puis il a eu peur. »")],
    5: [("Borne",
         "« Port-Cendre : 3 lieues. Quelqu'un a ajouté au couteau : « et les sangliers sont de mauvaise humeur ». »"),
        ("Ferme abandonnée",
         "« On est partis en laissant la soupe sur le feu. Si tu repasses, ne la mange pas. »"),
        ("Les pillards",
         "« Avant la Panne, les pillards n'étaient pas méchants, juste fauchés. Maintenant ils sont les deux. »")],
}
LORE_TOTAL = sum(len(v) for v in STELES.values())

RELICS = {
    "anneau":   ("Anneau de braise", "Ton mana revient presque deux fois plus vite."),
    "bottes":   ("Bottes du colporteur", "Tu cours 10 % plus vite."),
    "pointe":   ("Pointe de lance cassée", "Tes coups critiques sont deux fois plus fréquents."),
    "coeur":    ("Coeur de loup séché", "+25 PV max."),
    "pierre":   ("Pierre à aiguiser usée", "+4 dégâts."),
    "ecaille":  ("Écaille de noyé", "Tu encaisses 12 % de dégâts en moins."),
    "lanterne": ("Lanterne fêlée", "Tu y vois bien mieux la nuit."),
    "croc":     ("Croc d'alpha", "Chaque ennemi tué peut te rendre quelques PV."),
}

QUESTS = {
    "berthe": dict(title="Sangliers dans le potager", kind="sanglier", n=5, shards=30, xp=40,
                   ask=["Ah, un client ! Non ? Tant pis. Dis, tu sais te battre ? Des sangliers me dévastent le potager toutes les nuits. Cinq ou six bêtes, de très mauvaise humeur.",
                        "Débarrasse-m'en de cinq et je te paie ce que j'ai. C'est pas la fortune, mais c'est du liquide."],
                   ongoing="Alors, ces sangliers ? Il y en a un qui me regarde par la fenêtre, là.",
                   done=["Mes carottes te remercient. Moi aussi. La soupe est toujours chaude ici, par habitude."]),
    "ferme": dict(title="Les poules de Mireille", kind="bandit", n=6, shards=40, xp=50,
                  ask=["Des pillards m'ont pris douze poules. Douze ! Elles pondaient mieux que ma vache.",
                       "Si tu croises ces types, fais-leur passer l'envie. Six suffiront, je crois qu'ils ne sont pas plus."],
                  ongoing="Six pillards, pas un de moins. Je compte sur toi. Mes poules aussi.",
                  done=["Elles ne sont pas revenues, mes poules. Mais ça fait du bien de savoir qu'ils paient. Tiens."]),
    "bac": dict(title="Le bac et les frondes", kind="frondeur", n=5, shards=45, xp=55,
                ask=["Je passe les gens d'une rive à l'autre. Depuis quelques jours, des types avec des frondes s'entraînent sur mon bac. Ils visent mal, mais ils insistent.",
                     "Cinq frondeurs en moins et je te règle ça en éclats. Je ne te fais pas traverser gratis, faut pas exagérer."],
                ongoing="Il en reste. J'ai entendu un caillou rebondir sur ma cabane, pas plus tard que tout à l'heure.",
                done=["Plus de cailloux. Le bac est à toi quand tu veux, au tarif normal."]),
    "scierie": dict(title="Les loups de la scierie", kind="loup", n=8, shards=50, xp=60,
                    ask=["Les loups-cendre rôdent autour de ma scierie. Ils n'attaquent pas, ils regardent. C'est pire.",
                         "Huit de moins et je dormirai peut-être. Je sais que ce sont d'anciens chiens, mais ça n'arrange pas mes nuits."],
                    ongoing="Ils sont encore là. Je les entends respirer à travers le mur.",
                    done=["Ça fait du bien, le silence. Je ne pensais pas dire ça un jour d'une forêt."]),
    "pilotis": dict(title="Des noyés sur le ponton", kind="noye", n=6, shards=55, xp=70,
                    ask=["Les noyés montent sur mes pilotis le soir. Ils ne disent rien. Ils attendent quelque chose, et je crois que c'est moi qui fais office de relève.",
                         "Six de moins, ça me ferait du calme. Je sais que ce n'est pas très aimable de ma part."],
                    ongoing="Ils sont revenus ce soir. Ils s'alignent, ils sont polis, c'est ça qui me fatigue.",
                    done=["Merci. Je pêche en paix, enfin presque : il reste ceux que je n'ai pas vus."]),
    "guet": dict(title="Soldats creux", kind="creux", n=6, shards=65, xp=80,
                 ask=["Sergent Aude, poste de guet. Mon poste est surtout rempli de rien depuis la Panne. Sauf les Creux : anciens soldats de Karn, toujours en patrouille, toujours en retard sur les ordres.",
                      "Mets-en six à terre. Ils méritent de se reposer, et moi de dormir."],
                 ongoing="Ils défilent encore. Au pas, en plus, ça me vexe.",
                 done=["Au rapport : six soldats au repos. Tu aurais fait un bon sergent. Je te le dis sans enthousiasme."]),
    "four": dict(title="Les Cendre-Vives du four", kind="braise", n=5, shards=75, xp=90,
                 ask=["Je fais du charbon ici. Enfin, je faisais. Les Cendre-Vives viennent se réchauffer à mon four. Eux, ça va. Mon four, moins.",
                      "Cinq de moins et je pourrai rallumer proprement. Ça brûle fort, fais attention."],
                 ongoing="Elles sont toujours là. Je n'ose plus faire cuire mon pain.",
                 done=["Mon four est de nouveau à moi. Tu veux du pain ? Il est un peu noir, mais c'est le métier."]),
}

OUTPOSTS = [
    dict(b=5, name="Foyer de la Ferme-aux-Pies", quest="ferme", npc="Mireille la fermière", col=(205, 170, 110), rng=(16, 26)),
    dict(b=5, name="Foyer du Bac de Colin", quest="bac", npc="Colin le passeur", col=(120, 160, 200), rng=(24, 32)),
    dict(b=1, name="Foyer de la Scierie", quest="scierie", npc="Hubert le bûcheron", col=(150, 120, 80), rng=(40, 62)),
    dict(b=2, name="Foyer des Pilotis", quest="pilotis", npc="Roch le pêcheur", col=(110, 150, 140), rng=(40, 62)),
    dict(b=3, name="Foyer du Poste de guet", quest="guet", npc="Aude la sentinelle", col=(170, 170, 190), rng=(40, 62)),
    dict(b=4, name="Foyer du Dernier Four", quest="four", npc="Jehan le charbonnier", col=(200, 110, 70), rng=(40, 62)),
]

ASH_COL = {0: (190, 185, 180), 1: (240, 225, 130), 2: (140, 230, 180), 3: (200, 200, 225), 4: (255, 140, 60), 5: (225, 215, 150)}
ASH_VY = {0: 1.0, 1: 0.3, 2: 0.3, 3: 0.9, 4: -0.8, 5: 0.25}


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
        elif b == 5:    # rocher et buisson
            pygame.draw.ellipse(s, (70, 64, 58), (3, 12, 26, 18))
            pygame.draw.ellipse(s, (108, 102, 94), (6, 10, 20, 13))
            pygame.draw.ellipse(s, (60, 96, 46), (15, 3, 15, 13))
            pygame.draw.ellipse(s, (82, 124, 60), (18, 5, 8, 6))
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
        self.arenas = {1: (16, 14), 2: (MW - 17, 14), 3: (16, MH - 15), 4: (MW - 17, MH - 15)}
        self.biome = [[0] * MW for _ in range(MH)]
        for y in range(MH):
            for x in range(MW):
                dx = x - cx + 4 * math.sin(y * 0.23)
                dy = y - cy + 4 * math.sin(x * 0.19)
                if abs(x - cx) <= 9 and abs(y - cy) <= 7:
                    b = 0
                elif (dx / (MW * 0.2)) ** 2 + (dy / (MH * 0.2)) ** 2 < 1:
                    b = 5
                elif dx < 0 and dy < 0:
                    b = 1
                elif dx >= 0 and dy < 0:
                    b = 2
                elif dx < 0:
                    b = 3
                else:
                    b = 4
                self.biome[y][x] = b
        dens = {0: 0.0, 1: 0.43, 2: 0.41, 3: 0.39, 4: 0.41, 5: 0.34}
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
            self.clear_area(x, y, r)

        def walk(x, y, tx, ty, horiz_first):
            for o in (("h", "v") if horiz_first else ("v", "h")):
                if o == "h":
                    while x != tx:
                        x += 1 if tx > x else -1
                        clear(x, y, rnd.choice((2, 2, 3)))
                else:
                    while y != ty:
                        y += 1 if ty > y else -1
                        clear(x, y, rnd.choice((2, 2, 3)))

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
        for v in self.by_biome.values():
            v.sort()
        # emplacements des avant-postes (hameaux)
        self.op_pos, taken = [], []
        for op in OUTPOSTS:
            pos = None
            for _ in range(200):
                x, y = rnd.choice(self.by_biome[op["b"]])
                d = math.hypot(x - cx, y - cy)
                if not (op["rng"][0] <= d <= op["rng"][1]):
                    continue
                if any(math.hypot(x - ax, y - ay) < 16 for ax, ay in self.arenas.values()):
                    continue
                if any(math.hypot(x - tx, y - ty) < 22 for tx, ty in taken):
                    continue
                pos = (x, y)
                break
            if pos is None:
                pos = rnd.choice(self.by_biome[op["b"]])
            taken.append(pos)
            self.op_pos.append(pos)
            self.clear_area(pos[0], pos[1], 4)

    def clear_area(self, x, y, r):
        for yy in range(y - r, y + r + 1):
            for xx in range(x - r, x + r + 1):
                if 1 <= xx < MW - 1 and 1 <= yy < MH - 1:
                    self.solid[yy][xx] = False

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
        self.relics = set()
        self.quests, self.qprog = {}, {}
        self.spawn = None

    def xp_need(self):
        return 40 + 30 * (self.lvl - 1)


class Enemy:
    boss = False
    elite = False

    def __init__(self, kind, x, y, elite=False):
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
        self.elite = elite
        if elite:
            self.maxhp = self.hp = int(self.maxhp * 2.2)
            self.dmg = int(self.dmg * 1.3)
            self.r += 2
            self.xp *= 3
            self.shards = (self.shards[0] * 2, self.shards[1] * 3)
            self.name = d["name"] + " alpha"
            self.col = tuple(min(255, c + 40) for c in self.col)


class Boss:
    boss = True
    elite = False

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
        self.light_big = self.make_light(230)
        self.light_small = self.make_light(130)
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

    def make_light(self, R):
        s = pygame.Surface((R * 2, R * 2), pygame.SRCALPHA)
        steps = 24
        for i in range(steps):
            pygame.draw.circle(s, (0, 0, 0, int(255 * (i + 1) / steps)), (R, R), int(R * (1 - i / steps)))
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
        for b, n in ((1, 40), (2, 40), (3, 40), (4, 40), (5, 56)):
            for _ in range(n):
                s = self.random_spot(b, 400)
                if s:
                    self.enemies.append(Enemy(random.choice(BIOME_KINDS[b]), *s, elite=random.random() < 0.05))
        self.build_items()
        self.make_camps()
        self.minimap = self.make_minimap()
        self.fog = pygame.Surface((MW, MH), pygame.SRCALPHA)
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
            version=2, seed=self.seed, ts=time.time(), saved=time.strftime("%d/%m/%Y %H:%M"),
            lvl=p.lvl, nb=len(p.braises), lore=p.lore, play_time=self.play_time,
            zone=BIOMES[self.tile_biome(p.x, p.y)]["name"],
            player=dict(x=p.x, y=p.y, hp=p.hp, mp=p.mp, maxhp=p.maxhp, maxmp=p.maxmp, dmg=p.dmg, lvl=p.lvl, xp=p.xp,
                        shards=p.shards, potions=p.potions, braises=sorted(p.braises), lore=p.lore, forge=p.forge,
                        relics=sorted(p.relics), quests=p.quests, qprog=p.qprog,
                        spawn=list(p.spawn) if p.spawn else None),
            items=[dict(r=it.get("read"), s=it.get("seen"), t=it.get("truth"), o=it.get("open"), l=it.get("lit"))
                   for it in self.items],
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
        p.relics = set(pl.get("relics", []))
        p.quests = dict(pl.get("quests", {}))
        p.qprog = dict(pl.get("qprog", {}))
        sp = pl.get("spawn")
        p.spawn = tuple(sp) if sp else None
        for it, st in zip(self.items, d["items"]):
            if "read" in it:
                it["read"] = bool(st.get("r"))
            if "seen" in it:
                it["seen"] = bool(st.get("s"))
            if "open" in it:
                it["open"] = bool(st.get("o"))
            if "lit" in it:
                it["lit"] = bool(st.get("l"))
            if st.get("t"):
                it["truth"] = True
        for b in p.braises:
            self.bosses[b].hp = 0
        self.enemies = [e for e in self.enemies if e.hp > 0]
        self.explored = set(tuple(c) for c in d.get("explored", []))
        for ex, ey in self.explored:
            pygame.draw.circle(self.fog, (0, 0, 0, 0), (ex * 4 + 2, ey * 4 + 2), 8)
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
        ar = w.arenas.get(b)
        for _ in range(60):
            tx, ty = random.choice(w.by_biome[b])
            if ar and (tx - ar[0]) ** 2 + (ty - ar[1]) ** 2 < 100:
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
        self.items.append(dict(type="altar", name="Autel du Brasier", x=x, y=y))
        x, y = T(2, 1)
        self.items.append(dict(type="foyer", name="Foyer de Port-Cendre", x=x, y=y, lit=True))
        x, y = T(-5, -3)
        self.items.append(dict(
            type="npc", name="Maëlys l'Archiviste", x=x, y=y, col=(175, 140, 205), seen=False, service="rest",
            lines=["Alors c'est toi. Approche, que je te regarde. Hm. Tu as l'air tiède. C'est bon signe, vu l'époque.",
                   "Je suis Maëlys, j'écrivais les registres du phare. On m'appelle l'Archiviste, ce qui est un grand mot pour quelqu'un qui passe son temps à chercher ses lunettes.",
                   "Quatre gardiens ont chacun une braise : Sylvaine au nord-ouest, Vaelith au nord-est, Karn au sud-ouest, Ignis au sud-est. Je les ai connus. "
                   "Ne leur en veux pas trop, ils sont surtout fatigués.",
                   "Lis les stèles en chemin, elles en savent plus que moi. Il y a des foyers un peu partout : allume-les, ça te fera des raccourcis. "
                   "Et reviens ici quand tu es cassé, j'ai du thé."],
            lines2=["Tu as meilleure mine. Un peu. Tu veux te poser près du feu ? Je note où tu en es."],
            lines3=["Tu les as toutes. Alors je ne peux plus me taire.",
                    "Ta mère s'appelait Ysolde, elle tissait à Port-Cendre. Ton père était Karn. Je le sais parce que c'est moi qui t'ai mis au monde, "
                    "et que j'ai arraché une page du registre le lendemain.",
                    "Je ne voulais pas que tu cherches à lui ressembler. Ça n'a pas très bien marché : tu viens de lui prendre sa braise.",
                    "Pour le Brasier, tu décideras seul. Si tu as lu toutes les stèles, tu sais qu'il y a une troisième option. "
                    "Elle est moins spectaculaire que les deux autres."]))
        x, y = T(5, -3)
        self.items.append(dict(
            type="npc", name="Torvald le Forgeron", x=x, y=y, col=(190, 110, 70), seen=False, service="forge",
            lines=["Hmpf. Encore un gamin avec une lame émoussée. Torvald, forgeron. Je forgeais pour les gardiens, avant.",
                   "C'est moi qui ai fait la couronne de Karn. Il m'a dit que c'était pour une cérémonie. Je n'ai pas posé de questions, c'est mon seul vrai défaut.",
                   "Apporte-moi des éclats, je t'aiguise ça. Et les gardiens, ce ne sont pas des monstres. Mais ils te taperont dessus quand même."],
            lines2=["Des éclats ? Je t'écoute. Évite de mourir, ça fait mauvaise publicité."]))
        x, y = T(3, 4)
        self.items.append(dict(
            type="npc", name="Orin le Colporteur", x=x, y=y, col=(90, 170, 130), seen=False, service="shop",
            lines=["Psst ! Orin, colporteur. Potions de braise, fraîches, enfin tièdes. Je les fais avec ce qui brille encore.",
                   "Conseil gratuit : les gardiens attaquent toujours dans le même ordre. Roule dans leurs anneaux, renvoie les tirs à l'épée, et ne reste jamais planté là.",
                   "Ne me demande pas d'où vient la matière première."],
            lines2=["Une potion ? Toujours en stock. Et toujours un peu tiède."]))
        x, y = T(-3, 5)
        self.items.append(dict(type="npc", name="Berthe l'aubergiste", x=x, y=y, col=(205, 150, 120),
                               seen=False, service=None, quest="berthe"))
        for (title, text), (dx, dy) in zip(STELES[0], ((-7, 5), (8, -1))):
            x, y = T(dx, dy)
            self.items.append(dict(type="stele", title=title, x=x, y=y, text=text, read=False))
        for b in (1, 2, 3, 4, 5):
            for title, text in STELES[b]:
                s = self.random_spot(b)
                if s:
                    self.items.append(dict(type="stele", title=title, x=s[0], y=s[1], text=text, read=False))
        # avant-postes : un foyer et un villageois qui a besoin d'aide
        for op, (tx, ty) in zip(OUTPOSTS, w.op_pos):
            x, y = (tx + 0.5) * TILE, (ty + 0.5) * TILE
            self.items.append(dict(type="foyer", name=op["name"], x=x, y=y, lit=False))
            self.items.append(dict(type="npc", name=op["npc"], x=x + 60, y=y - 8, col=op["col"], seen=False,
                                   service=None, quest=op["quest"]))
        # coffres
        for b, n in ((1, 12), (2, 12), (3, 12), (4, 12), (5, 18)):
            for _ in range(n):
                s = self.random_spot(b)
                if s:
                    self.items.append(dict(type="chest", x=s[0], y=s[1], open=False, tier=b, rich=False))
        self.fires = [T(-4, 3), T(7, 1), T(-8, -5), T(8, 5)]

    def make_camps(self):
        w = self.world
        for b in (5, 5, 5, 5, 1, 1, 2, 2, 3, 3, 4, 4):
            s = self.random_spot(b, 400)
            if not s:
                continue
            w.clear_area(int(s[0] // TILE), int(s[1] // TILE), 3)
            self.fires.append(s)
            self.items.append(dict(type="chest", x=s[0] + 30, y=s[1] - 6, open=False, tier=b, rich=True))
            for i in range(5):
                a = i * 1.2566 + random.uniform(-0.3, 0.3)
                x, y = s[0] + math.cos(a) * 72, s[1] + math.sin(a) * 72
                if blocked(w, x, y, 12):
                    continue
                self.enemies.append(Enemy(random.choice(BIOME_KINDS[b]), x, y, elite=(i == 0)))

    def make_minimap(self):
        w = self.world
        s = pygame.Surface((MW, MH))
        for y in range(MH):
            for x in range(MW):
                c = BIOMES[w.biome[y][x]]["ground"]
                if w.solid[y][x]:
                    c = tuple(int(v * 0.4) for v in c)
                s.set_at((x, y), c)
        return s

    # ---------- utilitaires ----------
    def in_hub(self, e):
        return self.tile_biome(e.x, e.y) == 0

    def tile_biome(self, x, y):
        tx, ty = clamp(int(x // TILE), 0, MW - 1), clamp(int(y // TILE), 0, MH - 1)
        return self.world.biome[ty][tx]

    def darkness(self):
        ph = (self.play_time / DAY_LEN + 0.3) % 1.0
        d = 0.5 - 0.5 * math.cos(2 * math.pi * ph)
        return clamp((0.32 - d) * 2.5, 0.0, 1.0)

    def time_label(self):
        k = self.darkness()
        return "Jour" if k < 0.1 else ("Entre chien et loup" if k < 0.55 else "Nuit")

    def dmg_mul(self):
        return 1.12 if 3 in self.p.braises else 1.0

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

    def open_chest(self, it):
        p = self.p
        it["open"] = True
        rich = it["rich"]
        free = [r for r in RELICS if r not in p.relics]
        roll = random.random()
        self.burst(it["x"], it["y"], (240, 210, 100), 14)
        if free and roll < (0.55 if rich else 0.16):
            r = random.choice(free)
            p.relics.add(r)
            if r == "coeur":
                p.maxhp += 25
                p.hp += 25
            elif r == "pierre":
                p.dmg += 4
            self.gain_xp(25)
            return "Au fond du coffre : %s. %s" % (RELICS[r][0], RELICS[r][1])
        self.gain_xp(10)
        if roll < 0.45:
            n = random.randint(1, 2) + (1 if rich else 0)
            p.potions += n
            return "Quelques fioles de braise, miraculeusement intactes : +%d potion(s)." % n
        n = random.randint(8, 16) * (1 + it["tier"] // 2) * (2 if rich else 1)
        p.shards += n
        return "Un tas d'éclats mal rangés : +%d éclats." % n

    def travel(self, f):
        p = self.p
        for ox, oy in ((0, 40), (0, -40), (40, 0), (-40, 0), (0, 0)):
            if not blocked(self.world, f["x"] + ox, f["y"] + oy, p.r):
                p.x, p.y = f["x"] + ox, f["y"] + oy
                break
        self.cam = [clamp(p.x - W / 2, 0, MW * TILE - W), clamp(p.y - H / 2, 0, MH * TILE - H)]
        self.projs.clear()
        self.close_dialog()
        self.set_banner(f["name"], 2.5)
        return ""

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
        if svc == "foyer":
            opts = [(lambda: "Se reposer (soins complets + sauvegarde)", self.svc_rest)]
            for f in self.items:
                if f["type"] == "foyer" and f["lit"] and f is not self.near:
                    opts.append((lambda f=f: "Voyager : " + f["name"], lambda f=f: self.travel(f)))
            return opts
        if svc == "forge":
            return [(lambda: "Aiguiser la lame (+3 dégâts) - %d éclats" % (25 + 20 * p.forge), self.svc_forge)]
        if svc == "shop":
            return [(lambda: "Acheter une potion de braise - 20 éclats", self.svc_potion)]
        if svc.startswith("quest:"):
            qid = svc.split(":")[1]
            q, st = QUESTS[qid], p.quests.get(qid)
            if st is None:
                return [(lambda: "Accepter : %s" % q["title"], lambda: self.quest_accept(qid))]
            if st == "active" and p.qprog.get(qid, 0) >= q["n"]:
                return [(lambda: "Rendre la quête (+%d éclats)" % q["shards"], lambda: self.quest_turn(qid))]
            return []
        if svc == "altar":
            opts = [(lambda: "Rallumer le Brasier (tu y laisses ta braise, et toi avec)", lambda: self.finish(1)),
                    (lambda: "Garder les quatre braises pour toi", lambda: self.finish(2))]
            if p.lore >= LORE_TOTAL:
                opts.append((lambda: "Partager le feu entre tous  [fin véritable]", lambda: self.finish(3)))
            return opts
        return []

    def svc_rest(self):
        p, n = self.p, self.near
        p.hp, p.mp = p.maxhp, float(p.maxmp)
        p.spawn = (n["x"], n["y"] + 40) if n and n["type"] == "foyer" else None
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

    def quest_accept(self, qid):
        p = self.p
        if qid in p.quests:
            return "C'est déjà noté."
        p.quests[qid] = "active"
        p.qprog[qid] = 0
        return "Quête acceptée : %s." % QUESTS[qid]["title"]

    def quest_turn(self, qid):
        p, q = self.p, QUESTS[qid]
        if p.quests.get(qid) != "active" or p.qprog.get(qid, 0) < q["n"]:
            return "Ce n'est pas encore fini."
        p.quests[qid] = "done"
        p.shards += q["shards"]
        self.gain_xp(q["xp"])
        return "Récompense : %d éclats et %d d'expérience." % (q["shards"], q["xp"])

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
        t = it["type"]
        if t == "stele":
            lines = [it["text"]]
            if not it["read"]:
                it["read"] = True
                p.lore += 1
                self.gain_xp(15)
                lines.append("(Fragment de mémoire %d/%d - ajouté à ton Journal.)" % (p.lore, LORE_TOTAL))
            self.start_dialog("Stèle : " + it["title"], lines)
        elif t == "chest":
            if not it["open"]:
                self.start_dialog("Coffre", [self.open_chest(it)])
        elif t == "foyer":
            first = not it["lit"]
            it["lit"] = True
            if first:
                self.gain_xp(20)
                lines = ["Tu souffles sur ta braise et le foyer prend. Tu pourras revenir ici, ou t'y rendre depuis n'importe quel autre foyer allumé."]
            else:
                lines = ["Le foyer crépite tout seul. Tu peux te poser un moment ou filer vers un autre foyer."]
            self.start_dialog(it["name"], lines, "foyer")
        elif t == "npc":
            svc = it["service"]
            qid = it.get("quest")
            if qid:
                q, st = QUESTS[qid], p.quests.get(qid)
                if st == "done":
                    lines, svc = q["done"], None
                elif st == "active":
                    k = p.qprog.get(qid, 0)
                    lines = [q["ongoing"] if k < q["n"] else "Alors ? Tu as fini ? Montre un peu.",
                             "(Quête : %d/%d)" % (k, q["n"])]
                    svc = "quest:" + qid
                else:
                    lines, svc = q["ask"], "quest:" + qid
            else:
                if it.get("lines3") and len(p.braises) == 4 and not it.get("truth"):
                    lines = it["lines3"]
                    it["truth"] = True
                else:
                    lines = it["lines2"] if it["seen"] else it["lines"]
                it["seen"] = True
            self.start_dialog(it["name"], lines, svc)
        elif t == "altar":
            if len(p.braises) < 4:
                self.start_dialog("Autel du Brasier",
                                  ["Un creux de pierre noire, froid comme un puits. Quatre encoches attendent les braises.",
                                   "Braises rapportées : %d/4." % len(p.braises)])
            else:
                lines = ["Les quatre braises chauffent dans ta poitrine. L'autel les reconnaît, à sa manière, c'est-à-dire en grésillant.",
                         "Tu sais ce que tu peux faire. Ou ce que tu pourrais faire à la place."]
                if p.lore >= LORE_TOTAL:
                    lines.append("Tu as lu toutes les stèles. Il y a un troisième choix, celui dont personne n'a jamais voulu parce que c'est le plus compliqué.")
                self.start_dialog("Autel du Brasier", lines, "altar")

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
        p = self.p
        out = [BOSS_CODEX[b] for b in sorted(p.braises)]
        out += [(it["title"], it["text"]) for it in self.items if it["type"] == "stele" and it["read"]]
        for qid, st in p.quests.items():
            q = QUESTS[qid]
            if st == "active":
                out.append(("Quête : " + q["title"], "%s (%d/%d)" % (q["ask"][0], p.qprog.get(qid, 0), q["n"])))
            else:
                out.append(("Terminé : " + q["title"], q["done"][0]))
        out += [("Relique : " + RELICS[r][0], RELICS[r][1]) for r in sorted(p.relics)]
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
            elif key == K.K_m:
                self.set_state("map")
        elif s == "map":
            if key in (K.K_ESCAPE, K.K_m, K.K_RETURN, K.K_KP_ENTER):
                self.set_state("play")
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
        if "ecaille" in p.relics:
            dmg *= 0.88
        dmg = max(1, int(round(dmg)))
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
                    crit = random.random() < (0.24 if "pointe" in p.relics else 0.12)
                    dmg = p.dmg * random.uniform(0.9, 1.15) * (2 if crit else 1) * self.dmg_mul()
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
                   p.dmg * 1.7 * self.dmg_mul() * (1.35 if 4 in p.braises else 1.0), True, (255, 150, 50), 7, 1.1)

    def kill(self, e):
        p = self.p
        self.burst(e.x, e.y, e.col, 60 if e.boss else 14)
        sh = random.randint(*e.shards)
        p.shards += sh
        self.float(e.x, e.y - 20, "+%d éclats" % sh, (240, 210, 100))
        self.gain_xp(e.xp)
        for qid, st in p.quests.items():
            q = QUESTS[qid]
            if st == "active" and q["kind"] == e.kind and p.qprog.get(qid, 0) < q["n"]:
                p.qprog[qid] = p.qprog.get(qid, 0) + 1
                self.float(e.x, e.y - 46, "Quête %d/%d" % (p.qprog[qid], q["n"]), (190, 220, 255))
        if "croc" in p.relics and random.random() < 0.3:
            p.hp = min(p.maxhp, p.hp + 4)
            self.float(p.x, p.y - 36, "+4 PV", (120, 255, 140))
        if e.boss:
            d = BOSSES[e.biome]
            p.braises.add(e.biome)
            self.shake = 12
            lines = [d["last"], "Tu obtiens la %s ! (%d/4)  Effet : %s" % (d["braise"], len(p.braises), d["perk"])]
            if len(p.braises) == 4:
                lines.append("Les quatre braises chauffent dans ta poitrine. Retourne à l'autel de Port-Cendre.")
            self.start_dialog(d["name"], lines)
            self.autosave()
        elif random.random() < (0.45 if e.elite else 0.10):
            p.potions += 1
            self.float(e.x, e.y - 34, "Potion !", (255, 150, 150))

    def respawn(self):
        p, w = self.p, self.world
        p.hp, p.mp = p.maxhp, float(p.maxmp)
        p.shards //= 2
        p.x, p.y = p.spawn or ((w.cx + 0.5) * TILE, (w.cy + 2.5) * TILE)
        p.inv = 1.5
        self.projs.clear()
        for bo in self.bosses.values():
            if bo.hp > 0:
                bo.reset()
        self.state = "play"
        self.set_banner("Ta braise bat encore...", 2.5)

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
        mreg = 5 * (1.8 if "anneau" in p.relics else 1.0) * (1.5 if 2 in p.braises else 1.0)
        p.mp = min(p.maxmp, p.mp + mreg * dt)
        if 1 in p.braises and p.hp < p.maxhp:
            p.hp = min(p.maxhp, p.hp + 0.6 * dt)
        self.shake = max(0.0, self.shake - 30 * dt)
        self.banner_t = max(0.0, self.banner_t - dt)

        # déplacement
        if p.roll_t > 0:
            p.roll_t -= dt
            move_entity(w, p, p.roll_dir[0] * 390 * dt, p.roll_dir[1] * 390 * dt)
        else:
            ax, ay = self.move_vec()
            sp = p.speed * (1.1 if "bottes" in p.relics else 1.0)
            move_entity(w, p, ax * sp * dt, ay * sp * dt)
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
        # brouillard de la carte
        pygame.draw.circle(self.fog, (0, 0, 0, 0), (int(p.x / TILE), int(p.y / TILE)), 8)
        self.explored.add((int(p.x // TILE) // 4, int(p.y // TILE) // 4))

        # ennemis
        near = [e for e in self.enemies if not e.boss and abs(e.x - p.x) < 700 and abs(e.y - p.y) < 560]
        near_ids = {id(e) for e in near}
        for e in self.enemies:
            if e.boss:
                self.update_boss(e, dt)
            elif id(e) in near_ids:
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
        # réapparitions (plus fréquentes la nuit)
        self.spawn_t -= dt
        if self.spawn_t <= 0:
            self.spawn_t = 5.0 - 2.5 * self.darkness()
            if sum(1 for e in self.enemies if not e.boss) < 300:
                b = random.choice((1, 2, 3, 4, 5, 5))
                s = self.random_spot(b, 420)
                if s:
                    self.enemies.append(Enemy(random.choice(BIOME_KINDS[b]), *s, elite=random.random() < 0.05))
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
            if it["type"] == "chest" and it["open"]:
                continue
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
        elif s == "map":
            self.draw_map()
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
            elif it["type"] == "foyer":
                self.draw_foyer(it, sx, sy)
            elif it["type"] == "chest":
                self.draw_chest(it, sx, sy)
            else:
                pygame.draw.circle(screen, it["col"], (sx, sy), 12)
                pygame.draw.circle(screen, (30, 20, 30), (sx, sy), 12, 2)
                pygame.draw.circle(screen, (235, 215, 190), (sx, sy - 3), 5)
                q = it.get("quest")
                if q and self.p.quests.get(q) is None:
                    draw_text("!", F_B, (255, 230, 100), (sx, sy - 44), center=True)
                elif q and self.p.quests.get(q) == "active" and self.p.qprog.get(q, 0) >= QUESTS[q]["n"]:
                    draw_text("?", F_B, (120, 255, 160), (sx, sy - 44), center=True)
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
            draw_text("F : ouvrir" if it["type"] == "chest" else "F : interagir", F_S, (255, 230, 150),
                      (int(it["x"] - ox), int(it["y"] - oy) - 46), center=True)

        # ambiance
        z = self.tile_biome(p.x, p.y)
        tint = BIOMES[z]["tint"]
        if tint[3]:
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill(tint)
            screen.blit(ov, (0, 0))
        dark = self.darkness()
        if dark > 0.02:
            lf = 0.65 if "lanterne" in p.relics else 1.0
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            ov.fill((4, 6, 28, int(170 * dark * lf)))
            ov.blit(self.light_big, (int(p.x - ox) - 230, int(p.y - oy) - 230), special_flags=pygame.BLEND_RGBA_SUB)
            srcs = list(self.fires) + [(it["x"], it["y"]) for it in self.items if it["type"] == "foyer" and it["lit"]]
            for fx, fy in srcs:
                sx, sy = int(fx - ox), int(fy - oy)
                if -140 < sx < W + 140 and -140 < sy < H + 140:
                    ov.blit(self.light_small, (sx - 130, sy - 130), special_flags=pygame.BLEND_RGBA_SUB)
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

    def draw_foyer(self, it, sx, sy):
        pygame.draw.circle(screen, (58, 54, 60), (sx, sy + 2), 17)
        pygame.draw.circle(screen, (30, 26, 30), (sx, sy + 2), 12)
        if it["lit"]:
            fl = 8 + math.sin(self.t * 9 + sx) * 2
            pygame.draw.circle(screen, (230, 100, 30), (sx, sy - 2), int(fl))
            pygame.draw.circle(screen, (255, 215, 100), (sx, sy - 3), int(fl * 0.55))
        else:
            pygame.draw.line(screen, (90, 70, 55), (sx - 8, sy + 3), (sx + 8, sy - 3), 3)
            pygame.draw.line(screen, (90, 70, 55), (sx - 8, sy - 3), (sx + 8, sy + 3), 3)
        draw_text(it["name"], F_S, (235, 225, 200) if it["lit"] else (150, 145, 135), (sx, sy - 34), center=True)

    def draw_chest(self, it, sx, sy):
        pygame.draw.rect(screen, (70, 52, 34) if it["open"] else (120, 82, 44), (sx - 11, sy - 6, 22, 14), border_radius=2)
        pygame.draw.rect(screen, (30, 20, 12), (sx - 11, sy - 6, 22, 14), 2, border_radius=2)
        if it["open"]:
            pygame.draw.rect(screen, (40, 28, 18), (sx - 11, sy - 13, 22, 6), border_radius=2)
        else:
            pygame.draw.rect(screen, (150, 100, 55), (sx - 11, sy - 12, 22, 7), border_radius=3)
            pygame.draw.rect(screen, (225, 190, 90) if it["rich"] else (180, 160, 110), (sx - 3, sy - 4, 6, 6))

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
        if e.elite:
            pygame.draw.circle(screen, (255, 215, 90), (sx, sy), e.r + 6, 2)
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
        ty = 176
        for qid, st in p.quests.items():
            if st == "active":
                q = QUESTS[qid]
                k = p.qprog.get(qid, 0)
                draw_text("%s  %d/%d" % (q["title"], k, q["n"]), F_S,
                          (190, 220, 255) if k < q["n"] else (150, 255, 170), (14, ty))
                ty += 18
        if p.relics:
            draw_text("Reliques : %d/%d" % (len(p.relics), len(RELICS)), F_S, (230, 200, 255), (14, ty))
        # boss
        for b in self.bosses.values():
            if b.active and b.hp > 0:
                draw_text(b.name, F_M, (255, 220, 170), (W // 2, 16), center=True)
                draw_bar(W // 2 - 220, 30, 440, 14, b.hp / b.maxhp, tuple(b.bcol))
                break
        # minicarte
        VW, VH, S = 64, 48, 3
        ox0, oy0 = int(p.x // TILE) - VW // 2, int(p.y // TILE) - VH // 2
        mm = self.minimap.copy()
        mm.blit(self.fog, (0, 0))
        view = pygame.Surface((VW, VH))
        view.fill((6, 5, 8))
        view.blit(mm, (-ox0, -oy0))
        view = pygame.transform.scale(view, (VW * S, VH * S))
        mx0, my0 = W - VW * S - 12, 12
        screen.blit(view, (mx0, my0))

        def mpos(wx, wy):
            return mx0 + int((wx / TILE - ox0) * S), my0 + int((wy / TILE - oy0) * S)

        def revealed(wx, wy):
            return self.fog.get_at((clamp(int(wx // TILE), 0, MW - 1), clamp(int(wy // TILE), 0, MH - 1)))[3] == 0

        def inside(qx, qy):
            return mx0 < qx < mx0 + VW * S and my0 < qy < my0 + VH * S

        for b in self.bosses.values():
            if b.hp > 0 and revealed(*b.home):
                qx, qy = mpos(*b.home)
                if inside(qx, qy):
                    pygame.draw.circle(screen, (255, 60, 50), (qx, qy), 4)
        for it in self.items:
            if it["type"] == "foyer" and it["lit"]:
                qx, qy = mpos(it["x"], it["y"])
                if inside(qx, qy):
                    pygame.draw.rect(screen, (255, 170, 60), (qx - 2, qy - 2, 5, 5))
        pygame.draw.circle(screen, (255, 255, 255), mpos(p.x, p.y), 3)
        pygame.draw.rect(screen, (225, 205, 165), (mx0, my0, VW * S, VH * S), 1)
        draw_text(self.time_label(), F_S, (220, 215, 200), (mx0 + VW * S // 2, my0 + VH * S + 12), center=True)
        # bandeau de zone
        if self.banner_t > 0:
            draw_text(self.banner_text, F_L, (255, 225, 160), (W // 2, 110), center=True,
                      alpha=int(255 * clamp(self.banner_t, 0, 1)))
        if self.play_time < 14 and self.state == "play":
            draw_text("ZQSD : bouger | Souris : viser | Clic G : frapper | Clic D : braise | Maj : roulade | R : potion | F : parler | M : carte",
                      F_S, (220, 215, 200), (W // 2, H - 18), center=True,
                      alpha=int(255 * clamp((14 - self.play_time) / 2, 0, 1)))

    def draw_dialog(self):
        d = self.dlg
        h = 252
        if d["menu"]:
            h = max(252, 44 + 72 + 4 + 26 * (len(d["opts"]) + 1) + 40)
        box = pygame.Rect(40, H - 20 - h, W - 80, h)
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
            draw_text("La cendre te recouvre. Mais ta braise bat encore.", F_M, (230, 215, 200), (W // 2, H // 2 + 10), center=True)
        if self.dead_t > 1.0:
            draw_text("Entrée : renaître au dernier foyer (la moitié de tes éclats est perdue)", F_S, (200, 195, 185),
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
        draw_text("Le phare s'est éteint. Quelqu'un doit aller voir.", F_M, (190, 180, 165), (W // 2, 205), center=True)
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

    def draw_map(self):
        p = self.p
        screen.fill((10, 8, 12))
        S = 4
        mm = self.minimap.copy()
        mm.blit(self.fog, (0, 0))
        mm = pygame.transform.scale(mm, (MW * S, MH * S))
        x0, y0 = (W - MW * S) // 2, 66
        screen.blit(mm, (x0, y0))
        pygame.draw.rect(screen, (225, 205, 165), (x0, y0, MW * S, MH * S), 2)

        def pos(wx, wy):
            return x0 + int(wx / TILE * S), y0 + int(wy / TILE * S)

        def revealed(wx, wy):
            return self.fog.get_at((clamp(int(wx // TILE), 0, MW - 1), clamp(int(wy // TILE), 0, MH - 1)))[3] == 0

        for b in self.bosses.values():
            if b.hp > 0 and revealed(*b.home):
                pygame.draw.circle(screen, (255, 60, 50), pos(*b.home), 6)
                draw_text(b.name.split(",")[0], F_S, (255, 190, 170), (pos(*b.home)[0], pos(*b.home)[1] - 16), center=True)
        for it in self.items:
            if it["type"] == "foyer" and it["lit"]:
                qx, qy = pos(it["x"], it["y"])
                pygame.draw.rect(screen, (255, 170, 60), (qx - 3, qy - 3, 7, 7))
        qx, qy = pos(p.x, p.y)
        pygame.draw.circle(screen, (255, 255, 255), (qx, qy), 5)
        pygame.draw.circle(screen, (0, 0, 0), (qx, qy), 5, 1)
        draw_text("Carte d'Aethel", F_L, (255, 225, 160), (W // 2, 34), center=True)
        draw_text("Blanc : toi   |   Orange : foyers allumés   |   Rouge : gardiens repérés   |   Échap / M : fermer",
                  F_S, (150, 145, 135), (W // 2, H - 22), center=True)

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
            draw_text("Rien pour l'instant. Lis les stèles, aide les gens, vaincs les gardiens.", F_M, (190, 185, 170),
                      (W // 2, H // 2), center=True)
        else:
            self.journal_sel = clamp(self.journal_sel, 0, len(ents) - 1)
            first = max(0, min(self.journal_sel - 8, len(ents) - 10))
            for i in range(first, min(len(ents), first + 10)):
                yy = 90 + (i - first) * 42
                sel = i == self.journal_sel
                if sel:
                    pygame.draw.rect(screen, (60, 34, 24), (30, yy - 4, 330, 34), border_radius=6)
                draw_text(ents[i][0][:38], F_S, (255, 225, 150) if sel else (200, 192, 178), (42, yy + 3))
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
            title = "FIN : LE BRASIER"
            txt = ("Tu poses les quatre braises dans les encoches, puis la tienne par-dessus. Le Brasier reprend d'un coup, ça sent le pain brûlé. "
                   "Tu ne t'en relèves pas, mais tu ne sens plus rien non plus, ce qui est une sorte de compensation. La cendre redevient de la pluie, "
                   "les morts retournent où on les avait mis. À Port-Cendre, on a donné ton nom à une lanterne, puis à l'auberge, puis à une rue qui ne mène nulle part.")
        elif n == 2:
            title = "FIN : LA COURONNE DE CENDRE"
            txt = ("Tu refermes la main sur les quatre braises et tu gardes tout. Ça brûle, c'est puissant, et le Brasier reste éteint. "
                   "Les ombres s'inclinent sur ton passage. Tu règnes sur un monde froid où plus personne ne te contredit, ce qui finit par se remarquer. "
                   "Un soir, tu te surprends à parler à une chaise. Tu comprends un peu mieux Karn.")
        else:
            title = "FIN VÉRITABLE : LE FOYER"
            txt = ("Tu ne rallumes pas le Brasier et tu ne le gardes pas : tu le partages. Maëlys, Torvald, Orin, Berthe, les gosses du village, "
                   "chacun pose une main sur l'autel. Le feu se coupe en mille petits morceaux, un par cuisine d'Aethel. Plus de phare, plus de roi, "
                   "plus personne pour grimper là-haut avec des chaînes. Sylvaine, Vaelith, Karn et Ignis peuvent enfin dormir. "
                   "Ils auraient dû demander de l'aide plus tôt, mais ça, on le dit à tout le monde.")
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
