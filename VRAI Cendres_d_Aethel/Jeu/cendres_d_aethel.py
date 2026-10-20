#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CENDRES D'AETHEL - un action-RPG en pygame (fichier unique, aucun asset externe)
Édition ULTRA HARD : 3 difficultés, quête à suivre, 3 langues (FR / EN / ES),
options (chrono, quête, langue...), statistiques de partie et 3 fins.

Installation :  pip install pygame
Lancement    :  python cendres_d_aethel.py

COMMANDES
  ZQSD / WASD / Flèches : se déplacer         Souris : viser
  Clic gauche / Espace  : coup d'épée (pare les projectiles !)
  Clic droit / E        : boule de braise (12 mana)
  Maj                   : roulade (invulnérable un court instant)
  R                     : potion de braise     F / Entrée : interagir / dialogue
  Tab                   : afficher / masquer le suivi de quête
  Échap : pause / menu / sauvegarde   F11 : plein écran <-> fenêtre
  Menu principal : L = changer de langue
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "sauvegardes")
SETTINGS_FILE = os.path.join(SAVE_DIR, "reglages.json")

LANGS = [("fr", "Français"), ("en", "English"), ("es", "Español")]
DIFF_ORDER = ["normal", "hard", "ultra"]
DEFAULT_SETTINGS = dict(lang="fr", timer=True, quest=True, shake=True, fullscreen=True, diff="ultra", best={})

# Réglages de difficulté. "ultra" = le mode voulu : ennemis x2, tirs rapides et denses, soins rares.
DIFFS = {
    "normal": dict(ehp=1.0, edmg=1.0, espd=1.0, bhp=1.0, bdmg=1.0, bspd=1.0, pspd=1.0, cd=1.0, wind=0.7, bul=0,
                   heal=45, inv=0.7, drop=0.10, lose=0.50, rage=0.50, aggro=1.0, xp=1.0, mp=1.0,
                   spawn=5.0, cap=70, potions=2, pcost=20),
    "hard": dict(ehp=1.4, edmg=1.4, espd=1.05, bhp=1.5, bdmg=1.4, bspd=1.1, pspd=1.1, cd=0.85, wind=0.6, bul=4,
                 heal=40, inv=0.6, drop=0.08, lose=0.60, rage=0.60, aggro=1.15, xp=1.15, mp=0.9,
                 spawn=4.0, cap=80, potions=2, pcost=25),
    "ultra": dict(ehp=2.0, edmg=2.0, espd=1.12, bhp=2.2, bdmg=1.8, bspd=1.2, pspd=1.25, cd=0.7, wind=0.5, bul=6,
                  heal=30, inv=0.5, drop=0.05, lose=0.75, rage=0.70, aggro=1.3, xp=1.3, mp=0.8,
                  spawn=3.0, cap=95, potions=1, pcost=35),
}
DIFF = dict(DIFFS["ultra"])  # difficulté active (modifiée sur place au début de chaque partie)

STAT_KEYS = ["kills", "deaths", "hits_taken", "dmg_taken", "dmg_dealt", "swings", "swing_hits", "spells",
             "spell_hits", "parries", "rolls", "potions", "shards", "crits", "best_nohit"]


# --------------------------------------------------------------------------
#  RÉGLAGES (langue, chrono, quête...) - sauvegardés dans sauvegardes/reglages.json
# --------------------------------------------------------------------------
def load_settings():
    s = json.loads(json.dumps(DEFAULT_SETTINGS))
    try:
        with io.open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict):
            for k, v in s.items():
                if k in d and type(d[k]) is type(v):
                    s[k] = d[k]
    except (OSError, ValueError):
        pass
    if s["lang"] not in dict(LANGS):
        s["lang"] = "fr"
    if s["diff"] not in DIFF_ORDER:
        s["diff"] = "ultra"
    return s


SET = load_settings()


def save_settings():
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        tmp = SETTINGS_FILE + ".tmp"
        with io.open(tmp, "w", encoding="utf-8") as f:
            json.dump(SET, f, ensure_ascii=False)
        os.replace(tmp, SETTINGS_FILE)
    except OSError:
        pass


try:
    screen = pygame.display.set_mode((W, H), pygame.SCALED | (pygame.FULLSCREEN if SET["fullscreen"] else 0))
except pygame.error:
    screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Cendres d'Aethel")
clock = pygame.time.Clock()


# --------------------------------------------------------------------------
#  TEXTES DE L'INTERFACE (FR / EN / ES)
# --------------------------------------------------------------------------
UI = {}
UI["fr"] = dict(
    m_new="Nouvelle partie", m_continue="Continuer", m_load="Charger une partie", m_options="Options",
    m_credits="Crédits", m_quit="Quitter", m_resume="Reprendre", m_save="Sauvegarder", m_journal="Journal",
    m_stats="Statistiques", m_menu="Retour au menu principal", back="Retour", pause="PAUSE",
    subtitle="Un conte de feu, de cendre et de choix", by="par WILOOPE",
    main_hint="Flèches / ZQSD + Entrée, ou souris   |   L : langue   |   F11 : plein écran",
    opt_title="Options", opt_lang="Langue", opt_timer="Afficher le chrono", opt_quest="Afficher la quête",
    opt_shake="Tremblement d'écran", opt_full="Plein écran", on="Activé", off="Désactivé",
    opt_hint="Haut/Bas : choisir   |   Gauche/Droite ou Entrée : changer   |   Échap : retour",
    opt_diff_note="La difficulté se choisit au lancement d'une nouvelle partie.",
    diff_title="Choisis ta difficulté", diff_normal="Normal", diff_hard="Difficile", diff_ultra="ULTRA HARD",
    diff_normal_d="L'aventure telle qu'elle a été pensée : exigeante, mais juste.",
    diff_hard_d="Ennemis plus solides et plus violents, Gardiens plus agressifs, soins réduits, mort plus coûteuse.",
    diff_ultra_d="Pour les masochistes : ennemis 2 fois plus solides et plus mortels, tirs rapides et denses, "
                 "Gardiens enragés dès 70 % de vie, soins rares, la mort te coûte 75 % de tes éclats.",
    diff_hint="Haut/Bas : choisir   |   Entrée : commencer   |   Échap : retour",
    diff_best="Meilleur temps : %s",
    slots_load="Charger une partie", slots_save="Sauvegarder la partie", slot_auto="Sauvegarde automatique",
    slot_1="Emplacement 1", slot_2="Emplacement 2", slot_3="Emplacement 3", slot_empty="- vide -",
    slot_info="Niv. %d   |   Braises %d/4   |   Fragments %d/%d   |   %d min",
    slot_hint="Entrée : valider   |   Échap : retour   |   Suppr : supprimer une sauvegarde",
    slot_deleted="Sauvegarde supprimée.", slot_confirm="Appuie encore sur Suppr pour confirmer la suppression.",
    slot_saved="Sauvegardé dans : %s.", slot_fail="Impossible d'écrire la sauvegarde.",
    slot_empty_msg="Cet emplacement est vide.",
    toast_autosave="Sauvegarde automatique.", toast_saved="Partie sauvegardée.", toast_savefail="Échec de la sauvegarde.",
    toast_unreadable="Sauvegarde illisible.", toast_corrupt="Sauvegarde corrompue.",
    cr_by="Un jeu de", cr_concept="Concept & game design", cr_lore="Univers, lore & écriture",
    cr_prog="Programmation", cr_art="Direction artistique", cr_level="Level design & équilibrage",
    cr_made="Réalisé avec Python & pygame", cr_thanks="Merci d'avoir joué.", cr_back="Échap : retour",
    jr_title="Journal", jr_empty="Rien pour l'instant. Lis les stèles et vaincs les Gardiens.",
    jr_hint="Haut/Bas : parcourir   |   Échap : retour",
    intro_hint="Entrée : continuer   |   Échap : passer le prologue",
    loading="Chargement...  %d %%",
    hud_hp="PV %d/%d", hud_lvl="Niv. %d", hud_shards="Éclats : %d", hud_potions="Potions (R) : %d",
    hud_dmg="Dégâts : %d",
    help1="ZQSD : bouger | Souris : viser | Clic G / Espace : frapper | Clic D / E : boule de braise | Maj : roulade",
    help2="R : potion | F : interagir | Tab : quête | Échap : pause | F11 : plein écran",
    interact="F : interagir",
    float_hp="+%d PV", parry="Parade !", level_up="Niveau %d !", float_shards="+%d éclats", float_potion="Potion !",
    respawn_banner="Ta Braise bat encore...",
    dead_title="TU T'ÉTEINS...", dead_sub="La Cendre te recouvre. Mais ta Braise bat encore.",
    dead_hint="Entrée : renaître à Port-Cendre (tu perds %d %% de tes éclats)",
    dlg_hint_menu="Haut/Bas : choisir | Entrée : valider", dlg_hint_next="F / Entrée : continuer", dlg_leave="Partir",
    stele_prefix="Stèle : %s", stele_fragment="(Fragment de mémoire %d/%d - ajouté à ton Journal.)",
    altar_name="Autel de la Flamme",
    altar_empty1="Un cratère de pierre noire, froid comme une tombe. Quatre creux y attendent chacun une Braise.",
    altar_empty2="Braises rapportées : %d/4.",
    altar_ready1="Les quatre Braises vibrent dans ta poitrine. L'autel s'éclaire faiblement, comme s'il te reconnaissait.",
    altar_ready2="Tu sais ce que tu dois faire... ou ce que tu pourrais faire à la place.",
    altar_lore="Les %d fragments de mémoire résonnent en toi : une troisième voie, que Karn n'a jamais vue, s'ouvre devant toi.",
    opt_end1="Rallumer la Flamme (lui donner ton coeur)", opt_end2="Garder les Braises pour toi",
    opt_end3="Partager la Flamme avec tous  [fin véritable]",
    svc_rest_opt="Se reposer près du feu (soins complets + sauvegarde)",
    svc_rest_msg="Le feu te réchauffe. Tes forces reviennent. (Partie sauvegardée)",
    svc_forge_opt="Aiguiser la lame (+3 dégâts) - %d éclats", svc_forge_msg="Torvald aiguise ta lame. Dégâts : %d.",
    svc_shop_opt="Acheter une potion de braise - %d éclats", svc_shop_msg="Tu as maintenant %d potion(s).",
    svc_nomoney="Pas assez d'éclats.",
    braise_got="Tu obtiens la %s ! (%d/4)",
    braises_all="Les quatre Braises vibrent dans ta poitrine. Retourne à l'autel de Port-Cendre.",
    q_main="QUÊTE PRINCIPALE", q_side="QUÊTE SECONDAIRE", q_updated="Quête mise à jour",
    q0_t="Retrouver Maëlys", q0_d="Parle à Maëlys l'Archiviste, près de l'autel de Port-Cendre.",
    q1_t="Les quatre Braises", q1_d="Vaincs les quatre Gardiens et rapporte leurs Braises : %d/4.",
    q2_t="Rallumer la Flamme",
    q2_d="Retourne à l'autel de Port-Cendre avec les quatre Braises et décide du sort d'Aethel.",
    qs_t="Mémoire d'Aethel", qs_d="Lis toutes les stèles : %d/%d.",
    qs_done="Toutes les stèles sont lues. Une fin secrète t'attend à l'autel.",
    dir_1="nord-ouest", dir_2="nord-est", dir_3="sud-ouest", dir_4="sud-est",
    st_title="Statistiques", st_time="Temps de jeu", st_diff="Difficulté", st_level="Niveau",
    st_kills="Monstres vaincus", st_bosses="Gardiens vaincus", st_deaths="Morts", st_hits="Fois touché",
    st_dmg_taken="Dégâts subis", st_dmg_dealt="Dégâts infligés", st_nohit="Meilleure série sans être touché",
    st_swings="Coups d'épée (précision)", st_spells="Boules de braise (précision)",
    st_parries="Projectiles parés", st_rolls="Roulades", st_potions="Potions bues", st_shards="Éclats ramassés",
    st_lore="Fragments de mémoire", st_crits="Coups critiques",
    st_record="Record (%s) : %s", st_newrecord="Nouveau record !", st_hint="Échap : retour",
    end_hint="Entrée : voir les statistiques", end_hint2="Entrée : retour au menu",
    end_stats_title="Bilan de ta partie",
    end_summary="Niveau %d  |  Fragments de mémoire : %d/%d  |  Temps : %s", end_by="Un jeu de WILOOPE",
)

UI["en"] = dict(
    m_new="New game", m_continue="Continue", m_load="Load game", m_options="Options",
    m_credits="Credits", m_quit="Quit", m_resume="Resume", m_save="Save", m_journal="Journal",
    m_stats="Statistics", m_menu="Back to main menu", back="Back", pause="PAUSED",
    subtitle="A tale of fire, ash and choice", by="by WILOOPE",
    main_hint="Arrows / WASD + Enter, or mouse   |   L: language   |   F11: fullscreen",
    opt_title="Options", opt_lang="Language", opt_timer="Show timer", opt_quest="Show quest tracker",
    opt_shake="Screen shake", opt_full="Fullscreen", on="On", off="Off",
    opt_hint="Up/Down: select   |   Left/Right or Enter: change   |   Esc: back",
    opt_diff_note="Difficulty is chosen when you start a new game.",
    diff_title="Choose your difficulty", diff_normal="Normal", diff_hard="Hard", diff_ultra="ULTRA HARD",
    diff_normal_d="The adventure as intended: demanding, but fair.",
    diff_hard_d="Tougher, harder-hitting enemies, more aggressive Guardians, reduced healing, costlier death.",
    diff_ultra_d="For masochists: enemies twice as tough and deadly, fast and dense projectiles, "
                 "Guardians enrage at 70% health, scarce healing, and death costs you 75% of your shards.",
    diff_hint="Up/Down: select   |   Enter: start   |   Esc: back",
    diff_best="Best time: %s",
    slots_load="Load game", slots_save="Save game", slot_auto="Autosave",
    slot_1="Slot 1", slot_2="Slot 2", slot_3="Slot 3", slot_empty="- empty -",
    slot_info="Lv. %d   |   Embers %d/4   |   Fragments %d/%d   |   %d min",
    slot_hint="Enter: confirm   |   Esc: back   |   Del: delete a save",
    slot_deleted="Save deleted.", slot_confirm="Press Del again to confirm deletion.",
    slot_saved="Saved to: %s.", slot_fail="Unable to write the save file.",
    slot_empty_msg="This slot is empty.",
    toast_autosave="Autosaved.", toast_saved="Game saved.", toast_savefail="Save failed.",
    toast_unreadable="Unreadable save file.", toast_corrupt="Corrupted save file.",
    cr_by="A game by", cr_concept="Concept & game design", cr_lore="World, lore & writing",
    cr_prog="Programming", cr_art="Art direction", cr_level="Level design & balancing",
    cr_made="Made with Python & pygame", cr_thanks="Thanks for playing.", cr_back="Esc: back",
    jr_title="Journal", jr_empty="Nothing yet. Read the steles and defeat the Guardians.",
    jr_hint="Up/Down: browse   |   Esc: back",
    intro_hint="Enter: continue   |   Esc: skip the prologue",
    loading="Loading...  %d %%",
    hud_hp="HP %d/%d", hud_lvl="Lv. %d", hud_shards="Shards: %d", hud_potions="Potions (R): %d",
    hud_dmg="Damage: %d",
    help1="WASD: move | Mouse: aim | Left click / Space: strike | Right click / E: ember bolt | Shift: roll",
    help2="R: potion | F: interact | Tab: quest | Esc: pause | F11: fullscreen",
    interact="F: interact",
    float_hp="+%d HP", parry="Parry!", level_up="Level %d!", float_shards="+%d shards", float_potion="Potion!",
    respawn_banner="Your Ember still beats...",
    dead_title="YOU FADE...", dead_sub="The Ash covers you. But your Ember still beats.",
    dead_hint="Enter: be reborn in Port-Cendre (you lose %d %% of your shards)",
    dlg_hint_menu="Up/Down: select | Enter: confirm", dlg_hint_next="F / Enter: continue", dlg_leave="Leave",
    stele_prefix="Stele: %s", stele_fragment="(Memory fragment %d/%d - added to your Journal.)",
    altar_name="Altar of the Flame",
    altar_empty1="A crater of black stone, cold as a tomb. Four hollows each wait for an Ember.",
    altar_empty2="Embers brought back: %d/4.",
    altar_ready1="The four Embers tremble in your chest. The altar glows faintly, as if it recognized you.",
    altar_ready2="You know what you must do... or what you could do instead.",
    altar_lore="The %d memory fragments echo within you: a third path, one Karn never saw, opens before you.",
    opt_end1="Rekindle the Flame (give it your heart)", opt_end2="Keep the Embers for yourself",
    opt_end3="Share the Flame with everyone  [true ending]",
    svc_rest_opt="Rest by the fire (full heal + save)",
    svc_rest_msg="The fire warms you. Your strength returns. (Game saved)",
    svc_forge_opt="Sharpen the blade (+3 damage) - %d shards", svc_forge_msg="Torvald sharpens your blade. Damage: %d.",
    svc_shop_opt="Buy an ember potion - %d shards", svc_shop_msg="You now have %d potion(s).",
    svc_nomoney="Not enough shards.",
    braise_got="You obtain the %s! (%d/4)",
    braises_all="The four Embers tremble in your chest. Return to the altar of Port-Cendre.",
    q_main="MAIN QUEST", q_side="SIDE QUEST", q_updated="Quest updated",
    q0_t="Find Maëlys", q0_d="Speak to Maëlys the Archivist, near the altar of Port-Cendre.",
    q1_t="The Four Embers", q1_d="Defeat the four Guardians and bring back their Embers: %d/4.",
    q2_t="Rekindle the Flame",
    q2_d="Return to the altar of Port-Cendre with the four Embers and decide Aethel's fate.",
    qs_t="Memory of Aethel", qs_d="Read every stele: %d/%d.",
    qs_done="Every stele has been read. A secret ending awaits at the altar.",
    dir_1="north-west", dir_2="north-east", dir_3="south-west", dir_4="south-east",
    st_title="Statistics", st_time="Play time", st_diff="Difficulty", st_level="Level",
    st_kills="Monsters slain", st_bosses="Guardians defeated", st_deaths="Deaths", st_hits="Times hit",
    st_dmg_taken="Damage taken", st_dmg_dealt="Damage dealt", st_nohit="Longest hit-free streak",
    st_swings="Sword swings (accuracy)", st_spells="Ember bolts (accuracy)",
    st_parries="Projectiles parried", st_rolls="Rolls", st_potions="Potions drunk", st_shards="Shards collected",
    st_lore="Memory fragments", st_crits="Critical hits",
    st_record="Best time (%s): %s", st_newrecord="New record!", st_hint="Esc: back",
    end_hint="Enter: view statistics", end_hint2="Enter: back to menu",
    end_stats_title="Your run",
    end_summary="Level %d  |  Memory fragments: %d/%d  |  Time: %s", end_by="A game by WILOOPE",
)

