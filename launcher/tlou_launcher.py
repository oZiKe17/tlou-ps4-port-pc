#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""The Last of Us Remastered — PC launcher (Tkinter, Linux).

Portable: auto-detects game folder, PatchBuilderLinux, screen resolution, GPUs.
Settings live in ~/.config/tlou-launcher/settings.json.
Advanced section exposes all TLG_* environment variables.
"""
import json
import locale
import os
import queue
import shutil
import subprocess
import sys
import threading
from pathlib import Path

PORT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PORT))
try:
    import run as tlg_run
    HAS_RUN = True
except Exception:
    HAS_RUN = False

SETTINGS_PATH = Path.home() / ".config" / "tlou-launcher" / "settings.json"

TEXT = {
    'title': ('The Last of Us Remastered — PC', 'The Last of Us Remastered — PC'),
    'game': ('Game', 'Juego'),
    'game_dir': ('Game folder (auto-detected by eboot.bin)', 'Carpeta del juego (auto-detectada por eboot.bin)'),
    'system_lib_dir': ('Console system modules (optional)', 'Módulos del sistema del console (opcional)'),
    'browse': ('Browse…', 'Buscar…'),
    'auto_detect': ('Auto-detect', 'Auto-detectar'),
    'extract_pkg': ('Extract from PKG…', 'Extraer desde PKG…'),
    'advanced': ('Advanced', 'Avanzado'),
    'video': ('Video', 'Video'),
    'display_mode': ('Display mode', 'Modo de pantalla'),
    'Windowed': ('Windowed', 'Ventana'),
    'Borderless': ('Borderless window', 'Ventana sin bordes'),
    'Fullscreen': ('Fullscreen', 'Pantalla completa'),
    'show_fps': ('Show FPS overlay (F10 toggles)', 'Mostrar overlay de FPS (F10 alterna)'),
    'vram': ('Texture cache budget (MB of VRAM)', 'Orçamento do cache de texturas (MB de VRAM)'),
    'vram_hint': ('6 GB: 5600 · 8 GB: 7000 · 12 GB: 10500 · 16 GB: 14000', '6 GB: 5600 · 8 GB: 7000 · 12 GB: 10500 · 16 GB: 14000'),
    'render_resolution': ('Render resolution', 'Resolución de render'),
    'engine_fps': ('Engine FPS', 'FPS del motor'),
    'fps_limit': ('FPS limit (0 = unlimited)', 'Límite de FPS (0 = sin límite)'),
    'audio': ('Audio', 'Audio'),
    'native_audio': ('Native audio (libSceNgs2.sprx)', 'Áudio nativo (libSceNgs2.sprx)'),
    'play': ('Play', 'Jugar'),
    'saves': ('Saves folder', 'Carpeta de saves'),
    'logs': ('Logs folder', 'Carpeta de logs'),
    'clear_cache': ('Clear shader cache', 'Limpar cache de shaders'),
    'ready': ('Ready to play.', 'Pronto para jogar.'),
    'not_built': ('Port not built (run build.sh)', 'Port não compilado (rode o build.sh)'),
    'preparing': ('Preparing the game…', 'Preparando o jogo…'),
    'running': ('Playing — log:', 'Jogando — log:'),
    'ended': ('Game closed (exit code {code}).', 'Jogo fechado (código {code}).'),
    'crashed': ('The game closed with an error (code {code}).', 'O jogo fechou com erro (código {code}).'),
    'already': ('The game is already running.', 'O jogo já está rodando.'),
    'error': ('Error', 'Erro'),
    'no_eboot': ('No eboot.bin found.', 'Nenhum eboot.bin encontrado.'),
    'pkg_extracted': ('PKG extracted to: {path}', 'PKG extraído para: {path}'),
    'pkg_failed': ('PKG extraction failed: {error}', 'Falha na extração do PKG: {error}'),
    'advanced_title': ('Advanced settings (env vars)', 'Configuración avanzada (env vars)'),
    'dmem_mb': ('Direct memory (MB, retail=4608)', 'Memoria directa (MB, retail=4608)'),
    'fault_window': ('Fault window (KiB, default 256)', 'Ventana de fault (KiB, default 256)'),
    'copy_threads': ('Copy threads', 'Hilos de copia'),
    'staging_keep': ('Staging keep (MB)', 'Staging keep (MB)'),
    'phys_cores': ('Physical cores', 'Cores físicos'),
    'upscaler': ('Upscaler (0=off,1=fsr3,2=fsr4,4=taa)', 'Upscaler (0=off,1=fsr3,2=fsr4,4=taa)'),
    'object_motion': ('Object motion (reduces ghosting)', 'Motion de objetos (reduce ghosting)'),
    'async_shaders': ('Async shaders', 'Shaders asíncronos'),
    'deferred_readback': ('Deferred readback', 'Readback diferido'),
    'stale_readback': ('Stale readback', 'Readback stale'),
    'hot_pages': ('Hot pages (0=off,1=on)', 'Hot pages (0=off,1=on)'),
    'write_merge': ('Write merge', 'Write merge'),
    'port_by': ('PC port by HayatoG', 'Port para PC por HayatoG'),
}


def load_settings():
    try:
        return json.loads(SETTINGS_PATH.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def save_settings(settings):
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(settings, indent=2), encoding='utf-8')


def find_eboot(root):
    root = Path(root)
    if (root / 'eboot.bin').is_file():
        return root
    for p in root.rglob('eboot.bin'):
        return p.parent
    return None


def find_game_dir():
    """Auto-detect game folder by searching common locations."""
    # Check saved setting first
    settings = load_settings()
    saved = settings.get('game_dir', '')
    if saved and Path(saved).joinpath('eboot.bin').is_file():
        return saved
    # Common locations
    candidates = [
    ]
    for c in candidates:
        if (c / 'eboot.bin').is_file():
            return str(c)
    # Search under /media, /home, /mnt, /run/media
    for base in [Path('/media'), Path('/mnt'), Path('/run/media'), Path.home()]:
        if not base.exists():
            continue
        try:
            for p in base.rglob('eboot.bin'):
                return str(p.parent)
        except (PermissionError, OSError):
            continue
    return ''


def get_hardware_info():
    """Detect CPU, GPU, RAM for display in launcher."""
    info = {}
    try:
        with open('/proc/cpuinfo') as f:
            for line in f:
                if line.startswith('model name'):
                    info['cpu'] = line.split(':', 1)[1].strip()
                    break
    except Exception:
        info['cpu'] = 'Unknown'
    try:
        import subprocess
        out = subprocess.check_output(['free', '-h'], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            if line.startswith('Mem:'):
                info['ram'] = line.split()[1]
                break
    except Exception:
        info['ram'] = '?'
    try:
        import subprocess
        out = subprocess.check_output(['vulkaninfo', '--summary'], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            if 'deviceName' in line:
                info['gpu'] = line.split('=')[-1].strip()
                break
    except Exception:
        info['gpu'] = 'Unknown (vulkaninfo not found)'
    return info


def find_patchbuilder():
    """Auto-detect PatchBuilderLinux or PKG tools."""
    candidates = [
        Path(os.environ.get('PATCHBUILDER_DIR', '')),
        Path.home() / 'PatchBuilderLinux',
        Path('/opt/PatchBuilderLinux'),
    ]
    for c in candidates:
        if c and (c / 'engine' / 'PkgTool.Core.dll').is_file():
            return c
    # Search
    for base in [Path('/media'), Path.home(), Path('/opt')]:
        if not base.exists():
            continue
        try:
            for p in base.rglob('PkgTool.Core.dll'):
                return p.parent.parent
        except (PermissionError, OSError):
            continue
    return None


def get_screen_resolution():
    """Auto-detect screen resolution."""
    try:
        import subprocess
        out = subprocess.check_output(['xrandr'], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            if '*' in line:
                parts = line.split()
                for p in parts:
                    if 'x' in p and p[0].isdigit():
                        return p
    except Exception:
        pass
    return '1920x1080'


class Launcher:
    def __init__(self, root):
        self.root = root
        self.settings = load_settings()
        self.process = None
        self.lines = queue.Queue()
        # Auto-detect game dir
        if not self.settings.get('game_dir') or not Path(self.settings['game_dir']).joinpath('eboot.bin').is_file():
            detected = find_game_dir()
            if detected:
                self.settings['game_dir'] = detected
        # Auto-detect PatchBuilder
        self.patchbuilder = find_patchbuilder()
        self.build()
        self.root.after(100, self.pump)

    def t(self, key, **fmt):
        en, pt = TEXT.get(key, (key, key))
        lang = self.settings.get('ui_language', 'auto')
        use_pt = lang == 'pt_BR' or (lang == 'auto' and os.environ.get('LANG', '').startswith('pt'))
        text = pt if use_pt else en
        try:
            return text.format(**fmt)
        except (KeyError, ValueError):
            return text

    def build(self):
        for child in self.root.winfo_children():
            child.destroy()
        root = self.root
        root.title(self.t('title'))
        root.minsize(900, 700)
        pad = {'padx': 6, 'pady': 4}
        main = ttk.Frame(root, padding=12)
        main.pack(fill='both', expand=True)
        main.columnconfigure(0, weight=1)
        main.rowconfigure(4, weight=1)

        # Header
        header = ttk.Frame(main)
        header.pack(fill='x', pady=(0, 8))
        ttk.Label(header, text='The Last of Us Remastered', font=('TkDefaultFont', 20, 'bold')).pack(side='left')
        ttk.Label(header, text='PC Port — CUSA00552', foreground='#777').pack(side='left', padx=(10, 0))

        # Status
        self.status_label = ttk.Label(header, text='', foreground='#555')
        hw = get_hardware_info()
        hw_label = ttk.Label(header, text=f"CPU: {hw.get('cpu','?')} | GPU: {hw.get('gpu','?')} | RAM: {hw.get('ram','?')}", foreground='#888', font=('TkDefaultFont', 8))
        hw_label.pack(side='right', anchor='ne', padx=(10, 0))
        self.status_label.pack(side='right', anchor='ne')

        # Game section
        game_frame = ttk.LabelFrame(main, text=self.t('game'), padding=8)
        game_frame.pack(fill='x', pady=(0, 8))
        game_frame.columnconfigure(0, weight=1)

        ttk.Label(game_frame, text=self.t('game_dir')).grid(row=0, column=0, columnspan=3, sticky='w')
        self.game_dir_var = tk.StringVar(value=self.settings.get('game_dir', ''))
        ttk.Entry(game_frame, textvariable=self.game_dir_var).grid(row=1, column=0, sticky='ew', pady=(0, 4))
        ttk.Button(game_frame, text=self.t('browse'), command=self.browse_game).grid(row=1, column=1, padx=(4, 0), pady=(0, 4))
        ttk.Button(game_frame, text=self.t('auto_detect'), command=self.auto_detect).grid(row=1, column=2, padx=(4, 0), pady=(0, 4))
        ttk.Button(game_frame, text=self.t('extract_pkg'), command=self.extract_pkg).grid(row=2, column=0, sticky='w', pady=(4, 0))

        # Video section
        video_frame = ttk.LabelFrame(main, text=self.t('video'), padding=8)
        video_frame.pack(fill='x', pady=(0, 8))

        ttk.Label(video_frame, text=self.t('display_mode')).grid(row=0, column=0, sticky='w')
        self.display_var = tk.StringVar(value=self.settings.get('display_mode', 'Windowed'))
        ttk.Combobox(video_frame, textvariable=self.display_var, values=['Windowed', 'Borderless', 'Fullscreen'], state='readonly', width=20).grid(row=0, column=1, sticky='w', padx=(8, 0))

        ttk.Label(video_frame, text=self.t('render_resolution')).grid(row=1, column=0, sticky='w', pady=(4, 0))
        self.render_res_var = tk.StringVar(value=self.settings.get('render_resolution', 'native'))
        ttk.Combobox(video_frame, textvariable=self.render_res_var, values=['native', '480p', '720p', '1080p', '1440p', '4K'], state='readonly', width=20).grid(row=1, column=1, sticky='w', padx=(8, 0), pady=(4, 0))

        ttk.Label(video_frame, text=self.t('engine_fps')).grid(row=2, column=0, sticky='w', pady=(4, 0))
        self.engine_fps_var = tk.StringVar(value=str(self.settings.get('engine_fps', 60)))
        ttk.Combobox(video_frame, textvariable=self.engine_fps_var, values=['30', '60', '120'], state='readonly', width=20).grid(row=2, column=1, sticky='w', padx=(8, 0), pady=(4, 0))

        ttk.Label(video_frame, text=self.t('fps_limit')).grid(row=3, column=0, sticky='w', pady=(4, 0))
        self.fps_limit_var = tk.StringVar(value=str(self.settings.get('fps_limit', 60)))
        ttk.Entry(video_frame, textvariable=self.fps_limit_var, width=8).grid(row=3, column=1, sticky='w', padx=(8, 0), pady=(4, 0))

        self.show_fps_var = tk.BooleanVar(value=self.settings.get('show_fps', True))
        ttk.Checkbutton(video_frame, text=self.t('show_fps'), variable=self.show_fps_var).grid(row=4, column=0, columnspan=2, sticky='w', pady=(4, 0))

        ttk.Label(video_frame, text=self.t('vram')).grid(row=5, column=0, sticky='w', pady=(4, 0))
        self.vram_var = tk.StringVar(value=str(self.settings.get('vram', 5600)))
        ttk.Entry(video_frame, textvariable=self.vram_var, width=8).grid(row=5, column=1, sticky='w', padx=(8, 0), pady=(4, 0))
        ttk.Label(video_frame, text=self.t('vram_hint'), foreground='#777', font=('TkDefaultFont', 8)).grid(row=6, column=0, columnspan=2, sticky='w')

        ttk.Label(video_frame, text=self.t('upscaler')).grid(row=7, column=0, sticky='w', pady=(4, 0))
        self.upscaler_var = tk.StringVar(value=str(self.settings.get('upscaler', 0)))
        ttk.Combobox(video_frame, textvariable=self.upscaler_var, values=['0 (off)', '1 (FSR3)', '2 (FSR4)', '4 (TAA)'], state='readonly', width=20).grid(row=7, column=1, sticky='w', padx=(8, 0), pady=(4, 0))

        # Audio section
        audio_frame = ttk.LabelFrame(main, text=self.t('audio'), padding=8)
        audio_frame.pack(fill='x', pady=(0, 8))
        self.native_audio_var = tk.BooleanVar(value=self.settings.get('native_audio', True))
        ttk.Checkbutton(audio_frame, text=self.t('native_audio'), variable=self.native_audio_var).grid(row=0, column=0, sticky='w')

        # Advanced section
        adv_frame = ttk.LabelFrame(main, text=self.t('advanced_title'), padding=8)
        adv_frame.pack(fill='x', pady=(0, 8))
        adv_frame.columnconfigure(1, weight=1)

        adv_items = [
            ('dmem_mb', 'TLG_DMEM_MB', '4608'),
            ('fault_window', 'TLG_FAULT_WINDOW', '256'),
            ('copy_threads', 'TLG_COPY_THREADS', '6'),
            ('staging_keep', 'TLG_STAGING_KEEP_MB', '512'),
            ('phys_cores', 'TLG_PHYS_CORES', '6'),
            ('object_motion', 'TLG_OBJECT_MOTION', '1'),
            ('async_shaders', 'TLG_ASYNC_SHADERS', '1'),
            ('deferred_readback', 'TLG_DEFERRED_READBACK', '1'),
            ('stale_readback', 'TLG_STALE_READBACK', '1'),
            ('hot_pages', 'TLG_HOT_PAGES', '0'),
            ('write_merge', 'TLG_WRITE_MERGE', '1'),
        ]
        self.adv_vars = {}
        for i, (key, env_key, default) in enumerate(adv_items):
            ttk.Label(adv_frame, text=self.t(key)).grid(row=i, column=0, sticky='w', pady=(2, 0))
            var = tk.StringVar(value=str(self.settings.get(key, default)))
            self.adv_vars[key] = (var, env_key)
            ttk.Entry(adv_frame, textvariable=var, width=8).grid(row=i, column=1, sticky='w', padx=(8, 0), pady=(2, 0))

        # Log area
        log_frame = ttk.LabelFrame(main, text='Log', padding=8)
        log_frame.pack(fill='both', expand=True, pady=(0, 8))
        self.log_text = tk.Text(log_frame, height=10, wrap='word', state='disabled')
        self.log_text.pack(fill='both', expand=True)

        # Buttons
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill='x')
        ttk.Button(btn_frame, text=self.t('play'), command=self.play).pack(side='left', padx=(0, 8))
        ttk.Button(btn_frame, text=self.t('saves'), command=self.open_saves).pack(side='left', padx=(0, 8))
        ttk.Button(btn_frame, text=self.t('logs'), command=self.open_logs).pack(side='left', padx=(0, 8))
        ttk.Button(btn_frame, text=self.t('clear_cache'), command=self.clear_cache).pack(side='left', padx=(0, 8))

        self.update_status()

    def log(self, msg):
        self.log_text.config(state='normal')
        self.log_text.insert('end', msg + '\n')
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    def update_status(self):
        game_dir = self.game_dir_var.get()
        if game_dir and Path(game_dir).joinpath('eboot.bin').is_file():
            self.status_label.config(text=f"OK: {game_dir}", foreground='green')
        else:
            self.status_label.config(text=f"ERROR: {self.t('no_eboot')}", foreground='red')

    def browse_game(self):
        path = filedialog.askdirectory(title=self.t('game_dir'))
        if path:
            found = find_eboot(path)
            if found:
                self.game_dir_var.set(str(found))
                self.settings['game_dir'] = str(found)
                save_settings(self.settings)
                self.log(f"Found: {found}")
            else:
                messagebox.showerror(self.t('error'), self.t('no_eboot'))
            self.update_status()

    def auto_detect(self):
        detected = find_game_dir()
        if detected:
            self.game_dir_var.set(detected)
            self.settings['game_dir'] = detected
            save_settings(self.settings)
            self.log(f"Auto-detected: {detected}")
        else:
            messagebox.showinfo(self.t('error'), "No game folder found. Use Browse.")
        self.update_status()

    def extract_pkg(self):
        pkg = filedialog.askopenfilename(title='Select PKG', filetypes=[('PKG files', '*.pkg'), ('All', '*')])
        if not pkg:
            return
        out_dir = filedialog.askdirectory(title='Extract to folder')
        if not out_dir:
            return
        self.log(f"Extracting {pkg}...")
        # Find PatchBuilder
        pb = find_patchbuilder()
        if pb:
            pkgtool = pb / 'engine' / 'PkgTool.Core.dll'
            cmd = ['dotnet', str(pkgtool), 'pkg_extract', '--verbose', '--passcode', '00000000000000000000000000000000', pkg, out_dir]
        else:
            # Try ps4pkg
            messagebox.showerror(self.t('error'), "PatchBuilderLinux not found. Install it or set PATCHBUILDER_DIR.")
            return
        self.run_subprocess(cmd, self._on_extract_done, out_dir)

    def _on_extract_done(self, rc, out_dir):
        if rc == 0:
            found = find_eboot(out_dir)
            if found:
                self.game_dir_var.set(str(found))
                self.settings['game_dir'] = str(found)
                save_settings(self.settings)
                self.log(self.t('pkg_extracted', path=str(found)))
            else:
                self.log(self.t('pkg_failed', error="No eboot.bin found after extraction"))
        else:
            self.log(self.t('pkg_failed', error=f"exit code {rc}"))
        self.update_status()

    def run_subprocess(self, cmd, callback, *args):
        def worker():
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                self.lines.put(line.rstrip())
            proc.wait()
            self.lines.put(('__done__', proc.returncode, args))
        threading.Thread(target=worker, daemon=True).start()

    def pump(self):
        try:
            while True:
                item = self.lines.get_nowait()
                if isinstance(item, tuple) and item[0] == '__done__':
                    self._on_extract_done(item[1], *item[2])
                else:
                    self.log(item)
        except queue.Empty:
            pass
        self.root.after(100, self.pump)

    def play(self):
        game_dir = self.game_dir_var.get()
        if not game_dir or not Path(game_dir).joinpath('eboot.bin').is_file():
            messagebox.showerror(self.t('error'), self.t('no_eboot'))
            return
        # Save settings
        self.settings['game_dir'] = game_dir
        self.settings['display_mode'] = self.display_var.get()
        self.settings['show_fps'] = self.show_fps_var.get()
        try:
            self.settings['vram'] = int(self.vram_var.get())
        except ValueError:
            self.settings['vram'] = 5600
        self.settings['native_audio'] = self.native_audio_var.get()
        self.settings['render_resolution'] = self.render_res_var.get()
        try:
            self.settings['engine_fps'] = int(self.engine_fps_var.get())
        except ValueError:
            self.settings['engine_fps'] = 60
        try:
            self.settings['fps_limit'] = int(self.fps_limit_var.get())
        except ValueError:
            self.settings['fps_limit'] = 60
        self.settings['upscaler'] = int(self.upscaler_var.get().split()[0])
        for key, (var, env_key) in self.adv_vars.items():
            self.settings[key] = var.get()
        save_settings(self.settings)

        # Set env vars
        env = os.environ.copy()
        env['TLG_GAME_DIR'] = game_dir
        env['TLG_DMEM_MB'] = self.adv_vars['dmem_mb'][0].get() or '4608'
        env['TLG_VBLANK_HZ'] = '60'
        if self.show_fps_var.get():
            env['TLG_SHOW_FPS'] = '1'
        env['TLG_FAULT_WINDOW'] = self.adv_vars['fault_window'][0].get() or '256'
        env['TLG_COPY_THREADS'] = self.adv_vars['copy_threads'][0].get() or '6'
        env['TLG_STAGING_KEEP_MB'] = self.adv_vars['staging_keep'][0].get() or '512'
        env['TLG_PHYS_CORES'] = self.adv_vars['phys_cores'][0].get() or '6'
        env['TLG_OBJECT_MOTION'] = self.adv_vars['object_motion'][0].get() or '1'
        env['TLG_ASYNC_SHADERS'] = self.adv_vars['async_shaders'][0].get() or '1'
        env['TLG_DEFERRED_READBACK'] = self.adv_vars['deferred_readback'][0].get() or '1'
        env['TLG_STALE_READBACK'] = self.adv_vars['stale_readback'][0].get() or '1'
        env['TLG_HOT_PAGES'] = self.adv_vars['hot_pages'][0].get() or '0'
        env['TLG_WRITE_MERGE'] = self.adv_vars['write_merge'][0].get() or '1'
        env['TLG_UPSCALER'] = str(self.settings.get('upscaler', 0))

        # Update tlg.ini
        ini_path = PORT / 'tlg.ini'
        ini_lines = [
            f"render_resolution={self.render_res_var.get()}",
            f"engine_fps={self.engine_fps_var.get()}",
            f"fps_limit={self.fps_limit_var.get()}",
            f"async_shaders={self.adv_vars['async_shaders'][0].get()}",
            f"deferred_readback={self.adv_vars['deferred_readback'][0].get()}",
            f"stale_readback={self.adv_vars['stale_readback'][0].get()}",
            f"show_fps={'1' if self.show_fps_var.get() else '0'}",
            f"overlay_items=1",
            f"object_motion={self.adv_vars['object_motion'][0].get()}",
            f"upscaler={self.settings.get('upscaler', 0)}",
        ]
        ini_path.write_text('\n'.join(ini_lines) + '\n', encoding='utf-8')

        self.log(self.t('preparing'))
        self.process = subprocess.Popen(
            ['bash', str(PORT / 'run.sh')],
            cwd=str(PORT),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self._read_process()

    def _read_process(self):
        if self.process and self.process.poll() is None:
            line = self.process.stdout.readline()
            if line:
                self.log(line.rstrip())
            self.root.after(50, self._read_process)
        else:
            if self.process:
                code = self.process.returncode
                if code == 0:
                    self.log(self.t('ended', code=code))
                else:
                    self.log(self.t('crashed', code=code))
            self.process = None

    def open_saves(self):
        saves = PORT / 'user' / 'savedata'
        if saves.exists():
            subprocess.Popen(['xdg-open', str(saves)])

    def open_logs(self):
        logs = PORT.parent / 'logs'
        if logs.exists():
            subprocess.Popen(['xdg-open', str(logs)])

    def clear_cache(self):
        cache = PORT / 'user' / 'cache'
        if cache.exists():
            import shutil
            size = sum(f.stat().st_size for f in cache.rglob('*') if f.is_file())
            count = len(list(cache.rglob('*')))
            if count == 0:
                messagebox.showinfo('Cache', self.t('clear_cache_empty'))
                return
            if messagebox.askyesno('Cache', self.t('clear_cache_ask', size=f'{size/1024/1024:.1f} MB')):
                shutil.rmtree(cache, ignore_errors=True)
                cache.mkdir(parents=True, exist_ok=True)
                messagebox.showinfo('Cache', self.t('clear_cache_done', size=f'{size/1024/1024:.1f} MB'))


if __name__ == '__main__':
    root = tk.Tk()
    Launcher(root)
    root.mainloop()
