#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ajoute à "Cendres d'Aethel" : touches personnalisables, sons et musiques générés par le code
(rien à télécharger), volumes, et langues supplémentaires (Deutsch, Italiano, Português).

Utilisation :  python ajouter_options.py [cendres_d_aethel.py]
Une copie de sécurité (.bak) est créée avant toute modification.
"""
import os
import shutil
import sys

MARK = "EXTENSION : touches personnalisables"
ANCHOR = "\n\ndef main():\n    g = Game()"

BLOCK = r'''# ==========================================================================
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
            if pygame.mixer.get_init():
                pygame.mixer.quit()
            pygame.mixer.init(22050, -16, 1, 512)
            init = pygame.mixer.get_init()
            if not init or init[1] != -16:
                return
            pygame.mixer.set_num_channels(20)
            pygame.mixer.set_reserved(2)
            self.rate, self.nch = init[0], init[2]
            self.ok = True
            self.build_sfx()
            threading.Thread(target=self.build_tracks, daemon=True).start()
        except pygame.error:
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


'''


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "cendres_d_aethel.py")
    if not os.path.isfile(path):
        sys.exit("Fichier introuvable : %s\nUsage : python ajouter_options.py chemin/vers/cendres_d_aethel.py" % path)
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    if MARK in src:
        sys.exit("Ce fichier contient déjà l'extension : rien à faire.")
    if src.count(ANCHOR) != 1:
        sys.exit("Point d'insertion introuvable (def main(): g = Game()). Ce n'est pas la bonne version du jeu ?")
    shutil.copyfile(path, path + ".bak")
    src = src.replace(ANCHOR, "\n\n" + BLOCK.rstrip("\n") + "\n" + ANCHOR)
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    print("OK : extension ajoutée à %s (sauvegarde : %s.bak)" % (path, path))


if __name__ == "__main__":
    main()