UI["es"] = dict(
    m_new="Nueva partida", m_continue="Continuar", m_load="Cargar partida", m_options="Opciones",
    m_credits="Créditos", m_quit="Salir", m_resume="Reanudar", m_save="Guardar", m_journal="Diario",
    m_stats="Estadísticas", m_menu="Volver al menú principal", back="Volver", pause="PAUSA",
    subtitle="Un cuento de fuego, ceniza y elección", by="por WILOOPE",
    main_hint="Flechas / WASD + Enter, o ratón   |   L: idioma   |   F11: pantalla completa",
    opt_title="Opciones", opt_lang="Idioma", opt_timer="Mostrar cronómetro", opt_quest="Mostrar misión",
    opt_shake="Temblor de pantalla", opt_full="Pantalla completa", on="Activado", off="Desactivado",
    opt_hint="Arriba/Abajo: elegir   |   Izquierda/Derecha o Enter: cambiar   |   Esc: volver",
    opt_diff_note="La dificultad se elige al empezar una nueva partida.",
    diff_title="Elige tu dificultad", diff_normal="Normal", diff_hard="Difícil", diff_ultra="ULTRA HARD",
    diff_normal_d="La aventura tal como fue concebida: exigente, pero justa.",
    diff_hard_d="Enemigos más resistentes y violentos, Guardianes más agresivos, curación reducida, muerte más cara.",
    diff_ultra_d="Para masoquistas: enemigos el doble de duros y letales, proyectiles rápidos y densos, "
                 "Guardianes enfurecidos al 70 % de vida, curación escasa, la muerte te cuesta el 75 % de tus esquirlas.",
    diff_hint="Arriba/Abajo: elegir   |   Enter: empezar   |   Esc: volver",
    diff_best="Mejor tiempo: %s",
    slots_load="Cargar partida", slots_save="Guardar partida", slot_auto="Guardado automático",
    slot_1="Ranura 1", slot_2="Ranura 2", slot_3="Ranura 3", slot_empty="- vacía -",
    slot_info="Nv. %d   |   Brasas %d/4   |   Fragmentos %d/%d   |   %d min",
    slot_hint="Enter: confirmar   |   Esc: volver   |   Supr: borrar una partida",
    slot_deleted="Partida borrada.", slot_confirm="Pulsa Supr otra vez para confirmar el borrado.",
    slot_saved="Guardado en: %s.", slot_fail="No se puede escribir la partida.",
    slot_empty_msg="Esta ranura está vacía.",
    toast_autosave="Guardado automático.", toast_saved="Partida guardada.", toast_savefail="Error al guardar.",
    toast_unreadable="Partida ilegible.", toast_corrupt="Partida corrupta.",
    cr_by="Un juego de", cr_concept="Concepto y diseño de juego", cr_lore="Universo, historia y guion",
    cr_prog="Programación", cr_art="Dirección artística", cr_level="Diseño de niveles y equilibrio",
    cr_made="Hecho con Python y pygame", cr_thanks="Gracias por jugar.", cr_back="Esc: volver",
    jr_title="Diario", jr_empty="Nada por ahora. Lee las estelas y derrota a los Guardianes.",
    jr_hint="Arriba/Abajo: recorrer   |   Esc: volver",
    intro_hint="Enter: continuar   |   Esc: saltar el prólogo",
    loading="Cargando...  %d %%",
    hud_hp="PV %d/%d", hud_lvl="Nv. %d", hud_shards="Esquirlas: %d", hud_potions="Pociones (R): %d",
    hud_dmg="Daño: %d",
    help1="WASD: moverse | Ratón: apuntar | Clic izq. / Espacio: golpear | Clic der. / E: bola de brasa | Mayús: voltereta",
    help2="R: poción | F: interactuar | Tab: misión | Esc: pausa | F11: pantalla completa",
    interact="F: interactuar",
    float_hp="+%d PV", parry="¡Parada!", level_up="¡Nivel %d!", float_shards="+%d esquirlas", float_potion="¡Poción!",
    respawn_banner="Tu Brasa aún late...",
    dead_title="TE APAGAS...", dead_sub="La Ceniza te cubre. Pero tu Brasa aún late.",
    dead_hint="Enter: renacer en Port-Cendre (pierdes el %d %% de tus esquirlas)",
    dlg_hint_menu="Arriba/Abajo: elegir | Enter: confirmar", dlg_hint_next="F / Enter: continuar", dlg_leave="Irse",
    stele_prefix="Estela: %s", stele_fragment="(Fragmento de memoria %d/%d - añadido a tu Diario.)",
    altar_name="Altar de la Llama",
    altar_empty1="Un cráter de piedra negra, frío como una tumba. Cuatro huecos esperan cada uno una Brasa.",
    altar_empty2="Brasas traídas: %d/4.",
    altar_ready1="Las cuatro Brasas vibran en tu pecho. El altar se ilumina débilmente, como si te reconociera.",
    altar_ready2="Sabes lo que debes hacer... o lo que podrías hacer en su lugar.",
    altar_lore="Los %d fragmentos de memoria resuenan en ti: una tercera vía, que Karn nunca vio, se abre ante ti.",
    opt_end1="Reavivar la Llama (entregarle tu corazón)", opt_end2="Quedarte con las Brasas",
    opt_end3="Compartir la Llama con todos  [final verdadero]",
    svc_rest_opt="Descansar junto al fuego (curación total + guardado)",
    svc_rest_msg="El fuego te reconforta. Tus fuerzas vuelven. (Partida guardada)",
    svc_forge_opt="Afilar la hoja (+3 de daño) - %d esquirlas", svc_forge_msg="Torvald afila tu hoja. Daño: %d.",
    svc_shop_opt="Comprar una poción de brasa - %d esquirlas", svc_shop_msg="Ahora tienes %d poción(es).",
    svc_nomoney="No tienes bastantes esquirlas.",
    braise_got="¡Obtienes la %s! (%d/4)",
    braises_all="Las cuatro Brasas vibran en tu pecho. Vuelve al altar de Port-Cendre.",
    q_main="MISIÓN PRINCIPAL", q_side="MISIÓN SECUNDARIA", q_updated="Misión actualizada",
    q0_t="Encuentra a Maëlys", q0_d="Habla con Maëlys la Archivista, junto al altar de Port-Cendre.",
    q1_t="Las cuatro Brasas", q1_d="Derrota a los cuatro Guardianes y trae sus Brasas: %d/4.",
    q2_t="Reavivar la Llama",
    q2_d="Regresa al altar de Port-Cendre con las cuatro Brasas y decide el destino de Aethel.",
    qs_t="Memoria de Aethel", qs_d="Lee todas las estelas: %d/%d.",
    qs_done="Has leído todas las estelas. Un final secreto te espera en el altar.",
    dir_1="noroeste", dir_2="noreste", dir_3="suroeste", dir_4="sureste",
    st_title="Estadísticas", st_time="Tiempo de juego", st_diff="Dificultad", st_level="Nivel",
    st_kills="Monstruos derrotados", st_bosses="Guardianes derrotados", st_deaths="Muertes", st_hits="Veces golpeado",
    st_dmg_taken="Daño recibido", st_dmg_dealt="Daño infligido", st_nohit="Mejor racha sin ser golpeado",
    st_swings="Espadazos (precisión)", st_spells="Bolas de brasa (precisión)",
    st_parries="Proyectiles parados", st_rolls="Volteretas", st_potions="Pociones bebidas",
    st_shards="Esquirlas recogidas", st_lore="Fragmentos de memoria", st_crits="Golpes críticos",
    st_record="Récord (%s): %s", st_newrecord="¡Nuevo récord!", st_hint="Esc: volver",
    end_hint="Enter: ver estadísticas", end_hint2="Enter: volver al menú",
    end_stats_title="Resumen de tu partida",
    end_summary="Nivel %d  |  Fragmentos de memoria: %d/%d  |  Tiempo: %s", end_by="Un juego de WILOOPE",
)


# --------------------------------------------------------------------------
#  CONTENU NARRATIF (FR / EN / ES) : lore, Gardiens, stèles, PNJ, fins...
# --------------------------------------------------------------------------
CT = {}
CT["fr"] = dict(
    lore=[
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
    ],
    tips=[
        "Un coup d'épée bien placé détruit les projectiles ennemis (et te rend un peu de mana).",
        "La roulade (Maj) te rend invulnérable un bref instant : traverse les anneaux de projectiles.",
        "Les stèles donnent de l'expérience... et des réponses. La Flamme garde une fin secrète pour les curieux.",
        "Les monstres ne te poursuivent pas dans Port-Cendre : c'est ton refuge.",
        "Les Gardiens se réveillent quand tu t'approches de leur arène. Prépare-toi avant d'entrer.",
        "Sauvegarde auprès de Maëlys, ou depuis le menu pause (Échap).",
        "Chaque Gardien vaincu t'offre une Braise, et son histoire s'ajoute à ton Journal.",
        "Tab affiche ou masque le suivi de quête. La flèche dorée pointe vers ton objectif.",
        "En Ultra Hard, chaque coup compte : roule, pare, et ne reste jamais immobile.",
    ],
    biomes={0: "Port-Cendre, le dernier refuge", 1: "Forêt des Murmures", 2: "Marais de Vaelith",
            3: "Ruines de Karn-la-Haute", 4: "Cime de Cendre"},
    monsters=dict(loup="Loup-Cendre", errant="Cendreux", noye="Noyé", follet="Feu-follet", creux="Soldat Creux",
                  archer="Archer Creux", braise="Cendre-Vive", cracheur="Cracheur de braise"),
    bosses={
        1: dict(name="Sylvaine, l'Arbre-Mère", braise="Braise Verte",
                last="« Merci... Enfin, je sens la pluie. Porte ma Braise, enfant, et n'oublie pas la forêt. »"),
        2: dict(name="Vaelith la Noyée", braise="Braise Bleue",
                last="« Les eaux se retirent... Dis-leur, quand ils reviendront, que j'ai gardé le gué jusqu'au bout. »"),
        3: dict(name="Karn, le Roi Creux", braise="Braise Violette",
                last="« Ces yeux... elle avait ces mêmes yeux. Je voulais ne jamais mourir, et je n'ai jamais vécu. Prends la Braise, enfant. »"),
        4: dict(name="Ignis, Dernier Dragon de Cendre", braise="Braise Ardente",
                last="« Je me souviens... d'avoir été chaude. Rallume-nous. Ou ne le fais pas... mais choisis. »"),
    },
    codex={
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
    },
    steles={
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
    },
    npc=dict(
        maelys=dict(
            name="Maëlys l'Archiviste",
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
                    "Rends-la, garde-la... ou fais ce que Karn n'a jamais osé faire. Lis les stèles, enfant : elles disent ce que je n'ai jamais eu le courage d'écrire."]),
        torvald=dict(
            name="Torvald le Forgeron",
            lines=["Hmpf. Encore un gamin avec une lame émoussée. Je suis Torvald, forgeron. Je forgeais pour les Veilleurs, avant.",
                   "C'est moi qui ai forgé la couronne de Karn. Il m'avait juré qu'elle servirait à bâtir. Je n'ai jamais su me pardonner ma naïveté.",
                   "Apporte-moi des éclats, et je rendrai ta lame digne de ceux qui t'ont précédé. Les Gardiens ne sont pas des monstres... "
                   "mais ils ne te feront aucun cadeau."],
            lines2=["Des éclats ? Je t'écoute. Et ne meurs pas, ça fait mauvais genre pour mon métier."]),
        orin=dict(
            name="Orin le Colporteur",
            lines=["Psst ! Orin, colporteur, pour vous servir. Je vends des potions de braise, distillées à partir de tout ce qui brille encore.",
                   "Un tuyau gratuit : les Gardiens attaquent en motifs. Roule à travers leurs anneaux, pare leurs tirs avec ton épée... et ne reste jamais immobile.",
                   "Et ne me demandez pas où je trouve la matière première."],
            lines2=["Une potion ? Toujours en stock. Et toujours un peu tiède."]),
    ),
    endings={
        1: ("FIN : L'ÉTINCELLE",
            "Tu poses les quatre Braises dans les creux de l'autel, puis ta propre main. La Flamme jaillit, et pour la rallumer "
            "tu lui donnes ton coeur. Tu ne t'éteins pas : tu deviens la lumière. Les morts retrouvent le repos, la Cendre se change "
            "en pluie, et mille ans plus tard, un enfant de Port-Cendre allume encore une lanterne à ton nom."),
        2: ("FIN : LA COURONNE DE CENDRE",
            "Tu refermes la main sur les quatre Braises. Leur puissance t'envahit, et la Flamme, elle, reste morte. Les ombres "
            "s'agenouillent devant toi. Tu règnes sur un monde froid que plus rien ne menace... sauf ce qui a rongé Karn avant toi : "
            "la peur de mourir. Elle finit toujours par frapper à la porte des rois."),
        3: ("FIN VÉRITABLE : LE FOYER",
            "Tu n'offres pas la Flamme, tu ne la gardes pas : tu la partages. Maëlys, Torvald, Orin, les enfants de Port-Cendre, "
            "chacun pose une main sur l'autel. La Flamme se divise en mille braises, une dans chaque foyer d'Aethel. Plus de Veilleur "
            "unique, plus de trône, plus de peur. Dans les cendres, Sylvaine, Vaelith, Ignis et Karn trouvent enfin le sommeil : "
            "ils avaient seulement oublié qu'on ne garde pas seul un feu."),
    },
)

