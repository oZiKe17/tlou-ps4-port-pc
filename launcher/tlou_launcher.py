#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Responsive dark launcher for the TLOU Remastered Linux port."""
from __future__ import annotations

import json
import math
import os
import queue
import shutil
import subprocess
import sys
import threading
import ctypes
import ctypes.util
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

VENDOR_DIR = Path(__file__).resolve().parent / "vendor"
if VENDOR_DIR.is_dir() and str(VENDOR_DIR) not in sys.path:
    sys.path.insert(0, str(VENDOR_DIR))
try:
    from tkinterdnd2 import COPY as DND_COPY, DND_FILES, Tk as DragDropTk
except (ImportError, OSError):
    DND_COPY, DND_FILES, DragDropTk = "copy", "DND_Files", None

REPO = Path(__file__).resolve().parent.parent
PORT = REPO / "port" if (REPO / "port" / "run.sh").is_file() else REPO
RUN_LOGGED = REPO / "run_logged.sh"
LAUNCHER_VERSION = "1.0.0"
SETTINGS_PATH = Path.home() / ".config" / "tlou-launcher" / "settings.json"
BACKGROUND_IMAGE = Path(__file__).resolve().parent / "assets" / "neural_glass_background.png"
SIDEBAR_BACKGROUND_IMAGE = Path(__file__).resolve().parent / "assets" / "neural_glass_sidebar.png"
CONTROL_BACKGROUND_IMAGE = Path(__file__).resolve().parent / "assets" / "neural_glass_control.png"
HERO_IMAGE = Path(__file__).resolve().parent / "assets" / "neural_glass_banner.png"
ICON_IMAGE = Path(__file__).resolve().parent / "assets" / "tlou_guitar_icon.png"
GAME_ICON_BMP = Path(__file__).resolve().parent / "assets" / "tlou_guitar_icon.bmp"
HEADLINE_FONT_FILE = Path(__file__).resolve().parent / "assets" / "fonts" / "HeadlinerNo.45 DEMO.ttf"

# Frosted graphite panels, a soft monochrome neural backdrop, and a white neon accent.
THEME = {
    "bg": "#15181f", "sidebar": "#1b2028", "panel": "#1d222a", "panel2": "#242a33",
    "panel3": "#2e3540", "border": "#414854", "border_hi": "#59616e",
    "glass": "#303742", "shine": "#8b94a2", "bubble": "#454e5d",
    "text": "#f0f2f7", "muted": "#a0a6b1", "dim": "#68707c",
    "green": "#f2f4ff", "green_hi": "#ffffff", "green_low": "#454d59",
    "yellow": "#f0cb64", "yellow_hi": "#ffe28a",
    "red": "#e17d82", "black": "#090b0e",
}
FONT = "DejaVu Sans"
MONO = "DejaVu Sans Mono"
HEADLINE_FONT = "Headliner No. 45"
DEFAULTS = {
    "game_dir": "", "display_mode": "Windowed", "render_resolution": "native",
    "engine_fps": "60", "fps_limit": "60", "vram": "5600", "show_fps": True,
    "language": "es-LA", "region": "auto", "audio_device": "default",
    "audio_volume": "100", "gpu_device": "auto",
    "upscaler": "0", "upscale_preset": "1", "fsr_sharpness": "50", "native_audio": True, "dmem_mb": "4608", "fault_window": "256",
    "copy_threads": "auto", "staging_keep": "auto", "phys_cores": "0", "object_motion": "1",
    "async_shaders": "1", "deferred_readback": "1", "stale_readback": "1",
    "hot_pages": "0", "write_merge": "1", "auto_gyro": "0",
}
ADVANCED = [
    ("dmem_mb", "TLG_DMEM_MB", "Memoria directa", "MiB · retail: 4608"),
    ("fault_window", "TLG_FAULT_WINDOW", "Ventana de faults", "KiB"),
    ("copy_threads", "TLG_COPY_THREADS", "Hilos de copia", "auto = según CPUs disponibles"),
    ("staging_keep", "TLG_STAGING_KEEP_MB", "Reserva de staging", "auto = 128 / 256 / 512 MiB según RAM"),
    ("phys_cores", "TLG_PHYS_CORES", "Planificación de CPU", "Elige hilos lógicos o núcleos físicos"),
    ("object_motion", "TLG_OBJECT_MOTION", "Movimiento de objetos", "Mejora el tratamiento de vectores de movimiento"),
    ("async_shaders", "TLG_ASYNC_SHADERS", "Shaders asíncronos", "Compila shaders sin bloquear el hilo principal"),
    ("deferred_readback", "TLG_DEFERRED_READBACK", "Readback diferido", "Reduce esperas entre CPU y GPU"),
    ("stale_readback", "TLG_STALE_READBACK", "Readback anterior", "Reutiliza la lectura más reciente disponible"),
    ("hot_pages", "TLG_HOT_PAGES", "Hot pages · experimental", "Desactivado recomendado: probado con caída de FPS/timeouts"),
    ("write_merge", "TLG_WRITE_MERGE", "Combinar escrituras", "Agrupa escrituras pequeñas hacia la GPU"),
    ("auto_gyro", "TLG_AUTO_GYRO", "Asistencia de movimiento para linterna/recarga", "Emula sensor con stick y X/A sin bloquear controles normales"),
]
SWITCH_KEYS = {"phys_cores", "object_motion", "async_shaders", "deferred_readback",
               "stale_readback", "hot_pages", "write_merge", "auto_gyro"}
LANGUAGE_PRESETS = [
    ("Español", "es-LA", 20, "mx"),
    ("English", "en-US", 1, "us"),
    ("Português (Brasil)", "pt-BR", 17, "br"),
    ("Français", "fr-FR", 2, "fr"),
]
LANGUAGE_LABELS = {code: label for label, code, _language_id, _country in LANGUAGE_PRESETS}
LANGUAGE_CODES_BY_LABEL = {label: code for label, code, _language_id, _country in LANGUAGE_PRESETS}
LANGUAGE_BY_CODE = {code: (_language_id, _country) for _label, code, _language_id, _country in LANGUAGE_PRESETS}
# Keep old saved locale codes valid without exposing regional variants in the selector.
LANGUAGE_BY_CODE.update({"es-ES": (3, "es"), "en-GB": (18, "gb"),
                         "pt-PT": (7, "pt"), "fr-CA": (22, "ca")})
