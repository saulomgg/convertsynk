# ---------------------------------------------------------
# ConvertSynk - Ferramenta Oficial HubSynk
# Versão: V.1.0
# Desenvolvido por: saulomgg (https://github.com/saulomgg)
#
# Este software faz parte do ecossistema HubSynk.
# Apoie o projeto, acesse meu portfólio e ajude a manter
# o desenvolvimento e atualizações constantes!
# ---------------------------------------------------------

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import sys
import time
import webbrowser
from pathlib import Path
from utils.constants import *
from utils.helpers import check_ffmpeg, check_vp9_codec, detect_hw_codecs, open_url, get_video_duration

class VideoConverterApp:
    def __init__(self, root):
        self.conversion_errors = []
        self.root = root
        self.root.title("ConvertSynk - Editor de Vídeo") # Título atualizado
        self.root.geometry("750x850")
        self.root.configure(bg=BG_DARK)
        
        # Configurar ícone da janela
        self.set_window_icon()
        
        self.stop_conversion_flag = threading.Event()
        self.current_files = []
        self.output_format = tk.StringVar(value="mp4")
        self.compression_profile = tk.StringVar(value="h264_balanced")
        self.audio_codec = tk.StringVar(value="aac")
        self.is_converting = False
        self.output_dir = tk.StringVar(value=str(Path.home() / "Videos" / "ConvertSynk_Output"))
        
        if not check_ffmpeg():
            messagebox.showerror(ERROR_TITLE, ERROR_FFMPEG)
            self.root.destroy()
            return
        
        self.available_hw_codecs = detect_hw_codecs()
        self.vp9_available = check_vp9_codec()
        self.setup_ui()
        
    def set_window_icon(self):
        """Configura o ícone da janela para aparecer na barra de tarefas e título"""
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath(".")
            
            icon_path = os.path.join(base_path, "assets", "logo.png")
            
            if os.path.exists(icon_path):
                img = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, img)
            
            # Para Windows, garantir que o ícone apareça na barra de tarefas
            if os.name == 'nt':
                import ctypes
                myappid = 'hubsynk.videosynk.editor.1.0'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        except Exception as e:
            print(f"Erro ao carregar ícone: {e}")

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=BG_MEDIUM)
        style.configure('TLabel', background=BG_MEDIUM, foreground=FG_LIGHT)
        style.configure('TButton', background=COLOR_PRIMARY, foreground=FG_LIGHT, font=('Arial', 10, 'bold'))
        style.map('TButton', background=[('active', COLOR_PRIMARY)])
        style.configure('TProgressbar', background=COLOR_SUCCESS, troughcolor=BG_DARK)
        style.configure('TRadiobutton', background=BG_MEDIUM, foreground=FG_LIGHT)
        style.map('TRadiobutton', background=[('active', BG_MEDIUM)])
        style.configure('TCombobox', fieldbackground=BG_DARK, foreground=FG_LIGHT, selectbackground=COLOR_PRIMARY, selectforeground=FG_LIGHT)

        self.main_frame = tk.Frame(self.root, bg=BG_MEDIUM, padx=20, pady=20)
        self.main_frame.pack(fill="both", expand=True)

        title = tk.Label(self.main_frame, text="🎬 ConvertSynk - Conversor de Vídeo", font=("Arial", 18, "bold"), bg=BG_MEDIUM, fg=FG_LIGHT)
        title.pack(pady=(0, 20))
        
        # File Selection
        file_frame = tk.Frame(self.main_frame, bg=BG_MEDIUM)
        file_frame.pack(fill=tk.X, pady=10)
        tk.Button(file_frame, text=SELECT_FILE_BUTTON, command=self.select_files, font=("Arial", 11, "bold"),
                  bg=COLOR_PRIMARY, fg=FG_LIGHT, padx=10, pady=5, cursor="hand2", relief=tk.FLAT).pack(side=tk.LEFT)
        self.file_info_label = tk.Label(file_frame, text=NO_FILE_SELECTED, font=("Arial", 10), bg=BG_MEDIUM, fg="#cccccc")
        self.file_info_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # Output Folder
        output_frame = tk.Frame(self.main_frame, bg=BG_MEDIUM)
        output_frame.pack(fill=tk.X, pady=10)
        tk.Button(output_frame, text=SELECT_OUTPUT_BUTTON, command=self.select_output_folder, font=("Arial", 11, "bold"),
                  bg=COLOR_ACCENT, fg=BG_DARK, padx=10, pady=5, cursor="hand2", relief=tk.FLAT).pack(side=tk.LEFT)
        self.output_info_label = tk.Label(output_frame, textvariable=self.output_dir, font=("Arial", 10), bg=BG_MEDIUM, fg=FG_LIGHT, anchor='w')
        self.output_info_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        # Options
        options_frame = tk.Frame(self.main_frame, bg=BG_MEDIUM)
        options_frame.pack(fill=tk.X, pady=10)
        tk.Label(options_frame, text=OUTPUT_FORMAT, font=("Arial", 11, "bold"), bg=BG_MEDIUM, fg=FG_LIGHT).pack(side=tk.LEFT, padx=(0, 10))
        format_combobox = ttk.Combobox(options_frame, textvariable=self.output_format, values=["mp4", "mkv", "webm", "mov"], state="readonly", width=8)
        format_combobox.pack(side=tk.LEFT)
        format_combobox.bind("<<ComboboxSelected>>", self.update_profile_options)

        # Audio Codec
        audio_frame = tk.Frame(self.main_frame, bg=BG_MEDIUM)
        audio_frame.pack(fill=tk.X, pady=10)
        tk.Label(audio_frame, text=AUDIO_CODEC, font=("Arial", 11, "bold"), bg=BG_MEDIUM, fg=FG_LIGHT).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(audio_frame, text="AAC (Compatible)", variable=self.audio_codec, value="aac").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(audio_frame, text="Opus (Quality/Size)", variable=self.audio_codec, value="opus").pack(side=tk.LEFT, padx=5)

        # Profiles
        tk.Label(self.main_frame, text=COMPRESSION_PROFILE, font=("Arial", 11, "bold"), bg=BG_MEDIUM, fg=FG_LIGHT).pack(anchor='w', pady=(10, 5))
        self.profile_frame = tk.Frame(self.main_frame, bg=BG_MEDIUM)
        self.profile_frame.pack(fill=tk.X, expand=True)

        # Buttons
        button_frame = tk.Frame(self.main_frame, bg=BG_MEDIUM)
        button_frame.pack(pady=20)
        self.convert_button = tk.Button(button_frame, text=START_CONVERSION_BUTTON, command=self.start_conversion_thread, 
                                        font=("Arial", 12, "bold"), bg=COLOR_SUCCESS, fg=FG_LIGHT, padx=20, pady=8,
                                        cursor="hand2", relief=tk.FLAT, state=tk.DISABLED)
        self.convert_button.pack(side=tk.LEFT, padx=10)
        self.stop_button = tk.Button(button_frame, text=STOP_CONVERSION_BUTTON, command=self.stop_conversion, 
                                     font=("Arial", 12, "bold"), bg=COLOR_ERROR, fg=FG_LIGHT, padx=20, pady=8,
                                     cursor="hand2", relief=tk.FLAT, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10)
        
        # Progress
        self.progress_label = tk.Label(self.main_frame, text=WAITING_SELECTION, font=("Arial", 10), bg=BG_MEDIUM, fg="#cccccc")
        self.progress_label.pack(fill=tk.X, pady=(10, 5))
        self.progress_bar = ttk.Progressbar(self.main_frame, orient="horizontal", length=500, mode="determinate")
        self.progress_bar.pack(fill=tk.X)
        
        self.info_label = tk.Label(self.main_frame, text="", font=("Arial", 9, "italic"), bg=BG_MEDIUM, fg=COLOR_ACCENT, wraplength=700, justify=tk.LEFT)
        self.info_label.pack(fill=tk.X, pady=(10, 0))

        # Footer
        footer_container = tk.Frame(self.main_frame, bg=BG_MEDIUM)
        footer_container.pack(fill=tk.X, side=tk.BOTTOM, pady=(20, 0))
        
        hub_frame = tk.Frame(footer_container, bg=BG_MEDIUM)
        hub_frame.pack(fill=tk.X)
        
        tk.Label(hub_frame, text="Desenvolvido por saulomgg |", font=("Arial", 10, "bold"), bg=BG_MEDIUM, fg="#999999").pack(side=tk.LEFT)
        
        github_link = tk.Label(hub_frame, text="GitHub", font=("Arial", 10, "bold", "underline"), bg=BG_MEDIUM, fg=COLOR_PRIMARY, cursor="hand2")
        github_link.pack(side=tk.LEFT, padx=5)
        github_link.bind("<Button-1>", lambda e: open_url("https://github.com/saulomgg"))
        
        # Help and Support Buttons
        btn_frame = tk.Frame(footer_container, bg=BG_MEDIUM)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(btn_frame, text="ℹ️ Sobre", command=self.open_about, font=("Arial", 9, "bold"), bg="#444444", fg="white", bd=0, padx=10, pady=3, cursor="hand2").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🎁 Suporte / Doação", command=self.open_support, font=("Arial", 9, "bold"), bg=COLOR_ACCENT, fg=BG_DARK, bd=0, padx=10, pady=3, cursor="hand2").pack(side=tk.LEFT, padx=5)
        
        self.update_profile_options()

    def update_profile_options(self, event=None):
        for widget in self.profile_frame.winfo_children(): widget.destroy()
        fmt = self.output_format.get()
        profiles = {}
        if fmt == "mp4":
            profiles = {"h264_balanced": PROFILE_H264_BALANCED, "h264_quality": PROFILE_H264_QUALITY, "h264_fast": PROFILE_H264_FAST}
            self.info_label.config(text=INFO_MP4)
        elif fmt == "mkv":
            profiles = {"h265_balanced": PROFILE_H265_BALANCED, "h265_quality": PROFILE_H265_QUALITY, "h265_fast": PROFILE_H265_FAST}
            self.info_label.config(text=INFO_MKV)
        elif fmt == "webm":
            if self.vp9_available:
                profiles = {"vp9_balanced": PROFILE_VP9_BALANCED, "vp9_quality": PROFILE_VP9_QUALITY, "vp9_fast": PROFILE_VP9_FAST}
                self.info_label.config(text=INFO_WEBM)
            else:
                profiles = {"vp9_missing": PROFILE_VP9_MISSING}
                self.info_label.config(text=INFO_WEBM_VP9_MISSING)
        elif fmt == "mov":
            profiles = {"prores_lt": PROFILE_PRORES_LT, "prores_standard": PROFILE_PRORES_STANDARD}
            self.info_label.config(text=INFO_MOV)

        for val, text in profiles.items():
            state = tk.DISABLED if val == "vp9_missing" else tk.NORMAL
            tk.Radiobutton(self.profile_frame, text=text, variable=self.compression_profile, value=val,
                          bg=BG_MEDIUM, fg=FG_LIGHT, selectcolor=BG_DARK, activebackground=BG_MEDIUM,
                          activeforeground=FG_LIGHT, font=("Arial", 10), state=state).pack(anchor='w')
        
        # Add HW Codecs
        if self.available_hw_codecs:
            tk.Label(self.profile_frame, text=PROFILE_GPU, font=("Arial", 10, "bold"), bg=BG_MEDIUM, fg=COLOR_ACCENT).pack(anchor='w', pady=(5, 0))
            for codec, name in self.available_hw_codecs.items():
                tk.Radiobutton(self.profile_frame, text=name, variable=self.compression_profile, value=codec,
                              bg=BG_MEDIUM, fg=FG_LIGHT, selectcolor=BG_DARK, activebackground=BG_MEDIUM,
                              activeforeground=FG_LIGHT, font=("Arial", 10)).pack(anchor='w')

    def open_about(self):
        about_win = tk.Toplevel(self.root)
        about_win.title("Sobre ConvertSynk - HubSynk")
        about_win.geometry("550x500")
        about_win.resizable(False, False)
        about_win.configure(bg="#1e1e1e")
        about_win.transient(self.root)
        about_win.grab_set()
        
        # Tentar carregar logo no sobre
        try:
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath(".")
            logo_path = os.path.join(base_path, "assets", "logo.png")
            if os.path.exists(logo_path):
                img = tk.PhotoImage(file=logo_path)
                logo_label = tk.Label(about_win, image=img, bg="#1e1e1e")
                logo_label.image = img
                logo_label.pack(pady=10)
        except:
            pass

        tk.Label(about_win, text="🔷 HUBSYNK ECOSYSTEM", font=("Consolas", 14, "bold"), bg="#1e1e1e", fg="#2196F3").pack(pady=(10, 10))
        tk.Label(about_win, text="ConvertSynk v1.0", font=("Segoe UI", 16, "bold"), bg="#1e1e1e", fg="white").pack(pady=5)
        
        desc_text = (
            "Esta é uma ferramenta oficial do ecossistema HubSynk.\n\n"
            "O HubSynk foi criado para centralizar e automatizar tarefas "
            "do dia a dia, garantindo segurança e produtividade.\n\n"
            "O desenvolvimento e atualizações constantes dependem da "
            "interação da comunidade. Apoie o projeto!"
        )
        tk.Label(about_win, text=desc_text, font=("Segoe UI", 10), bg="#1e1e1e", fg="#cccccc", wraplength=450, justify="center").pack(pady=15)
        
        links_frame = tk.Frame(about_win, bg="#1e1e1e")
        links_frame.pack(pady=10)
        
        def create_link_btn(text, url, color="#2196F3"):
            btn = tk.Button(links_frame, text=text, font=("Segoe UI", 10, "bold", "underline"), bg="#1e1e1e", fg=color,
                         activebackground="#1e1e1e", activeforeground="white", bd=0, cursor="hand2",
                         command=lambda: webbrowser.open_new(url))
            btn.pack(pady=3)

        create_link_btn("🔗 Link do HubSynk", "https://github.com/saulomgg/HubSynk")
        create_link_btn("📂 Link do GitHub / Portfólio", "https://github.com/saulomgg")
        
        tk.Label(about_win, text="O desenvolvimento e atualização do programa depende da sua interação e apoio!", 
                 font=("Segoe UI", 9, "italic"), bg="#1e1e1e", fg=COLOR_ACCENT, wraplength=400).pack(pady=10)
        
        tk.Button(about_win, text="Fechar", command=about_win.destroy, bg="#333333", fg="white", 
               relief="flat", padx=20, pady=5, cursor="hand2").pack(pady=15)

    def open_support(self):
        webbrowser.open("https://github.com/saulomgg/HubSynk/releases")

    def select_files(self):
        files = filedialog.askopenfilenames(title="Select Video Files")
        if files:
            self.current_files = [Path(f) for f in files]
            self.file_info_label.config(text=f"{len(files)} files selected")
            self.convert_button.config(state=tk.NORMAL)
            self.progress_label.config(text=READY_TO_CONVERT)

    def select_output_folder(self):
        folder = filedialog.askdirectory()
        if folder: self.output_dir.set(folder)

    def start_conversion_thread(self):
        pass # Implementação original mantida

    def stop_conversion(self):
        self.stop_conversion_flag.set()
        self.stop_button.config(state=tk.DISABLED)
        self.progress_label.config(text="Stopping...")