CT["en"] = dict(
    lore=[
        "In the beginning there was only the Cold. Then the First Breath fell upon bare stone and lit the Eternal Flame. "
        "Around it Aethelgard was born, the Beacon-City, and with it, the world.",
        "Five Wardens swore never to let it die. Four received an Ember and a Circle to keep: "
        "Sylvaine the Forest, Vaelith the Waters, Karn the Stone, Ignis the Fire. The fifth, Maëlys, received no Ember: she received Memory.",
        "But Karn, the builder-king, had loved a mortal woman. When she died, the Flame refused to call her back: it does not return what has gone. "
        "So the fear of death gnawed at him, until he believed that merely possessing the Flame would be enough to bend it.",
        "This was the Night of Silence. Karn tore the Flame from its altar. It cannot be taken: it went out in his hands. "
        "The cold returned, the dead rose, the Ash began to fall, and the four Embers, orphaned, drove their keepers mad.",
        "They say that at the instant the Flame died, one last spark fell into the cradle of a child of Port-Cendre, "
        "the last village of Aethel. That child is you. The Ember-Bearer: the only heart still warm in a world of ash.",
        "The Ash is closing in on the walls of Port-Cendre. Maëlys watched you grow up and kept many things from you. "
        "It is time to leave, to return to the Guardians what they have lost... and to discover what the Flame truly awaited of you.",
    ],
    tips=[
        "A well-placed sword strike destroys enemy projectiles (and restores a little mana).",
        "The roll (Shift) makes you invulnerable for a brief instant: dash through rings of projectiles.",
        "Steles grant experience... and answers. The Flame keeps a secret ending for the curious.",
        "Monsters do not follow you into Port-Cendre: it is your refuge.",
        "The Guardians awaken when you approach their arena. Prepare before you enter.",
        "Save with Maëlys, or from the pause menu (Esc).",
        "Each Guardian you defeat grants you an Ember, and their story is added to your Journal.",
        "Tab shows or hides the quest tracker. The golden arrow points toward your objective.",
        "On Ultra Hard, every hit counts: roll, parry, and never stand still.",
    ],
    biomes={0: "Port-Cendre, the Last Refuge", 1: "Forest of Whispers", 2: "Marshes of Vaelith",
            3: "Ruins of Karn-la-Haute", 4: "Summit of Ash"},
    monsters=dict(loup="Ash-Wolf", errant="Ashen", noye="Drowned", follet="Will-o'-Wisp", creux="Hollow Soldier",
                  archer="Hollow Archer", braise="Living Cinder", cracheur="Ember Spitter"),
    bosses={
        1: dict(name="Sylvaine, the Mother Tree", braise="Green Ember",
                last="“Thank you... At last, I can feel the rain. Carry my Ember, child, and never forget the forest.”"),
        2: dict(name="Vaelith the Drowned", braise="Blue Ember",
                last="“The waters recede... Tell them, when they return, that I kept the ford to the very end.”"),
        3: dict(name="Karn, the Hollow King", braise="Violet Ember",
                last="“Those eyes... she had those same eyes. I wanted never to die, and I never lived. Take the Ember, child.”"),
        4: dict(name="Ignis, Last Dragon of Ash", braise="Burning Ember",
                last="“I remember... being warm. Rekindle us. Or do not... but choose.”"),
    },
    codex={
        1: ("Sylvaine, the Green Warden",
            "Keeper of the Green Circle, she planted a tree for every soul she soothed. On the Night of Silence she rooted herself so as not to watch "
            "her forest fall, and the Ash turned her into the Mother Tree. Her Ember is green as the first rain."),
        2: ("Vaelith, the Warden of the Waters",
            "A ferrywoman of the dead, she guided the departed across the ford of the Marshes. When the Flame went out, no one could cross anymore: "
            "she drowned in her own waiting. Her Ember is blue as a farewell."),
        3: ("Karn, the Hollow King",
            "Builder-king of Aethelgard, he loved a mortal whom the Flame refused to call back. His fear of death made him steal the Flame, "
            "and the Flame went out in his hands. His last words spoke of eyes that you seemed to recall to him."),
        4: ("Ignis, the Warden of Fire",
            "When the Flame died, she kept burning alone, until she became a living ash that legends call a dragon. "
            "Her Ember is the last: it still burns like a reproach."),
    },
    steles={
        0: [("The Five Oaths",
             "“Five Wardens, five oaths: Sylvaine swore to guard the living, Vaelith to guide the dead, Ignis to keep the warmth, "
             "Karn to keep the law, Maëlys to keep the memory. May no oath ever fade.”"),
            ("Port-Cendre",
             "“Port-Cendre was founded by the last pilgrims of Aethelgard. Hearth fires are still kept lit out of habit, "
             "the way one talks to the dead.”")],
        1: [("Sylvaine the First",
             "“Sylvaine planted a tree for every soul she soothed. Today the forest whispers their names, endlessly, and no longer knows how to hush them.”"),
            ("The Ash-Wolves",
             "“The ash-wolves were not born this way. They are the dogs of Aethel's shepherds, still loyal to masters long dead.”"),
            ("The Mother Tree",
             "“At the heart of the Green Circle stands the Mother Tree. Sylvaine rooted herself there on the Night of Silence so as not to watch her forest fall. "
             "Its roots drink the Ash.”")],
        2: [("The Ford of the Dead",
             "“Vaelith watched over the ford where the departed cross to their final sleep. Since the Night of Silence, no one crosses. "
             "The drowned wait.”"),
            ("The Will-o'-the-Wisps",
             "“Will-o'-the-wisps are the prayers no one answered. Do not follow them.”"),
            ("Letters to Karn",
             "“Vaelith wrote to Karn every evening of the winter of Silence, begging him to set the Flame back. "
             "The letters sleep at the bottom of the water, unanswered.”")],
        3: [("Karn-la-Haute",
             "“Here stood Karn-la-Haute. The king built a thousand towers to climb toward the Flame. He never understood that it was already below, "
             "among the people.”"),
            ("The Offered Heart",
             "“The Hollow King has no heart. He offered it to the Flame, and the Flame refused it. Ever since, he searches for it among the stones.”"),
            ("The Weaver",
             "“They say Karn loved a weaver of Port-Cendre. She died in winter, while she was carrying a child. The Flame refused to call her back. "
             "The chronicles stop there: the Archivist tore out the next page.”")],
        4: [("Ignis",
             "“Ignis was never a dragon. She was the Warden of Fire. When the Flame went out, she kept burning alone, "
             "and turned into living ash.”"),
            ("The Choice",
             "“Carved into the rock: when the four Embers are reunited, the Ember-Bearer shall choose. Rekindle the Flame, or keep it.”"),
            ("What the Flame Asks",
             "“The Flame is not taken. It is not stolen. It is given, from a beating heart to a beating heart. "
             "Karn had known this, long ago. He had forgotten.”")],
    },
    npc=dict(
        maelys=dict(
            name="Maëlys the Archivist",
            lines=["An Ember-Bearer... So the prophecy was more than a lullaby. Come closer, let me look at your heart: it is lukewarm, which is a good sign.",
                   "I am Maëlys, the last Warden. Not the most powerful: the oldest. I keep the Memory of Aethel, and I owe you a little of that memory.",
                   "Four Guardians each hold an Ember: Sylvaine to the north-west, Vaelith to the north-east, Karn to the south-west, Ignis to the south-east. "
                   "They were my brothers and sisters of the order. Do not hate them: they are in mourning.",
                   "Read the steles along your road: the memory of Aethel took refuge in them. And come back to rest here when you need to. I will watch over your fire."],
            lines2=["May the Ember keep you. Would you like to rest by the fire? I will note where you stand."],
            lines3=["You have them all... Then I can no longer stay silent.",
                    "Your mother was the weaver of Port-Cendre the steles speak of. Your father was Karn. "
                    "I hid the truth from you: I was afraid you would come to resemble him.",
                    "It is for you that the Flame kept a spark, the night it died. Karn wanted to possess the Flame. "
                    "You are its last living ember.",
                    "Return it, keep it... or do what Karn never dared to do. Read the steles, child: they say what I never had the courage to write."]),
        torvald=dict(
            name="Torvald the Blacksmith",
            lines=["Hmpf. Another kid with a dull blade. I'm Torvald, blacksmith. I used to forge for the Wardens, back then.",
                   "I forged Karn's crown. He swore to me it would serve to build. I never forgave myself for my naivety.",
                   "Bring me shards, and I'll make your blade worthy of those who came before you. The Guardians are not monsters... "
                   "but they will give you no gifts."],
            lines2=["Shards? I'm listening. And try not to die, it looks bad for my trade."]),
        orin=dict(
            name="Orin the Peddler",
            lines=["Psst! Orin, peddler, at your service. I sell ember potions, distilled from everything that still shines.",
                   "A free tip: the Guardians attack in patterns. Roll through their rings, parry their shots with your sword... and never stand still.",
                   "And don't ask me where I get the raw material."],
            lines2=["A potion? Always in stock. And always a little lukewarm."]),
    ),
    endings={
        1: ("ENDING: THE SPARK",
            "You place the four Embers in the hollows of the altar, then your own hand. The Flame leaps up, and to rekindle it "
            "you give it your heart. You do not fade: you become the light. The dead find rest, the Ash turns to rain, "
            "and a thousand years later, a child of Port-Cendre still lights a lantern in your name."),
        2: ("ENDING: THE CROWN OF ASH",
            "You close your fist around the four Embers. Their power floods you, and the Flame itself stays dead. The shadows kneel before you. "
            "You rule a cold world that nothing threatens any more... except what gnawed at Karn before you: "
            "the fear of dying. It always ends up knocking at the door of kings."),
        3: ("TRUE ENDING: THE HEARTH",
            "You do not offer the Flame, you do not keep it: you share it. Maëlys, Torvald, Orin, the children of Port-Cendre, "
            "each lays a hand on the altar. The Flame divides into a thousand embers, one in every hearth of Aethel. No more lone Warden, "
            "no more throne, no more fear. In the ashes, Sylvaine, Vaelith, Ignis and Karn at last find sleep: "
            "they had only forgotten that no one keeps a fire alone."),
    },
)

CT["es"] = dict(
    lore=[
        "Al principio solo existía el Frío. Después el Primer Aliento cayó sobre la piedra desnuda y encendió la Llama Eterna. "
        "A su alrededor nació Aethelgard, la Ciudad-Faro, y con ella, el mundo.",
        "Cinco Vigías juraron no dejarla morir jamás. Cuatro recibieron una Brasa y un Círculo que custodiar: "
        "Sylvaine el Bosque, Vaelith las Aguas, Karn la Piedra, Ignis el Fuego. La quinta, Maëlys, no recibió ninguna Brasa: recibió la Memoria.",
        "Pero Karn, el rey constructor, había amado a una mortal. Cuando ella murió, la Llama se negó a devolverla: no devuelve lo que se ha ido. "
        "Entonces el miedo a la muerte lo carcomió, hasta hacerle creer que bastaba con poseer la Llama para doblegarla.",
        "Fue la Noche del Silencio. Karn arrancó la Llama de su altar. No se deja tomar: se apagó entre sus manos. "
        "El frío volvió, los muertos se alzaron, la Ceniza empezó a caer, y las cuatro Brasas, huérfanas, enloquecieron a sus guardianes.",
        "Cuentan que, en el instante en que la Llama moría, una última chispa cayó en la cuna de un bebé de Port-Cendre, "
        "la última aldea de Aethel. Ese bebé eres tú. El Portador de la Brasa: el único corazón aún cálido en un mundo de ceniza.",
        "La Ceniza se acerca a las murallas de Port-Cendre. Maëlys te vio crecer y te ocultó muchas cosas. "
        "Es hora de partir, de devolver a los Guardianes lo que han perdido... y de descubrir lo que la Llama esperaba realmente de ti.",
    ],
    tips=[
        "Un golpe de espada bien colocado destruye los proyectiles enemigos (y te devuelve un poco de maná).",
        "La voltereta (Mayús) te hace invulnerable un breve instante: atraviesa los anillos de proyectiles.",
        "Las estelas dan experiencia... y respuestas. La Llama guarda un final secreto para los curiosos.",
        "Los monstruos no te persiguen dentro de Port-Cendre: es tu refugio.",
        "Los Guardianes despiertan cuando te acercas a su arena. Prepárate antes de entrar.",
        "Guarda con Maëlys, o desde el menú de pausa (Esc).",
        "Cada Guardián derrotado te otorga una Brasa, y su historia se añade a tu Diario.",
        "Tab muestra u oculta el seguimiento de misión. La flecha dorada apunta a tu objetivo.",
        "En Ultra Hard cada golpe cuenta: rueda, para y no te quedes nunca quieto.",
    ],
    biomes={0: "Port-Cendre, el último refugio", 1: "Bosque de los Susurros", 2: "Pantanos de Vaelith",
            3: "Ruinas de Karn-la-Haute", 4: "Cumbre de Ceniza"},
    monsters=dict(loup="Lobo de Ceniza", errant="Ceniciento", noye="Ahogado", follet="Fuego Fatuo",
                  creux="Soldado Hueco", archer="Arquero Hueco", braise="Ceniza Viva", cracheur="Escupidor de Brasas"),
    bosses={
        1: dict(name="Sylvaine, el Árbol Madre", braise="Brasa Verde",
                last="« Gracias... Por fin siento la lluvia. Lleva mi Brasa, criatura, y no olvides el bosque. »"),
        2: dict(name="Vaelith la Ahogada", braise="Brasa Azul",
                last="« Las aguas se retiran... Diles, cuando vuelvan, que guardé el vado hasta el final. »"),
        3: dict(name="Karn, el Rey Hueco", braise="Brasa Violeta",
                last="« Esos ojos... ella tenía esos mismos ojos. Quise no morir jamás, y nunca viví. Toma la Brasa, criatura. »"),
        4: dict(name="Ignis, Último Dragón de Ceniza", braise="Brasa Ardiente",
                last="« Recuerdo... haber sido cálida. Reavívanos. O no lo hagas... pero elige. »"),
    },
    codex={
        1: ("Sylvaine, la Vigía Verde",
            "Guardiana del Círculo Verde, plantaba un árbol por cada alma que apaciguaba. La Noche del Silencio echó raíces para no ver caer "
            "su bosque, y la Ceniza la convirtió en el Árbol Madre. Su Brasa es verde como la primera lluvia."),
        2: ("Vaelith, la Vigía de las Aguas",
            "Barquera de los muertos, guiaba a los difuntos a través del vado de los Pantanos. Cuando la Llama se apagó, nadie pudo cruzar: "
            "se ahogó en su propia espera. Su Brasa es azul como una despedida."),
        3: ("Karn, el Rey Hueco",
            "Rey constructor de Aethelgard, amó a una mortal que la Llama se negó a devolver. Su miedo a la muerte lo llevó a robar la Llama, "
            "y la Llama se apagó entre sus manos. Sus últimas palabras hablaban de unos ojos que parecías recordarle."),
        4: ("Ignis, la Vigía del Fuego",
            "Cuando la Llama murió, siguió ardiendo sola, hasta convertirse en una ceniza viva que las leyendas llaman dragón. "
            "Su Brasa es la última: aún arde como un reproche."),
    },
    steles={
        0: [("Los Cinco Juramentos",
             "« Cinco Vigías, cinco juramentos: Sylvaine juró custodiar a los vivos, Vaelith guiar a los muertos, Ignis guardar el calor, "
             "Karn guardar la ley, Maëlys guardar el recuerdo. Que ningún juramento se apague. »"),
            ("Port-Cendre",
             "« Port-Cendre fue fundado por los últimos peregrinos de Aethelgard. Aún se mantienen encendidos los fuegos de las cocinas "
             "por costumbre, como se habla con los muertos. »")],
        1: [("Sylvaine la Primera",
             "« Sylvaine plantaba un árbol por cada alma apaciguada. Hoy el bosque murmura sus nombres, sin fin, y ya no sabe acallarlos. »"),
            ("Los Lobos de Ceniza",
             "« Los lobos de ceniza no nacieron así. Son los perros de los pastores de Aethel, fieles aún a amos muertos. »"),
            ("El Árbol Madre",
             "« En el corazón del Círculo Verde se alza el árbol madre. Sylvaine echó raíces en él la Noche del Silencio para no ver caer su bosque. "
             "Sus raíces beben la Ceniza. »")],
        2: [("El Vado de los Muertos",
             "« Vaelith velaba el vado por donde los difuntos cruzan hacia su último sueño. Desde la Noche del Silencio, nadie cruza. "
             "Los ahogados esperan. »"),
            ("Los Fuegos Fatuos",
             "« Los fuegos fatuos son las plegarias que nadie escuchó. No los sigas. »"),
            ("Cartas a Karn",
             "« Vaelith escribió a Karn cada noche del invierno del Silencio, suplicándole que devolviera la Llama a su sitio. "
             "Las cartas duermen en el fondo del agua, sin respuesta. »")],
        3: [("Karn-la-Haute",
             "« Aquí se alzaba Karn-la-Haute. El rey levantó mil torres para subir hacia la Llama. Nunca comprendió que ya estaba abajo, "
             "entre la gente. »"),
            ("El Corazón Ofrecido",
             "« El Rey Hueco ya no tiene corazón. Se lo ofreció a la Llama, y la Llama lo rechazó. Desde entonces lo busca entre las piedras. »"),
            ("La Tejedora",
             "« Dicen que Karn amó a una tejedora de Port-Cendre. Murió en invierno, mientras esperaba un hijo. La Llama se negó a devolverla. "
             "Las crónicas se detienen ahí: la Archivista arrancó la página siguiente. »")],
        4: [("Ignis",
             "« Ignis nunca fue un dragón. Era la Vigía del Fuego. Cuando la Llama se apagó, siguió ardiendo sola "
             "y se convirtió en ceniza viva. »"),
            ("La Elección",
             "« Grabado en la roca: cuando las cuatro Brasas estén reunidas, el Portador de la Brasa deberá elegir. Devolver la Llama, o conservarla. »"),
            ("Lo que pide la Llama",
             "« La Llama no se toma. No se roba. Se entrega, de un corazón que late a un corazón que late. "
             "Karn lo supo, antaño. Lo había olvidado. »")],
    },
    npc=dict(
        maelys=dict(
            name="Maëlys la Archivista",
            lines=["Un Portador de la Brasa... Así que la profecía era algo más que una nana. Acércate, deja que mire tu corazón: está tibio, y es buena señal.",
                   "Soy Maëlys, la última Vigía. No la más poderosa: la más antigua. Guardo la Memoria de Aethel, y te debo un poco de esa memoria.",
                   "Cuatro Guardianes poseen cada uno una Brasa: Sylvaine al noroeste, Vaelith al noreste, Karn al suroeste, Ignis al sureste. "
                   "Fueron mis hermanos y hermanas de orden. No los odies: están de luto.",
                   "Lee las estelas de tu camino: la memoria de Aethel se refugió en ellas. Y vuelve a descansar aquí cuando lo necesites. Yo velaré tu fuego."],
            lines2=["Que la Brasa te guarde. ¿Quieres descansar junto al fuego? Anotaré dónde te encuentras."],
            lines3=["Las tienes todas... Entonces ya no puedo callar.",
                    "Tu madre era la tejedora de Port-Cendre de la que hablan las estelas. Tu padre era Karn. "
                    "Te oculté la verdad: temía que te parecieras a él.",
                    "Es por ti que la Llama guardó una chispa la noche en que murió. Karn quería poseer la Llama. "
                    "Tú eres su última brasa viva.",
                    "Devuélvela, consérvala... o haz lo que Karn nunca se atrevió a hacer. Lee las estelas, criatura: dicen lo que yo nunca tuve el valor de escribir."]),
        torvald=dict(
            name="Torvald el Herrero",
            lines=["Hmpf. Otro chaval con la hoja desafilada. Soy Torvald, herrero. Antes forjaba para los Vigías.",
                   "Yo forjé la corona de Karn. Me juró que serviría para construir. Nunca supe perdonarme mi ingenuidad.",
                   "Tráeme esquirlas y haré tu hoja digna de quienes te precedieron. Los Guardianes no son monstruos... "
                   "pero no te harán ningún regalo."],
            lines2=["¿Esquirlas? Te escucho. Y procura no morir, queda mal para mi negocio."]),
        orin=dict(
            name="Orin el Buhonero",
            lines=["¡Psst! Orin, buhonero, a su servicio. Vendo pociones de brasa, destiladas con todo lo que aún brilla.",
                   "Un consejo gratis: los Guardianes atacan en patrones. Rueda a través de sus anillos, para sus disparos con la espada... y nunca te quedes quieto.",
                   "Y no me preguntes de dónde saco la materia prima."],
            lines2=["¿Una poción? Siempre hay existencias. Y siempre un poco tibia."]),
    ),
    endings={
        1: ("FINAL: LA CHISPA",
            "Colocas las cuatro Brasas en los huecos del altar, y luego tu propia mano. La Llama brota, y para reavivarla le entregas "
            "tu corazón. No te apagas: te conviertes en la luz. Los muertos hallan el descanso, la Ceniza se vuelve lluvia, "
            "y mil años después, un niño de Port-Cendre aún enciende una linterna en tu nombre."),
        2: ("FINAL: LA CORONA DE CENIZA",
            "Cierras el puño sobre las cuatro Brasas. Su poder te invade, y la Llama sigue muerta. Las sombras se arrodillan ante ti. "
            "Reinas sobre un mundo frío al que nada amenaza... salvo lo que corroyó a Karn antes que a ti: "
            "el miedo a morir. Siempre acaba llamando a la puerta de los reyes."),
        3: ("FINAL VERDADERO: EL HOGAR",
            "No ofreces la Llama, no la conservas: la compartes. Maëlys, Torvald, Orin, los niños de Port-Cendre, "
            "cada uno posa una mano sobre el altar. La Llama se divide en mil brasas, una en cada hogar de Aethel. Ya no hay Vigía único, "
            "ni trono, ni miedo. Entre las cenizas, Sylvaine, Vaelith, Ignis y Karn encuentran por fin el sueño: "
            "solo habían olvidado que un fuego no se guarda en soledad."),
    },
)

LORE_TOTAL = sum(len(v) for v in CT["fr"]["steles"].values())
BOSS_SHORT = {1: "Sylvaine", 2: "Vaelith", 3: "Karn", 4: "Ignis"}


def tr(key, *a):
    """Texte d'interface dans la langue courante (repli sur le français)."""
    s = UI[SET["lang"]].get(key)
    if s is None:
        s = UI["fr"].get(key, key)
    return s % a if a else s


def ct(key):
    """Contenu narratif dans la langue courante (repli sur le français)."""
    c = CT.get(SET["lang"], {})
    return c[key] if key in c else CT["fr"][key]


def fmt_time(sec):
    sec = max(0.0, float(sec))
    h, r = divmod(int(sec), 3600)
    m, s = divmod(r, 60)
    cs = int((sec - int(sec)) * 100)
    return ("%d:%02d:%02d.%02d" % (h, m, s, cs)) if h else ("%02d:%02d.%02d" % (m, s, cs))


def font(size, bold=False):
    return pygame.font.SysFont("georgia,garamond,palatino,serif", size, bold=bold)


F_S, F_M, F_B, F_L, F_XL = font(15), font(19), font(24), font(30, True), font(58, True)