REGION_PRESETS = [
    ("Automática · según idioma", "auto"), ("Estados Unidos", "us"),
    ("México", "mx"), ("España", "es"), ("Argentina", "ar"), ("Chile", "cl"),
    ("Colombia", "co"), ("Paraguay", "py"), ("Brasil", "br"), ("Portugal", "pt"),
    ("Reino Unido", "gb"), ("Francia", "fr"), ("Canadá", "ca"), ("Alemania", "de"),
    ("Italia", "it"), ("Japón", "jp"), ("Corea del Sur", "kr"),
]
REGION_LABELS = {code: label for label, code in REGION_PRESETS}
REGION_CODES_BY_LABEL = {label: code for label, code in REGION_PRESETS}
LAUNCHER_LANGUAGES = ("Español", "Português (Brasil)", "English", "Français")
LAUNCHER_LANGUAGE_CODES = {"Español": "es", "Português (Brasil)": "pt", "English": "en", "Français": "fr"}
MOTION_HELP_TEXT = {
    "es": {
        "title": "Asistencia de movimiento", "link": "Cómo funciona",
        "intro": "Emula el sensor de movimiento con los controles normales:",
        "stick": "Stick izquierdo: inclina el mando.", "shake": "X/A: genera la sacudida para la linterna o la recarga.",
        "keyboard": "Teclado: T inclina a la derecha, G a la izquierda y Y sacude.",
        "note": "No detecta el aviso ni actúa por sí solo. Usa estos controles cuando aparezca la indicación; el movimiento y los botones normales siguen funcionando.",
        "close": "Cerrar",
    },
    "pt": {
        "title": "Assistência de movimento", "link": "Como funciona",
        "intro": "Emula o sensor de movimento usando os controles normais:",
        "stick": "Analógico esquerdo: inclina o controle.", "shake": "X/A: simula a sacudida da lanterna ou da recarga.",
        "keyboard": "Teclado: T inclina para a direita, G para a esquerda e Y sacode.",
        "note": "Não detecta o aviso nem age sozinho. Use esses controles quando a indicação aparecer; o movimento e os botões normais continuam funcionando.",
        "close": "Fechar",
    },
    "en": {
        "title": "Motion assist", "link": "How it works",
        "intro": "Emulates motion-sensor input from normal controls:",
        "stick": "Left stick: tilt the controller.", "shake": "X/A: simulate the flashlight or reload shake.",
        "keyboard": "Keyboard: T tilts right, G tilts left, and Y shakes.",
        "note": "It does not detect prompts or act by itself. Use these controls when a prompt appears; normal movement and buttons remain available.",
        "close": "Close",
    },
    "fr": {
        "title": "Assistance de mouvement", "link": "Fonctionnement",
        "intro": "Émule les mouvements du capteur avec les commandes habituelles :",
        "stick": "Stick gauche : incline la manette.", "shake": "X/A : simule la secousse de la lampe ou du rechargement.",
        "keyboard": "Clavier : T incline à droite, G à gauche et Y secoue.",
        "note": "L'assistance ne détecte pas l'invite et n'agit pas seule. Utilisez ces commandes quand elle apparaît ; les commandes normales restent actives.",
        "close": "Fermer",
    },
}
UI_TRANSLATIONS = {
    "en": {
        "CENTRO DE CONTROL": "CONTROL CENTER", "INICIO": "HOME", "GRÁFICOS": "GRAPHICS", "AUDIO": "AUDIO",
        "SISTEMA": "SYSTEM", "AVANZADO": "ADVANCED", "TRUCOS": "CHEATS", "BUILD": "BUILD",
        "DETECTANDO HARDWARE": "DETECTING HARDWARE", "Tu juego, listo.": "Your game, ready.",
        "Configura el port y entra directamente al juego.": "Configure the port and launch the game.",
        "Ajustes gráficos": "Graphics settings", "Configura la presentación, resolución y presupuesto de vídeo.": "Configure display, resolution, and video memory.",
        "Audio": "Audio", "Estado de la ruta de audio implementada por el port.": "Port audio settings and output device.",
        "Idioma y región": "Language and region", "El juego consulta el idioma del sistema al arrancar.": "The game reads the system language at startup.",
        "Ajustes avanzados": "Advanced settings", "Parámetros del runtime. Los valores iniciales ya están configurados.": "Runtime parameters. Defaults are configured.",
        "Trucos y códigos": "Cheats and codes", "Cheats para la versión 01.00 (CUSA00552).": "Cheats for version 01.00 (CUSA00552).",
        "UBICACIÓN DEL JUEGO": "GAME LOCATION",
        "Arrastra aquí la carpeta del juego o un archivo .pkg; también puedes usar Examinar.": "Drop the game folder or a .pkg file here, or use Browse.", "EXAMINAR": "BROWSE",
        "DETECTAR": "DETECT", "EXTRAER PKG": "EXTRACT PKG", "Selecciona la carpeta del juego para habilitar el inicio.": "Select the game folder to enable launch.",
        "PANTALLA": "DISPLAY", "Modo de presentación de la ventana.": "Window display mode.", "MODO DE PANTALLA": "DISPLAY MODE",
        "RESOLUCIÓN": "RESOLUTION", "Escala interna de renderizado.": "Internal render resolution.", "RESOLUCIÓN DE RENDER": "RENDER RESOLUTION",
        "FPS DEL MOTOR": "ENGINE FPS", "PRESUPUESTO DE GPU": "GPU MEMORY BUDGET", "Caché de texturas según memoria de vídeo.": "Texture cache based on video memory.",
        "PRESENTACIÓN": "PRESENTATION", "Límite de cuadros y contador.": "Frame limit and counter.", "LÍMITE DE FPS · 0 = ILIMITADO": "FPS LIMIT · 0 = UNLIMITED",
        "Mostrar contador de FPS": "Show FPS counter", "F10 alterna el overlay durante el juego.": "F10 toggles the in-game overlay.",
        "ESCALADO": "UPSCALE MODE", "Selecciona el método de postprocesado.": "Choose a post-processing method.",
        "DISPOSITIVO VULKAN": "VULKAN DEVICE", "Elige qué GPU renderiza el juego.": "Choose the GPU that renders the game.",
        "GPU detectada": "Detected GPU", "Automática (recomendada)": "Automatic (recommended)",
        "RUTA DE AUDIO": "AUDIO", "El backend nativo se carga junto con el port.": "The native audio backend loads with the port.",
        "DISPOSITIVO DE SALIDA": "OUTPUT DEVICE", "DISPOSITIVO DE AUDIO": "AUDIO DEVICE", "Detectar automáticamente": "Automatic",
        "VOLUMEN DEL JUEGO": "GAME VOLUME", "Se aplica al audio del juego, sin cambiar el volumen del escritorio.": "Applies to game audio without changing desktop volume.",
        "Idioma y región": "Language and region", "IDIOMA DEL SISTEMA": "SYSTEM LANGUAGE", "IDIOMA / VARIANTE": "LANGUAGE / VARIANT",
        "PAÍS DEL PERFIL": "PROFILE COUNTRY", "PAÍS / REGIÓN": "COUNTRY / REGION", "Automática · según idioma": "Automatic · based on language",
        "Estados Unidos": "United States", "México": "Mexico", "España": "Spain", "Argentina": "Argentina", "Chile": "Chile",
        "Colombia": "Colombia", "Paraguay": "Paraguay", "Brasil": "Brazil", "Portugal": "Portugal", "Reino Unido": "United Kingdom",
        "Francia": "France", "Canadá": "Canada", "Alemania": "Germany", "Italia": "Italy", "Japón": "Japan", "Corea del Sur": "South Korea",
        "QUÉ CAMBIA": "WHAT CHANGES", "Preferencias emuladas del sistema PS4.": "Emulated PS4 system preferences.",
        "El idioma se selecciona al arrancar. Español latinoamericano es el valor inicial; también puedes elegir español de España o detección del escritorio.": "Language is selected at launch. Latin American Spanish is the default; Spanish (Spain) and desktop auto-detection are also available.",
        "El país ajusta el locale de cuenta que entrega el runtime. No convierte CUSA00552 en otra edición regional ni añade doblajes/subtítulos ausentes del dump.": "Country sets the runtime account locale. It does not change the CUSA00552 region or add localization files missing from the dump.",
        "MEMORIA Y PLANIFICACIÓN": "MEMORY AND SCHEDULING", "RUTA DE RENDER": "RENDER PIPELINE", "Los cambios se guardan al iniciar el juego.": "Changes are saved when launching the game.",
        "Memoria directa": "Direct memory", "Ventana de faults": "Fault window", "Hilos de copia": "Copy threads", "Reserva de staging": "Staging reserve",
        "Contar núcleos físicos": "Prefer physical CPU cores", "Usa núcleos físicos en vez de hilos SMT": "Use physical cores instead of SMT threads",
        "Movimiento de objetos": "Object motion", "Mejora el tratamiento de vectores de movimiento": "Improves motion-vector handling",
        "Shaders asíncronos": "Async shaders", "Compila shaders sin bloquear el hilo principal": "Compile shaders without blocking the main thread",
        "Readback diferido": "Deferred readback", "Reduce esperas entre CPU y GPU": "Reduces CPU/GPU waits", "Readback anterior": "Stale readback",
        "Reutiliza la lectura más reciente disponible": "Reuse the latest available readback", "Hot pages · experimental": "Hot pages · experimental",
        "Desactivado recomendado: probado con caída de FPS/timeouts": "Recommended off: FPS drops and timeouts observed", "Combinar escrituras": "Merge writes",
        "Agrupa escrituras pequeñas hacia la GPU": "Batch small writes to the GPU", "SAVES": "SAVES", "LOGS": "LOGS", "CACHÉ": "CACHE",
        "▶   INICIAR JUEGO": "▶   PLAY GAME", "INICIANDO…": "STARTING…", "ACTIVIDAD": "ACTIVITY", "Salida reciente del proceso de inicio.": "Recent launcher output.",
        "TRUCOS Y CÓDIGOS": "CHEATS AND CODES", "Referencias para el juego 01.00 (CUSA00552).": "References for game version 01.00 (CUSA00552).",
        "ARCHIVO LOCAL": "LOCAL FILE", "Seleccionar archivo .shn": "Choose .shn file", "ABRIR ARCHIVO": "OPEN FILE", "ARCHIVO .SHN": ".SHN FILE",
        "ABRIR REPOSITORIO": "OPEN REPOSITORY", "GESTOR DE PARTIDAS": "SAVE MANAGER", "Abre la carpeta o copia manualmente los saves del port.": "Browse or export save files from the port.",
        "ABRIR CARPETA": "OPEN FOLDER", "EXPORTAR SELECCIÓN": "EXPORT SELECTION", "ACTUALIZAR": "REFRESH", "CERRAR": "CLOSE",
        "No hay partidas guardadas todavía.": "No saved games yet.", "Selecciona una partida para exportarla.": "Select a save file to export.",
        "Seleccionar carpeta de destino": "Select destination folder", "Copia exportada": "Save exported", "No se pudo exportar la copia": "Could not export save",
        "Auto-giro (linterna/recarga)": "Motion simulation (flashlight/reload)", "Para controladores sin sensor de movimiento": "Left stick tilts; X/A shakes, no motion sensor required",
        "Idioma del lanzador": "Launcher language", "Inglés": "English", "Portugués": "Portuguese", "Francés": "French", "Español": "Spanish",
    },
    "pt": {
        "CENTRO DE CONTROL": "CENTRO DE CONTROLE", "INICIO": "INÍCIO", "GRÁFICOS": "GRÁFICOS", "AUDIO": "ÁUDIO",
        "SISTEMA": "SISTEMA", "AVANZADO": "AVANÇADO", "TRUCOS": "TRUQUES", "BUILD": "BUILD",
        "DETECTANDO HARDWARE": "DETECTANDO HARDWARE", "Tu juego, listo.": "Seu jogo, pronto.",
        "Configura el port y entra directamente al juego.": "Configure o port e inicie o jogo.", "Ajustes gráficos": "Configurações gráficas",
        "Configura la presentación, resolución y presupuesto de vídeo.": "Configure a tela, a resolução e a memória de vídeo.", "Audio": "Áudio",
        "Estado de la ruta de audio implementada por el port.": "Configurações de áudio e dispositivo de saída.", "Idioma y región": "Idioma e região",
        "El juego consulta el idioma del sistema al arrancar.": "O jogo consulta o idioma do sistema ao iniciar.", "Ajustes avanzados": "Configurações avançadas",
        "Parámetros del runtime. Los valores iniciales ya están configurados.": "Parâmetros do runtime. Os padrões estão configurados.",
        "Trucos y códigos": "Truques e códigos", "Cheats para la versión 01.00 (CUSA00552).": "Códigos para a versão 01.00 (CUSA00552).",
        "UBICACIÓN DEL JUEGO": "LOCAL DO JOGO",
        "Arrastra aquí la carpeta del juego o un archivo .pkg; también puedes usar Examinar.": "Solte a pasta do jogo ou um arquivo .pkg aqui, ou use Procurar.", "EXAMINAR": "PROCURAR", "DETECTAR": "DETECTAR", "EXTRAER PKG": "EXTRAIR PKG",
        "Selecciona la carpeta del juego para habilitar el inicio.": "Selecione a pasta do jogo para habilitar a inicialização.", "PANTALLA": "TELA",
        "Modo de presentación de la ventana.": "Modo de exibição da janela.", "MODO DE PANTALLA": "MODO DE TELA", "RESOLUCIÓN": "RESOLUÇÃO",
        "Escala interna de renderizado.": "Resolução interna de renderização.", "RESOLUCIÓN DE RENDER": "RESOLUÇÃO DE RENDER", "FPS DEL MOTOR": "FPS DO MOTOR",
        "PRESUPUESTO DE GPU": "ORÇAMENTO DA GPU", "Caché de texturas según memoria de vídeo.": "Cache de texturas conforme a memória de vídeo.",
        "PRESENTACIÓN": "APRESENTAÇÃO", "Límite de cuadros y contador.": "Limite de quadros e contador.", "LÍMITE DE FPS · 0 = ILIMITADO": "LIMITE DE FPS · 0 = ILIMITADO",
        "Mostrar contador de FPS": "Mostrar contador de FPS", "F10 alterna el overlay durante el juego.": "F10 alterna o overlay durante o jogo.",
        "ESCALADO": "MODO DE UPSCALE", "Selecciona el método de postprocesado.": "Escolha o método de pós-processamento.",
        "DISPOSITIVO VULKAN": "DISPOSITIVO VULKAN", "Elige qué GPU renderiza el juego.": "Escolha a GPU que renderiza o jogo.", "GPU detectada": "GPU detectada",
        "Automática (recomendada)": "Automática (recomendada)", "RUTA DE AUDIO": "ÁUDIO", "El backend nativo se carga junto con el port.": "O backend nativo carrega com o port.",
        "DISPOSITIVO DE SALIDA": "DISPOSITIVO DE SAÍDA", "DISPOSITIVO DE AUDIO": "DISPOSITIVO DE ÁUDIO", "Detectar automáticamente": "Detectar automaticamente",
        "VOLUMEN DEL JUEGO": "VOLUME DO JOGO", "Se aplica al audio del juego, sin cambiar el volumen del escritorio.": "Afeta o áudio do jogo sem mudar o volume do desktop.",
        "IDIOMA DEL SISTEMA": "IDIOMA DO SISTEMA", "IDIOMA / VARIANTE": "IDIOMA / VARIANTE", "PAÍS DEL PERFIL": "PAÍS DO PERFIL",
        "PAÍS / REGIÓN": "PAÍS / REGIÃO", "Automática · según idioma": "Automático · conforme o idioma", "QUÉ CAMBIA": "O QUE MUDA",
        "Preferencias emuladas del sistema PS4.": "Preferências emuladas do sistema PS4.",
        "El idioma se selecciona al arrancar. Español latinoamericano es el valor inicial; también puedes elegir español de España o detección del escritorio.": "O idioma é escolhido ao iniciar. Espanhol latino-americano é o padrão; espanhol da Espanha e detecção do desktop também estão disponíveis.",
        "El país ajusta el locale de cuenta que entrega el runtime. No convierte CUSA00552 en otra edición regional ni añade doblajes/subtítulos ausentes del dump.": "O país define o locale da conta. Não altera a região CUSA00552 nem adiciona arquivos ausentes do dump.",
        "MEMORIA Y PLANIFICACIÓN": "MEMÓRIA E PLANEJAMENTO", "RUTA DE RENDER": "CAMINHO DE RENDER", "Los cambios se guardan al iniciar el juego.": "As alterações são salvas ao iniciar o jogo.",
        "Memoria directa": "Memória direta", "Ventana de faults": "Janela de faults", "Hilos de copia": "Threads de cópia", "Reserva de staging": "Reserva de staging",
        "Contar núcleos físicos": "Preferir núcleos físicos", "Usa núcleos físicos en vez de hilos SMT": "Usa núcleos físicos em vez de threads SMT",
        "Movimiento de objetos": "Movimento de objetos", "Mejora el tratamiento de vectores de movimiento": "Melhora o tratamento dos vetores de movimento",
        "Shaders asíncronos": "Shaders assíncronos", "Compila shaders sin bloquear el hilo principal": "Compila shaders sem bloquear a thread principal",
        "Readback diferido": "Readback diferido", "Reduce esperas entre CPU y GPU": "Reduz esperas entre CPU e GPU", "Readback anterior": "Readback anterior",
        "Reutiliza la lectura más reciente disponible": "Reutiliza a leitura mais recente disponível", "Hot pages · experimental": "Hot pages · experimental",
        "Desactivado recomendado: probado con caída de FPS/timeouts": "Recomendado desligado: houve queda de FPS e timeouts", "Combinar escrituras": "Combinar escritas",
        "Agrupa escrituras pequeñas hacia la GPU": "Agrupa escritas pequenas para a GPU", "SAVES": "SAVES", "LOGS": "LOGS", "CACHÉ": "CACHE",
        "▶   INICIAR JUEGO": "▶   INICIAR JOGO", "ACTIVIDAD": "ATIVIDADE", "Salida reciente del proceso de inicio.": "Saída recente da inicialização.",
        "TRUCOS Y CÓDIGOS": "TRUQUES E CÓDIGOS", "Referencias para el juego 01.00 (CUSA00552).": "Referências para o jogo 01.00 (CUSA00552).",
        "ARCHIVO LOCAL": "ARQUIVO LOCAL", "Seleccionar archivo .shn": "Selecionar arquivo .shn", "ABRIR ARCHIVO": "ABRIR ARQUIVO", "ARCHIVO .SHN": "ARQUIVO .SHN",
        "ABRIR REPOSITORIO": "ABRIR REPOSITÓRIO", "GESTOR DE PARTIDAS": "GERENCIADOR DE SAVES", "Abre la carpeta o copia manualmente los saves del port.": "Abra a pasta ou exporte saves do port.",
        "ABRIR CARPETA": "ABRIR PASTA", "EXPORTAR SELECCIÓN": "EXPORTAR SELEÇÃO", "ACTUALIZAR": "ATUALIZAR", "CERRAR": "FECHAR",
        "No hay partidas guardadas todavía.": "Ainda não há saves.", "Selecciona una partida para exportarla.": "Selecione um save para exportar.",
        "Seleccionar carpeta de destino": "Selecionar pasta de destino", "Copia exportada": "Cópia exportada", "No se pudo exportar la copia": "Falha ao exportar a cópia",
        "Auto-giro (linterna/recarga)": "Simulação de movimento (lanterna/recarga)", "Para controladores sin sensor de movimiento": "Analógico esquerdo inclina; X/A sacode, sem sensor necessário",
        "Idioma del lanzador": "Idioma do launcher", "Inglés": "Inglês", "Portugués": "Português", "Francés": "Francês", "Español": "Espanhol",
    },
    "fr": {
        "CENTRO DE CONTROL": "CENTRE DE CONTRÔLE", "INICIO": "ACCUEIL", "GRÁFICOS": "GRAPHIQUES", "AUDIO": "AUDIO",
        "SISTEMA": "SYSTÈME", "AVANZADO": "AVANCÉ", "TRUCOS": "ASTUCES", "BUILD": "BUILD",
        "DETECTANDO HARDWARE": "DÉTECTION DU MATÉRIEL", "Tu juego, listo.": "Votre jeu est prêt.",
        "Configura el port y entra directamente al juego.": "Configurez le port et lancez le jeu.", "Ajustes gráficos": "Réglages graphiques",
        "Configura la presentación, resolución y presupuesto de vídeo.": "Réglez l'affichage, la résolution et la mémoire vidéo.", "Audio": "Audio",
        "Estado de la ruta de audio implementada por el port.": "Réglages audio et périphérique de sortie.", "Idioma y región": "Langue et région",
        "El juego consulta el idioma del sistema al arrancar.": "Le jeu lit la langue système au démarrage.", "Ajustes avanzados": "Réglages avancés",
        "Parámetros del runtime. Los valores iniciales ya están configurados.": "Paramètres du runtime. Les valeurs par défaut sont configurées.",
        "Trucos y códigos": "Codes et astuces", "Cheats para la versión 01.00 (CUSA00552).": "Codes pour la version 01.00 (CUSA00552).",
        "UBICACIÓN DEL JUEGO": "EMPLACEMENT DU JEU",
        "Arrastra aquí la carpeta del juego o un archivo .pkg; también puedes usar Examinar.": "Déposez le dossier du jeu ou un fichier .pkg ici, ou utilisez Parcourir.", "EXAMINAR": "PARCOURIR", "DETECTAR": "DÉTECTER", "EXTRAER PKG": "EXTRAIRE PKG",
        "Selecciona la carpeta del juego para habilitar el inicio.": "Choisissez le dossier du jeu pour activer le lancement.", "PANTALLA": "AFFICHAGE",
        "Modo de presentación de la ventana.": "Mode d'affichage de la fenêtre.", "MODO DE PANTALLA": "MODE D'AFFICHAGE", "RESOLUCIÓN": "RÉSOLUTION",
        "Escala interna de renderizado.": "Résolution interne du rendu.", "RESOLUCIÓN DE RENDER": "RÉSOLUTION DE RENDU", "FPS DEL MOTOR": "FPS DU MOTEUR",
        "PRESUPUESTO DE GPU": "BUDGET GPU", "Caché de texturas según memoria de vídeo.": "Cache de textures selon la mémoire vidéo.",
        "PRESENTACIÓN": "PRÉSENTATION", "Límite de cuadros y contador.": "Limite d'images et compteur.", "LÍMITE DE FPS · 0 = ILIMITADO": "LIMITE FPS · 0 = ILLIMITÉ",
        "Mostrar contador de FPS": "Afficher le compteur FPS", "F10 alterna el overlay durante el juego.": "F10 active l'overlay en jeu.",
        "ESCALADO": "MODE UPSCALE", "Selecciona el método de postprocesado.": "Choisissez le post-traitement.",
        "DISPOSITIVO VULKAN": "PÉRIPHÉRIQUE VULKAN", "Elige qué GPU renderiza el juego.": "Choisissez le GPU qui exécute le jeu.", "GPU detectada": "GPU détecté",
        "Automática (recomendada)": "Automatique (recommandé)", "RUTA DE AUDIO": "AUDIO", "El backend nativo se carga junto con el port.": "Le backend audio natif est chargé avec le port.",
        "DISPOSITIVO DE SALIDA": "PÉRIPHÉRIQUE DE SORTIE", "DISPOSITIVO DE AUDIO": "PÉRIPHÉRIQUE AUDIO", "Detectar automáticamente": "Automatique",
        "VOLUMEN DEL JUEGO": "VOLUME DU JEU", "Se aplica al audio del juego, sin cambiar el volumen del escritorio.": "Agit sur le jeu sans changer le volume du bureau.",
        "IDIOMA DEL SISTEMA": "LANGUE SYSTÈME", "IDIOMA / VARIANTE": "LANGUE / VARIANTE", "PAÍS DEL PERFIL": "PAYS DU PROFIL",
        "PAÍS / REGIÓN": "PAYS / RÉGION", "Automática · según idioma": "Automatique · selon la langue", "QUÉ CAMBIA": "CE QUI CHANGE",
        "Preferencias emuladas del sistema PS4.": "Préférences émulées du système PS4.",
        "El idioma se selecciona al arrancar. Español latinoamericano es el valor inicial; también puedes elegir español de España o detección del escritorio.": "La langue est choisie au démarrage. L'espagnol d'Amérique latine est le défaut; espagnol d'Espagne et détection système sont aussi disponibles.",
        "El país ajusta el locale de cuenta que entrega el runtime. No convierte CUSA00552 en otra edición regional ni añade doblajes/subtítulos ausentes del dump.": "Le pays règle le locale du compte. Il ne change pas la région CUSA00552 et n'ajoute pas de fichiers absents du dump.",
        "MEMORIA Y PLANIFICACIÓN": "MÉMOIRE ET PLANIFICATION", "RUTA DE RENDER": "PIPELINE DE RENDU", "Los cambios se guardan al iniciar el juego.": "Les réglages sont enregistrés au lancement.",
        "Memoria directa": "Mémoire directe", "Ventana de faults": "Fenêtre de faults", "Hilos de copia": "Threads de copie", "Reserva de staging": "Réserve de staging",
        "Contar núcleos físicos": "Privilégier les cœurs physiques", "Usa núcleos físicos en vez de hilos SMT": "Utilise les cœurs physiques plutôt que les threads SMT",
        "Movimiento de objetos": "Mouvement des objets", "Mejora el tratamiento de vectores de movimiento": "Améliore le traitement des vecteurs de mouvement",
        "Shaders asíncronos": "Shaders asynchrones", "Compila shaders sin bloquear el hilo principal": "Compile les shaders sans bloquer le thread principal",
        "Readback diferido": "Readback différé", "Reduce esperas entre CPU y GPU": "Réduit les attentes CPU/GPU", "Readback anterior": "Readback précédent",
        "Reutiliza la lectura más reciente disponible": "Réutilise la lecture la plus récente", "Hot pages · experimental": "Hot pages · expérimental",
        "Desactivado recomendado: probado con caída de FPS/timeouts": "Désactivé recommandé : baisse de FPS et timeouts observés", "Combinar escrituras": "Fusionner les écritures",
        "Agrupa escrituras pequeñas hacia la GPU": "Regroupe les petites écritures vers le GPU", "SAVES": "SAUVEGARDES", "LOGS": "JOURNAUX", "CACHÉ": "CACHE",
        "▶   INICIAR JUEGO": "▶   LANCER LE JEU", "ACTIVIDAD": "ACTIVITÉ", "Salida reciente del proceso de inicio.": "Sortie récente du lanceur.",
        "TRUCOS Y CÓDIGOS": "CODES ET ASTUCES", "Referencias para el juego 01.00 (CUSA00552).": "Références pour le jeu 01.00 (CUSA00552).",
        "ARCHIVO LOCAL": "FICHIER LOCAL", "Seleccionar archivo .shn": "Choisir un fichier .shn", "ABRIR ARCHIVO": "OUVRIR LE FICHIER", "ARCHIVO .SHN": "FICHIER .SHN",
        "ABRIR REPOSITORIO": "OUVRIR LE DÉPÔT", "GESTOR DE PARTIDAS": "GESTION DES SAUVEGARDES", "Abre la carpeta o copia manualmente los saves del port.": "Parcourez ou exportez les sauvegardes du port.",
        "ABRIR CARPETA": "OUVRIR LE DOSSIER", "EXPORTAR SELECCIÓN": "EXPORTER LA SÉLECTION", "ACTUALIZAR": "ACTUALISER", "CERRAR": "FERMER",
        "No hay partidas guardadas todavía.": "Aucune sauvegarde pour le moment.", "Selecciona una partida para exportarla.": "Sélectionnez une sauvegarde à exporter.",
        "Seleccionar carpeta de destino": "Choisir le dossier de destination", "Copia exportada": "Sauvegarde exportée", "No se pudo exportar la copia": "Échec de l'exportation",
        "Auto-giro (linterna/recarga)": "Simulation de mouvement (lampe/rechargement)", "Para controladores sin sensor de movimiento": "Stick gauche pour incliner, X/A pour secouer, sans capteur requis",
        "Idioma del lanzador": "Langue du lanceur", "Inglés": "Anglais", "Portugués": "Portugais", "Francés": "Français", "Español": "Espagnol",
    },
}
UI_TRANSLATIONS["en"].update({
    "El idioma se aplica al iniciar. Puedes elegir español, portugués de Brasil, inglés o francés.": "The game language is applied at launch. Choose Spanish, Brazilian Portuguese, English, or French.",
    "VERSIÓN DEL LANZADOR": "LAUNCHER VERSION",
    "Español": "Spanish", "Português (Brasil)": "Portuguese (Brazil)", "English": "English", "Français": "French",
    "01  /  LIBRERÍA": "01  /  LIBRARY", "02  /  IMAGEN": "02  /  GRAPHICS", "03  /  SONIDO": "03  /  AUDIO",
    "04  /  PREFERENCIAS": "04  /  SYSTEM", "05  /  MOTOR": "05  /  ENGINE", "06  /  TRUCOS": "06  /  CHEATS",
    "Español": "Spanish", "Português (Brasil)": "Portuguese (Brazil)", "English": "English", "Français": "French",
    "PROCESADOR": "CPU", "GRÁFICOS": "GPU", "MEMORIA": "MEMORY", "VRAM · MB": "VRAM · MB",
    "Carpeta del juego verificada": "Game folder verified", "No se encontró eboot.bin": "eboot.bin not found",
    "Esperando carpeta del juego": "Waiting for game folder", "Buscando eboot.bin…": "Searching for eboot.bin…",
    "País efectivo": "Effective country", "Auto sigue la variante elegida arriba.": "Auto follows the language variant above.",
    "Memoria directa": "Direct memory", "Ventana de faults": "Fault window", "Hilos de copia": "Copy threads",
    "auto = según CPUs disponibles": "auto = based on available CPUs", "Reserva de staging": "Staging reserve",
    "auto = 128 / 256 / 512 MiB según RAM": "auto = 128 / 256 / 512 MiB based on RAM",
    "IDIOMA DEL LANZADOR": "LAUNCHER LANGUAGE", "VOLUMEN": "VOLUME", "Método de escalado": "Upscale method",
    "Planificación de CPU": "CPU scheduling", "Elige hilos lógicos o núcleos físicos": "Choose logical threads or physical cores",
    "Todos los hilos lógicos": "All logical threads", "Núcleos físicos": "Physical cores",
    "Asistencia de movimiento para linterna/recarga": "Motion assist for flashlight/reload",
    "Emula sensor con stick y X/A sin bloquear controles normales": "Maps stick movement and X/A to motion data without consuming normal controls",
    "Gestionado por el escritorio Linux.": "Managed by the Linux desktop.", "Detectar idioma del sistema": "Detect system language",
    "Español · Latinoamérica": "Spanish · Latin America", "Español · España": "Spanish · Spain",
    "English · United States": "English · United States", "English · United Kingdom": "English · United Kingdom",
    "Português · Brasil": "Portuguese · Brazil", "Português · Portugal": "Portuguese · Portugal",
    "Français · France": "French · France", "Français · Canada": "French · Canada",
    "Desactivado · nativo": "Off · native", "Windowed": "Windowed", "Borderless": "Borderless", "Fullscreen": "Fullscreen", "native": "Native",
    "Idioma del sistema": "System language", "País efectivo": "Effective country",
    "Selecciona el dispositivo de salida y el volumen del juego.": "Choose the output device and game volume.",
    "Los archivos .shn se aplican con GoldHEN o con el sistema de patches del port. El repositorio oficial contiene más códigos para otras versiones.": "SHN files are used with GoldHEN or the port's patch system. The official repository has more codes for other versions.",
    "Archivo de trucos local para CUSA00552.": "Local cheat file for CUSA00552.",
    "Detectar automáticamente": "Automatic", "Dispositivo predeterminado del sistema": "System default device",
    "PERFIL FSR": "FSR PROFILE", "Calidad / Velocidad": "Quality / Speed", "NITIDEZ": "SHARPNESS",
    "BORRAR PARTIDA": "DELETE SAVE", "Borrar partida": "Delete save",
    "¿Borrar la partida seleccionada? Esta acción no se puede deshacer.": "Delete the selected save? This cannot be undone.",
    "Selecciona una partida para borrarla.": "Select a save to delete.", "Error al borrar": "Delete failed",
    "La ruta seleccionada no pertenece a la carpeta de partidas.": "The selected path is outside the save folder.",
})
UI_TRANSLATIONS["pt"].update({
    "El idioma se aplica al iniciar. Puedes elegir español, portugués de Brasil, inglés o francés.": "O idioma do jogo é aplicado ao iniciar. Escolha espanhol, português do Brasil, inglês ou francês.",
    "VERSIÓN DEL LANZADOR": "VERSÃO DO LAUNCHER",
    "Español": "Espanhol", "Português (Brasil)": "Português (Brasil)", "English": "Inglês", "Français": "Francês",
    "01  /  LIBRERÍA": "01  /  BIBLIOTECA", "02  /  IMAGEN": "02  /  GRÁFICOS", "03  /  SONIDO": "03  /  ÁUDIO",
    "04  /  PREFERENCIAS": "04  /  SISTEMA", "05  /  MOTOR": "05  /  MOTOR", "06  /  TRUCOS": "06  /  TRUQUES",
    "Español": "Espanhol", "Português (Brasil)": "Português (Brasil)", "English": "Inglês", "Français": "Francês",
    "PROCESADOR": "PROCESSADOR", "GRÁFICOS": "GPU", "MEMORIA": "MEMÓRIA", "VRAM · MB": "VRAM · MB",
    "Carpeta del juego verificada": "Pasta do jogo verificada", "No se encontró eboot.bin": "eboot.bin não encontrado",
    "Esperando carpeta del juego": "Aguardando a pasta do jogo", "Buscando eboot.bin…": "Procurando eboot.bin…",
    "País efectivo": "País efetivo", "Auto sigue la variante elegida arriba.": "Auto segue a variante de idioma acima.",
    "Memoria directa": "Memória direta", "Ventana de faults": "Janela de faults", "Hilos de copia": "Threads de cópia",
    "auto = según CPUs disponibles": "auto = conforme CPUs disponíveis", "Reserva de staging": "Reserva de staging",
    "auto = 128 / 256 / 512 MiB según RAM": "auto = conforme a RAM: 128 / 256 / 512 MiB",
    "IDIOMA DEL LANZADOR": "IDIOMA DO LAUNCHER", "VOLUMEN": "VOLUME", "Método de escalado": "Método de upscale",
    "Planificación de CPU": "Planejamento da CPU", "Elige hilos lógicos o núcleos físicos": "Escolha threads lógicas ou núcleos físicos",
    "Todos los hilos lógicos": "Todas as threads lógicas", "Núcleos físicos": "Núcleos físicos",
    "Asistencia de movimiento para linterna/recarga": "Assistência de movimento para lanterna/recarga",
    "Emula sensor con stick y X/A sin bloquear controles normales": "Converte o analógico e X/A em movimento sem bloquear os controles normais",
    "Gestionado por el escritorio Linux.": "Gerenciado pelo desktop Linux.", "Detectar idioma del sistema": "Detectar idioma do sistema",
    "Español · Latinoamérica": "Espanhol · América Latina", "Español · España": "Espanhol · Espanha",
    "English · United States": "Inglês · Estados Unidos", "English · United Kingdom": "Inglês · Reino Unido",
    "Português · Brasil": "Português · Brasil", "Português · Portugal": "Português · Portugal",
    "Français · France": "Francês · França", "Français · Canada": "Francês · Canadá",
    "Desactivado · nativo": "Desativado · nativo", "Windowed": "Janela", "Borderless": "Sem bordas", "Fullscreen": "Tela cheia", "native": "Nativa",
    "País efectivo": "País efetivo", "Selecciona el dispositivo de salida y el volumen del juego.": "Escolha o dispositivo de saída e o volume do jogo.",
    "Los archivos .shn se aplican con GoldHEN o con el sistema de patches del port. El repositorio oficial contiene más códigos para otras versiones.": "Arquivos .shn funcionam com GoldHEN ou com o sistema de patches do port. O repositório oficial tem mais códigos para outras versões.",
    "Archivo de trucos local para CUSA00552.": "Arquivo de truques local para CUSA00552.",
    "Detectar automáticamente": "Detectar automaticamente", "Dispositivo predeterminado del sistema": "Dispositivo padrão do sistema",
    "BORRAR PARTIDA": "APAGAR SAVE", "Borrar partida": "Apagar save",
    "¿Borrar la partida seleccionada? Esta acción no se puede deshacer.": "Apagar o save selecionado? Esta ação não pode ser desfeita.",
    "Selecciona una partida para borrarla.": "Selecione um save para apagar.", "Error al borrar": "Erro ao apagar",
    "La ruta seleccionada no pertenece a la carpeta de partidas.": "O caminho selecionado não está na pasta de saves.",
})
UI_TRANSLATIONS["fr"].update({
    "El idioma se aplica al iniciar. Puedes elegir español, portugués de Brasil, inglés o francés.": "La langue du jeu est appliquée au démarrage. Choisissez l'espagnol, le portugais du Brésil, l'anglais ou le français.",
    "VERSIÓN DEL LANZADOR": "VERSION DU LANCEUR",
    "Español": "Espagnol", "Português (Brasil)": "Portugais (Brésil)", "English": "Anglais", "Français": "Français",
    "01  /  LIBRERÍA": "01  /  BIBLIOTHÈQUE", "02  /  IMAGEN": "02  /  IMAGE", "03  /  SONIDO": "03  /  AUDIO",
    "04  /  PREFERENCIAS": "04  /  PRÉFÉRENCES", "05  /  MOTOR": "05  /  MOTEUR", "06  /  TRUCOS": "06  /  CODES",
    "Español": "Espagnol", "Português (Brasil)": "Portugais (Brésil)", "English": "Anglais", "Français": "Français",
    "PROCESADOR": "PROCESSEUR", "GRÁFICOS": "GPU", "MEMORIA": "MÉMOIRE", "VRAM · MB": "VRAM · Mo",
    "Carpeta del juego verificada": "Dossier du jeu vérifié", "No se encontró eboot.bin": "eboot.bin introuvable",
    "Esperando carpeta del juego": "En attente du dossier du jeu", "Buscando eboot.bin…": "Recherche de eboot.bin…",
    "País efectivo": "Pays effectif", "Auto sigue la variante elegida arriba.": "Auto suit la variante linguistique ci-dessus.",
    "Memoria directa": "Mémoire directe", "Ventana de faults": "Fenêtre de faults", "Hilos de copia": "Threads de copie",
    "auto = según CPUs disponibles": "auto = selon les CPU disponibles", "Reserva de staging": "Réserve de staging",
    "auto = 128 / 256 / 512 MiB según RAM": "auto = 128 / 256 / 512 Mio selon la RAM",
    "IDIOMA DEL LANZADOR": "LANGUE DU LANCEUR", "VOLUMEN": "VOLUME", "Método de escalado": "Méthode d'upscale",
    "Planificación de CPU": "Planification CPU", "Elige hilos lógicos o núcleos físicos": "Choisissez threads logiques ou cœurs physiques",
    "Todos los hilos lógicos": "Tous les threads logiques", "Núcleos físicos": "Cœurs physiques",
    "Asistencia de movimiento para linterna/recarga": "Assistance de mouvement lampe/rechargement",
    "Emula sensor con stick y X/A sin bloquear controles normales": "Convertit le stick et X/A en mouvement sans bloquer les commandes normales",
    "Gestionado por el escritorio Linux.": "Géré par le bureau Linux.", "Detectar idioma del sistema": "Détecter la langue système",
    "Español · Latinoamérica": "Espagnol · Amérique latine", "Español · España": "Espagnol · Espagne",
    "English · United States": "Anglais · États-Unis", "English · United Kingdom": "Anglais · Royaume-Uni",
    "Português · Brasil": "Portugais · Brésil", "Português · Portugal": "Portugais · Portugal",
    "Français · France": "Français · France", "Français · Canada": "Français · Canada",
    "Desactivado · nativo": "Désactivé · natif", "Windowed": "Fenêtré", "Borderless": "Sans bordure", "Fullscreen": "Plein écran", "native": "Native",
    "País efectivo": "Pays effectif", "Selecciona el dispositivo de salida y el volumen del juego.": "Choisissez la sortie audio et le volume du jeu.",
    "Los archivos .shn se aplican con GoldHEN o con el sistema de patches del port. El repositorio oficial contiene más códigos para otras versiones.": "Les fichiers .shn s'utilisent avec GoldHEN ou le système de patches du port. Le dépôt officiel contient d'autres codes.",
    "Archivo de trucos local para CUSA00552.": "Fichier de codes local pour CUSA00552.",
    "Detectar automáticamente": "Automatique", "Dispositivo predeterminado del sistema": "Périphérique système par défaut",
    "BORRAR PARTIDA": "SUPPRIMER LA SAUVEGARDE", "Borrar partida": "Supprimer la sauvegarde",
    "¿Borrar la partida seleccionada? Esta acción no se puede deshacer.": "Supprimer la sauvegarde sélectionnée ? Cette action est irréversible.",
    "Selecciona una partida para borrarla.": "Sélectionnez une sauvegarde à supprimer.", "Error al borrar": "Échec de la suppression",
    "La ruta seleccionada no pertenece a la carpeta de partidas.": "Le chemin sélectionné est hors du dossier de sauvegarde.",
})
UPSCALER_OPTIONS = [("Desactivado · nativo", "0"), ("AMD FSR 3", "1"), ("AMD FSR 4", "2"), ("TAA", "4")]
UPSCALER_LABEL_BY_CODE = {code: label for label, code in UPSCALER_OPTIONS}
UPSCALER_RUNTIME_NAME = {"0": "off", "1": "fsr3", "2": "fsr4", "4": "taa"}
UPSCALER_PRESETS = [("Native AA", "0"), ("Quality", "1"), ("Balanced", "2"), ("Performance", "3"), ("Ultra Performance", "4")]
UPSCALER_PRESET_LABEL_BY_CODE = {code: label for label, code in UPSCALER_PRESETS}


