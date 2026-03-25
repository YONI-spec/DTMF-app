import tkinter as tk
import customtkinter as ctk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Configuration CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")  # Thème par défaut, nous définirons les couleurs manuellement

class SignalAnalyzerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Analyseur de Signal | DTMF & Live Goertzel")
        self.geometry("1400x900")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Palette de couleurs personnalisée
        self.color_bg = "#111116"
        self.color_card = "#16161c"
        self.color_accent = "#34bfa3"  # Teal/Cyan
        # CORRECTIF: Remplacement de "#34bfa350" (8 chars invalide) par un code 6 chars valide (#1F4B46)
        self.color_accent_glow = "#1f4b46"  # Sarcelle foncée pour simuler opacité
        self.color_text = "#ffffff"
        self.color_text_muted = "#888888"

        self.configure(fg_color=self.color_bg)

        # --- Conteneur principal (simulant le navigateur) ---
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)

        # --- Barre de titre du navigateur (factice) ---
        self.nav_bar = ctk.CTkFrame(self.main_container, height=40, fg_color="#18181e", corner_radius=0)
        self.nav_bar.grid(row=0, column=0, sticky="ew")
        self.nav_bar.grid_columnconfigure(2, weight=1)

        # Icônes de contrôle de fenêtre (Unicode pour la simplicité)
        ctk.CTkButton(self.nav_bar, text="<", width=30, fg_color="transparent", text_color=self.color_text_muted, font=("Arial", 14)).grid(row=0, column=0, padx=5)
        ctk.CTkButton(self.nav_bar, text=">", width=30, fg_color="transparent", text_color=self.color_text_muted, font=("Arial", 14)).grid(row=0, column=1, padx=5, sticky="w")
        self.url_bar = ctk.CTkEntry(self.nav_bar, fg_color="#111111", border_color="#333333", text_color=self.color_text_muted)
        self.url_bar.insert(0, "Analyseur de Signal | DTMF Goertzel (Live)")
        self.url_bar.grid(row=0, column=2, sticky="ew", padx=(10, 0), pady=5)
        ctk.CTkButton(self.nav_bar, text="👤", width=30, fg_color="transparent", text_color=self.color_text_muted, font=("Arial", 14)).grid(row=0, column=3, padx=10)

        # --- Contenu du tableau de bord ---
        self.dashboard_content = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.dashboard_content.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.dashboard_content.grid_columnconfigure(0, weight=1)  # Colonne contrôles
        self.dashboard_content.grid_columnconfigure(1, weight=2)  # Colonne graphique
        self.dashboard_content.grid_rowconfigure(0, weight=1)

        # --- Colonne de gauche (Contrôles) ---
        self.controls_panel = ctk.CTkFrame(self.dashboard_content, fg_color="transparent")
        self.controls_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.controls_panel.grid_columnconfigure(0, weight=1)

        # Carte: Source du Signal
        self.source_card = self.create_card(self.controls_panel, "Source du Signal")
        self.source_card.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Onglets
        self.source_tabs = ctk.CTkSegmentedButton(self.source_card, values=["[Fichier]", "[[En Direct]]"], command=None,
                                                 fg_color="#111111", text_color=self.color_text, selected_color="#111111",
                                                 selected_hover_color="#111111", unselected_color="#111111", unselected_hover_color="#111111")
        self.source_tabs.set("[Fichier]")
        self.source_tabs.grid(row=1, column=0, sticky="ew", padx=10, pady=(10, 0))

        # Zone d'upload
        self.upload_frame = ctk.CTkFrame(self.source_card, fg_color="#22222a", corner_radius=10, border_color="#333333", border_width=1)
        self.upload_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10, ipady=10)
        ctk.CTkLabel(self.upload_frame, text="Uploader un Fichier Audio", text_color=self.color_text, font=("Arial", 14)).pack(pady=10)
        ctk.CTkLabel(self.upload_frame, text="Glissez-déposez ici", text_color=self.color_text_muted, font=("Arial", 12)).pack()

        # Nom du fichier
        ctk.CTkLabel(self.source_card, text="Nom du Fichier", text_color=self.color_text_muted).grid(row=3, column=0, padx=10, pady=(10, 0), sticky="w")
        self.file_name_entry = ctk.CTkEntry(self.source_card, fg_color="#22222a", border_color="#333333", text_color=self.color_text, font=("Arial", 12))
        self.file_name_entry.insert(0, "Nom du Fichier")
        self.file_name_entry.grid(row=4, column=0, sticky="ew", padx=10, pady=5)
        self.browse_btn = ctk.CTkButton(self.source_card, text="📁 Parcourir", width=80, fg_color="#22222a", text_color=self.color_text, corner_radius=8, font=("Arial", 11))
        self.browse_btn.grid(row=4, column=0, sticky="e", padx=(0, 15), pady=5)

        # Carte: Analysis Configuration
        self.config_card = self.create_card(self.controls_panel, "Analysis Configuration")
        self.config_card.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # Entrée audio
        ctk.CTkLabel(self.config_card, text="Entrée Audio", text_color=self.color_text_muted).grid(row=1, column=0, padx=10, pady=(10, 0), sticky="w")
        self.audio_input_entry = ctk.CTkComboBox(self.config_card, values=["Microphone Interne"], fg_color="#22222a", border_color="#333333", text_color=self.color_text, font=("Arial", 12))
        self.audio_input_entry.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        # Compteur de barres (Simulé)
        self.bar_meter_frame = ctk.CTkFrame(self.config_card, fg_color="transparent", height=40)
        self.bar_meter_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        self.bar_meter_frame.grid_columnconfigure(tuple(range(10)), weight=1)
        for i in range(10):
            bar_height = np.random.randint(5, 30)
            bar = ctk.CTkFrame(self.bar_meter_frame, width=8, height=bar_height, fg_color=self.color_accent, corner_radius=2)
            bar.grid(row=0, column=i, sticky="s", padx=1)

        # Carte: Résultats Décodés & Saisie
        self.results_card = self.create_card(self.controls_panel, "Résultats Décodés & Saisie")
        self.results_card.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        # Indicateur LIVE
        self.live_indicator_frame = ctk.CTkFrame(self.results_card, fg_color="transparent")
        self.live_indicator_frame.grid(row=0, column=0, sticky="e", padx=10, pady=(5, 0))
        self.live_dot = ctk.CTkButton(self.live_indicator_frame, text="", width=10, height=10, fg_color="#d43c2d", corner_radius=5, state="disabled")
        self.live_dot.pack(side="left")
        ctk.CTkLabel(self.live_indicator_frame, text="LIVE", text_color="#d43c2d", font=("Arial", 11, "bold")).pack(side="left", padx=5)

        # Écran numérique stylisé
        self.display_screen = ctk.CTkFrame(self.results_card, fg_color="#18181e", corner_radius=10, border_color=self.color_accent, border_width=2)
        self.display_screen.grid(row=1, column=0, sticky="ew", padx=10, pady=10, ipady=10)
        ctk.CTkLabel(self.display_screen, text="SÉQUENCE : 1 5 9", text_color=self.color_accent, font=("Arial", 28, "bold")).pack(pady=10)
        ctk.CTkLabel(self.display_screen, text="DETECTÉ : 770Hz + 1477Hz -> 159", text_color=self.color_accent, font=("Arial", 16)).pack()

        # Clavier téléphonique
        self.keypad_frame = ctk.CTkFrame(self.results_card, fg_color="transparent")
        self.keypad_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        self.keypad_frame.grid_columnconfigure(tuple(range(3)), weight=1)

        keys = [
            ("1", "ABC"), ("2", "DEF"), ("3", "GHI"),
            ("4", "JKL"), ("5", "MNO"), ("6", "PQRS"),
            ("7", "TUV"), ("8", "WXYZ"), ("9", ""),
            ("*", ""), ("0", ""), ("#", "")
        ]

        for i, (key, letters) in enumerate(keys):
            row, col = divmod(i, 3)
            btn_frame = ctk.CTkFrame(self.keypad_frame, fg_color="transparent")
            btn_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            
            # Bouton rond stylisé
            btn = ctk.CTkButton(btn_frame, text=key, font=("Arial", 22, "bold"), text_color=self.color_text,
                                 fg_color="#18181e", border_color=self.color_accent, border_width=2,
                                 corner_radius=25, width=50, height=50)
            btn.pack()
            ctk.CTkLabel(btn_frame, text=letters, text_color=self.color_text_muted, font=("Arial", 11)).pack(pady=2)

        # --- Colonne de droite (Visualisation) ---
        self.viz_panel = ctk.CTkFrame(self.dashboard_content, fg_color="transparent")
        self.viz_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        self.viz_panel.grid_columnconfigure(0, weight=1)
        self.viz_panel.grid_rowconfigure(0, weight=1)

        # Carte: Analyseur de spectre
        self.spectrum_card = self.create_card(self.viz_panel, "Analyseur de spectre")
        self.spectrum_card.grid(row=0, column=0, sticky="nsew")
        self.spectrum_card.grid_rowconfigure(1, weight=1)

        # Intégration de Matplotlib
        fig, ax = plt.subplots(figsize=(8, 6), facecolor=self.color_card)
        self.ax = ax
        self.ax.set_facecolor(self.color_bg)
        self.ax.set_title("Spectrogramme", color=self.color_text)
        self.ax.set_xlabel("Signalue (dBs)", color=self.color_text)
        self.ax.set_ylabel("Fréquence (Hz)", color=self.color_text)
        self.ax.set_xlim(-50, 0)
        self.ax.set_ylim(0, 1600)
        self.ax.tick_params(colors=self.color_text)

        # Génération de données synthétiques
        num_points = 500
        freqs = np.linspace(0, 1600, num_points)
        noise = np.random.normal(-35, 3, num_points)
        signal = noise.copy()
        dtmf_freqs = [697, 770, 852, 941, 1209, 1336, 1477, 1633]
        for f in dtmf_freqs:
            idx = np.abs(freqs - f).argmin()
            signal[idx] = -12

        # Tracé bleu sarcelle
        self.ax.plot(signal, freqs, color=self.color_accent, linewidth=1.5)

        # Bandes de fréquence DTMF
        for i, f in enumerate(dtmf_freqs):
            self.ax.axhline(f, color=self.color_accent, alpha=0.3, linestyle='--', linewidth=1)
            self.ax.text(-48, f + 15, f"{f} Hz", color=self.color_text_muted, fontsize=9)

        # Annotation du curseur simulée
        annotation_text = "Fréquence : 770 Hz\nMagnitude : -12 dBs\nDTMF Bande : 770\nConfidence : High"
        self.ax.annotate(annotation_text, xy=(-12, 770), xytext=(-30, 850),
                         arrowprops=dict(facecolor=self.color_text, arrowstyle="->", connectionstyle="arc3,rad=.2"),
                         color=self.color_text, backgroundcolor=self.color_card, fontsize=9, bbox=dict(facecolor=self.color_card, edgecolor=self.color_text_muted, boxstyle="round,pad=0.5"))

        # Grille
        self.ax.grid(color=self.color_text_muted, alpha=0.2)

        # Toile Matplotlib pour Tkinter
        self.canvas = FigureCanvasTkAgg(fig, master=self.spectrum_card)
        self.canvas.draw()
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        plt.close(fig)  # Éviter l'utilisation excessive de la mémoire

        # --- Ligne inférieure (Résultats/Actions) ---
        self.bottom_content = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.bottom_content.grid(row=2, column=0, sticky="ew", padx=10, pady=(10, 0))
        self.bottom_content.grid_columnconfigure(0, weight=1)
        self.bottom_content.grid_columnconfigure(1, weight=1)

        # Carte: Contrôles du Décodage (Journal)
        self.log_card = self.create_card(self.bottom_content, "Contrôles du Décodage")
        self.log_card.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.log_card.grid_columnconfigure(0, weight=1)

        for i in range(3):
            line = ctk.CTkFrame(self.log_card, fg_color="#18181e", corner_radius=5)
            line.grid(row=i+1, column=0, sticky="ew", padx=10, pady=3)
            ctk.CTkLabel(line, text="...", text_color=self.color_text_muted).pack(pady=3)

        # Carte: Contrôles du Décodage (Actions)
        self.action_card = self.create_card(self.bottom_content, "Contrôles du Décodage")
        self.action_card.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        self.action_card.grid_columnconfigure(tuple(range(2)), weight=1)

        # Bouton principal (couleur sarcelle)
        self.start_btn = ctk.CTkButton(self.action_card, text="🎤 Démarrer l'Analyse en Direct", width=180, fg_color=self.color_accent, text_color=self.color_bg, corner_radius=8, font=("Arial", 13, "bold"))
        self.start_btn.grid(row=1, column=0, padx=10, pady=10, sticky="ew", ipady=5)

        # Boutons secondaires
        self.stop_btn = ctk.CTkButton(self.action_card, text="Arrêter", width=100, fg_color="#22222a", text_color=self.color_text, corner_radius=8, font=("Arial", 12))
        self.stop_btn.grid(row=1, column=1, padx=(10, 5), pady=10, sticky="e")
        self.clear_btn = ctk.CTkButton(self.action_card, text="Effacer", width=100, fg_color="#22222a", text_color=self.color_text, corner_radius=8, font=("Arial", 12))
        self.clear_btn.grid(row=1, column=1, padx=(5, 10), pady=10, sticky="w")

        # Indicateur d'état
        self.status_frame = ctk.CTkFrame(self.action_card, fg_color="transparent")
        self.status_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        self.status_dot = ctk.CTkButton(self.status_frame, text="", width=12, height=12, fg_color=self.color_accent, corner_radius=6, state="disabled")
        self.status_dot.pack(side="left")
        ctk.CTkLabel(self.status_frame, text="Prêt pour l'analyse.", text_color=self.color_text_muted, font=("Arial", 12)).pack(side="left", padx=10)

        # Bouton factice pour la lueur d'arrière-plan (ILLUSION DU CORRECTIF)
        self.bg_glow = ctk.CTkButton(self, text="✨", width=30, height=30, fg_color="transparent", text_color=self.color_accent_glow, font=("Arial", 18), state="disabled")
        self.bg_glow.place(relx=0.95, rely=0.92, anchor="center")

    def create_card(self, parent, title):
        card = ctk.CTkFrame(parent, fg_color=self.color_card, corner_radius=15)
        card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(card, text=title, text_color=self.color_text, font=("Arial", 14, "bold")).grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        return card

if __name__ == "__main__":
    app = SignalAnalyzerApp()
    app.mainloop()