CREDITS = [
    ("title", "CENDRES D'AETHEL"),
    ("space", ""),
    ("small", "cr_by"),
    ("big", "WILOOPE"),
    ("space", ""),
    ("role", "cr_concept", "WILOOPE"),
    ("role", "cr_lore", "WILOOPE"),
    ("role", "cr_prog", "WILOOPE"),
    ("role", "cr_art", "WILOOPE"),
    ("role", "cr_level", "WILOOPE"),
    ("space", ""),
    ("small", "cr_made"),
    ("space", ""),
    ("small", "cr_thanks"),
    ("big", "WILOOPE"),
]

SLOTS = ["auto", "1", "2", "3"]


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
    0: dict(ground=(112, 98, 74), tint=(0, 0, 0, 0)),
    1: dict(ground=(34, 72, 42), tint=(0, 30, 10, 38)),
    2: dict(ground=(52, 66, 54), tint=(10, 40, 40, 48)),
    3: dict(ground=(84, 82, 92), tint=(20, 20, 50, 42)),
    4: dict(ground=(66, 52, 50), tint=(70, 15, 0, 52)),
}

KINDS = {
    "loup":     dict(hp=22, spd=120, dmg=7, r=9, xp=8, col=(125, 125, 132), ranged=False, shards=(1, 3)),
    "errant":   dict(hp=32, spd=70, dmg=9, r=10, xp=10, col=(165, 165, 175), ranged=False, shards=(1, 4)),
    "noye":     dict(hp=44, spd=58, dmg=12, r=11, xp=14, col=(70, 125, 135), ranged=False, shards=(2, 5)),
    "follet":   dict(hp=20, spd=70, dmg=8, r=8, xp=12, col=(120, 235, 175), ranged=True, shards=(2, 4)),
    "creux":    dict(hp=55, spd=80, dmg=13, r=11, xp=16, col=(145, 140, 165), ranged=False, shards=(3, 6)),
    "archer":   dict(hp=30, spd=64, dmg=10, r=10, xp=15, col=(175, 155, 195), ranged=True, shards=(3, 6)),
    "braise":   dict(hp=62, spd=94, dmg=15, r=11, xp=20, col=(235, 115, 50), ranged=False, shards=(4, 8)),
    "cracheur": dict(hp=38, spd=62, dmg=12, r=10, xp=20, col=(245, 165, 60), ranged=True, shards=(4, 8)),
}
BIOME_KINDS = {
    1: ["loup", "loup", "errant"],
    2: ["noye", "noye", "follet"],
    3: ["creux", "creux", "archer"],
    4: ["braise", "braise", "cracheur"],
}

BOSSES = {
    1: dict(hp=380, r=26, spd=48, col=(70, 150, 80), bcol=(112, 220, 110), pats=["ring", "summon", "aimed", "ring"]),
    2: dict(hp=460, r=24, spd=62, col=(80, 140, 185), bcol=(110, 190, 255), pats=["aimed", "charge", "ring", "aimed"]),
    3: dict(hp=560, r=26, spd=72, col=(150, 142, 175), bcol=(190, 150, 255), pats=["charge", "shock", "summon", "aimed"]),
    4: dict(hp=700, r=30, spd=56, col=(215, 85, 40), bcol=(255, 140, 50), pats=["spiral", "aimed", "ring", "charge", "shock"]),
}

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


def draw_text_r(text, fnt, col, right, y, shadow=True):
    """Texte aligné à droite (bord droit en x = right)."""
    img = fnt.render(text, True, col)
    r = img.get_rect()
    r.topright = (right, y)
    if shadow:
        screen.blit(fnt.render(text, True, (0, 0, 0)), r.move(2, 2))
    screen.blit(img, r)
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
#  ENTITÉS (la difficulté active DIFF s'applique à la création)
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
        self.kind = kind
        self.x, self.y, self.r = x, y, d["r"]
        self.maxhp = self.hp = int(round(d["hp"] * DIFF["ehp"]))
        self.spd, self.xp = d["spd"] * DIFF["espd"], d["xp"]
        self.dmg = d["dmg"] * DIFF["edmg"]
        self.col, self.ranged, self.shards = d["col"], d["ranged"], d["shards"]
        self.cd = random.uniform(0.3, 1.5)
        self.hurt = 0.0
        self.kx = self.ky = 0.0
        self.ang = random.uniform(0, 6.28)
        self.wt = random.uniform(0, 2)
        self.moving = False

    @property
    def name(self):
        return ct("monsters")[self.kind]