def load_settings():
    try:
        saved = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        settings = {**DEFAULTS, **saved}
        if settings.get("launcher_language") == "Português":
            settings["launcher_language"] = "Português (Brasil)"
        language_aliases = {"auto": detect_system_language(), "es-ES": "es-LA", "en-GB": "en-US",
                            "pt-PT": "pt-BR", "fr-CA": "fr-FR"}
        settings["language"] = language_aliases.get(settings.get("language"), settings.get("language"))
        if settings["language"] not in LANGUAGE_BY_CODE:
            settings["language"] = DEFAULTS["language"]
        for key, old_default in (("copy_threads", "6"), ("staging_keep", "512"), ("phys_cores", "6")):
            if str(saved.get(key, "")) == old_default:
                settings[key] = DEFAULTS[key]
        if str(saved.get("hot_pages", "0")) == "1":
            settings["hot_pages"] = "0"
        return settings
    except (OSError, ValueError, TypeError):
        return DEFAULTS.copy()


def save_settings(settings):
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = SETTINGS_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(settings, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(SETTINGS_PATH)


_FONTCONFIG_HANDLE = None


def register_headline_font():
    """Register the bundled display font for this process without installing it system-wide."""
    global _FONTCONFIG_HANDLE
    if not HEADLINE_FONT_FILE.is_file():
        return False
    try:
        library = ctypes.util.find_library("fontconfig")
        if not library:
            return False
        _FONTCONFIG_HANDLE = ctypes.CDLL(library)
        _FONTCONFIG_HANDLE.FcConfigGetCurrent.restype = ctypes.c_void_p
        config = _FONTCONFIG_HANDLE.FcConfigGetCurrent()
        if not config:
            return False
        _FONTCONFIG_HANDLE.FcConfigAppFontAddFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
        _FONTCONFIG_HANDLE.FcConfigAppFontAddFile.restype = ctypes.c_int
        registered = _FONTCONFIG_HANDLE.FcConfigAppFontAddFile(config, os.fsencode(HEADLINE_FONT_FILE))
        if registered:
            _FONTCONFIG_HANDLE.FcConfigBuildFonts.argtypes = [ctypes.c_void_p]
            _FONTCONFIG_HANDLE.FcConfigBuildFonts.restype = ctypes.c_int
            _FONTCONFIG_HANDLE.FcConfigBuildFonts(config)
        return bool(registered)
    except (OSError, AttributeError, TypeError):
        return False


def find_eboot(folder: str | Path) -> Path | None:
    folder = Path(folder).expanduser()
    if (folder / "eboot.bin").is_file():
        return folder
    try:
        for current, dirs, files in os.walk(folder):
            dirs[:] = [name for name in dirs if name not in {".git", "out", "user", ".cache", "node_modules"}]
            if "eboot.bin" in files:
                return Path(current)
    except OSError:
        pass
    return None


def find_game_dir(settings=None, deep=False):
    settings = settings or {}
    saved = settings.get("game_dir", "")
    if saved and (Path(saved) / "eboot.bin").is_file():
        return str(saved)
    candidates = [
        Path.home() / "Games" / "CUSA00552", Path.home() / "Games" / "The Last of Us Remastered",
    ]
    if deep:
        for mount in (Path("/media") / os.environ.get("USER", ""), Path("/run/media") / os.environ.get("USER", "")):
            if mount.is_dir():
                try:
                    candidates.extend(p for p in mount.iterdir() if p.is_dir())
                except OSError:
                    pass
    for candidate in candidates:
        if candidate.is_dir():
            found = find_eboot(candidate)
            if found:
                return str(found)
    if deep:
        for base in (Path("/media"), Path("/mnt"), Path("/run/media")):
            if not base.is_dir():
                continue
            try:
                for current, dirs, files in os.walk(base):
                    dirs[:] = [d for d in dirs if d not in {".git", "out", "user", ".cache", "node_modules"}]
                    if "eboot.bin" in files:
                        return current
            except OSError:
                continue
    return ""


def detect_hardware():
    result = {"cpu": "No detectado", "gpu": "No detectada", "ram": "—", "audio": []}
    try:
        for line in Path("/proc/cpuinfo").read_text(errors="ignore").splitlines():
            if line.startswith("model name"):
                result["cpu"] = line.split(":", 1)[1].strip()
                break
    except OSError:
        pass
    try:
        for line in subprocess.check_output(["free", "-h"], text=True, timeout=2, stderr=subprocess.DEVNULL).splitlines():
            if line.startswith("Mem:"):
                result["ram"] = line.split()[1]
                break
    except (OSError, subprocess.SubprocessError):
        pass
    gpus = detect_gpus()
    if gpus:
        result["gpu"] = gpus[0][1]
    result["audio"] = detect_audio_devices()
    return result


def detect_gpus():
    tool = PORT / "out" / "tlg-gpu-capabilities"
    try:
        if tool.is_file():
            output = subprocess.check_output([str(tool), "--list"], text=True, timeout=5,
                                             stderr=subprocess.DEVNULL)
            devices = []
            for line in output.splitlines():
                fields = line.split("\t", 2)
                if len(fields) == 3 and fields[0].isdigit():
                    devices.append((fields[0], fields[1], fields[2]))
            if devices:
                return devices
    except (OSError, subprocess.SubprocessError):
        pass
    try:
        output = subprocess.check_output(["vulkaninfo", "--summary"], text=True, timeout=5,
                                         stderr=subprocess.DEVNULL)
        names = []
        for line in output.splitlines():
            if "deviceName" in line and "=" in line:
                name = line.split("=", 1)[1].strip()
                if name and (not names or name != names[-1][1]):
                    names.append((str(len(names)), name, "other"))
        return names
    except (OSError, subprocess.SubprocessError):
        return []


def detect_audio_devices():
    sinks = []
    sink_names = []
    try:
        out = subprocess.check_output(["pactl", "list", "short", "sinks"], text=True, timeout=2, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2:
                sink_names.append(parts[1])
    except (OSError, subprocess.SubprocessError):
        pass
    descriptions = {}
    if sink_names:
        try:
            out = subprocess.check_output(["pactl", "list", "sinks"], text=True, timeout=2, stderr=subprocess.DEVNULL)
            current_name = None
            for line in out.splitlines():
                stripped = line.strip()
                if stripped.startswith(("Name:", "Nombre:")):
                    current_name = stripped.split(":", 1)[1].strip()
                elif current_name and stripped.startswith(("Description:", "Descripción:")):
                    descriptions[current_name] = stripped.split(":", 1)[1].strip()
                    current_name = None
        except (OSError, subprocess.SubprocessError):
            pass
        sinks = [f"{descriptions[name]} [{name}]" if name in descriptions else name for name in sink_names]
    if not sinks:
        try:
            out = subprocess.check_output(["wpctl", "status"], text=True, timeout=2, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                if "Audio Output" in line or "Sink" in line:
                    sinks.append(line.strip())
        except (OSError, subprocess.SubprocessError):
            pass
    return list(dict.fromkeys(sinks)) or ["default"]


def find_pkg_extractor():
    executable = "ps4-pkg-tool.exe" if os.name == "nt" else "ps4-pkg-tool"
    configured = os.environ.get("TLG_PKG_EXTRACTOR", "").strip()
    candidates = ([Path(configured).expanduser()] if configured else [])
    candidates.extend((Path(__file__).resolve().parent / "vendor" / "pkgtool" / "bin" / executable,
                       PORT / "out" / executable))
    for candidate in candidates:
        if candidate.is_file() and (os.name == "nt" or os.access(candidate, os.X_OK)):
            return candidate
    located = shutil.which(executable)
    return Path(located) if located else None


def resolve_language_profile(language_code, region_code="auto"):
    if language_code == "auto":
        language_code = detect_system_language()
    language_id, default_country = LANGUAGE_BY_CODE.get(language_code, LANGUAGE_BY_CODE["es-LA"])
    country = default_country if region_code == "auto" else region_code
    valid_countries = {code for _label, code in REGION_PRESETS if code != "auto"}
    if country not in valid_countries:
        country = default_country
    return language_id, country


def detect_system_language():
    raw = (os.environ.get("LC_ALL") or os.environ.get("LC_MESSAGES") or
           os.environ.get("LANGUAGE", "").split(":", 1)[0] or os.environ.get("LANG", ""))
    tag = raw.split(".", 1)[0].split("@", 1)[0].replace("_", "-").lower()
    if tag.startswith("en"):
        return "en-US"
    if tag.startswith("pt"):
        return "pt-BR"
    if tag.startswith("fr"):
        return "fr-FR"
    return "es-LA"


class GlassSwitch(tk.Canvas):
    """Compact animated switch drawn on a frosted-glass track, without 0/1 text."""

    def __init__(self, parent, variable, command=None):
        super().__init__(parent, width=54, height=30, bg=parent.cget("bg"),
                         highlightthickness=0, bd=0, cursor="hand2", takefocus=True)
        self.variable = variable
        self.command = command
        self.position = 1.0 if variable.get() else 0.0
        self.target = self.position
        self.bind("<Button-1>", self._toggle)
        self.bind("<space>", self._toggle)
        self.bind("<Return>", self._toggle)
        self.bind("<Enter>", lambda _event: self._paint(hover=True))
        self.bind("<Leave>", lambda _event: self._paint())
        self._trace = variable.trace_add("write", self._changed)
        self.bind("<Destroy>", self._on_destroy, add="+")
        self._paint()

    def _toggle(self, _event=None):
        self.variable.set(not bool(self.variable.get()))
        if self.command:
            self.command()
        return "break"

    def _changed(self, *_args):
        self.target = 1.0 if self.variable.get() else 0.0
        self._animate_step()

    def _animate_step(self):
        delta = self.target - self.position
        if abs(delta) <= 0.08:
            self.position = self.target
            self._paint()
            return
        self.position += 0.32 if delta > 0 else -0.32
        self._paint()
        self._after_id = self.after(14, self._animate_step)

    def _paint(self, hover=False):
        self.delete("all")
        active = self.position > 0.5
        track = THEME["green_low"] if active else (THEME["panel3"] if not hover else THEME["glass"])
        edge = THEME["shine"] if active or hover else THEME["border"]
        self.create_rectangle(13, 5, 41, 25, fill=track, outline="")
        self.create_oval(3, 5, 23, 25, fill=track, outline="")
        self.create_oval(31, 5, 51, 25, fill=track, outline="")
        self.create_rectangle(12, 5, 42, 25, outline=edge, width=1)
        self.create_oval(3, 5, 23, 25, outline=edge, width=1)
        self.create_oval(31, 5, 51, 25, outline=edge, width=1)
        center = 14 + self.position * 26
        self.create_oval(center - 8, 7, center + 8, 23,
                         fill=THEME["green_hi"] if active else THEME["muted"],
                         outline=THEME["text"] if hover else THEME["border_hi"], width=1)
        self.create_arc(center - 5, 8, center + 5, 17, start=25, extent=130,
                        style="arc", outline=THEME["text"], width=1)

    def _on_destroy(self, event):
        if event.widget is self:
            try:
                self.variable.trace_remove("write", self._trace)
            except tk.TclError:
                pass


class RoundedEntry(tk.Frame):
    """Borderless text input set into a softly rounded canvas field."""

    def __init__(self, parent, variable, width=36):
        super().__init__(parent, bg=parent.cget("bg"), bd=0, highlightthickness=0)
        requested_width = max(180, min(760, width * 9 + 28))
        self.canvas = tk.Canvas(self, width=requested_width, height=38,
                                bg=parent.cget("bg"), highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.entry = tk.Entry(self.canvas, textvariable=variable, width=width,
                              bg=THEME["panel3"], fg=THEME["text"], insertbackground=THEME["green"],
                              relief="flat", bd=0, highlightthickness=0, font=(FONT, 9),
                              selectbackground=THEME["green_low"], selectforeground=THEME["text"])
        self.window_id = self.canvas.create_window(11, 5, window=self.entry, anchor="nw",
                                                   width=requested_width - 22, height=28)
        self.focused = False
        self.entry.bind("<FocusIn>", self._focus_in, add="+")
        self.entry.bind("<FocusOut>", self._focus_out, add="+")
        self.canvas.bind("<Configure>", self._resize)
        self._paint()

    def _resize(self, event):
        self.canvas.coords(self.window_id, 11, max(4, (event.height - 28) // 2))
        self.canvas.itemconfigure(self.window_id, width=max(40, event.width - 22))
        self._paint()

    def _focus_in(self, _event=None):
        self.focused = True
        self._paint()

    def _focus_out(self, _event=None):
        self.focused = False
        self._paint()

    def _paint(self):
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        if width < 4 or height < 4:
            return
        self.canvas.delete("rounded-field")
        radius = min(9, height // 3)
        points = []
        corners = ((width-radius-1, radius, -90, 0),
                   (width-radius-1, height-radius-1, 0, 90),
                   (radius, height-radius-1, 90, 180),
                   (radius, radius, 180, 270))
        for center_x, center_y, start, end in corners:
            for step in range(7):
                angle = math.radians(start + (end-start) * step / 6)
                points.extend((center_x + radius * math.cos(angle),
                               center_y + radius * math.sin(angle)))
        shape = self.canvas.create_polygon(*points, smooth=True, splinesteps=8,
                                           fill=THEME["panel3"],
                                           outline=THEME["shine"] if self.focused else THEME["border_hi"],
                                           width=1, tags="rounded-field")
        self.canvas.tag_lower(shape, self.window_id)


class Launcher:
    MAX_PAGE_WIDTH = 1420
    NAV = [("home", "01", "INICIO"), ("graphics", "02", "GRÁFICOS"),
           ("audio", "03", "AUDIO"), ("system", "04", "SISTEMA"),
           ("advanced", "05", "AVANZADO")]

    def __init__(self, root):
        self.root = root
        self.settings = load_settings()
        self.ui_language = LAUNCHER_LANGUAGE_CODES.get(self.settings.get("launcher_language", "Español"), "es")
        self.hardware_info = {"cpu": "No detectado", "gpu": "No detectada", "ram": "—", "audio": []}
        self.gpu_devices = detect_gpus()
        self.events = queue.Queue()
        self.process = None
        self.busy = False
        self.app_fullscreen = False
        self.fullscreen_override = False
        self.minimized_for_game = False
        self.restore_fullscreen_after_game = False
        self.page = "home"
        self.logs = []
        self.nav_items = {}
        self.vars = {key: tk.StringVar(value=str(self.settings.get(key, default)))
                     for key, default in DEFAULTS.items()
                     if not isinstance(default, bool) and key not in SWITCH_KEYS}
        self.bools = {key: tk.BooleanVar(value=bool(self.settings.get(key, default)))
                      for key, default in DEFAULTS.items() if isinstance(default, bool)}
        self.switch_vars = {key: tk.BooleanVar(value=str(self.settings.get(key, default)) in {"1", "true", "yes", "on"})
                            for key, default in DEFAULTS.items() if key in SWITCH_KEYS}
        self.cpu_mode_var = tk.StringVar(value="Núcleos físicos" if self.switch_vars["phys_cores"].get()
                                         else "Todos los hilos lógicos")
        self.language_choice_var = tk.StringVar(value=self.settings.get("launcher_language", "Español"))
        self.region_choice_var = tk.StringVar()
        self.audio_choice_var = tk.StringVar(value=self.settings.get("audio_device", "default"))
        self.upscaler_choice_var = tk.StringVar(value=UPSCALER_LABEL_BY_CODE.get(str(self.settings.get("upscaler", "0")), UPSCALER_OPTIONS[0][0]))
        self.upscale_preset_var = tk.StringVar(value=UPSCALER_PRESET_LABEL_BY_CODE.get(str(self.settings.get("upscale_preset", "1")), UPSCALER_PRESETS[1][0]))
        self.fsr_sharpness_var = tk.StringVar(value=str(self.settings.get("fsr_sharpness", "50")))
        self.gpu_choice_var = tk.StringVar(value=str(self.settings.get("gpu_device", "auto")))
        self._audio_control_vars = {}
        self._configure_window()
        try:
            self.wallpaper_base = tk.PhotoImage(file=str(BACKGROUND_IMAGE))
            self.wallpaper = self.wallpaper_base
        except tk.TclError:
            self.wallpaper = self.wallpaper_base = None
        try:
            self.sidebar_wallpaper = tk.PhotoImage(file=str(SIDEBAR_BACKGROUND_IMAGE))
        except tk.TclError:
            self.sidebar_wallpaper = self.wallpaper_base
        try:
            self.control_wallpaper = tk.PhotoImage(file=str(CONTROL_BACKGROUND_IMAGE))
        except tk.TclError:
            self.control_wallpaper = self.sidebar_wallpaper
        try:
            self.icon_image = tk.PhotoImage(file=str(ICON_IMAGE))
            self.root.iconphoto(True, self.icon_image)
        except tk.TclError:
            self.icon_image = None
        self._configure_styles()
        self._build_layout()
        self._show_page("home")
        self.vars["game_dir"].trace_add("write", self._game_path_changed)
        self._refresh_game_state()
        threading.Thread(target=lambda: self.events.put(("hardware", detect_hardware())), daemon=True).start()
        threading.Thread(target=self._startup_detect, daemon=True).start()
        self.root.after(70, self._poll_events)

    def _tr(self, text):
        if not isinstance(text, str) or self.ui_language == "es":
            return text
        return UI_TRANSLATIONS.get(self.ui_language, {}).get(text, text)

    def _resize_backdrop(self, _event=None):
        canvas = getattr(self, "page_backdrop", None)
        if canvas is None or not canvas.winfo_exists():
            return
        self._draw_wallpaper_region(canvas, align_to_window=False, image=self.control_wallpaper)

    def _draw_wallpaper_region(self, canvas, align_to_window=True, image=None):
        image = image or self.wallpaper_base
        if not image or not canvas.winfo_exists():
            return
        canvas.delete("wallpaper")
        image_width, image_height = image.width(), image.height()
        if align_to_window:
            x = canvas.winfo_rootx() - self.root.winfo_rootx()
            y = canvas.winfo_rooty() - self.root.winfo_rooty()
            origin_x = (self.root.winfo_width() - image_width) // 2 - x
            origin_y = (self.root.winfo_height() - image_height) // 2 - y
        else:
            origin_x = (canvas.winfo_width() - image_width) // 2
            origin_y = (canvas.winfo_height() - image_height) // 2
        canvas.create_image(origin_x, origin_y, image=image,
                            anchor="nw", tags="wallpaper")
        canvas.tag_lower("wallpaper")

    def _wallpaper_layer(self, parent, image=None):
        layer = tk.Canvas(parent, bg=THEME["bg"], highlightthickness=0, bd=0)
        layer.place(x=0, y=0, relwidth=1, relheight=1)
        layer.bind("<Configure>", lambda _event, canvas=layer, photo=image:
                   self._draw_wallpaper_region(canvas, image=photo))
        self._draw_wallpaper_region(layer, image=image)
        return layer

    def _configure_window(self):
        self.root.title(f"The Last of Us Remastered · Launcher {LAUNCHER_VERSION}")
        self.root.configure(bg=THEME["bg"])
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        width, height = max(560, min(1260, sw - 48)), max(440, min(820, sh - 72))
        self.root.geometry(f"{width}x{height}+{max(0, (sw-width)//2)}+{max(0, (sh-height)//2)}")
        self.root.minsize(min(900, width), min(620, height))
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.root.bind("<Escape>", self._exit_fullscreen)

    def _toggle_fullscreen(self, _event=None):
        if self.app_fullscreen:
            self._exit_fullscreen()
        else:
            self._enter_fullscreen()
        return "break"

    def _enter_fullscreen(self):
        self.windowed_geometry = self.root.geometry()
        self.app_fullscreen = True
        self.fullscreen_override = False
        try:
            self.root.attributes("-fullscreen", True)
            self.root.update_idletasks()
            if str(self.root.attributes("-fullscreen")).lower() in {"1", "true"}:
                return
        except tk.TclError:
            pass
        # Some X11 window managers ignore Tk's fullscreen attribute. The borderless geometry
        # fallback still fills the work display and can be restored without destroying the root.
        self.fullscreen_override = True
        self.root.overrideredirect(True)
        self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        self.root.lift()

    def _exit_fullscreen(self, _event=None):
        if self.app_fullscreen:
            self.app_fullscreen = False
            if self.fullscreen_override:
                self.root.overrideredirect(False)
                self.root.geometry(self.windowed_geometry)
                self.fullscreen_override = False
            else:
                self.root.attributes("-fullscreen", False)
            return "break"
        return None

    def _ensure_minimized_for_game(self):
        if not self.minimized_for_game:
            return
        try:
            if self.root.state() not in {"iconic", "withdrawn"}:
                # Some X11 compositors ignore Tk's iconify request; lowering keeps the launcher
                # mapped and in the window switcher; the exit event raises the same window again.
                self.root.lower()
        except tk.TclError:
            pass

    def _restore_window_after_game(self):
        if not self.minimized_for_game:
            return
        restore_fullscreen = getattr(self, "restore_fullscreen_after_game", False)
        self.minimized_for_game = False
        self.restore_fullscreen_after_game = False
        try:
            self.root.deiconify()
            if restore_fullscreen:
                self._enter_fullscreen()
            self.root.lift()
            self.root.focus_force()
        except tk.TclError:
            pass

    def _configure_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Dark.TCombobox", fieldbackground=THEME["panel3"], background=THEME["panel3"],
                        foreground=THEME["text"], arrowcolor=THEME["muted"], bordercolor=THEME["border"],
                        lightcolor=THEME["border"], darkcolor=THEME["border"], padding=(10, 8))
        style.map("Dark.TCombobox", fieldbackground=[("readonly", THEME["panel3"])],
                  foreground=[("readonly", THEME["text"])], selectbackground=[("readonly", THEME["panel3"])])
        style.configure("Dark.Vertical.TScrollbar", background=THEME["panel2"], troughcolor=THEME["bg"],
                        bordercolor=THEME["bg"], arrowcolor=THEME["muted"], width=8)
        self.root.option_add("*TCombobox*Listbox.background", THEME["panel2"])
        self.root.option_add("*TCombobox*Listbox.foreground", THEME["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", THEME["green_low"])

    def _build_layout(self):
        shell = tk.Frame(self.root, bg=THEME["bg"])
        shell.pack(fill="both", expand=True)
        shell.grid_rowconfigure(1, weight=1)
        shell.grid_columnconfigure(1, weight=1)
        self.shell = shell
        self._wallpaper_layer(shell)
        self._build_header()
        self._build_sidebar()
        self._build_pages()
        self._build_footer()

    def _build_header(self):
        header = tk.Frame(self.shell, bg=THEME["bg"], height=76)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_propagate(False)
        self._wallpaper_layer(header)
        header.grid_columnconfigure(1, weight=1)
        brand = tk.Frame(header, bg=THEME["bg"])
        brand.grid(row=0, column=0, sticky="w", padx=(26, 0))
        wordmark = tk.Frame(brand, bg=THEME["bg"])
        wordmark.pack(side="left")
        self._label(wordmark, "THE LAST OF US", 10, THEME["text"], bold=True, display=True).pack(anchor="w")
        self._label(wordmark, "REMASTERED   /   PC PORT", 7, THEME["muted"], mono=True).pack(anchor="w", pady=(4, 0))
        right_info = tk.Frame(header, bg=THEME["bg"])
        right_info.grid(row=0, column=1, sticky="e", padx=(10, 26))
        hardware_text = (f"{self.hardware_info['gpu']}   ·   {self.hardware_info['ram']} RAM"
                         if self.hardware_info["gpu"] != "No detectada" else "DETECTANDO HARDWARE")
        self.hardware_header = self._label(right_info, hardware_text, 8, THEME["muted"], mono=True)
        self.hardware_header.grid(row=0, column=0, sticky="e")
        language_row = tk.Frame(right_info, bg=THEME["bg"])
        language_row.grid(row=1, column=0, sticky="e", pady=(5, 0))
        self._label(language_row, "IDIOMA DEL LANZADOR", 7, THEME["yellow"], mono=True).pack(side="left", padx=(0, 8))
        self.launcher_lang_var = tk.StringVar(value=self.settings.get("launcher_language", "Español"))
        self.launcher_lang_combo = ttk.Combobox(language_row, textvariable=self.launcher_lang_var, values=LAUNCHER_LANGUAGES, state="readonly", width=11, font=(FONT, 8))
        self.launcher_lang_combo.pack(side="left")
        self.launcher_lang_combo.bind("<<ComboboxSelected>>", self._launcher_lang_changed)
        tk.Frame(header, bg=THEME["border"], height=1).place(relx=0, rely=1, relwidth=1, anchor="sw")

    def _build_sidebar(self):
        side = tk.Frame(self.shell, bg=THEME["sidebar"], width=214)
        side.grid(row=1, column=0, sticky="nsew")
        side.grid_propagate(False)
        self._wallpaper_layer(side, self.sidebar_wallpaper)
        control_heading = tk.Canvas(side, height=30, bg=THEME["sidebar"], highlightthickness=0, bd=0)
        control_heading.pack(fill="x", padx=10, pady=(17, 9))
        self._draw_wallpaper_region(control_heading, image=self.sidebar_wallpaper)
        self.control_heading_id = control_heading.create_text(11, 15, text=self._tr("CENTRO DE CONTROL"),
                                                              anchor="w", fill=THEME["text"], font=(MONO, 8, "bold"))
        control_heading.bind("<Configure>", lambda _event, canvas=control_heading, photo=self.sidebar_wallpaper:
                             self._draw_wallpaper_region(canvas, image=photo))
        for key, number, label in self.NAV:
            row = tk.Frame(side, bg=THEME["sidebar"], height=46, cursor="hand2")
            row.pack(fill="x", padx=10, pady=2)
            row.pack_propagate(False)
            stripe = tk.Frame(row, bg=THEME["sidebar"], width=2)
            stripe.pack(side="left", fill="y")
            inner = tk.Frame(row, bg=THEME["sidebar"])
            inner.pack(side="left", fill="both", expand=True, padx=(12, 5))
            num = self._label(inner, number, 8, THEME["dim"], mono=True)
            num.pack(side="left", padx=(0, 12))
            name = self._label(inner, label, 8, THEME["muted"], bold=True)
            name.pack(side="left")
            for widget in (row, inner, num, name, stripe):
                widget.bind("<Button-1>", lambda _event, page=key: self._show_page(page))
                widget.bind("<Enter>", lambda _event, item=row, page=key: self._hover_nav(item, page, True))
                widget.bind("<Leave>", lambda _event, item=row, page=key: self._hover_nav(item, page, False))
            self.nav_items[key] = (row, stripe, num, name)
        foot = tk.Frame(side, bg=THEME["sidebar"])
        foot.pack(side="bottom", fill="x", padx=20, pady=20)
        tk.Frame(foot, bg=THEME["border"], height=1).pack(fill="x", pady=(0, 13))
        self._label(foot, "VERSIÓN DEL LANZADOR", 7, THEME["dim"], mono=True).pack(anchor="w")
        self._label(foot, LAUNCHER_VERSION, 8, THEME["text"], mono=True, bold=True).pack(anchor="w", pady=(4, 0))
        self._label(foot, "CUSA00552  ·  RETAIL", 7, THEME["muted"], mono=True).pack(anchor="w", pady=(3, 0))
        tk.Frame(self.shell, bg=THEME["border"], width=1).grid(row=1, column=0, sticky="nse")

    def _build_pages(self):
        area = tk.Frame(self.shell, bg=THEME["bg"])
        area.grid(row=1, column=1, sticky="nsew")
        self._wallpaper_layer(area, self.control_wallpaper)
        area.grid_rowconfigure(1, weight=1)
        area.grid_columnconfigure(0, weight=1)
        self.area = area
        self.heading = tk.Canvas(area, bg=THEME["bg"], height=86, highlightthickness=0, bd=0)
        self.heading.grid(row=0, column=0, sticky="ew", padx=32, pady=(18, 5))
        self._draw_wallpaper_region(self.heading, image=self.control_wallpaper)
        self.heading.bind("<Configure>", lambda _event, canvas=self.heading, photo=self.control_wallpaper:
                          self._draw_wallpaper_region(canvas, image=photo))
        self.eyebrow_id = self.heading.create_text(0, 2, text=self._tr("01  /  LIBRERÍA"),
                                                   anchor="nw", fill=THEME["yellow"], font=(MONO, 8, "bold"))
        self.title_id = self.heading.create_text(0, 22, text=self._tr("Tu juego, listo."),
                                                 anchor="nw", fill=THEME["text"], font=(FONT, 21, "bold"))
        self.subtitle_id = self.heading.create_text(0, 57, text=self._tr("Configura el port y entra directamente al juego."),
                                                    anchor="nw", fill=THEME["muted"], font=(FONT, 8))
        self.heading.bind("<Configure>", self._heading_resized, add="+")
        self.canvas = tk.Canvas(area, bg=THEME["bg"], highlightthickness=0, bd=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=(25, 4), pady=(4, 8))
        self.scrollbar = ttk.Scrollbar(area, orient="vertical", command=self.canvas.yview, style="Dark.Vertical.TScrollbar")
        self.scrollbar.grid(row=1, column=1, sticky="ns", pady=(4, 8), padx=(0, 7))
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.page_frame = tk.Frame(self.canvas, bg=THEME["bg"])
        self.page_window = self.canvas.create_window((0, 0), window=self.page_frame, anchor="nw")
        self.page_backdrop = tk.Canvas(self.page_frame, bg=THEME["bg"], highlightthickness=0, bd=0)
        self.page_backdrop.place(x=0, y=0, relwidth=1, relheight=1)
        self.page_backdrop.bind("<Configure>", self._resize_backdrop)
        self._resize_backdrop()
        self.page_frame.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._resize_page_content)
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(-1 if e.delta > 0 else 1, "units"))
        self.canvas.bind_all("<Button-4>", lambda _e: self.canvas.yview_scroll(-3, "units"))
        self.canvas.bind_all("<Button-5>", lambda _e: self.canvas.yview_scroll(3, "units"))

    def _resize_page_content(self, event):
        viewport_width = max(1, event.width)
        content_width = min(viewport_width, self.MAX_PAGE_WIDTH)
        margin = (viewport_width - content_width) // 2
        self.canvas.coords(self.page_window, margin, 0)
        self.canvas.itemconfigure(self.page_window, width=content_width)
        if self.heading.winfo_exists():
            self.heading.grid_configure(padx=(25 + margin, 4 + margin))

    def _build_footer(self):
        footer = tk.Frame(self.shell, bg=THEME["sidebar"], height=72)
        footer.grid(row=2, column=0, columnspan=2, sticky="ew")
        footer.grid_propagate(False)
        self._wallpaper_layer(footer)
        footer.grid_columnconfigure(0, weight=1)
        tk.Frame(footer, bg=THEME["border"], height=1).place(relx=0, rely=0, relwidth=1, height=1)
        status = tk.Frame(footer, bg=THEME["sidebar"])
        status.grid(row=0, column=0, sticky="w", padx=24, pady=11)
        self.dot = tk.Canvas(status, width=10, height=10, bg=THEME["sidebar"], highlightthickness=0)
        self.dot.pack(side="left", padx=(0, 9))
        self.dot_id = self.dot.create_oval(2, 2, 8, 8, fill=THEME["dim"], outline="")
        self.status = self._label(status, "Esperando carpeta del juego", 8, THEME["muted"])
        self.status.pack(side="left")
        actions = tk.Frame(footer, bg=THEME["sidebar"])
        actions.grid(row=0, column=1, sticky="e", padx=23, pady=10)
        self._button(actions, "SAVES", self.open_saves, "quiet", 7).pack(side="left", padx=(0, 5))
        self._button(actions, "LOGS", self.open_logs, "quiet", 7).pack(side="left", padx=(0, 5))
        self._button(actions, "CACHÉ", self.clear_cache, "quiet", 7).pack(side="left", padx=(0, 11))
        self.play_button = self._button(actions, "▶   INICIAR JUEGO", self.play, "primary", 22, 40)
        self.play_button.pack(side="left")

    def _label(self, parent, text, size=9, color=None, bold=False, mono=False, display=False):
        family = HEADLINE_FONT if display else MONO if mono else FONT
        return tk.Label(parent, text=self._tr(text), bg=parent.cget("bg"), fg=color or THEME["text"],
                        font=(family, size, "bold" if bold else "normal"), anchor="w", justify="left")

    def _heading_resized(self, event):
        self.heading.itemconfigure(self.subtitle_id, width=max(1, event.width - 8))

    def _set_heading(self, eyebrow, title, subtitle):
        self.heading.itemconfigure(self.eyebrow_id, text=self._tr(eyebrow))
        self.heading.itemconfigure(self.title_id, text=self._tr(title))
        self.heading.itemconfigure(self.subtitle_id, text=self._tr(subtitle))

    def _button(self, parent, text, command, kind="secondary", width=None, height=32):
        if kind == "primary":
            bg, fg, hover, edge = THEME["green"], THEME["black"], THEME["green_hi"], THEME["green"]
        elif kind == "danger":
            bg, fg, hover, edge = "#512f35", THEME["text"], "#693b43", THEME["red"]
        elif kind == "quiet":
            bg, fg, hover, edge = THEME["sidebar"], THEME["muted"], THEME["panel2"], THEME["border"]
        else:
            bg, fg, hover, edge = THEME["panel3"], THEME["text"], THEME["border_hi"], THEME["border"]
        button = tk.Button(parent, text=self._tr(text), command=command, bg=bg, fg=fg,
                           activebackground=hover, activeforeground=fg, relief="flat", bd=0,
                           highlightthickness=1, highlightbackground=edge, highlightcolor=THEME["green"],
                           cursor="hand2", font=(FONT, 8, "bold"), padx=12, pady=7)
        if width:
            button.configure(width=width)
        button.bind("<Enter>", lambda _e, b=button, h=hover: b.configure(bg=h) if b["state"] != "disabled" else None)
        button.bind("<Leave>", lambda _e, b=button, base=bg: b.configure(bg=base) if b["state"] != "disabled" else None)
        return button

    def _card(self, parent, heading=None, hint=None, accent=False):
        edge = tk.Frame(parent, bg=THEME["border_hi"] if accent else THEME["border"])
        surface = tk.Frame(edge, bg=THEME["panel2"])
        surface.pack(fill="both", expand=True, padx=1, pady=1)
        tk.Frame(surface, bg=THEME["shine"], height=1).pack(fill="x", padx=14, pady=(1, 1))
        body = tk.Frame(surface, bg=THEME["panel2"])
        body.pack(fill="both", expand=True, padx=16, pady=15)
        if heading:
            self._label(body, heading, 9, THEME["text"], bold=True).pack(anchor="w")
        if hint:
            self._label(body, hint, 8, THEME["muted"]).pack(anchor="w", pady=(4, 0))
        return edge, body

    def _entry(self, parent, variable, width=36):
        return RoundedEntry(parent, variable, width)

    def _combo(self, parent, variable, values, width=20):
        source_values = [str(value) for value in values]
        visible_values = [self._tr(value) for value in source_values]
        display_to_source = dict(zip(visible_values, source_values))
        source_to_display = dict(zip(source_values, visible_values))
        display_var = tk.StringVar(parent, value=source_to_display.get(variable.get(), self._tr(variable.get())))
        combo = ttk.Combobox(parent, textvariable=display_var, values=visible_values, state="readonly",
                             style="Dark.TCombobox", width=width, font=(FONT, 9))
        combo.bind("<<ComboboxSelected>>",
                   lambda _event, var=variable, shown=display_var, mapping=display_to_source:
                   var.set(mapping.get(shown.get(), shown.get())))
        combo._source_variable = variable
        combo._display_variable = display_var
        return combo

    def _check(self, parent, variable, label, detail=""):
        row = tk.Frame(parent, bg=THEME["panel"])
        row.pack(fill="x", pady=(11, 2))
        tk.Checkbutton(row, text=self._tr(label), variable=variable, bg=THEME["panel"], fg=THEME["text"],
                       activebackground=THEME["panel"], activeforeground=THEME["text"],
                       selectcolor=THEME["panel3"], highlightthickness=0, bd=0,
                       font=(FONT, 9), cursor="hand2").pack(anchor="w")
        if detail:
            self._label(row, detail, 8, THEME["muted"]).pack(anchor="w", padx=(25, 0), pady=(1, 0))

    def _show_page(self, name):
        self.page = name
        for key, (row, stripe, num, label) in self.nav_items.items():
            active = key == name
            bg = THEME["panel2"] if active else THEME["sidebar"]
            row.configure(bg=bg)
            stripe.configure(bg=THEME["green"] if active else bg)
            num.configure(bg=bg, fg=THEME["green"] if active else THEME["dim"])
            label.configure(bg=bg, fg=THEME["text"] if active else THEME["muted"])
        for child in self.page_frame.winfo_children():
            if child is not self.page_backdrop:
                child.destroy()
        self.page_frame.columnconfigure(0, weight=1)
        if name == "home":
            self._set_heading("01  /  LIBRERÍA", "Tu juego, listo.",
                              "Configura el port y entra directamente al juego.")
            self._page_home()
        elif name == "graphics":
            self._set_heading("02  /  IMAGEN", "Ajustes gráficos",
                              "Configura la presentación, resolución y presupuesto de vídeo.")
            self._page_graphics()
        elif name == "audio":
            self._set_heading("03  /  SONIDO", "Audio",
                              "Estado de la ruta de audio implementada por el port.")
            self._page_audio()
        elif name == "system":
            self._set_heading("04  /  PREFERENCIAS", "Idioma y región",
                              "El juego consulta el idioma del sistema al arrancar.")
            self._page_system()
        else:
            self._set_heading("05  /  MOTOR", "Ajustes avanzados",
                              "Parámetros del runtime. Los valores iniciales ya están configurados.")
            self._page_advanced()
        self.canvas.yview_moveto(0)

    def _page_home(self):
        hero_edge = tk.Frame(self.page_frame, bg=THEME["border_hi"])
        hero_edge.grid(row=0, column=0, sticky="ew", pady=(1, 12))
        hero = tk.Canvas(hero_edge, bg=THEME["panel"], height=206, highlightthickness=0, bd=0)
        hero.pack(fill="x", padx=1, pady=1)
        hero.bind("<Configure>", lambda event, canvas=hero: self._draw_home_hero(canvas, event.width, event.height))
        self._draw_home_hero(hero, 900, 206)
        edge, body = self._card(self.page_frame, "UBICACIÓN DEL JUEGO",
                                "Arrastra aquí la carpeta del juego o un archivo .pkg; también puedes usar Examinar.")
        edge.grid(row=1, column=0, sticky="ew", pady=(0, 11))
        body.columnconfigure(0, weight=1)
        path_row = tk.Frame(body, bg=THEME["panel"])
        path_row.pack(fill="x", pady=(11, 0))
        path_row.columnconfigure(0, weight=1)
        game_path_entry = self._entry(path_row, self.vars["game_dir"])
        game_path_entry.grid(row=0, column=0, sticky="ew", ipady=8)
        self._button(path_row, "EXAMINAR", self.browse_game, width=11).grid(row=0, column=1, padx=(7, 0))
        self._button(path_row, "DETECTAR", self.auto_detect, "quiet", 10).grid(row=0, column=2, padx=(5, 0))
        self._register_drop_target_tree(edge)
        self._button(body, "EXTRAER PKG", self.extract_pkg, "quiet", 14).pack(anchor="w", pady=(9, 0))
        self.validation = self._label(body, "", 8, THEME["muted"])
        self.validation.pack(anchor="w", pady=(8, 0))
        stats = tk.Frame(self.page_frame, bg=THEME["bg"])
        stats.grid(row=2, column=0, sticky="ew", pady=(0, 11))
        for col in range(3):
            stats.columnconfigure(col, weight=1, uniform="spec")
        self.spec_cpu = self._stat(stats, 0, "PROCESADOR", "Consultando…")
        self.spec_gpu = self._stat(stats, 1, "GRÁFICOS", "Consultando…")
        self.spec_ram = self._stat(stats, 2, "MEMORIA", "Consultando…")
        edge, body = self._card(self.page_frame, "ACTIVIDAD", "Salida reciente del proceso de inicio.")
        edge.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        self.log_view = tk.Text(body, height=4, wrap="word", state="disabled", bg=THEME["sidebar"],
                                fg=THEME["muted"], insertbackground=THEME["green"], relief="flat", bd=0,
                                font=(MONO, 8), padx=9, pady=7)
        self.log_view.pack(fill="both", expand=True, pady=(9, 0))
        for line in self.logs[-40:]:
            self._insert_log(line)

    def _draw_home_hero(self, canvas, width, height):
        canvas.delete("all")
        self._draw_wallpaper_region(canvas, image=self.control_wallpaper)
        canvas.create_text(17, 31, text="CUSA00552", anchor="w",
                           fill=THEME["yellow"], font=(MONO, 12, "bold"))
        canvas.create_text(20, 97, text="THE LAST OF US", anchor="w",
                           fill=THEME["text"], font=(HEADLINE_FONT, 36, "bold"))
        canvas.create_text(22, 145, text="REMASTERED", anchor="w",
                           fill=THEME["text"], font=(FONT, 15, "bold"))

    def _stat(self, parent, col, title, value):
        edge, body = self._card(parent)
        edge.grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 5, 0 if col == 2 else 5))
        self._label(body, title, 7, THEME["dim"], mono=True).pack(anchor="w")
        label = self._label(body, value, 8, THEME["text"], bold=True)
        label.pack(anchor="w", pady=(7, 0))
        return label

    def _page_graphics(self):
        grid = tk.Frame(self.page_frame, bg=THEME["bg"])
        grid.grid(row=0, column=0, sticky="ew")
        grid.columnconfigure(0, weight=1, uniform="graphics")
        grid.columnconfigure(1, weight=1, uniform="graphics")
        edge, body = self._card(grid, "PANTALLA", "Modo de presentación de la ventana.")
        edge.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 11))
        self._label(body, "MODO DE PANTALLA", 8, THEME["muted"]).pack(anchor="w", pady=(12, 5))
        self._combo(body, self.vars["display_mode"], ["Windowed", "Borderless", "Fullscreen"], 22).pack(anchor="w", fill="x")
        edge, body = self._card(grid, "RESOLUCIÓN Y ESCALADO", "No disponible en esta versión del juego (requiere parches del eboot).")
        edge.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=(0, 11))
        self._label(body, "RESOLUCIÓN DE RENDER", 8, THEME["muted"]).pack(anchor="w", pady=(12, 5))
        self._combo(body, self.vars["render_resolution"], ["native"], 20).pack(anchor="w", fill="x")
        self._combo(body, self.vars["render_resolution"], ["native"], 20).configure(state="disabled")
        self._label(body, "FPS DEL MOTOR", 8, THEME["muted"]).pack(anchor="w", pady=(11, 5))
        self._combo(body, self.vars["engine_fps"], ["30", "60", "120"], 20).pack(anchor="w", fill="x")
        self._combo(body, self.vars["engine_fps"], ["30", "60", "120"], 20).configure(state="disabled")
        self._label(body, "ESCALADO", 8, THEME["muted"]).pack(anchor="w", pady=(11, 5))
        self._combo(body, self.vars["upscaler"], ["No disponible"], 20).pack(anchor="w", fill="x")
        self._combo(body, self.vars["upscaler"], ["No disponible"], 20).configure(state="disabled")
        edge, body = self._card(grid, "PRESUPUESTO DE GPU", "Caché de texturas según memoria de vídeo.")
        edge.grid(row=1, column=0, sticky="nsew", padx=(0, 6), pady=(0, 11))
        self._label(body, "VRAM · MB", 8, THEME["muted"]).pack(anchor="w", pady=(12, 5))
        self._entry(body, self.vars["vram"], 12).pack(anchor="w", ipady=7)
        self._label(body, "6 GB: 5600   ·   8 GB: 7000   ·   12 GB: 10500", 7, THEME["muted"]).pack(anchor="w", pady=(7, 0))
        edge, body = self._card(grid, "PRESENTACIÓN", "Límite de cuadros y contador.")
        edge.grid(row=1, column=1, sticky="nsew", padx=(6, 0), pady=(0, 11))
        self._label(body, "LÍMITE DE FPS · 0 = ILIMITADO", 8, THEME["muted"]).pack(anchor="w", pady=(12, 5))
        self._entry(body, self.vars["fps_limit"], 12).pack(anchor="w", ipady=7)
        self._check(body, self.bools["show_fps"], "Mostrar contador de FPS", "F10 alterna el overlay durante el juego.")
        edge, body = self._card(grid, "DISPOSITIVO VULKAN", "Elige qué GPU renderiza el juego.")
        edge.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 11))
        self._label(body, "GPU detectada", 8, THEME["muted"]).pack(anchor="w", pady=(11, 5))
        self.gpu_option_values = {"Automática (recomendada)": "auto"}
        gpu_options = ["Automática (recomendada)"]
        for index, name, _kind in self.gpu_devices:
            label = f"{index} · {name}"
            gpu_options.append(label)
            self.gpu_option_values[label] = index
        selected_gpu = str(self.vars["gpu_device"].get())
        selected_gpu_label = next((label for label, index in self.gpu_option_values.items() if index == selected_gpu),
                                  gpu_options[0])
        self.gpu_choice_var.set(selected_gpu_label)
        gpu_combo = self._combo(body, self.gpu_choice_var, gpu_options, 52)
        gpu_combo.pack(anchor="w", fill="x")
        gpu_combo.bind("<<ComboboxSelected>>", self._gpu_selected, add="+")

    def _page_audio(self):
        edge, body = self._card(self.page_frame, "RUTA DE AUDIO", "El backend nativo se carga junto con el port.", True)
        edge.grid(row=0, column=0, sticky="ew", pady=(0, 11))
        self._label(body, "libSceNgs2.sprx", 11, THEME["text"], bold=True).pack(anchor="w", pady=(12, 3))
        self._label(body, "Selecciona el dispositivo de salida y el volumen del juego.", 8, THEME["muted"]).pack(anchor="w", pady=(3, 0))
        edge, body = self._card(self.page_frame, "DISPOSITIVO DE SALIDA", "Gestionado por el escritorio Linux.")
        edge.grid(row=1, column=0, sticky="ew")
        self._label(body, "DISPOSITIVO DE AUDIO", 8, THEME["muted"]).pack(anchor="w", pady=(12, 5))
        selected_device = str(self.settings.get("audio_device", "default"))
        audio_devices = detect_audio_devices()
        if selected_device not in audio_devices:
            selected_device = "default"
        self.audio_choice_var.set("Detectar automáticamente" if selected_device in {"", "default"} else selected_device)
        self.audio_combo = self._combo(body, self.audio_choice_var,
                                       ["Detectar automáticamente"] + audio_devices, 52)
        self.audio_combo.pack(anchor="w", fill="x")
        self.audio_combo.bind("<<ComboboxSelected>>", self._audio_selected, add="+")
        try:
            default = subprocess.check_output(["sh", "-lc", "pactl get-default-sink 2>/dev/null || wpctl status 2>/dev/null | head -1"],
                                             text=True, timeout=2).strip()
        except (OSError, subprocess.SubprocessError):
            default = "Dispositivo predeterminado del sistema"
        self._label(body, default or "Dispositivo predeterminado del sistema", 8, THEME["muted"]).pack(anchor="w", pady=(10, 0))
        edge, body = self._card(self.page_frame, "VOLUMEN DEL JUEGO", "Se aplica al audio del juego, sin cambiar el volumen del escritorio.")
        edge.grid(row=2, column=0, sticky="ew", pady=(11, 0))
        self._label(body, "VOLUMEN", 8, THEME["muted"]).pack(anchor="w", pady=(10, 4))
        volume_row = tk.Frame(body, bg=THEME["panel"])
        volume_row.pack(fill="x")
        volume = tk.Scale(volume_row, from_=0, to=100, orient="horizontal", variable=self.vars["audio_volume"],
                          showvalue=True, resolution=1, bg=THEME["panel"], fg=THEME["text"],
                          troughcolor=THEME["panel3"], activebackground=THEME["green"], highlightthickness=0,
                          bd=0, length=360)
        volume.pack(anchor="w")

    def _audio_selected(self, _event=None):
        choice = self.audio_choice_var.get()
        if choice == "Detectar automáticamente":
            self.settings["audio_device"] = "default"
            self.vars["audio_device"].set("default")
        else:
            self.settings["audio_device"] = choice
            self.vars["audio_device"].set(choice)
        self._log(f"Dispositivo de audio: {choice}")

    def _upscaler_selected(self, _event=None):
        label = self.upscaler_choice_var.get()
        value = dict(UPSCALER_OPTIONS).get(label, "0")
        self.vars["upscaler"].set(value)
        self.settings["upscaler"] = value
        save_settings(self.settings)

    def _upscale_preset_selected(self, _event=None):
        label = self.upscale_preset_var.get()
        value = dict(UPSCALER_PRESETS).get(label, "1")
        self.vars["upscale_preset"].set(value)
        self.settings["upscale_preset"] = value
        save_settings(self.settings)

    def _gpu_selected(self, _event=None):
        label = self.gpu_choice_var.get()
        self.vars["gpu_device"].set(getattr(self, "gpu_option_values", {}).get(label, "auto"))
        self._log(f"GPU seleccionada: {label}")

    def _page_system(self):
        edge, body = self._card(self.page_frame, "IDIOMA DEL SISTEMA", "Se entrega al juego antes de inicializar su interfaz.", True)
        edge.grid(row=0, column=0, sticky="ew", pady=(0, 11))
        self._label(body, "IDIOMA / VARIANTE", 8, THEME["muted"]).pack(anchor="w", pady=(12, 5))
        selected_language = self.vars["language"].get()
        self.language_choice_var.set(LANGUAGE_LABELS.get(selected_language, LANGUAGE_LABELS["es-LA"]))
        self.language_combo = self._combo(body, self.language_choice_var,
                                          [label for label, *_ in LANGUAGE_PRESETS], 30)
        self.language_combo.pack(anchor="w", fill="x")
        self.language_combo.bind("<<ComboboxSelected>>", self._language_selected, add="+")
        language_id, _language_country = resolve_language_profile(selected_language)
        self.language_info = self._label(body, f"PS4 language ID {language_id:02d}  ·  {selected_language}",
                                         7, THEME["muted"], mono=True)
        self.language_info.pack(anchor="w", pady=(8, 0))
        edge, body = self._card(self.page_frame, "PAÍS DEL PERFIL", "Auto sigue la variante elegida arriba.")
        edge.grid(row=1, column=0, sticky="ew", pady=(0, 11))
        self._label(body, "PAÍS / REGIÓN", 8, THEME["muted"]).pack(anchor="w", pady=(12, 5))
        region_code = self.vars["region"].get()
        self.region_choice_var.set(REGION_LABELS.get(region_code, REGION_LABELS["auto"]))
        self.region_combo = self._combo(body, self.region_choice_var,
                                        [label for label, _code in REGION_PRESETS], 24)
        self.region_combo.pack(anchor="w", fill="x")
        self.region_combo.bind("<<ComboboxSelected>>", self._region_selected, add="+")
        _language_id, effective_country = resolve_language_profile(selected_language, region_code)
        self.region_info = self._label(body, f"País efectivo: {effective_country.upper()}",
                                        7, THEME["muted"], mono=True)
        self.region_info.pack(anchor="w", pady=(8, 0))
        edge, body = self._card(self.page_frame, "QUÉ CAMBIA", "Preferencias emuladas del sistema PS4.")
        edge.grid(row=2, column=0, sticky="ew", pady=(0, 11))
        self._label(body, "El idioma se aplica al iniciar. Puedes elegir español, portugués de Brasil, inglés o francés.",
                    8, THEME["text"]).pack(anchor="w", pady=(10, 5))
        self._label(body, "El país ajusta el locale de cuenta que entrega el runtime. No convierte CUSA00552 en otra edición regional ni añade doblajes/subtítulos ausentes del dump.",
                    8, THEME["muted"]).pack(anchor="w")

    def _language_selected(self, _event=None):
        code = LANGUAGE_CODES_BY_LABEL.get(self.language_choice_var.get(), "es-LA")
        self.vars["language"].set(code)
        language_id, country = resolve_language_profile(code, self.vars["region"].get())
        if hasattr(self, "language_info") and self.language_info.winfo_exists():
            self.language_info.configure(text=f"PS4 language ID {language_id:02d}  ·  {code}")
        if hasattr(self, "region_info") and self.region_info.winfo_exists():
            self.region_info.configure(text=f"País efectivo: {country.upper()}")
        self._log(f"Idioma del sistema: {code} · PS4 ID {language_id} · país {country.upper()}")

    def _region_selected(self, _event=None):
        code = REGION_CODES_BY_LABEL.get(self.region_choice_var.get(), "auto")
        self.vars["region"].set(code)
        _language_id, country = resolve_language_profile(self.vars["language"].get(), code)
        if hasattr(self, "region_info") and self.region_info.winfo_exists():
            self.region_info.configure(text=f"País efectivo: {country.upper()}")
        self._log(f"País del perfil: {country.upper()}")

    def _page_advanced(self):
        for row, (heading, values) in enumerate((("MEMORIA Y PLANIFICACIÓN", ADVANCED[:5]), ("RUTA DE RENDER", ADVANCED[5:]))):
            edge, body = self._card(self.page_frame, heading, "Los cambios se guardan al iniciar el juego.")
            edge.grid(row=row, column=0, sticky="ew", pady=(0, 11))
            fields = tk.Frame(body, bg=THEME["panel"])
            fields.pack(fill="x", pady=(10, 0))
            fields.columnconfigure(1, weight=1)
            for i, (key, env_name, label, note) in enumerate(values):
                y = i * 2
                self._label(fields, label, 8, THEME["text"], bold=True).grid(row=y, column=0, sticky="w", pady=(5, 1))
                if key == "auto_gyro":
                    help_link = tk.Label(fields, text=f"{env_name}  ·  {MOTION_HELP_TEXT[self.ui_language]['link']}",
                                         bg=THEME["panel"], fg=THEME["yellow"],
                                         font=(MONO, 7), anchor="w", cursor="hand2")
                    help_link.bind("<Button-1>", lambda _event: self._show_motion_help())
                    help_link.bind("<Enter>", lambda _event, widget=help_link: widget.configure(fg=THEME["yellow_hi"]))
                    help_link.bind("<Leave>", lambda _event, widget=help_link: widget.configure(fg=THEME["yellow"]))
                    help_link.grid(row=y+1, column=0, sticky="w", pady=(0, 5))
                else:
                    self._label(fields, f"{env_name}  ·  {note}", 7, THEME["muted"], mono=True).grid(row=y+1, column=0, sticky="w", pady=(0, 5))
                if key == "phys_cores":
                    self.cpu_mode_var.set("Núcleos físicos" if self.switch_vars[key].get() else "Todos los hilos lógicos")
                    cpu_combo = self._combo(fields, self.cpu_mode_var,
                                            ["Todos los hilos lógicos", "Núcleos físicos"], 25)
                    cpu_combo.grid(row=y, column=1, rowspan=2, sticky="e", padx=(15, 2))
                    cpu_combo.bind("<<ComboboxSelected>>", self._cpu_mode_selected, add="+")
                elif key in SWITCH_KEYS:
                    GlassSwitch(fields, self.switch_vars[key]).grid(row=y, column=1, rowspan=2,
                                                                    sticky="e", padx=(15, 2))
                else:
                    self._entry(fields, self.vars[key], 12).grid(row=y, column=1, rowspan=2,
                                                                  sticky="e", padx=(15, 2), ipady=6)
                tk.Frame(fields, bg=THEME["border"], height=1).grid(row=y+2, column=0, columnspan=2, sticky="ew", pady=(4, 3))

    def _cpu_mode_selected(self, _event=None):
        self.switch_vars["phys_cores"].set(self.cpu_mode_var.get() == "Núcleos físicos")

    def _show_motion_help(self):
        text = MOTION_HELP_TEXT.get(self.ui_language, MOTION_HELP_TEXT["es"])
        window = tk.Toplevel(self.root)
        window.title(text["title"])
        window.configure(bg=THEME["bg"])
        window.transient(self.root)
        window.resizable(False, False)
        width, height = 480, 280
        x = self.root.winfo_rootx() + max(0, (self.root.winfo_width() - width) // 2)
        y = self.root.winfo_rooty() + max(0, (self.root.winfo_height() - height) // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")
        body = tk.Frame(window, bg=THEME["panel2"], padx=22, pady=20)
        body.pack(fill="both", expand=True, padx=1, pady=1)
        self._label(body, text["title"], 13, THEME["text"], bold=True, display=True).pack(anchor="w")
        self._label(body, text["intro"], 9, THEME["muted"]).pack(anchor="w", pady=(12, 8))
        for key in ("stick", "shake", "keyboard"):
            self._label(body, f"•  {text[key]}", 9, THEME["text"]).pack(anchor="w", pady=2)
        note = self._label(body, text["note"], 8, THEME["muted"])
        note.configure(wraplength=430)
        note.pack(anchor="w", pady=(10, 10))
        self._button(body, text["close"], window.destroy, "quiet", 12).pack(anchor="e")
        window.bind("<Escape>", lambda _event: window.destroy())
        window.grab_set()

    def _hover_nav(self, row, key, entering):
        if key != self.page:
            row.configure(bg=THEME["panel"] if entering else THEME["sidebar"])

    def _set_status(self, text, good=False):
        if self.status.winfo_exists():
            self.status.configure(text=self._tr(text), fg=THEME["green"] if good else THEME["muted"])
        if hasattr(self, "dot") and self.dot.winfo_exists():
            self.dot.itemconfigure(self.dot_id, fill=THEME["green"] if good else THEME["dim"])

    def _launcher_lang_changed(self, _event=None):
        self.settings["launcher_language"] = self.launcher_lang_var.get()
        self.ui_language = LAUNCHER_LANGUAGE_CODES.get(self.launcher_lang_var.get(), "es")
        save_settings(self.settings)
        self.shell.destroy()
        self.nav_items = {}
        self._build_layout()
        self._show_page(self.page)
        self._refresh_game_state()
        self._log(f"Idioma del launcher: {self.launcher_lang_var.get()}")

    def _refresh_game_state(self, *_args):
        game = self.vars["game_dir"].get().strip()
        valid = bool(game and (Path(game) / "eboot.bin").is_file())
        if hasattr(self, "validation") and self.validation.winfo_exists():
            self.validation.configure(
                text=(f"●  eboot.bin encontrado  ·  {game}" if valid else
                      "●  No se encontró eboot.bin en la carpeta indicada." if game else
                      "●  Selecciona la carpeta del juego para habilitar el inicio."),
                fg=THEME["green"] if valid else THEME["red"] if game else THEME["muted"])
        if valid:
            self._set_status("Carpeta del juego verificada", True)
        elif game:
            self._set_status("No se encontró eboot.bin")
        else:
            self._set_status("Esperando carpeta del juego")

    def _game_path_changed(self, *_args):
        self._refresh_game_state()

    def _register_drop_target(self, widget):
        if not hasattr(widget, "drop_target_register"):
            return
        try:
            widget.drop_target_register(DND_FILES)
            widget.dnd_bind("<<Drop>>", self._handle_game_drop)
        except (tk.TclError, RuntimeError):
            pass

    def _register_drop_target_tree(self, widget):
        self._register_drop_target(widget)
        for child in widget.winfo_children():
            self._register_drop_target_tree(child)

    def _handle_game_drop(self, event):
        try:
            dropped = self.root.tk.splitlist(event.data)
        except (tk.TclError, AttributeError):
            dropped = (str(getattr(event, "data", "")).strip().strip("{}"),)
        for value in dropped:
            candidate = Path(str(value).strip()).expanduser()
            if candidate.suffix.lower() == ".pkg" and candidate.is_file():
                self._log(f"PKG arrastrado · {candidate.name}")
                self.extract_pkg(str(candidate))
                return DND_COPY
            folder = candidate.parent if candidate.is_file() and candidate.name.lower() == "eboot.bin" else candidate
            if folder.is_dir():
                found = find_eboot(folder)
                if found:
                    self.vars["game_dir"].set(str(found))
                    self._set_status("Carpeta del juego verificada", True)
                    self._log(f"Carpeta del juego arrastrada · {found}")
                    return DND_COPY
        self._set_status("Arrastra una carpeta con eboot.bin o un archivo .pkg")
        return "refuse_drop"

    def browse_game(self):
        chosen = filedialog.askdirectory(title="Seleccionar carpeta del juego")
        if not chosen:
            return
        found = find_eboot(chosen)
        if found:
            self.vars["game_dir"].set(str(found))
            self._log(f"Carpeta seleccionada: {found}")
        else:
            messagebox.showerror("Juego no encontrado", "No se encontró eboot.bin en esa carpeta.")

    def auto_detect(self):
        self._set_status("Buscando eboot.bin…")
        self._log("Búsqueda automática iniciada")
        threading.Thread(target=lambda: self.events.put(("detected", find_game_dir(self.settings, deep=True))), daemon=True).start()

    def _startup_detect(self):
        found = find_game_dir(self.settings)
        if found:
            self.events.put(("detected", found))

    def extract_pkg(self, package_path=None):
        package = str(package_path) if package_path else filedialog.askopenfilename(
            parent=self.root, title="Seleccionar PKG",
            filetypes=[("Paquetes PS4", "*.pkg"), ("Todos", "*")])
        if not package:
            return
        if not Path(package).is_file():
            messagebox.showerror("PKG no encontrado", "No se puede abrir el archivo PKG seleccionado.", parent=self.root)
            return
        extractor = find_pkg_extractor()
        if extractor is None:
            messagebox.showerror(
                "Extractor PKG no disponible",
                "No se encontró ps4-pkg-tool. Verifica que el paquete incluya el extractor "
                "correspondiente a este sistema o configura TLG_PKG_EXTRACTOR.", parent=self.root)
            return
        destination = filedialog.askdirectory(parent=self.root, title="Extraer en",
                                              initialdir=str(Path(package).parent))
        if not destination:
            return
        command = [str(extractor), package, destination]
        self._set_status("Extrayendo PKG…")
        self._log(f"Extracción iniciada: {Path(package).name}")
        threading.Thread(target=self._extract_worker, args=(command, destination), daemon=True).start()

    def _extract_worker(self, command, destination):
        try:
            process = subprocess.Popen(command, cwd=str(PORT), stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True, bufsize=1)
            for line in process.stdout:
                self.events.put(("log", line.rstrip()))
            self.events.put(("extract_done", process.wait(), destination))
        except (OSError, subprocess.SubprocessError) as exc:
            self.events.put(("log", f"Error de extracción: {exc}"))
            self.events.put(("extract_done", -1, destination))

    def _launch_worker(self, command, env, cwd):
        try:
            process = subprocess.Popen(command, cwd=str(cwd), env=env, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True, bufsize=1)
            self.process = process
            for line in process.stdout:
                self.events.put(("log", line.rstrip()))
            self.events.put(("launch_done", process.wait()))
        except (OSError, subprocess.SubprocessError) as exc:
            self.events.put(("log", f"No se pudo iniciar el juego: {exc}"))
            self.events.put(("launch_done", -1))

    def _collect_settings(self):
        result = dict(self.settings)
        for key, variable in self.vars.items():
            result[key] = variable.get().strip()
        for key, variable in self.bools.items():
            result[key] = bool(variable.get())
        for key, variable in self.switch_vars.items():
            result[key] = "1" if variable.get() else "0"
        for key in ("engine_fps", "fps_limit", "vram", "dmem_mb", "fault_window", "audio_volume"):
            try:
                result[key] = str(int(result[key]))
            except (ValueError, TypeError):
                result[key] = DEFAULTS[key]
                self.vars[key].set(result[key])
        for key, minimum, maximum in (("copy_threads", 1, 16), ("staging_keep", 0, 8192)):
            value = str(result[key]).strip().lower()
            if value == "auto":
                result[key] = "auto"
            else:
                try:
                    result[key] = str(max(minimum, min(maximum, int(value))))
                except (ValueError, TypeError):
                    result[key] = "auto"
            self.vars[key].set(result[key])
        result["phys_cores"] = str(result["phys_cores"]).strip()
        if result["phys_cores"] not in {"0", "1"}:
            result["phys_cores"] = "0"
            self.switch_vars["phys_cores"].set(False)
        if result["upscaler"] not in {"0", "1", "2", "4"}:
            result["upscaler"] = "0"
        if result.get("upscale_preset", "1") not in {"0", "1", "2", "3", "4"}:
            result["upscale_preset"] = "1"
        result["fsr_sharpness"] = str(max(0, min(100, int(result.get("fsr_sharpness", "50")))))
        result["audio_volume"] = str(max(0, min(100, int(result["audio_volume"]))))
        gpu_id = str(result.get("gpu_device", "auto"))
        valid_gpu_ids = {index for index, _name, _kind in getattr(self, "gpu_devices", [])}
        if gpu_id != "auto" and gpu_id not in valid_gpu_ids:
            gpu_id = "auto"
            self.vars["gpu_device"].set("auto")
        result["gpu_device"] = gpu_id
        for key in ("object_motion", "async_shaders", "deferred_readback", "stale_readback", "hot_pages", "write_merge", "auto_gyro"):
            result[key] = "1" if str(result[key]).lower() in {"1", "true", "yes", "on"} else "0"
        if result["language"] not in LANGUAGE_BY_CODE:
            result["language"] = "es-LA"
            self.vars["language"].set("es-LA")
        if result["region"] not in REGION_LABELS:
            result["region"] = "auto"
            self.vars["region"].set("auto")
        return result

    def play(self):
        if self.busy:
            return
        game = self.vars["game_dir"].get().strip()
        if not game or not (Path(game) / "eboot.bin").is_file():
            self._show_page("home")
            messagebox.showerror("Juego no configurado", "Selecciona una carpeta válida que contenga eboot.bin.")
            return
        has_prebuilt = (PORT / "out" / "tlg-probe").is_file()
        run_script = RUN_LOGGED if RUN_LOGGED.is_file() and has_prebuilt else PORT / "run.sh"
        if not run_script.is_file():
            messagebox.showerror("Port incompleto", f"No se encontró el script de inicio:\n{run_script}")
            return
        settings = self._collect_settings()
        settings["game_dir"] = game
        self.settings.update(settings)
        try:
            save_settings(self.settings)
            data_dir = Path(os.environ.get("TLG_DATA_DIR", "")).expanduser() if os.environ.get("TLG_DATA_DIR") else (Path.home() / ".local" / "share" / "tlou-pc")
            data_dir.mkdir(parents=True, exist_ok=True)
            os.environ.setdefault("TLG_DATA_DIR", str(data_dir))
            ini = data_dir / "tlg.ini"
            lines = [f"display_mode={settings['display_mode']}", f"render_resolution={settings['render_resolution']}",
                     f"engine_fps={settings['engine_fps']}", f"fps_limit={settings['fps_limit']}",
                     f"async_shaders={settings['async_shaders']}", f"deferred_readback={settings['deferred_readback']}",
                     f"stale_readback={settings['stale_readback']}", f"show_fps={int(settings['show_fps'])}",
                      "overlay_items=1", f"object_motion={settings['object_motion']}"]
            ini.write_text("\n".join(lines) + "\n", encoding="utf-8")
            os.environ["TLG_CONFIG"] = str(ini)
        except OSError as exc:
            messagebox.showerror("No se pudo guardar la configuración", str(exc))
            return
        env = os.environ.copy()
        if "TLG_DATA_DIR" not in env:
            data_dir = Path.home() / ".local" / "share" / "tlou-pc"
            data_dir.mkdir(parents=True, exist_ok=True)
            env["TLG_DATA_DIR"] = str(data_dir)
        if has_prebuilt:
            env.setdefault("TLG_PREBUILT", "1")
            env.setdefault("TLG_PROBE", str(PORT / "out" / "tlg-probe"))
        language_id, region_code = resolve_language_profile(settings["language"], settings["region"])
        env.update({"TLG_GAME_DIR": game, "TLG_DMEM_MB": settings["dmem_mb"], "TLG_VBLANK_HZ": "60",
                    "TLG_FAULT_WINDOW": settings["fault_window"], "TLG_PHYS_CORES": settings["phys_cores"],
                    "TLG_LANGUAGE": str(language_id),
                    "TLG_OBJECT_MOTION": settings["object_motion"], "TLG_ASYNC_SHADERS": settings["async_shaders"],
                    "TLG_DEFERRED_READBACK": settings["deferred_readback"], "TLG_STALE_READBACK": settings["stale_readback"],
                    "TLG_HOT_PAGES": settings["hot_pages"], "TLG_WRITE_MERGE": settings["write_merge"],
                    "TLG_SHOW_FPS": "1" if settings["show_fps"] else "0",
                    "TLG_GC_BUDGET_MB": settings.get("vram", "5600"),
                    "TLG_AUDIO_VOLUME": settings["audio_volume"], "TLG_AUTO_GYRO": settings["auto_gyro"],
                    "TLG_UI_LANG": self.ui_language})
        if settings["audio_device"] in {"", "default", "Detectar automáticamente"}:
            env.pop("TLG_AUDIO_DEVICE", None)
        else:
            env["TLG_AUDIO_DEVICE"] = settings["audio_device"]
        if settings["gpu_device"] == "auto":
            env.pop("TLG_GPU_ID", None)
        else:
            env["TLG_GPU_ID"] = settings["gpu_device"]
        if settings["copy_threads"] == "auto":
            env.pop("TLG_COPY_THREADS", None)
        else:
            env["TLG_COPY_THREADS"] = settings["copy_threads"]
        if settings["staging_keep"] == "auto":
            env.pop("TLG_STAGING_KEEP_MB", None)
        else:
            env["TLG_STAGING_KEEP_MB"] = settings["staging_keep"]
        if settings["region"] == "auto":
            env.pop("TLG_REGION", None)
        else:
            env["TLG_REGION"] = region_code
        if GAME_ICON_BMP.is_file():
            env["TLG_WINDOW_ICON"] = str(GAME_ICON_BMP)
        if not has_prebuilt:
            # A source checkout without a prebuilt runtime uses run.sh's build path.
            env.pop("TLG_PREBUILT", None)
        else:
            env.setdefault("TLG_PREBUILT", "1")
        self.busy = True
        self.play_button.configure(state="disabled", text="INICIANDO…")
        self._set_status("Preparando el juego…", True)
        self._log(f"Inicio solicitado · {game}")
        if self.app_fullscreen or settings["display_mode"] == "Fullscreen":
            self.minimized_for_game = True
            self.restore_fullscreen_after_game = self.app_fullscreen
            if self.app_fullscreen:
                self._exit_fullscreen()
            try:
                self.root.iconify()
                self.root.after(250, self._ensure_minimized_for_game)
            except tk.TclError:
                self.minimized_for_game = False
        threading.Thread(target=self._launch_worker, args=(["bash", str(run_script)], env, REPO), daemon=True).start()

    def _poll_events(self):
        try:
            while True:
                item = self.events.get_nowait()
                if item[0] == "log":
                    self._log(item[1])
                elif item[0] == "hardware":
                    info = item[1]
                    self.hardware_info = info
                    self.hardware_header.configure(text=f"{info['gpu']}   ·   {info['ram']} RAM")
                    for attr, value in (("spec_cpu", info["cpu"]), ("spec_gpu", info["gpu"]), ("spec_ram", info["ram"])):
                        widget = getattr(self, attr, None)
                        if widget is not None and widget.winfo_exists():
                            widget.configure(text=self._short(value, 30))
                elif item[0] == "detected":
                    if item[1]:
                        self.vars["game_dir"].set(item[1])
                        self._log(f"Juego detectado · {item[1]}")
                    else:
                        self._set_status("No se encontró el juego")
                        messagebox.showinfo("Búsqueda finalizada", "No se encontró eboot.bin. Indica la carpeta con Examinar.")
                elif item[0] == "extract_done":
                    code, destination = item[1], item[2]
                    found = find_eboot(destination) if code == 0 else None
                    if found:
                        self.vars["game_dir"].set(str(found))
                        self._set_status("Extracción completada", True)
                        self._log(f"PKG listo · {found}")
                    else:
                        self._set_status("Falló la extracción del PKG")
                        messagebox.showerror("Extracción fallida", "Revisa el log y la configuración de PatchBuilder/.NET.")
                elif item[0] == "launch_done":
                    code = item[1]
                    self.busy = False
                    self.process = None
                    self._restore_window_after_game()
                    self.play_button.configure(state="normal", text="▶   INICIAR JUEGO", bg=THEME["green"])
                    self._set_status("Juego cerrado" if code == 0 else f"El proceso terminó con código {code}", code == 0)
                    self._log(f"Proceso finalizado · código {code}")
        except queue.Empty:
            pass
        self.root.after(70, self._poll_events)

    @staticmethod
    def _short(value, limit):
        return value if len(value) <= limit else value[:limit - 1] + "…"

    def _log(self, message):
        self.logs.append(str(message))
        self.logs = self.logs[-250:]
        if hasattr(self, "log_view") and self.log_view.winfo_exists():
            self._insert_log(str(message))

    def _insert_log(self, message):
        self.log_view.config(state="normal")
        self.log_view.insert("end", message + "\n")
        self.log_view.see("end")
        self.log_view.config(state="disabled")

    def open_logs(self):
        logs = REPO / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        subprocess.Popen(["xdg-open", str(logs)])

    def open_saves(self):
        save_window = tk.Toplevel(self.root)
        save_window.title(self._tr("Gestor de partidas"))
        save_window.configure(bg=THEME["bg"])
        save_window.transient(self.root)
        save_window.grab_set()
        save_window.geometry("760x450")
        save_window.resizable(True, True)
        body = tk.Frame(save_window, bg=THEME["bg"], padx=16, pady=16)
        body.pack(fill="both", expand=True)
        self._label(body, "GESTOR DE PARTIDAS", 10, THEME["text"], bold=True).pack(anchor="w")
        self._label(body, "Abre la carpeta o copia manualmente los saves del port.", 8, THEME["muted"]).pack(anchor="w", pady=(4, 12))
        saves = PORT / "user" / "savedata"
        saves.mkdir(parents=True, exist_ok=True)
        save_list = tk.Listbox(body, bg=THEME["panel2"], fg=THEME["text"], relief="flat", bd=0,
                               highlightthickness=1, highlightbackground=THEME["border"], selectbackground=THEME["green_low"])
        save_list.pack(fill="both", expand=True)
        save_files = []

        def refresh_saves():
            save_files.clear()
            save_list.delete(0, "end")
            save_files.extend(path for path in saves.rglob("*")
                              if path.is_dir() and path.name.startswith("SAVEDATA")
                              and not path.name.endswith(".sce_sys") and path.parent.name.startswith("CUSA"))
            if not save_files:
                save_files.extend(path for path in saves.rglob("*") if path.is_file())
            save_files.sort(key=lambda path: str(path.relative_to(saves)).casefold())
            for path in save_files:
                save_list.insert("end", str(path.relative_to(saves)))
            if not save_files:
                save_list.insert("end", self._tr("No hay partidas guardadas todavía."))

        def export_selected():
            selected = save_list.curselection()
            if not selected or selected[0] >= len(save_files):
                messagebox.showinfo(self._tr("Gestor de partidas"), self._tr("Selecciona una partida para exportarla."), parent=save_window)
                return
            source = save_files[selected[0]]
            destination = filedialog.askdirectory(parent=save_window, title=self._tr("Seleccionar carpeta de destino"))
            if not destination:
                return
            target = Path(destination) / source.name
            suffix = 1
            while target.exists():
                target = Path(destination) / f"{source.stem} (copia {suffix}){source.suffix}"
                suffix += 1
            try:
                if source.is_dir():
                    shutil.copytree(source, target)
                    metadata = source.with_name(source.name + ".sce_sys")
                    if metadata.is_dir():
                        shutil.copytree(metadata, target.with_name(target.name + ".sce_sys"))
                else:
                    shutil.copy2(source, target)
                messagebox.showinfo(self._tr("Copia exportada"), str(target), parent=save_window)
            except OSError as exc:
                messagebox.showerror(self._tr("No se pudo exportar la copia"), str(exc), parent=save_window)

        def delete_selected():
            selected = save_list.curselection()
            if not selected or selected[0] >= len(save_files):
                messagebox.showinfo(self._tr("Gestor de partidas"), self._tr("Selecciona una partida para borrarla."), parent=save_window)
                return
            source = save_files[selected[0]]
            try:
                relative = source.resolve().relative_to(saves.resolve())
            except (OSError, ValueError):
                messagebox.showerror(self._tr("Error al borrar"), self._tr("La ruta seleccionada no pertenece a la carpeta de partidas."), parent=save_window)
                return
            question = f"{self._tr('¿Borrar la partida seleccionada? Esta acción no se puede deshacer.')}\n\n{relative}"
            if not messagebox.askyesno(self._tr("Borrar partida"), question, icon="warning", parent=save_window):
                return
            try:
                is_save_group = source.is_dir() and source.name.startswith("SAVEDATA")
                if source.is_symlink():
                    source.unlink()
                elif source.is_dir():
                    shutil.rmtree(source)
                elif source.exists():
                    source.unlink()
                if is_save_group:
                    metadata = source.with_name(source.name + ".sce_sys")
                    try:
                        metadata.resolve().relative_to(saves.resolve())
                    except (OSError, ValueError):
                        metadata = None
                    if metadata and metadata.is_symlink():
                        metadata.unlink()
                    elif metadata and metadata.is_dir():
                        shutil.rmtree(metadata)
                refresh_saves()
                self._log(f"Partida borrada · {relative}")
            except OSError as exc:
                messagebox.showerror(self._tr("Error al borrar"), str(exc), parent=save_window)

        refresh_saves()
        button_row = tk.Frame(body, bg=THEME["bg"])
        button_row.pack(fill="x", pady=(12, 0))
        self._button(button_row, "ABRIR CARPETA", lambda: subprocess.Popen(["xdg-open", str(saves)]), "quiet", 15).pack(side="left", padx=(0, 6))
        self._button(button_row, "EXPORTAR SELECCIÓN", export_selected, "quiet", 20).pack(side="left", padx=(0, 6))
        self._button(button_row, "BORRAR PARTIDA", delete_selected, "danger", 16).pack(side="left", padx=(0, 6))
        self._button(button_row, "ACTUALIZAR", refresh_saves, "quiet", 12).pack(side="left", padx=(0, 6))
        self._button(button_row, "CERRAR", save_window.destroy, "quiet", 12).pack(side="right")

    def clear_cache(self):
        cache = PORT / "user" / "cache"
        files = [p for p in cache.rglob("*") if p.is_file()] if cache.exists() else []
        size = sum(p.stat().st_size for p in files)
        if not files:
            messagebox.showinfo("Caché de shaders", "La caché está vacía.")
            return
        if not messagebox.askyesno("Limpiar caché", f"Eliminar {len(files)} archivos ({size / 1048576:.1f} MB)?"):
            return
        shutil.rmtree(cache)
        cache.mkdir(parents=True, exist_ok=True)
        self._log(f"Caché limpiada · {size / 1048576:.1f} MB")

    def _close(self):
        if self.busy and not messagebox.askyesno("Juego en ejecución", "¿Cerrar el launcher? El juego seguirá ejecutándose."):
            return
        self.root.destroy()


def main():
    register_headline_font()
    if DragDropTk is not None:
        try:
            root = DragDropTk()
        except (tk.TclError, RuntimeError, OSError):
            root = tk.Tk()
    else:
        root = tk.Tk()
    Launcher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