class Boss:
    boss = True

    def __init__(self, biome, x, y):
        d = BOSSES[biome]
        self.biome, self.kind = biome, "boss"
        self.x, self.y, self.home = x, y, (x, y)
        self.r, self.spd = d["r"], d["spd"] * DIFF["bspd"]
        self.maxhp = int(round(d["hp"] * DIFF["bhp"]))
        self.hp = self.maxhp
        self.col, self.bcol, self.pats = d["col"], d["bcol"], d["pats"]
        self.dmg, self.xp, self.shards, self.ranged = 16 * DIFF["bdmg"], 150, (50, 70), False
        self.active = False
        self.cd, self.pat_i = 1.5, 0
        self.wind = self.dash = self.dir = 0.0
        self.spiral_t = self.spiral_cd = self.spiral_a = 0.0
        self.touch = self.hurt = 0.0
        self.kx = self.ky = 0.0

    @property
    def name(self):
        return ct("bosses")[self.biome]["name"]

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
        self.opt_from = self.stats_from = "main"
        self.journal_sel = 0
        self.load_ok = True
        self.diff = SET["diff"]
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
        self.load_tip = random.choice(ct("tips"))
        self.hits = []

    def set_state(self, s):
        self.state, self.sel, self.hits = s, 0, []
        if s in ("main", "pause", "slots"):
            self.refresh_saves()

    def new_game(self, seed=None, diff=None):
        self.diff = diff if diff in DIFFS else SET["diff"]
        DIFF.clear()
        DIFF.update(DIFFS[self.diff])
        self.D = DIFF
        self.seed = seed if seed is not None else random.randrange(10 ** 9)
        random.seed(self.seed)  # monde, stèles et ennemis reproductibles pour les sauvegardes
        self.world = w = World(self.seed)
        self.p = Player((w.cx + 0.5) * TILE, (w.cy + 2.5) * TILE)
        self.p.potions = self.D["potions"]
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
        self.stats = dict.fromkeys(STAT_KEYS, 0)
        self.stats["best_nohit"] = 0.0
        self.nohit_t = 0.0
        self.qstage = -1
        self.end_page, self.new_record = 1, False
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
            zid=self.tile_biome(p.x, p.y), diff=self.diff, stats=self.stats,
            player=dict(x=p.x, y=p.y, hp=p.hp, mp=p.mp, maxhp=p.maxhp, maxmp=p.maxmp, dmg=p.dmg, lvl=p.lvl, xp=p.xp,
                        shards=p.shards, potions=p.potions, braises=sorted(p.braises), lore=p.lore, forge=p.forge),
            items=[dict(r=it.get("read"), s=it.get("seen"), t=it.get("truth")) for it in self.items],
            explored=[list(c) for c in self.explored])

    def save_to(self, slot, auto=False):
        ok = write_slot(slot, self.snapshot())
        self.refresh_saves()
        self.toast((tr("toast_autosave") if auto else tr("toast_saved")) if ok else tr("toast_savefail"))
        return ok

    def autosave(self):
        if self.world is not None and self.p is not None:
            self.save_to("auto", True)

    def load_from(self, d):
        self.new_game(d["seed"], d.get("diff", "normal"))  # les anciennes sauvegardes restent en "normal"
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
        for k, v in (d.get("stats") or {}).items():
            if k in self.stats and isinstance(v, (int, float)):
                self.stats[k] = v
        self.cam = [clamp(p.x - W / 2, 0, MW * TILE - W), clamp(p.y - H / 2, 0, MH * TILE - H)]

    def start_new(self, diff=None):
        d = diff if diff in DIFFS else SET["diff"]
        SET["diff"] = d
        save_settings()
        self.begin_loading(lambda: self.new_game(None, d), self.start_prologue, 3.5)

    def start_prologue(self):
        self.set_state("intro")
        self.page, self.chars = 1, 0.0

    def start_load(self, slot):
        d = read_slot(slot)
        if not d:
            self.toast(tr("toast_unreadable"))
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
            self.toast(tr("toast_corrupt"))

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
        self.items.append(dict(type="altar", x=x, y=y))
        x, y = T(-5, -3)
        self.items.append(dict(type="npc", id="maelys", x=x, y=y, col=(175, 140, 205), seen=False, service="rest"))
        x, y = T(5, -3)
        self.items.append(dict(type="npc", id="torvald", x=x, y=y, col=(190, 110, 70), seen=False, service="forge"))
        x, y = T(3, 4)
        self.items.append(dict(type="npc", id="orin", x=x, y=y, col=(90, 170, 130), seen=False, service="shop"))
        for k, (dx, dy) in enumerate(((-7, 5), (8, -1))):
            x, y = T(dx, dy)
            self.items.append(dict(type="stele", b=0, k=k, x=x, y=y, read=False))
        for b in (1, 2, 3, 4):
            for k in range(len(CT["fr"]["steles"][b])):
                s = self.random_spot(b)
                if s:
                    self.items.append(dict(type="stele", b=b, k=k, x=s[0], y=s[1], read=False))
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
            self.set_banner(tr("level_up", p.lvl), 2.5)
            self.burst(p.x, p.y, (255, 220, 120), 30)

    def item_name(self, it):
        if it["type"] == "altar":
            return tr("altar_name")
        if it["type"] == "npc":
            return ct("npc")[it["id"]]["name"]
        return ct("steles")[it["b"]][it["k"]][0]

    def slot_zone(self, d):
        zid = d.get("zid")
        if zid in BIOMES:
            return ct("biomes")[zid]
        return d.get("zone", "")

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
            return [(lambda: tr("svc_rest_opt"), self.svc_rest)]
        if svc == "forge":
            return [(lambda: tr("svc_forge_opt", 25 + 20 * p.forge), self.svc_forge)]
        if svc == "shop":
            return [(lambda: tr("svc_shop_opt", self.D["pcost"]), self.svc_potion)]
        if svc == "altar":
            opts = [(lambda: tr("opt_end1"), lambda: self.finish(1)),
                    (lambda: tr("opt_end2"), lambda: self.finish(2))]
            if p.lore >= LORE_TOTAL:
                opts.append((lambda: tr("opt_end3"), lambda: self.finish(3)))
            return opts
        return []

    def svc_rest(self):
        self.p.hp, self.p.mp = self.p.maxhp, float(self.p.maxmp)
        self.autosave()
        return tr("svc_rest_msg")

    def svc_forge(self):
        p = self.p
        c = 25 + 20 * p.forge
        if p.shards < c:
            return tr("svc_nomoney")
        p.shards -= c
        p.forge += 1
        p.dmg += 3
        return tr("svc_forge_msg", p.dmg)

    def svc_potion(self):
        p = self.p
        cost = self.D["pcost"]
        if p.shards < cost:
            return tr("svc_nomoney")
        p.shards -= cost
        p.potions += 1
        return tr("svc_shop_msg", p.potions)

    def finish(self, n):
        self.ending = n
        self.state = "ending"
        self.end_t = 0.0
        self.end_page = 1
        self.dlg = None
        self.stats["best_nohit"] = max(self.stats["best_nohit"], self.nohit_t)
        best = SET["best"].get(self.diff)
        self.new_record = best is None or self.play_time < best
        if self.new_record:
            SET["best"][self.diff] = round(self.play_time, 2)
            save_settings()
        return ""

    def interact(self):
        it, p = self.near, self.p
        if not it:
            return
        if it["type"] == "stele":
            title, text = ct("steles")[it["b"]][it["k"]]
            lines = [text]
            if not it["read"]:
                it["read"] = True
                p.lore += 1
                self.gain_xp(15)
                lines.append(tr("stele_fragment", p.lore, LORE_TOTAL))
            self.start_dialog(tr("stele_prefix", title), lines)
        elif it["type"] == "npc":
            n = ct("npc")[it["id"]]
            if n.get("lines3") and len(p.braises) == 4 and not it.get("truth"):
                lines = n["lines3"]
                it["truth"] = True
            else:
                lines = n["lines2"] if it["seen"] else n["lines"]
            it["seen"] = True
            self.start_dialog(n["name"], lines, it["service"])
        elif it["type"] == "altar":
            if len(p.braises) < 4:
                self.start_dialog(tr("altar_name"), [tr("altar_empty1"), tr("altar_empty2", len(p.braises))])
            else:
                lines = [tr("altar_ready1"), tr("altar_ready2")]
                if p.lore >= LORE_TOTAL:
                    lines.append(tr("altar_lore", LORE_TOTAL))
                self.start_dialog(tr("altar_name"), lines, "altar")

    # ---------- entrées ----------
    def handle(self, ev):
        if ev.type == pygame.QUIT:
            self.quit_game()
        if ev.type == pygame.KEYDOWN:
            self.on_key(ev.key)
        elif ev.type == pygame.MOUSEMOTION:
            self.mouse_motion(ev.pos)
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.state in ("main", "pause", "slots", "options", "diff"):
                self.mouse_click(ev.pos)
            elif self.state in ("intro", "dead", "ending", "loading", "credits", "stats") or \
                    (self.state == "dialogue" and not self.dlg["menu"]):
                self.on_key(pygame.K_RETURN)

    def quit_game(self):
        save_settings()
        pygame.quit()
        sys.exit()

    def toggle_fullscreen(self):
        try:
            pygame.display.toggle_fullscreen()
            SET["fullscreen"] = bool(pygame.display.get_surface().get_flags() & pygame.FULLSCREEN)
            save_settings()
        except pygame.error:
            pass

    def mouse_motion(self, pos):
        if self.state in ("main", "pause", "slots", "options", "diff"):
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
            return [(tr("m_new"), self.open_diff, True),
                    (tr("m_continue"), self.continue_game, self.has_save()),
                    (tr("m_load"), lambda: self.open_slots("load", "main"), self.has_save()),
                    (tr("m_options"), lambda: self.open_options("main"), True),
                    (tr("m_credits"), self.open_credits, True),
                    (tr("m_quit"), self.quit_game, True)]
        if self.state == "pause":
            return [(tr("m_resume"), lambda: self.set_state("play"), True),
                    (tr("m_save"), lambda: self.open_slots("save", "pause"), True),
                    (tr("m_load"), lambda: self.open_slots("load", "pause"), self.has_save()),
                    (tr("m_journal"), self.open_journal, True),
                    (tr("m_stats"), lambda: self.open_stats("pause"), True),
                    (tr("m_options"), lambda: self.open_options("pause"), True),
                    (tr("m_menu"), lambda: self.set_state("main"), True)]
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

    def open_options(self, back):
        self.set_state("options")
        self.opt_from = back

    def open_diff(self):
        self.set_state("diff")
        self.sel = DIFF_ORDER.index(SET["diff"])

    def open_stats(self, back):
        self.set_state("stats")
        self.stats_from = back

    def slot_list(self):
        return SLOTS if self.slot_mode == "load" else SLOTS[1:]

    def journal_entries(self):
        cod, ste = ct("codex"), ct("steles")
        out = [cod[b] for b in sorted(self.p.braises)]
        out += [ste[it["b"]][it["k"]] for it in self.items if it["type"] == "stele" and it["read"]]
        return out

    def on_key(self, key):
        K = pygame
        if key == K.K_F11:
            self.toggle_fullscreen()
            return
        confirm = key in (K.K_RETURN, K.K_KP_ENTER, K.K_SPACE, K.K_f)
        up = key in (K.K_UP, K.K_z, K.K_w)
        down = key in (K.K_DOWN, K.K_s)
        left = key in (K.K_LEFT, K.K_q, K.K_a)
        right = key in (K.K_RIGHT, K.K_d)
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
            elif key == K.K_l and s == "main":
                self.opt_lang(1)
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
                    self.slot_msg, self.slot_del = tr("slot_deleted"), -1
                else:
                    self.slot_del = self.sel
                    self.slot_msg = tr("slot_confirm")
            elif confirm:
                if self.sel >= len(slots):
                    self.set_state(self.slot_from)
                else:
                    slot = slots[self.sel]
                    if self.slot_mode == "save":
                        if self.save_to(slot):
                            self.slot_msg = tr("slot_saved", tr("slot_" + slot))
                        else:
                            self.slot_msg = tr("slot_fail")
                    elif self.saves.get(slot):
                        self.start_load(slot)
                    else:
                        self.slot_msg = tr("slot_empty_msg")
        elif s == "options":
            opts = self.options_items()
            if up or down:
                self.sel = (self.sel + (-1 if up else 1)) % len(opts)
            elif key == K.K_ESCAPE:
                self.set_state(self.opt_from)
            elif left or right or confirm:
                opts[self.sel][1](-1 if left else 1)
        elif s == "diff":
            n = len(DIFF_ORDER) + 1
            if up or down:
                self.sel = (self.sel + (-1 if up else 1)) % n
            elif key == K.K_ESCAPE:
                self.set_state("main")
            elif confirm:
                if self.sel >= len(DIFF_ORDER):
                    self.set_state("main")
                else:
                    self.start_new(DIFF_ORDER[self.sel])
        elif s == "stats":
            if confirm or key == K.K_ESCAPE:
                self.set_state(self.stats_from)
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
                text = ct("lore")[self.page - 1]
                if self.chars < len(text):
                    self.chars = len(text)
                else:
                    self.page, self.chars = self.page + 1, 0.0
                    if self.page > len(ct("lore")):
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
            elif key == K.K_TAB:
                SET["quest"] = not SET["quest"]
                save_settings()
        elif s == "dead":
            if confirm and self.dead_t > 1.0:
                self.respawn()
        elif s == "ending":
            if confirm and self.end_t > 2.0:
                if self.end_page == 1:
                    self.end_page = 2
                else:
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
        self.stats["rolls"] += 1
        self.burst(p.x, p.y, (200, 190, 170), 6)

    def use_potion(self):
        p = self.p
        if p.potions > 0 and p.hp < p.maxhp:
            p.potions -= 1
            self.stats["potions"] += 1
            heal = self.D["heal"]
            p.hp = min(p.maxhp, p.hp + heal)
            self.float(p.x, p.y - 24, tr("float_hp", heal), (120, 255, 140))
            self.burst(p.x, p.y, (255, 140, 140), 12)

    # ---------- combat ----------
    def hurt_player(self, dmg):
        p = self.p
        if p.inv > 0 or self.state != "play":
            return False
        dmg = int(round(dmg))
        p.hp -= dmg
        p.inv = self.D["inv"]
        st = self.stats
        st["hits_taken"] += 1
        st["dmg_taken"] += dmg
        st["best_nohit"] = max(st["best_nohit"], self.nohit_t)
        self.nohit_t = 0.0
        self.shake = max(self.shake, 7)
        self.float(p.x, p.y - 24, "-%d" % dmg, (255, 90, 80))
        self.burst(p.x, p.y, (200, 40, 40), 10)
        if p.hp <= 0:
            p.hp = 0
            st["deaths"] += 1
            self.state = "dead"
            self.dead_t = 0.0
        return True

    def damage_enemy(self, e, dmg, kx=0.0, ky=0.0, crit=False):
        dmg = int(round(dmg))
        self.stats["dmg_dealt"] += max(0, min(dmg, int(e.hp)))
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
        p, st = self.p, self.stats
        p.atk_cd, p.atk_t = 0.36, 0.16
        st["swings"] += 1
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
                    if crit:
                        st["crits"] += 1
                    dmg = p.dmg * random.uniform(0.9, 1.15) * (2 if crit else 1)
                    self.damage_enemy(e, dmg, math.cos(a) * 230, math.sin(a) * 230, crit)
                    hit = True
        for pr in self.projs:
            if not pr["fr"] and dist(pr["x"], pr["y"], p.x, p.y) < 66:
                a = math.atan2(pr["y"] - p.y, pr["x"] - p.x)
                if abs((a - p.face + math.pi) % (2 * math.pi) - math.pi) < 1.2:
                    pr["life"] = 0
                    st["parries"] += 1
                    p.mp = min(p.maxmp, p.mp + 4)
                    self.float(pr["x"], pr["y"], tr("parry"), (180, 220, 255))
                    self.burst(pr["x"], pr["y"], (180, 220, 255), 8)
        if hit:
            st["swing_hits"] += 1
            p.mp = min(p.maxmp, p.mp + 3)
            self.shake = max(self.shake, 3)

    def cast(self):
        p = self.p
        if p.spell_cd > 0 or p.mp < 12:
            return
        p.mp -= 12
        p.spell_cd = 0.45
        self.stats["spells"] += 1
        self.shoot(p.x + math.cos(p.face) * 14, p.y + math.sin(p.face) * 14, p.face, 400,
                   p.dmg * 1.7, True, (255, 150, 50), 7, 1.1)

    def kill(self, e):
        p, D = self.p, self.D
        self.burst(e.x, e.y, e.col, 60 if e.boss else 14)
        sh = random.randint(*e.shards)
        p.shards += sh
        self.stats["shards"] += sh
        self.float(e.x, e.y - 20, tr("float_shards", sh), (240, 210, 100))
        self.gain_xp(int(e.xp * D["xp"]))
        if e.boss:
            bt = ct("bosses")[e.biome]
            p.braises.add(e.biome)
            self.shake = 12
            lines = [bt["last"], tr("braise_got", bt["braise"], len(p.braises))]
            if len(p.braises) == 4:
                lines.append(tr("braises_all"))
            self.start_dialog(bt["name"], lines)
            self.autosave()
        else:
            self.stats["kills"] += 1
            if random.random() < D["drop"]:
                p.potions += 1
                self.float(e.x, e.y - 34, tr("float_potion"), (255, 150, 150))

    def respawn(self):
        p, w = self.p, self.world
        p.hp, p.mp = p.maxhp, float(p.maxmp)
        p.shards = int(p.shards * (1 - self.D["lose"]))
        p.x, p.y = (w.cx + 0.5) * TILE, (w.cy + 2.5) * TILE
        p.inv = 1.5
        self.nohit_t = 0.0
        self.projs.clear()
        for bo in self.bosses.values():
            if bo.hp > 0:
                bo.reset()
        self.state = "play"
        self.set_banner(tr("respawn_banner"), 2.5)

    # ---------- quêtes ----------
    def quest_stage(self):
        mael = next((it for it in self.items if it.get("id") == "maelys"), None)
        if mael is not None and not mael["seen"]:
            return 0
        return 1 if len(self.p.braises) < 4 else 2

    def update_quest(self):
        s = self.quest_stage()
        if s != self.qstage:
            if self.qstage != -1:
                self.set_banner(tr("q_updated"), 2.5)
            self.qstage = s

    def quest_target(self):
        p, s = self.p, self.qstage
        if s == 0:
            it = next((i for i in self.items if i.get("id") == "maelys"), None)
            return (it["x"], it["y"]) if it else None
        if s == 1:
            live = [b for b in self.bosses.values() if b.hp > 0]
            if not live:
                return None
            return min(live, key=lambda b: dist(b.home[0], b.home[1], p.x, p.y)).home
        if s == 2:
            it = next((i for i in self.items if i["type"] == "altar"), None)
            return (it["x"], it["y"]) if it else None
        return None

    # ---------- options ----------
    def options_items(self):
        def onoff(v):
            return tr("on") if v else tr("off")
        return [
            (tr("opt_lang") + " : " + dict(LANGS)[SET["lang"]], self.opt_lang),
            (tr("opt_timer") + " : " + onoff(SET["timer"]), lambda d: self.opt_flag("timer")),
            (tr("opt_quest") + " : " + onoff(SET["quest"]), lambda d: self.opt_flag("quest")),
            (tr("opt_shake") + " : " + onoff(SET["shake"]), lambda d: self.opt_flag("shake")),
            (tr("opt_full") + " : " + onoff(SET["fullscreen"]), lambda d: self.toggle_fullscreen()),
            (tr("back"), lambda d: self.set_state(self.opt_from)),
        ]

    def opt_lang(self, d=1):
        codes = [c for c, _ in LANGS]
        SET["lang"] = codes[(codes.index(SET["lang"]) + d) % len(codes)]
        save_settings()

    def opt_flag(self, k):
        SET[k] = not SET[k]
        save_settings()

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
        self.nohit_t += dt
        mx, my = pygame.mouse.get_pos()
        p.face = math.atan2(my + self.cam[1] - p.y, mx + self.cam[0] - p.x)
        for name in ("atk_cd", "atk_t", "spell_cd", "roll_cd", "inv"):
            setattr(p, name, max(0.0, getattr(p, name) - dt))
        p.mp = min(p.maxmp, p.mp + 5 * self.D["mp"] * dt)
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
            self.set_banner(ct("biomes")[z], 3.0)
        self.update_quest()
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
                        self.stats["spell_hits"] += 1
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
            self.spawn_t = self.D["spawn"]
            if sum(1 for e in self.enemies if not e.boss) < self.D["cap"]:
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
        p, w, D = self.p, self.world, self.D
        e.hurt = max(0.0, e.hurt - dt)
        e.cd -= dt
        if abs(e.kx) + abs(e.ky) > 5:
            move_entity(w, e, e.kx * dt, e.ky * dt)
            f = max(0.0, 1 - 9 * dt)
            e.kx *= f
            e.ky *= f
        d = dist(e.x, e.y, p.x, p.y)
        if not self.in_hub(p) and d < (330 if e.ranged else 280) * D["aggro"]:
            a = math.atan2(p.y - e.y, p.x - e.x)
            if e.ranged:
                mv = -1 if d < 150 else (1 if d > 230 else 0)
                if mv:
                    move_entity(w, e, math.cos(a) * e.spd * mv * dt, math.sin(a) * e.spd * mv * dt)
                if e.cd <= 0:
                    e.cd = random.uniform(1.4, 2.2) * D["cd"]
                    self.shoot(e.x, e.y, a + random.uniform(-0.08, 0.08), 190 * D["pspd"], e.dmg, False, e.col, 5, 2.5)
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
        p, w, D = self.p, self.world, self.D
        b.hurt = max(0.0, b.hurt - dt)
        d = dist(b.x, b.y, p.x, p.y)
        if not b.active:
            if d < 330 and not self.in_hub(p):
                b.active = True
                self.set_banner(b.name, 3.0)
            return
        rage = b.hp < b.maxhp * D["rage"]
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
                b.cd = (1.5 if rage else 2.2) * D["cd"]
        if b.spiral_t > 0:
            b.spiral_t -= dt
            b.spiral_cd -= dt
            if b.spiral_cd <= 0:
                b.spiral_cd = 0.07 if rage else 0.09
                b.spiral_a += 0.45
                for k in range(2):
                    self.shoot(b.x, b.y, b.spiral_a + k * math.pi, 175 * D["pspd"], 11 * D["bdmg"], False, b.bcol, 6, 4)
        if d < b.r + p.r and b.touch <= 0:
            if self.hurt_player(b.dmg * (1.6 if dashing else 1)):
                b.touch = 0.8

    def boss_attack(self, b, ang, rage):
        D = self.D
        bd, sp, extra = D["bdmg"], D["pspd"], D["bul"]
        pat = b.pats[b.pat_i % len(b.pats)]
        b.pat_i += 1
        if pat == "ring":
            n, off = (22 if rage else 16) + extra, random.uniform(0, 6.28)
            for i in range(n):
                self.shoot(b.x, b.y, off + 6.2832 * i / n, 140 * sp, 12 * bd, False, b.bcol, 6, 4)
        elif pat == "aimed":
            n = (5 if rage else 3) + extra // 3
            for i in range(n):
                self.shoot(b.x, b.y, ang + (i - (n - 1) / 2) * 0.22, 230 * sp, 13 * bd, False, b.bcol, 6, 3)
        elif pat == "spiral":
            b.spiral_t, b.spiral_a = 2.4, ang
        elif pat == "charge":
            b.wind, b.dir = D["wind"], ang
        elif pat == "shock":
            for spd, off in ((95, 0.0), (170, 0.13)):
                for i in range(20 + extra):
                    self.shoot(b.x, b.y, off + 6.2832 * i / (20 + extra), spd * sp, 12 * bd, False, b.bcol, 6, 4)
        elif pat == "summon":
            if sum(1 for e in self.enemies if not e.boss and dist(e.x, e.y, b.x, b.y) < 400) < 6 + extra // 2:
                for i in range(3 + extra // 3):
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
        elif s == "options":
            self.draw_options()
        elif s == "diff":
            self.draw_diff()
        elif s == "stats":
            self.draw_stats_screen()
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
        sh = self.shake if (self.state == "play" and SET["shake"]) else 0
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
                draw_text(self.item_name(it), F_S, (235, 225, 200), (sx, sy - 28), center=True)

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
            draw_text(tr("interact"), F_S, (255, 230, 150), (int(it["x"] - ox), int(it["y"] - oy) - 46), center=True)

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
        draw_text(tr("hud_hp", p.hp, p.maxhp), F_S, (255, 240, 230), (22, 12), shadow=True)
        draw_bar(14, 34, 190, 12, p.mp / p.maxmp, (70, 120, 230))
        draw_bar(14, 50, 230, 6, p.xp / p.xp_need(), (230, 200, 80))
        draw_text(tr("hud_lvl", p.lvl), F_M, (255, 220, 140), (14, 60))
        draw_text(tr("hud_shards", p.shards), F_S, (240, 210, 100), (14, 86))
        draw_text(tr("hud_potions", p.potions), F_S, (255, 160, 160), (14, 104))
        draw_text(tr("hud_dmg", p.dmg), F_S, (220, 220, 230), (14, 122))
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
        # chrono + suivi de quête + flèche d'objectif
        self.draw_timer_quest()
        # bandeau de zone
        if self.banner_t > 0:
            draw_text(self.banner_text, F_L, (255, 225, 160), (W // 2, 110), center=True,
                      alpha=int(255 * clamp(self.banner_t, 0, 1)))
        if self.play_time < 14 and self.state == "play":
            self.draw_help()

    def draw_help(self):
        a = int(255 * clamp((14 - self.play_time) / 2, 0, 1))
        draw_text(tr("help1"), F_S, (220, 215, 200), (W // 2, H - 40), center=True, alpha=a)
        draw_text(tr("help2"), F_S, (220, 215, 200), (W // 2, H - 18), center=True, alpha=a)

    def draw_timer_quest(self):
        y = 158
        if SET["timer"]:
            draw_text_r(fmt_time(self.play_time), F_M, (240, 230, 200), W - 14, y)
            y += 30
        if SET["quest"]:
            self.draw_quest(y + 2)
            if self.state == "play":
                self.draw_compass()

    def draw_quest(self, y):
        s, p = self.qstage, self.p
        if s < 0:
            return
        pw = 262
        x = W - pw - 12
        gold, txt, green = (200, 170, 110), (225, 218, 200), (130, 205, 140)
        rows = [(tr("q_main"), F_S, gold), (tr("q%d_t" % s), F_M, (255, 225, 150))]
        desc = tr("q1_d", len(p.braises)) if s == 1 else tr("q%d_d" % s)
        rows += [(ln, F_S, txt) for ln in wrap(desc, F_S, pw - 24)]
        if s == 1:
            for b in (1, 2, 3, 4):
                ok = b in p.braises
                rows.append((("[x] " if ok else "[ ] ") + BOSS_SHORT[b] + " - " + tr("dir_%d" % b), F_S,
                             green if ok else (195, 190, 175)))
        if s >= 1:
            rows.append(("", F_S, txt))
            rows.append((tr("q_side"), F_S, gold))
            rows.append((tr("qs_t"), F_M, (255, 225, 150)))
            if p.lore >= LORE_TOTAL:
                rows += [(ln, F_S, green) for ln in wrap(tr("qs_done"), F_S, pw - 24)]
            else:
                rows.append((tr("qs_d", p.lore, LORE_TOTAL), F_S, txt))
        h = sum(r[1].get_height() + 2 for r in rows) + 16
        panel = pygame.Surface((pw, h), pygame.SRCALPHA)
        panel.fill((10, 8, 14, 150))
        screen.blit(panel, (x, y))
        pygame.draw.rect(screen, (150, 125, 85), (x, y, pw, h), 1, border_radius=4)
        yy = y + 8
        for text, f, col in rows:
            if text:
                draw_text(text, f, col, (x + 12, yy))
            yy += f.get_height() + 2

    def draw_compass(self):
        tgt = self.quest_target()
        if not tgt:
            return
        p = self.p
        px, py = p.x - self.cam[0], p.y - self.cam[1]
        tx, ty = tgt[0] - self.cam[0], tgt[1] - self.cam[1]
        if 30 < tx < W - 30 and 30 < ty < H - 30:
            return
        a = math.atan2(tgt[1] - p.y, tgt[0] - p.x)
        pts = [(px + math.cos(a) * 84, py + math.sin(a) * 84),
               (px + math.cos(a + 0.2) * 64, py + math.sin(a + 0.2) * 64),
               (px + math.cos(a - 0.2) * 64, py + math.sin(a - 0.2) * 64)]
        pygame.draw.polygon(screen, (255, 215, 90), pts)
        pygame.draw.polygon(screen, (60, 40, 10), pts, 2)

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
            labels = [o[0]() for o in d["opts"]] + [tr("dlg_leave")]
            for i, lab in enumerate(labels):
                sel = i == d["sel"]
                draw_text(("> " if sel else "   ") + lab, F_M, (255, 225, 130) if sel else (190, 185, 170), (box.x + 30, y))
                y += 26
            if d["msg"]:
                draw_text(d["msg"], F_S, (150, 230, 160), (box.x + 30, box.bottom - 28))
            draw_text_r(tr("dlg_hint_menu"), F_S, (150, 145, 135), box.right - 16, box.y + 12, shadow=False)
        else:
            draw_text_r(tr("dlg_hint_next"), F_S, (150, 145, 135), box.right - 16, box.bottom - 26, shadow=False)

    def draw_overlay(self):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((60, 0, 0, int(clamp(self.dead_t * 200, 0, 190))))
        screen.blit(ov, (0, 0))
        if self.dead_t > 0.4:
            draw_text(tr("dead_title"), F_XL, (230, 70, 60), (W // 2, H // 2 - 50), center=True)
            draw_text(tr("dead_sub"), F_M, (230, 215, 200), (W // 2, H // 2 + 10), center=True)
        if self.dead_t > 1.0:
            draw_text(tr("dead_hint", int(self.D["lose"] * 100)), F_S, (200, 195, 185),
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
                        draw_text(tr(c[1]), F_M, (200, 192, 178), (W // 2, y), center=True, alpha=a)
                    elif k == "role":
                        draw_text(tr(c[1]), F_S, (150, 145, 135), (W // 2, y), center=True, alpha=a)
                        draw_text(c[2], F_B, (255, 225, 150), (W // 2, y + 24), center=True, alpha=a)
            y += hts[k]

    def draw_loading(self):
        screen.fill((8, 6, 10))
        self.draw_ash((150, 140, 130))
        draw_text("CENDRES D'AETHEL", F_L, (225, 150, 60), (W // 2, 46), center=True)
        self.draw_credit_lines(96, 430, self.load_t, 52)
        prog = clamp(self.load_t / self.load_min, 0, 1) * (1.0 if self.load_done else 0.85)
        draw_text(tr("loading", int(prog * 100)), F_S, (210, 200, 185), (W // 2, 462), center=True)
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
        draw_text(tr("subtitle"), F_M, (190, 180, 165), (W // 2, 205), center=True)
        draw_text(tr("by"), F_B, (255, 215, 140), (W // 2, 240), center=True)
        items = self.menu_items()
        self.draw_list([i[0] for i in items], [i[2] for i in items], 285, self.sel)
        draw_text(tr("main_hint"), F_S, (130, 125, 115), (W // 2, H - 28), center=True)

    def draw_pause(self):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 175))
        screen.blit(ov, (0, 0))
        draw_text(tr("pause"), F_XL, (255, 225, 160), (W // 2, 110), center=True)
        items = self.menu_items()
        self.draw_list([i[0] for i in items], [i[2] for i in items], 190, self.sel)

    def draw_slots(self):
        screen.fill((10, 8, 12))
        self.draw_ash((150, 140, 130))
        title = tr("slots_load") if self.slot_mode == "load" else tr("slots_save")
        draw_text(title, F_L, (255, 225, 160), (W // 2, 60), center=True)
        slots = self.slot_list()
        self.hits = []
        for i, sl in enumerate(slots):
            y = 110 + i * 92
            sel = i == self.sel
            pygame.draw.rect(screen, (60, 34, 24) if sel else (24, 18, 22), (120, y, W - 240, 80), border_radius=8)
            pygame.draw.rect(screen, (230, 170, 80) if sel else (90, 76, 66), (120, y, W - 240, 80), 2, border_radius=8)
            draw_text(tr("slot_" + sl), F_B, (255, 225, 150) if sel else (215, 205, 190), (144, y + 8))
            d = self.saves.get(sl)
            if d:
                mins = int(d.get("play_time", 0)) // 60
                draw_text(tr("slot_info") % (d.get("lvl", 1), d.get("nb", 0), d.get("lore", 0), LORE_TOTAL, mins),
                          F_S, (200, 192, 178), (144, y + 40))
                dk = d.get("diff") if d.get("diff") in DIFFS else "normal"
                draw_text("%s   -   %s   -   %s" % (self.slot_zone(d), d.get("saved", ""), tr("diff_" + dk)),
                          F_S, (150, 145, 135), (144, y + 58))
            else:
                draw_text(tr("slot_empty"), F_S, (110, 104, 98), (144, y + 44))
            self.hits.append((120, y, W - 240, 80, i))
        i = len(slots)
        y = 110 + i * 92
        sel = i == self.sel
        pygame.draw.rect(screen, (60, 34, 24) if sel else (24, 18, 22), (W // 2 - 110, y, 220, 40), border_radius=8)
        pygame.draw.rect(screen, (230, 170, 80) if sel else (90, 76, 66), (W // 2 - 110, y, 220, 40), 2, border_radius=8)
        draw_text(tr("back"), F_B, (255, 225, 150) if sel else (215, 205, 190), (W // 2, y + 20), center=True)
        self.hits.append((W // 2 - 110, y, 220, 40, i))
        if self.slot_msg:
            draw_text(self.slot_msg, F_M, (170, 235, 180), (W // 2, H - 56), center=True)
        draw_text(tr("slot_hint"), F_S, (130, 125, 115), (W // 2, H - 24), center=True)

    def draw_options(self):
        screen.fill((10, 8, 12))
        self.draw_ash((150, 140, 130))
        draw_text(tr("opt_title"), F_L, (255, 225, 160), (W // 2, 70), center=True)
        items = self.options_items()
        self.draw_list([i[0] for i in items], [True] * len(items), 150, self.sel, w=600)
        draw_text(tr("opt_diff_note"), F_S, (170, 160, 145), (W // 2, 150 + len(items) * 46 + 14), center=True)
        draw_text(tr("opt_hint"), F_S, (130, 125, 115), (W // 2, H - 24), center=True)

    def draw_diff(self):
        screen.fill((10, 8, 12))
        self.draw_ash((150, 140, 130))
        draw_text(tr("diff_title"), F_L, (255, 225, 160), (W // 2, 60), center=True)
        self.hits = []
        cols = {"normal": (150, 215, 150), "hard": (240, 190, 90), "ultra": (240, 80, 60)}
        for i, k in enumerate(DIFF_ORDER):
            y = 110 + i * 96
            sel = i == self.sel
            pygame.draw.rect(screen, (60, 34, 24) if sel else (24, 18, 22), (120, y, W - 240, 86), border_radius=8)
            pygame.draw.rect(screen, (230, 170, 80) if sel else (90, 76, 66), (120, y, W - 240, 86), 2, border_radius=8)
            draw_text(tr("diff_" + k), F_B, cols[k], (144, y + 8))
            best = SET["best"].get(k)
            if best is not None:
                draw_text_r(tr("diff_best", fmt_time(best)), F_S, (200, 192, 178), W - 144, y + 14)
            for j, ln in enumerate(wrap(tr("diff_%s_d" % k), F_S, W - 288)[:3]):
                draw_text(ln, F_S, (215, 205, 190) if sel else (160, 154, 142), (144, y + 42 + j * 17))
            self.hits.append((120, y, W - 240, 86, i))
        i = len(DIFF_ORDER)
        y = 110 + i * 96
        sel = i == self.sel
        pygame.draw.rect(screen, (60, 34, 24) if sel else (24, 18, 22), (W // 2 - 110, y, 220, 40), border_radius=8)
        pygame.draw.rect(screen, (230, 170, 80) if sel else (90, 76, 66), (W // 2 - 110, y, 220, 40), 2, border_radius=8)
        draw_text(tr("back"), F_B, (255, 225, 150) if sel else (215, 205, 190), (W // 2, y + 20), center=True)
        self.hits.append((W // 2 - 110, y, 220, 40, i))
        draw_text(tr("diff_hint"), F_S, (130, 125, 115), (W // 2, H - 24), center=True)

    def stat_rows(self):
        p, st = self.p, self.stats

        def pct(a, b):
            return "%d %%" % round(100.0 * a / b) if b else "-"

        return [
            (tr("st_time"), fmt_time(self.play_time)),
            (tr("st_diff"), tr("diff_" + self.diff)),
            (tr("st_level"), str(p.lvl)),
            (tr("st_kills"), str(int(st["kills"]))),
            (tr("st_bosses"), "%d/4" % len(p.braises)),
            (tr("st_deaths"), str(int(st["deaths"]))),
            (tr("st_hits"), str(int(st["hits_taken"]))),
            (tr("st_dmg_taken"), str(int(st["dmg_taken"]))),
            (tr("st_dmg_dealt"), str(int(st["dmg_dealt"]))),
            (tr("st_nohit"), fmt_time(max(st["best_nohit"], self.nohit_t))),
            (tr("st_swings"), "%d  (%s)" % (st["swings"], pct(st["swing_hits"], st["swings"]))),
            (tr("st_spells"), "%d  (%s)" % (st["spells"], pct(st["spell_hits"], st["spells"]))),
            (tr("st_parries"), str(int(st["parries"]))),
            (tr("st_rolls"), str(int(st["rolls"]))),
            (tr("st_potions"), str(int(st["potions"]))),
            (tr("st_shards"), str(int(st["shards"]))),
            (tr("st_lore"), "%d/%d" % (p.lore, LORE_TOTAL)),
            (tr("st_crits"), str(int(st["crits"]))),
        ]

    def draw_stats_panel(self, top):
        rows = self.stat_rows()
        half = (len(rows) + 1) // 2
        ph = half * 38 + 20
        pan = pygame.Surface((W - 100, ph), pygame.SRCALPHA)
        pan.fill((8, 6, 12, 170))
        screen.blit(pan, (50, top - 14))
        pygame.draw.rect(screen, (150, 125, 85), (50, top - 14, W - 100, ph), 1, border_radius=4)
        for i, (lab, val) in enumerate(rows):
            col, row = divmod(i, half)
            x0 = 90 + col * 410
            y = top + row * 38
            draw_text(lab, F_S, (205, 198, 182), (x0, y))
            draw_text_r(val, F_M, (255, 225, 150), x0 + 370, y - 3)

    def draw_stats_screen(self):
        screen.fill((10, 8, 12))
        self.draw_ash((150, 140, 130))
        draw_text(tr("st_title"), F_L, (255, 225, 160), (W // 2, 60), center=True)
        self.draw_stats_panel(130)
        best = SET["best"].get(self.diff)
        if best is not None:
            draw_text(tr("st_record", tr("diff_" + self.diff), fmt_time(best)), F_S, (200, 190, 170),
                      (W // 2, 520), center=True)
        draw_text(tr("st_hint"), F_S, (130, 125, 115), (W // 2, H - 24), center=True)

    def draw_credits_screen(self):
        screen.fill((8, 6, 10))
        self.draw_ash((150, 140, 130))
        self.draw_credit_lines(70, H - 60, self.cred_t, 48)
        draw_text(tr("cr_back"), F_S, (130, 125, 115), (W // 2, H - 24), center=True)

    def draw_journal(self):
        screen.fill((10, 8, 12))
        self.draw_ash((150, 140, 130))
        draw_text(tr("jr_title"), F_L, (255, 225, 160), (W // 2, 40), center=True)
        ents = self.journal_entries()
        if not ents:
            draw_text(tr("jr_empty"), F_M, (190, 185, 170), (W // 2, H // 2), center=True)
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
        draw_text(tr("jr_hint"), F_S, (130, 125, 115), (W // 2, H - 24), center=True)

    def draw_intro(self):
        screen.fill((8, 6, 10))
        self.draw_ash((150, 145, 140))
        pages = ct("lore")
        text = pages[self.page - 1]
        rem, y = int(self.chars), 150
        for ln in wrap(text, F_B, 720):
            if rem > 0:
                draw_text(ln[:rem], F_B, (225, 215, 195), (W // 2, y), center=True)
            rem -= len(ln) + 1
            y += 38
        draw_text("%d / %d" % (self.page, len(pages)), F_S, (120, 115, 105), (W // 2, H - 60), center=True)
        draw_text(tr("intro_hint"), F_S, (150, 145, 135), (W // 2, H - 36), center=True)

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
        if self.end_page == 1:
            title, txt = ct("endings")[n]
            draw_text(title, F_L, (255, 225, 150), (W // 2, 120), center=True)
            y = 190
            for ln in wrap(txt, F_M, 740):
                draw_text(ln, F_M, (240, 230, 210), (W // 2, y), center=True)
                y += 30
            draw_text(tr("end_summary", p.lvl, p.lore, LORE_TOTAL, fmt_time(self.play_time)),
                      F_S, (200, 190, 170), (W // 2, 450), center=True)
            draw_text(tr("end_by"), F_B, (255, 215, 140), (W // 2, 500), center=True)
            hint = "end_hint"
        else:
            draw_text(tr("end_stats_title"), F_L, (255, 225, 150), (W // 2, 60), center=True)
            self.draw_stats_panel(120)
            best = SET["best"].get(self.diff)
            if self.new_record:
                draw_text(tr("st_newrecord"), F_B, (255, 225, 120), (W // 2, 505), center=True)
            elif best is not None:
                draw_text(tr("st_record", tr("diff_" + self.diff), fmt_time(best)), F_S, (220, 210, 190),
                          (W // 2, 505), center=True)
            hint = "end_hint2"
        if self.end_t > 2.0 and int(self.t * 1.6) % 2 == 0:
            draw_text(tr(hint), F_M, (240, 225, 190), (W // 2, 560), center=True)
        fade = pygame.Surface((W, H))
        fade.set_alpha(int(clamp(255 - self.end_t * 120, 0, 255)))
        screen.blit(fade, (0, 0))


# ==========================================================================
#  EXTENSION : touches personnalisables, sons & musiques synthétisés, langues
#  (aucun fichier à télécharger : tout est généré par le code)
# ==========================================================================
import array
import copy
import threading

PLUS_FILE = os.path.join(SAVE_DIR, "parametres_plus.json")
LANGS.extend([("de", "Deutsch"), ("it", "Italiano"), ("pt", "Português")])
LANG_ORDER = ["fr", "en", "es", "de", "it", "pt"]

# ---- nouveaux textes : (fr, en, es, de, it, pt) ----
NEWKEYS = {
    "opt_music": ("Volume de la musique", "Music volume", "Volumen de la música", "Musiklautstärke", "Volume della musica", "Volume da música"),
    "opt_sfx": ("Volume des effets sonores", "Sound effects volume", "Volumen de efectos", "Effektlautstärke", "Volume effetti sonori", "Volume dos efeitos"),
    "opt_keys": ("Commandes (touches)...", "Controls (keys)...", "Controles (teclas)...", "Steuerung (Tasten)...", "Comandi (tasti)...", "Controlos (teclas)..."),
    "ky_title": ("Commandes", "Controls", "Controles", "Steuerung", "Comandi", "Controlos"),
    "ky_reset": ("Réinitialiser les touches", "Reset keys to default", "Restablecer teclas", "Tasten zurücksetzen", "Ripristina i tasti", "Repor teclas"),
    "ky_press": ("Appuie sur une touche...   (Échap : annuler, Suppr : effacer)", "Press a key...   (Esc: cancel, Del: clear)",
                 "Pulsa una tecla...   (Esc: cancelar, Supr: borrar)", "Drücke eine Taste...   (Esc: abbrechen, Entf: löschen)",
                 "Premi un tasto...   (Esc: annulla, Canc: cancella)", "Prime uma tecla...   (Esc: cancelar, Del: apagar)"),
    "ky_hint": ("Flèches : choisir   |   Entrée : changer la touche   |   Échap : retour", "Arrows: choose   |   Enter: rebind   |   Esc: back",
                "Flechas: elegir   |   Enter: cambiar tecla   |   Esc: volver", "Pfeile: wählen   |   Enter: Taste ändern   |   Esc: zurück",
                "Frecce: scegli   |   Invio: cambia tasto   |   Esc: indietro", "Setas: escolher   |   Enter: mudar tecla   |   Esc: voltar"),
    "act_up": ("Haut", "Up", "Arriba", "Hoch", "Su", "Cima"),
    "act_down": ("Bas", "Down", "Abajo", "Runter", "Giù", "Baixo"),
    "act_left": ("Gauche", "Left", "Izquierda", "Links", "Sinistra", "Esquerda"),
    "act_right": ("Droite", "Right", "Derecha", "Rechts", "Destra", "Direita"),
    "act_attack": ("Coup d'épée", "Sword strike", "Golpe de espada", "Schwertschlag", "Colpo di spada", "Golpe de espada"),
    "act_spell": ("Boule de braise", "Ember bolt", "Bola de brasa", "Glutball", "Palla di brace", "Bola de brasa"),
    "act_roll": ("Roulade", "Roll", "Voltereta", "Rolle", "Rotolata", "Rolamento"),
    "act_potion": ("Potion", "Potion", "Poción", "Trank", "Pozione", "Poção"),
    "act_interact": ("Interagir / parler", "Interact / talk", "Interactuar / hablar", "Interagieren / sprechen", "Interagire / parlare", "Interagir / falar"),
    "act_quest": ("Suivi de quête", "Quest tracker", "Seguimiento de misión", "Quest-Anzeige", "Tracciamento missione", "Seguimento de missão"),
    "interact_k": ("%s : interagir", "%s: interact", "%s: interactuar", "%s: interagieren", "%s: interagisci", "%s: interagir"),
    "help_dyn1": ("%s : bouger | Souris : viser | Clic G / %s : frapper | Clic D / %s : boule de braise | %s : roulade",
                  "%s: move | Mouse: aim | Left click / %s: strike | Right click / %s: ember bolt | %s: roll",
                  "%s: moverse | Ratón: apuntar | Clic izq. / %s: golpear | Clic der. / %s: bola de brasa | %s: voltereta",
                  "%s: bewegen | Maus: zielen | Linksklick / %s: schlagen | Rechtsklick / %s: Glutball | %s: rollen",
                  "%s: muovi | Mouse: mira | Clic sx / %s: colpisci | Clic dx / %s: palla di brace | %s: rotola",
                  "%s: mover | Rato: apontar | Clique esq. / %s: atacar | Clique dir. / %s: bola de brasa | %s: rolar"),
    "help_dyn2": ("%s : potion | %s : interagir | %s : quête | Échap : pause | F11 : plein écran",
                  "%s: potion | %s: interact | %s: quest | Esc: pause | F11: fullscreen",
                  "%s: poción | %s: interactuar | %s: misión | Esc: pausa | F11: pantalla completa",
                  "%s: Trank | %s: interagieren | %s: Quest | Esc: Pause | F11: Vollbild",
                  "%s: pozione | %s: interagisci | %s: missione | Esc: pausa | F11: schermo intero",
                  "%s: poção | %s: interagir | %s: missão | Esc: pausa | F11: ecrã inteiro"),
    "no_audio": ("(aucune carte son détectée)", "(no sound device detected)", "(no se detecta dispositivo de sonido)",
                 "(kein Audiogerät gefunden)", "(nessun dispositivo audio rilevato)", "(nenhum dispositivo de som detetado)"),
}

# ---- traduction de l'interface existante en allemand / italien / portugais : (de, it, pt) ----
# (les clés absentes retombent sur l'anglais ; le récit complet reste en FR / EN / ES, les autres langues le lisent en anglais)
PARTIAL = {
    "m_new": ("Neues Spiel", "Nuova partita", "Novo jogo"),
    "m_continue": ("Fortsetzen", "Continua", "Continuar"),
    "m_load": ("Spiel laden", "Carica partita", "Carregar jogo"),
    "m_options": ("Einstellungen", "Impostazioni", "Opções"),
    "m_credits": ("Mitwirkende", "Crediti", "Créditos"),
    "m_quit": ("Beenden", "Esci", "Sair"),
    "m_resume": ("Weiter", "Riprendi", "Retomar"),
    "m_save": ("Speichern", "Salva", "Guardar"),
    "m_journal": ("Tagebuch", "Diario", "Diário"),
    "m_stats": ("Statistiken", "Statistiche", "Estatísticas"),
    "m_menu": ("Zurück zum Hauptmenü", "Torna al menu principale", "Voltar ao menu principal"),
    "back": ("Zurück", "Indietro", "Voltar"),
    "pause": ("PAUSE", "PAUSA", "PAUSA"),
    "subtitle": ("Eine Geschichte aus Feuer, Asche und Entscheidung", "Un racconto di fuoco, cenere e scelta", "Um conto de fogo, cinza e escolha"),
    "by": ("von WILOOPE", "di WILOOPE", "por WILOOPE"),
    "main_hint": ("Pfeile / WASD + Enter oder Maus   |   L: Sprache   |   F11: Vollbild",
                  "Frecce / WASD + Invio, o mouse   |   L: lingua   |   F11: schermo intero",
                  "Setas / WASD + Enter, ou rato   |   L: idioma   |   F11: ecrã inteiro"),
    "opt_title": ("Einstellungen", "Impostazioni", "Opções"),
    "opt_lang": ("Sprache", "Lingua", "Idioma"),
    "opt_timer": ("Timer anzeigen", "Mostra il cronometro", "Mostrar cronómetro"),
    "opt_quest": ("Quest-Anzeige", "Mostra la missione", "Mostrar missão"),
    "opt_shake": ("Bildschirmwackeln", "Tremolio dello schermo", "Tremor do ecrã"),
    "opt_full": ("Vollbild", "Schermo intero", "Ecrã inteiro"),
    "on": ("An", "Attivo", "Ativado"),
    "off": ("Aus", "Disattivo", "Desativado"),
    "opt_hint": ("Hoch/Runter: wählen   |   Links/Rechts oder Enter: ändern   |   Esc: zurück",
                 "Su/Giù: scegli   |   Sx/Dx o Invio: cambia   |   Esc: indietro",
                 "Cima/Baixo: escolher   |   Esq./Dir. ou Enter: mudar   |   Esc: voltar"),
    "opt_diff_note": ("Der Schwierigkeitsgrad wird beim Start eines neuen Spiels gewählt.",
                      "La difficoltà si sceglie all'inizio di una nuova partita.",
                      "A dificuldade escolhe-se ao iniciar um novo jogo."),
    "diff_title": ("Wähle deinen Schwierigkeitsgrad", "Scegli la difficoltà", "Escolhe a dificuldade"),
    "diff_normal": ("Normal", "Normale", "Normal"),
    "diff_hard": ("Schwer", "Difficile", "Difícil"),
    "diff_normal_d": ("Das Abenteuer wie gedacht: fordernd, aber fair.", "L'avventura come era stata pensata: impegnativa, ma giusta.",
                      "A aventura como foi pensada: exigente, mas justa."),
    "diff_hard_d": ("Zähere, härter treffende Gegner, aggressivere Wächter, weniger Heilung, teurerer Tod.",
                    "Nemici più resistenti e violenti, Guardiani più aggressivi, cure ridotte, morte più costosa.",
                    "Inimigos mais resistentes e violentos, Guardiões mais agressivos, cura reduzida, morte mais cara."),
    "diff_ultra_d": ("Für Masochisten: doppelt so zähe und tödliche Gegner, schnelle, dichte Projektile, Wächter rasen ab 70 % Leben, knappe Heilung, der Tod kostet 75 % deiner Splitter.",
                     "Per masochisti: nemici il doppio più duri e letali, proiettili rapidi e fitti, Guardiani infuriati al 70% di vita, cure rare, la morte costa il 75% delle schegge.",
                     "Para masoquistas: inimigos duas vezes mais duros e mortais, projéteis rápidos e densos, Guardiões enfurecidos aos 70% de vida, cura rara, a morte custa 75% dos estilhaços."),
    "diff_hint": ("Hoch/Runter: wählen   |   Enter: starten   |   Esc: zurück", "Su/Giù: scegli   |   Invio: inizia   |   Esc: indietro",
                  "Cima/Baixo: escolher   |   Enter: começar   |   Esc: voltar"),
    "diff_best": ("Bestzeit: %s", "Miglior tempo: %s", "Melhor tempo: %s"),
    "slots_load": ("Spiel laden", "Carica partita", "Carregar jogo"),
    "slots_save": ("Spiel speichern", "Salva partita", "Guardar jogo"),
    "slot_auto": ("Automatisch gespeichert", "Salvataggio automatico", "Gravação automática"),
    "slot_1": ("Speicherplatz 1", "Slot 1", "Espaço 1"),
    "slot_2": ("Speicherplatz 2", "Slot 2", "Espaço 2"),
    "slot_3": ("Speicherplatz 3", "Slot 3", "Espaço 3"),
    "slot_empty": ("- leer -", "- vuoto -", "- vazio -"),
    "slot_info": ("Stufe %d   |   Glutkerne %d/4   |   Fragmente %d/%d   |   %d Min.", "Liv. %d   |   Braci %d/4   |   Frammenti %d/%d   |   %d min",
                  "Nív. %d   |   Brasas %d/4   |   Fragmentos %d/%d   |   %d min"),
    "slot_hint": ("Enter: bestätigen   |   Esc: zurück   |   Entf: Speicherstand löschen", "Invio: conferma   |   Esc: indietro   |   Canc: elimina",
                  "Enter: confirmar   |   Esc: voltar   |   Del: apagar gravação"),
    "slot_deleted": ("Speicherstand gelöscht.", "Salvataggio eliminato.", "Gravação apagada."),
    "slot_confirm": ("Drücke Entf erneut zum Bestätigen.", "Premi di nuovo Canc per confermare.", "Prime Del outra vez para confirmar."),
    "slot_saved": ("Gespeichert in: %s.", "Salvato in: %s.", "Guardado em: %s."),
    "slot_fail": ("Speichern nicht möglich.", "Impossibile scrivere il salvataggio.", "Não foi possível gravar."),
    "slot_empty_msg": ("Dieser Platz ist leer.", "Questo slot è vuoto.", "Este espaço está vazio."),
    "toast_autosave": ("Automatisch gespeichert.", "Salvataggio automatico.", "Gravação automática."),
    "toast_saved": ("Spiel gespeichert.", "Partita salvata.", "Jogo guardado."),
    "toast_savefail": ("Speichern fehlgeschlagen.", "Salvataggio non riuscito.", "Falha ao guardar."),
    "toast_unreadable": ("Speicherstand unlesbar.", "Salvataggio illeggibile.", "Gravação ilegível."),
    "toast_corrupt": ("Speicherstand beschädigt.", "Salvataggio corrotto.", "Gravação corrompida."),
    "cr_by": ("Ein Spiel von", "Un gioco di", "Um jogo de"),
    "cr_concept": ("Konzept & Spieldesign", "Concept e game design", "Conceito e design de jogo"),
    "cr_lore": ("Welt, Hintergrund & Text", "Universo, lore e scrittura", "Universo, história e escrita"),
    "cr_prog": ("Programmierung", "Programmazione", "Programação"),
    "cr_art": ("Art Direction", "Direzione artistica", "Direção artística"),
    "cr_level": ("Leveldesign & Balancing", "Level design e bilanciamento", "Design de níveis e equilíbrio"),
    "cr_made": ("Entwickelt mit Python & pygame", "Realizzato con Python e pygame", "Feito com Python e pygame"),
    "cr_thanks": ("Danke fürs Spielen.", "Grazie per aver giocato.", "Obrigado por jogares."),
    "cr_back": ("Esc: zurück", "Esc: indietro", "Esc: voltar"),
    "jr_title": ("Tagebuch", "Diario", "Diário"),
    "jr_empty": ("Noch nichts. Lies die Stelen und besiege die Wächter.", "Ancora niente. Leggi le stele e sconfiggi i Guardiani.",
                 "Nada por agora. Lê as estelas e vence os Guardiões."),
    "jr_hint": ("Hoch/Runter: blättern   |   Esc: zurück", "Su/Giù: scorri   |   Esc: indietro", "Cima/Baixo: percorrer   |   Esc: voltar"),
    "intro_hint": ("Enter: weiter   |   Esc: Prolog überspringen", "Invio: continua   |   Esc: salta il prologo", "Enter: continuar   |   Esc: saltar o prólogo"),
    "loading": ("Laden...  %d %%", "Caricamento...  %d %%", "A carregar...  %d %%"),
    "hud_hp": ("LP %d/%d", "PV %d/%d", "PV %d/%d"),
    "hud_lvl": ("Stufe %d", "Liv. %d", "Nív. %d"),
    "hud_shards": ("Splitter: %d", "Schegge: %d", "Estilhaços: %d"),
    "hud_potions": ("Tränke (R): %d", "Pozioni (R): %d", "Poções (R): %d"),
    "hud_dmg": ("Schaden: %d", "Danno: %d", "Dano: %d"),
    "float_hp": ("+%d LP", "+%d PV", "+%d PV"),
    "parry": ("Parade!", "Parata!", "Defesa!"),
    "level_up": ("Stufe %d!", "Livello %d!", "Nível %d!"),
    "float_shards": ("+%d Splitter", "+%d schegge", "+%d estilhaços"),
    "float_potion": ("Trank!", "Pozione!", "Poção!"),
    "respawn_banner": ("Deine Glut schlägt noch...", "La tua brace batte ancora...", "A tua brasa ainda bate..."),
    "dead_title": ("DU ERLISCHST...", "TI SPEGNI...", "APAGAS-TE..."),
    "dead_sub": ("Die Asche bedeckt dich. Doch deine Glut schlägt noch.", "La cenere ti ricopre. Ma la tua brace batte ancora.",
                 "A cinza cobre-te. Mas a tua brasa ainda bate."),
    "dead_hint": ("Enter: in Port-Cendre wiedergeboren (du verlierst %d %% deiner Splitter)", "Invio: rinasci a Port-Cendre (perdi il %d %% delle schegge)",
                  "Enter: renascer em Port-Cendre (perdes %d %% dos estilhaços)"),
    "dlg_hint_menu": ("Hoch/Runter: wählen | Enter: bestätigen", "Su/Giù: scegli | Invio: conferma", "Cima/Baixo: escolher | Enter: confirmar"),
    "dlg_hint_next": ("F / Enter: weiter", "F / Invio: continua", "F / Enter: continuar"),
    "dlg_leave": ("Gehen", "Andare via", "Sair"),
    "stele_prefix": ("Stele: %s", "Stele: %s", "Estela: %s"),
    "stele_fragment": ("(Erinnerungsfragment %d/%d - deinem Tagebuch hinzugefügt.)", "(Frammento di memoria %d/%d - aggiunto al Diario.)",
                       "(Fragmento de memória %d/%d - adicionado ao Diário.)"),
    "altar_name": ("Altar der Flamme", "Altare della Fiamma", "Altar da Chama"),
    "opt_end1": ("Die Flamme neu entzünden (ihr dein Herz geben)", "Riaccendere la Fiamma (darle il tuo cuore)", "Reacender a Chama (dar-lhe o teu coração)"),
    "opt_end2": ("Die Glutkerne für dich behalten", "Tenere le Braci per te", "Ficar com as Brasas"),
    "opt_end3": ("Die Flamme mit allen teilen  [wahres Ende]", "Dividere la Fiamma con tutti  [vero finale]", "Partilhar a Chama com todos  [final verdadeiro]"),
    "svc_rest_opt": ("Am Feuer ausruhen (volle Heilung + speichern)", "Riposare accanto al fuoco (cura completa + salva)", "Descansar junto ao fogo (cura total + guardar)"),
    "svc_rest_msg": ("Das Feuer wärmt dich. Deine Kräfte kehren zurück. (Gespeichert)", "Il fuoco ti scalda. Le forze tornano. (Partita salvata)",
                     "O fogo aquece-te. As forças voltam. (Jogo guardado)"),
    "svc_forge_opt": ("Klinge schärfen (+3 Schaden) - %d Splitter", "Affilare la lama (+3 danno) - %d schegge", "Afiar a lâmina (+3 de dano) - %d estilhaços"),
    "svc_forge_msg": ("Torvald schärft deine Klinge. Schaden: %d.", "Torvald affila la tua lama. Danno: %d.", "Torvald afia a tua lâmina. Dano: %d."),
    "svc_shop_opt": ("Glutrank kaufen - %d Splitter", "Comprare una pozione di brace - %d schegge", "Comprar uma poção de brasa - %d estilhaços"),
    "svc_shop_msg": ("Du hast jetzt %d Trank/Tränke.", "Ora hai %d pozione/i.", "Tens agora %d poção(ões)."),
    "svc_nomoney": ("Nicht genug Splitter.", "Schegge insufficienti.", "Estilhaços insuficientes."),
    "braise_got": ("Du erhältst: %s! (%d/4)", "Ottieni: %s! (%d/4)", "Obténs: %s! (%d/4)"),
    "braises_all": ("Die vier Glutkerne brennen in deiner Brust. Kehre zum Altar von Port-Cendre zurück.",
                    "Le quattro Braci ardono nel tuo petto. Torna all'altare di Port-Cendre.", "As quatro Brasas ardem-te no peito. Volta ao altar de Port-Cendre."),
    "q_main": ("HAUPTQUEST", "MISSIONE PRINCIPALE", "MISSÃO PRINCIPAL"),
    "q_side": ("NEBENQUEST", "MISSIONE SECONDARIA", "MISSÃO SECUNDÁRIA"),
    "q_updated": ("Quest aktualisiert", "Missione aggiornata", "Missão atualizada"),
    "q0_t": ("Maëlys finden", "Trova Maëlys", "Encontrar Maëlys"),
    "q1_t": ("Die vier Glutkerne", "Le quattro Braci", "As quatro Brasas"),
    "q2_t": ("Die Flamme neu entzünden", "Riaccendere la Fiamma", "Reacender a Chama"),
    "qs_t": ("Erinnerung an Aethel", "Memoria di Aethel", "Memória de Aethel"),
    "st_title": ("Statistiken", "Statistiche", "Estatísticas"),
    "st_time": ("Spielzeit", "Tempo di gioco", "Tempo de jogo"),
    "st_diff": ("Schwierigkeit", "Difficoltà", "Dificuldade"),
    "st_level": ("Stufe", "Livello", "Nível"),
    "st_kills": ("Besiegte Monster", "Mostri sconfitti", "Monstros derrotados"),
    "st_bosses": ("Besiegte Wächter", "Guardiani sconfitti", "Guardiões derrotados"),
    "st_deaths": ("Tode", "Morti", "Mortes"),
    "st_hits": ("Mal getroffen", "Volte colpito", "Vezes atingido"),
    "st_dmg_taken": ("Erlittener Schaden", "Danno subito", "Dano sofrido"),
    "st_dmg_dealt": ("Verursachter Schaden", "Danno inflitto", "Dano causado"),
    "st_nohit": ("Längste Serie ohne Treffer", "Serie più lunga senza essere colpito", "Maior série sem ser atingido"),
    "st_swings": ("Schwerthiebe (Genauigkeit)", "Colpi di spada (precisione)", "Golpes de espada (precisão)"),
    "st_spells": ("Glutbälle (Genauigkeit)", "Palle di brace (precisione)", "Bolas de brasa (precisão)"),
    "st_parries": ("Abgewehrte Projektile", "Proiettili parati", "Projéteis defendidos"),
    "st_rolls": ("Rollen", "Rotolate", "Rolamentos"),
    "st_potions": ("Getrunkene Tränke", "Pozioni bevute", "Poções bebidas"),
    "st_shards": ("Gesammelte Splitter", "Schegge raccolte", "Estilhaços recolhidos"),
    "st_lore": ("Erinnerungsfragmente", "Frammenti di memoria", "Fragmentos de memória"),
    "st_crits": ("Kritische Treffer", "Colpi critici", "Golpes críticos"),
    "st_newrecord": ("Neuer Rekord!", "Nuovo record!", "Novo recorde!"),
    "st_hint": ("Esc: zurück", "Esc: indietro", "Esc: voltar"),
    "end_hint": ("Enter: Statistiken ansehen", "Invio: vedi le statistiche", "Enter: ver estatísticas"),
    "end_hint2": ("Enter: zurück zum Menü", "Invio: torna al menu", "Enter: voltar ao menu"),
    "end_stats_title": ("Dein Durchlauf", "La tua partita", "A tua partida"),
}
for _i, _code in enumerate(LANG_ORDER):
    UI.setdefault(_code, {})
    for _k, _v in NEWKEYS.items():
        UI[_code][_k] = _v[_i]
for _j, _code in enumerate(("de", "it", "pt")):
    for _k, _v in PARTIAL.items():
        UI[_code][_k] = _v[_j]


# ---- réglages supplémentaires (langue, volumes, touches) ----
ACTIONS = ["up", "down", "left", "right", "attack", "spell", "roll", "potion", "interact", "quest"]
DEFAULT_BINDS = {
    "up": [pygame.K_z, pygame.K_w, pygame.K_UP], "down": [pygame.K_s, None, pygame.K_DOWN],
    "left": [pygame.K_q, pygame.K_a, pygame.K_LEFT], "right": [pygame.K_d, None, pygame.K_RIGHT],
    "attack": [pygame.K_SPACE, None, None], "spell": [pygame.K_e, None, None],
    "roll": [pygame.K_LSHIFT, pygame.K_RSHIFT, None], "potion": [pygame.K_r, None, None],
    "interact": [pygame.K_f, pygame.K_RETURN, pygame.K_KP_ENTER], "quest": [pygame.K_TAB, None, None],
}


def load_plus():
    p = dict(lang=SET["lang"], music=7, sfx=8, binds=copy.deepcopy(DEFAULT_BINDS))
    try:
        with io.open(PLUS_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        if d.get("lang") in dict(LANGS):
            p["lang"] = d["lang"]
        p["music"] = int(clamp(int(d.get("music", 7)), 0, 10))
        p["sfx"] = int(clamp(int(d.get("sfx", 8)), 0, 10))
        for a in ACTIONS:
            v = d.get("binds", {}).get(a)
            if isinstance(v, list) and len(v) == 3:
                p["binds"][a] = [x if isinstance(x, int) else None for x in v]
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    return p


def save_plus():
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        with io.open(PLUS_FILE, "w", encoding="utf-8") as f:
            json.dump(PLUS, f, ensure_ascii=False)
    except OSError:
        pass


PLUS = load_plus()
SET["lang"] = PLUS["lang"]


def key_label(k):
    return "-" if k is None else pygame.key.name(k).upper()


def _kl(act):
    return key_label(next((k for k in PLUS["binds"][act] if k is not None), None))


# ---- traduction : repli sur l'anglais (et non plus sur le français) pour les langues ajoutées ----
def tr(key, *a):
    lang = SET["lang"]
    s = UI.get(lang, {}).get(key)
    if s is None:
        s = UI["en"].get(key)
    if s is None:
        s = UI["fr"].get(key, key)
    if key == "interact":
        s = UI.get(lang, UI["en"]).get("interact_k", UI["en"]["interact_k"]) % _kl("interact")
    elif key == "hud_potions":
        s = s.replace("(R)", "(%s)" % _kl("potion"))
    return s % a if a else s


def ct(key):
    c = CT.get(SET["lang"]) or CT["en"]
    return c[key] if key in c else CT["fr"][key]


# ---- AUDIO : sons et musiques synthétisés ----
SCALES = {"minor": [0, 2, 3, 5, 7, 8, 10], "major": [0, 2, 4, 5, 7, 9, 11], "dorian": [0, 2, 3, 5, 7, 9, 10],
          "phryg": [0, 1, 3, 5, 7, 8, 10]}
# nom: (note racine MIDI, gamme, tempo, progression, densité mélodie, percussions, timbre)
TRACKS = {
    "menu":   (57, "minor", 66, [0, 5, 3, 4], 0.35, False, "soft"),
    "hub":    (50, "major", 76, [0, 3, 4, 3], 0.50, False, "soft"),
    "forest": (52, "dorian", 70, [0, 3, 0, 4], 0.40, False, "soft"),
    "marsh":  (45, "phryg", 56, [0, 1, 0, 6], 0.22, False, "bell"),
    "ruins":  (50, "minor", 62, [0, 5, 6, 4], 0.30, False, "bell"),
    "ash":    (40, "phryg", 84, [0, 1, 0, 1], 0.28, True, "saw"),
    "boss":   (43, "minor", 132, [0, 0, 5, 6], 0.70, True, "saw"),
}
BIOME_TRACK = {0: "hub", 1: "forest", 2: "marsh", 3: "ruins", 4: "ash"}


class Audio:
    def __init__(self, music=7, sfx=8):
        self.ok = False
        self.mv, self.sv = music / 10.0, sfx / 10.0
        self.sfx, self.tracks = {}, {}
        self.cur, self.ci, self.cur_snd = None, 0, None
        try:
            # Certaines installations Linux de Pygame n'incluent pas le module mixer.
            # Le jeu doit quand même pouvoir démarrer sans audio.
            mixer = getattr(pygame, "mixer", None)
            if mixer is None:
                return
            if mixer.get_init():
                mixer.quit()
            mixer.init(22050, -16, 1, 512)
            init = mixer.get_init()
            if not init or init[1] != -16:
                return
            mixer.set_num_channels(20)
            mixer.set_reserved(2)
            self.rate, self.nch = init[0], init[2]
            self.ok = True
            self.build_sfx()
            threading.Thread(target=self.build_tracks, daemon=True).start()
        except Exception:
            # L'audio est facultatif : une erreur du périphérique ou du mixer
            # ne doit pas empêcher le lancement du jeu.
            self.ok = False

    def to_sound(self, buf, peak):
        m = max(max(abs(v) for v in buf), 1e-6)
        k = 32767.0 * peak / m
        a = array.array("h", [int(v * k) for v in buf])
        if self.nch == 2:
            b = array.array("h", [0]) * (2 * len(a))
            b[0::2] = a
            b[1::2] = a
            a = b
        return pygame.mixer.Sound(buffer=a.tobytes())

    def osc(self, kind, f, dur, f2=None, att=0.004, decay=1.6, vol=1.0):
        R = self.rate
        n = int(dur * R)
        out = [0.0] * n
        ph = 0.0
        w = 6.2831853 / R
        for i in range(n):
            t = i / n
            ph += w * (f if f2 is None else f + (f2 - f) * t)
            if kind == "sin":
                v = math.sin(ph)
            elif kind == "saw":
                v = ((ph / 6.2831853) % 1.0) * 2 - 1
            elif kind == "sq":
                v = 1.0 if math.sin(ph) > 0 else -1.0
            else:
                v = abs(((ph / 6.2831853) % 1.0) * 4 - 2) - 1
            out[i] = v * min(1.0, i / max(1, att * R)) * (1 - t) ** decay * vol
        return out

    def noise(self, dur, vol=1.0, lp=0.3, decay=2.0, att=0.003):
        R = self.rate
        n = int(dur * R)
        out, y = [0.0] * n, 0.0
        for i in range(n):
            y += lp * (random.uniform(-1, 1) - y)
            t = i / n
            out[i] = y * min(1.0, i / max(1, att * R)) * (1 - t) ** decay * vol
        return out

    def mix(self, *parts):
        n = max(int(off * self.rate) + len(p) for off, p in parts)
        out = [0.0] * n
        for off, p in parts:
            o = int(off * self.rate)
            for i, v in enumerate(p):
                out[o + i] += v
        return out

    def note(self, midi):
        return 440.0 * 2 ** ((midi - 69) / 12.0)

    def build_sfx(self):
        o, nz, mx, nt = self.osc, self.noise, self.mix, self.note
        d = {}
        d["swing"] = (mx((0, nz(0.16, 0.9, 0.5, 1.4)), (0, o("sin", 420, 0.14, 160, vol=0.3))), 0.55)
        d["hit"] = (mx((0, nz(0.1, 0.9, 0.6, 2.5)), (0, o("sin", 160, 0.12, 60, vol=0.9))), 0.7)
        d["hurt"] = (mx((0, o("saw", 230, 0.28, 90, vol=0.6)), (0, nz(0.2, 0.5, 0.4, 2))), 0.8)
        d["spell"] = (mx((0, o("sin", 280, 0.34, 980, decay=0.8, vol=0.6)), (0, nz(0.34, 0.35, 0.2, 1.2))), 0.55)
        d["roll"] = (nz(0.22, 0.8, 0.08, 1.0, att=0.06), 0.45)
        d["potion"] = (mx(*[(0.06 * i, o("sin", 520 + 90 * i, 0.12, 700 + 90 * i, vol=0.6)) for i in range(4)]), 0.6)
        d["parry"] = (mx((0, o("sin", 1250, 0.18, decay=3, vol=0.6)), (0, o("sin", 1870, 0.14, decay=3, vol=0.4)), (0, nz(0.04, 0.6, 0.7, 2))), 0.6)
        d["kill"] = (mx((0, o("sin", 190, 0.22, 55, vol=0.9)), (0, nz(0.18, 0.5, 0.3, 2))), 0.6)
        d["coin"] = (mx((0, o("sq", 988, 0.07, decay=0.5, vol=0.4)), (0.07, o("sq", 1319, 0.16, decay=1.5, vol=0.4))), 0.5)
        d["levelup"] = (mx(*[(0.1 * i, o("tri", nt(m), 0.35, vol=0.6)) for i, m in enumerate((67, 72, 76, 79, 84))]), 0.65)
        d["select"] = (o("sq", 660, 0.09, 880, decay=1.0, vol=0.35), 0.45)
        d["move"] = (o("sq", 440, 0.04, decay=0.8, vol=0.3), 0.35)
        d["death"] = (mx((0, o("saw", 300, 1.0, 40, decay=1.0, vol=0.6)), (0, nz(0.9, 0.3, 0.1, 1.5))), 0.8)
        d["boss"] = (mx((0, o("saw", 70, 0.9, 50, decay=0.8, vol=0.8)), (0, nz(0.9, 0.6, 0.12, 1.0, att=0.1))), 0.8)
        d["foyer"] = (mx((0, nz(0.5, 0.8, 0.5, 1.5, att=0.05)), (0, o("sin", 110, 0.5, decay=1.0, vol=0.5))), 0.55)
        d["quest"] = (mx((0, o("tri", nt(64), 0.2, vol=0.6)), (0.12, o("tri", nt(71), 0.3, vol=0.6))), 0.55)
        for name, (buf, peak) in d.items():
            self.sfx[name] = (self.to_sound(buf, peak), peak)

    def make_track(self, spec, seed):
        root, scale, bpm, prog, dens, perc, tone = spec
        rnd = random.Random(seed)
        R = self.rate
        sc = SCALES[scale]

        def pitch(deg):
            return root + sc[deg % 7] + 12 * (deg // 7)

        beat = 60.0 / bpm
        total = int(4 * 4 * beat * R)
        buf = [0.0] * total

        def add(start_s, samples, g):
            o = int(start_s * R)
            for i, v in enumerate(samples):
                if o + i < total:
                    buf[o + i] += v * g
            time.sleep(0)  # laisse respirer la boucle de jeu

        wave = "saw" if tone == "saw" else ("tri" if tone == "soft" else "sin")
        for bar, deg in enumerate(prog):
            t0 = bar * 4 * beat
            for k in (0, 2, 4):
                f = self.note(pitch(deg + k) + 12)
                add(t0, self.osc("sin" if tone != "saw" else "tri", f, 4 * beat * 0.98, decay=0.35, att=0.25), 0.22)
            add(t0, self.osc("sin", self.note(pitch(deg) - 12), 2 * beat, decay=0.9, att=0.02), 0.5)
            add(t0 + 2 * beat, self.osc("sin", self.note(pitch(deg) - 12 + (7 if tone == "saw" else 0)), 2 * beat * 0.95, decay=0.9, att=0.02), 0.4)
            pos = rnd.randint(2, 6)
            for s in range(8):
                if rnd.random() < dens:
                    pos = clamp(pos + rnd.choice((-2, -1, 0, 1, 2)), 0, 9)
                    add(t0 + s * beat * 0.5, self.osc(wave, self.note(pitch(pos + 7)), beat * rnd.choice((0.5, 0.5, 1.0)), decay=2.2, att=0.006), 0.3)
            if perc:
                for b in range(4):
                    add(t0 + b * beat, self.osc("sin", 110, 0.16, 38, decay=2.5), 0.8)
                    add(t0 + (b + 0.5) * beat, self.noise(0.04, 0.8, 0.8, 2.5), 0.22)
        return self.to_sound(buf, 0.6)

    def build_tracks(self):
        try:
            for i, name in enumerate(("menu", "hub", "forest", "boss", "marsh", "ruins", "ash")):
                self.tracks[name] = self.make_track(TRACKS[name], 100 + i)
        except Exception:  # la musique est facultative : jamais de plantage pour ça
            pass

    def play(self, name, vol=1.0):
        if not self.ok or self.sv <= 0:
            return
        e = self.sfx.get(name)
        if e:
            e[0].set_volume(clamp(self.sv * vol, 0.0, 1.0))
            e[0].play()

    def set_music(self, name):
        if not self.ok or name == self.cur:
            return
        snd = self.tracks.get(name) if name else None
        if name and snd is None:
            return  # pas encore généré : on réessaiera
        pygame.mixer.Channel(self.ci).fadeout(900)
        self.ci = 1 - self.ci
        self.cur, self.cur_snd = name, snd
        if snd:
            snd.set_volume(self.mv)
            pygame.mixer.Channel(self.ci).play(snd, loops=-1, fade_ms=1500)

    def set_volumes(self, music, sfx):
        self.mv, self.sv = music / 10.0, sfx / 10.0
        if self.ok and self.cur_snd:
            self.cur_snd.set_volume(self.mv)


# ---- touches : proxy qui redirige les touches par défaut (Espace, E) vers les touches choisies ----
_REAL_GP = pygame.key.get_pressed


class _KeyProxy:
    def __init__(self, real, game):
        self.real, self.g = real, game

    def __getitem__(self, k):
        if k == pygame.K_SPACE:
            return self.g.held("attack", self.real)
        if k == pygame.K_e:
            return self.g.held("spell", self.real)
        return self.real[k]


_BaseGame = Game


class Game2(_BaseGame):
    def __init__(self):
        self.audio = Audio(PLUS["music"], PLUS["sfx"])
        self.mus_t, self.rebind, self.kcol = 0.0, None, 0
        super().__init__()

    # -- touches --
    def bound(self, act, key):
        return key in PLUS["binds"][act]

    def held(self, act, keys):
        return any(keys[c] for c in PLUS["binds"][act] if c is not None)

    def move_vec(self):
        k = _REAL_GP()
        ax = int(self.held("right", k)) - int(self.held("left", k))
        ay = int(self.held("down", k)) - int(self.held("up", k))
        n = math.hypot(ax, ay)
        return (ax / n, ay / n) if n else (0.0, 0.0)

    def update(self, dt):
        self.mus_t -= dt
        if self.mus_t <= 0:
            self.mus_t = 0.4
            self.update_music()
        if self.state == "play":
            real = _REAL_GP()
            pygame.key.get_pressed = lambda: _KeyProxy(real, self)
            try:
                super().update(dt)
            finally:
                pygame.key.get_pressed = _REAL_GP
        else:
            super().update(dt)

    def on_key(self, key):
        K = pygame
        s = self.state
        if s == "keys":
            self.keys_input(key)
            return
        if key == K.K_F11:
            super().on_key(key)
            return
        if s == "play":
            if key == K.K_ESCAPE:
                super().on_key(key)
            elif self.bound("interact", key):
                self.interact()
            elif self.bound("roll", key):
                self.roll()
            elif self.bound("potion", key):
                self.use_potion()
            elif self.bound("quest", key):
                SET["quest"] = not SET["quest"]
                save_settings()
            return
        up = key in (K.K_UP, K.K_z, K.K_w)
        down = key in (K.K_DOWN, K.K_s)
        confirm = key in (K.K_RETURN, K.K_KP_ENTER, K.K_SPACE, K.K_f)
        if s in ("main", "pause", "slots", "options", "diff", "dialogue") and (up or down or confirm):
            self.audio.play("move" if (up or down) else "select", 0.8)
        super().on_key(key)

    # -- options : volumes + commandes --
    def vol_bar(self, v):
        return "<  [%s%s]  %d  >" % ("#" * v, "-" * (10 - v), v)

    def change_vol(self, k, d):
        v = PLUS[k]
        PLUS[k] = 0 if (d > 0 and v >= 10) else int(clamp(v + d, 0, 10))
        self.audio.set_volumes(PLUS["music"], PLUS["sfx"])
        save_plus()
        if k == "sfx":
            self.audio.play("hit")

    def options_items(self):
        items = super().options_items()
        back = items.pop()
        items += [(tr("opt_music") + " : " + self.vol_bar(PLUS["music"]), lambda d: self.change_vol("music", d)),
                  (tr("opt_sfx") + " : " + self.vol_bar(PLUS["sfx"]), lambda d: self.change_vol("sfx", d)),
                  (tr("opt_keys"), lambda d: self.open_keys()), back]
        return items

    def opt_lang(self, d=1):
        super().opt_lang(d)
        PLUS["lang"] = SET["lang"]
        save_plus()

    def open_keys(self):
        self.set_state("keys")
        self.kcol = 0

    def keys_input(self, key):
        K = pygame
        if self.rebind:
            act, col = self.rebind
            self.rebind = None
            b = PLUS["binds"]
            if key == K.K_ESCAPE:
                return
            if key == K.K_DELETE:
                b[act][col] = None
            elif key != K.K_F11:
                for a in ACTIONS:
                    for i in range(3):
                        if b[a][i] == key:
                            b[a][i] = None
                b[act][col] = key
            save_plus()
            self.audio.play("select")
            return
        n = len(ACTIONS) + 2
        up = key in (K.K_UP, K.K_z, K.K_w)
        down = key in (K.K_DOWN, K.K_s)
        confirm = key in (K.K_RETURN, K.K_KP_ENTER, K.K_SPACE)
        if up or down:
            self.sel = (self.sel + (-1 if up else 1)) % n
            self.audio.play("move", 0.8)
        elif key in (K.K_LEFT, K.K_q, K.K_a):
            self.kcol = (self.kcol - 1) % 3
        elif key in (K.K_RIGHT, K.K_d):
            self.kcol = (self.kcol + 1) % 3
        elif key == K.K_ESCAPE:
            self.set_state("options")
            self.sel = 7
        elif confirm:
            self.audio.play("select", 0.8)
            if self.sel < len(ACTIONS):
                self.rebind = (ACTIONS[self.sel], self.kcol)
            elif self.sel == len(ACTIONS):
                PLUS["binds"] = copy.deepcopy(DEFAULT_BINDS)
                save_plus()
            else:
                self.set_state("options")
                self.sel = 7

    def draw(self):
        if self.state == "keys":
            self.draw_keys()
        else:
            super().draw()

    def draw_keys(self):
        screen.fill((10, 8, 12))
        self.draw_ash((150, 140, 130))
        draw_text(tr("ky_title"), F_L, (255, 225, 160), (W // 2, 44), center=True)
        n = len(ACTIONS)
        for i in range(n + 2):
            y = 90 + i * 40
            sel = i == self.sel
            pygame.draw.rect(screen, (60, 34, 24) if sel else (24, 18, 22), (130, y, W - 260, 36), border_radius=6)
            pygame.draw.rect(screen, (230, 170, 80) if sel else (60, 52, 46), (130, y, W - 260, 36), 1, border_radius=6)
            col = (255, 225, 150) if sel else (215, 205, 190)
            if i < n:
                a = ACTIONS[i]
                draw_text(tr("act_" + a), F_M, col, (150, y + 7))
                for c in range(3):
                    cx = 430 + c * 150
                    cs = sel and c == self.kcol
                    pygame.draw.rect(screen, (110, 64, 36) if cs else (36, 28, 30), (cx, y + 3, 140, 30), border_radius=5)
                    lab = "..." if (self.rebind and self.rebind == (a, c)) else key_label(PLUS["binds"][a][c])
                    draw_text(lab[:14], F_S, (255, 235, 170) if cs else (200, 192, 178), (cx + 70, y + 18), center=True)
            else:
                draw_text(tr("ky_reset") if i == n else tr("back"), F_M, col, (W // 2, y + 18), center=True)
        if self.rebind:
            draw_text(tr("ky_press"), F_M, (255, 230, 130), (W // 2, 598), center=True)
        draw_text(tr("ky_hint"), F_S, (130, 125, 115), (W // 2, H - 14), center=True)

    def draw_options(self):
        super().draw_options()
        if not self.audio.ok:
            draw_text(tr("no_audio"), F_S, (230, 150, 130), (W // 2, 590), center=True)

    def draw_help(self):
        a = int(255 * clamp((14 - self.play_time) / 2, 0, 1))
        mv = "".join(_kl(x) for x in ("up", "left", "down", "right"))
        draw_text(tr("help_dyn1", mv, _kl("attack"), _kl("spell"), _kl("roll")), F_S, (220, 215, 200), (W // 2, H - 40), center=True, alpha=a)
        draw_text(tr("help_dyn2", _kl("potion"), _kl("interact"), _kl("quest")), F_S, (220, 215, 200), (W // 2, H - 18), center=True, alpha=a)

    # -- musique --
    def update_music(self):
        s = self.state
        if self.p is None or self.world is None or s in ("loading", "main", "slots", "options", "keys", "diff", "credits", "intro"):
            name = "menu"
        elif s == "ending":
            name = "hub"
        elif s == "dead":
            name = None
        elif any(b.active and b.hp > 0 for b in self.bosses.values()):
            name = "boss"
        else:
            name = BIOME_TRACK[self.tile_biome(self.p.x, self.p.y)]
        self.audio.set_music(name)

    # -- effets sonores : on appelle le code d'origine, puis on joue le son --
    def attack(self):
        n = self.stats["parries"]
        super().attack()
        self.audio.play("swing")
        if self.stats["parries"] > n:
            self.audio.play("parry")

    def cast(self):
        n = self.stats["spells"]
        super().cast()
        if self.stats["spells"] > n:
            self.audio.play("spell")

    def roll(self):
        n = self.stats["rolls"]
        super().roll()
        if self.stats["rolls"] > n:
            self.audio.play("roll")

    def use_potion(self):
        n = self.stats["potions"]
        super().use_potion()
        if self.stats["potions"] > n:
            self.audio.play("potion")

    def hurt_player(self, dmg):
        r = super().hurt_player(dmg)
        if r:
            self.audio.play("death" if self.state == "dead" else "hurt")
        return r

    def damage_enemy(self, e, dmg, kx=0.0, ky=0.0, crit=False):
        super().damage_enemy(e, dmg, kx, ky, crit)
        self.audio.play("hit", 0.6)

    def kill(self, e):
        super().kill(e)
        self.audio.play("kill")

    def gain_xp(self, n):
        lv = self.p.lvl
        super().gain_xp(n)
        if self.p.lvl > lv:
            self.audio.play("levelup")

    def interact(self):
        it = self.near
        super().interact()
        if it:
            self.audio.play("quest" if it["type"] == "stele" else "select")

    def update_boss(self, b, dt):
        was = b.active
        super().update_boss(b, dt)
        if b.active and not was:
            self.audio.play("boss")

    def svc_rest(self):
        self.audio.play("foyer")
        return super().svc_rest()

    def svc_forge(self):
        g = self.p.shards
        r = super().svc_forge()
        if self.p.shards < g:
            self.audio.play("coin")
        return r

    def svc_potion(self):
        g = self.p.shards
        r = super().svc_potion()
        if self.p.shards < g:
            self.audio.play("coin")
        return r


Game = Game2


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