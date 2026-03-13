#!/usr/bin/env python3
"""
Meeting Recap Agent — GUI
Interfaccia grafica con customtkinter.

Avvio: python gui.py
"""

import threading
import os
from pathlib import Path
from datetime import datetime
import time

import customtkinter as ctk
from tkinter import filedialog, messagebox

from agent import (
    transcribe,
    prepare_audio,
    generate_recap,
    generate_simple_recap,
    save_docx,
    get_output_dir,
    WHISPER_MODEL_DEFAULT,
    GEMINI_MODEL,
    VIDEO_EXTENSIONS,
    _ensure_ffmpeg_in_path,
)
from google import genai
from dotenv import load_dotenv

load_dotenv()
_ensure_ffmpeg_in_path()

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Meeting Recap Agent")
        self.geometry("800x560")
        self.minsize(600, 400)

        self._audio_path = None
        self._running = False

        self._build_ui()

    # -----------------------------------------------------------------------
    # UI
    # -----------------------------------------------------------------------
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)  # log espandibile

        # --- Riga 0: file picker ---
        file_frame = ctk.CTkFrame(self)
        file_frame.grid(row=0, column=0, padx=16, pady=(16, 6), sticky="ew")
        file_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(file_frame, text="File audio:").grid(
            row=0, column=0, padx=(12, 6), pady=10, sticky="w"
        )
        self.file_label = ctk.CTkLabel(
            file_frame, text="Nessun file selezionato", anchor="w", text_color="gray"
        )
        self.file_label.grid(row=0, column=1, padx=6, pady=10, sticky="ew")
        ctk.CTkButton(
            file_frame, text="Sfoglia...", width=100, command=self._pick_file
        ).grid(row=0, column=2, padx=(6, 12), pady=10)

        # --- Riga 1: modalità ---
        mode_frame = ctk.CTkFrame(self)
        mode_frame.grid(row=1, column=0, padx=16, pady=6, sticky="ew")

        ctk.CTkLabel(mode_frame, text="Modalità:").grid(
            row=0, column=0, padx=(12, 6), pady=10, sticky="w"
        )
        self.mode_var = ctk.StringVar(value="full")
        ctk.CTkRadioButton(
            mode_frame,
            text="Recap completo  (2 passaggi Gemini, formato email)",
            variable=self.mode_var,
            value="full",
        ).grid(row=0, column=1, padx=12, pady=10, sticky="w")
        ctk.CTkRadioButton(
            mode_frame,
            text="Recap semplice  (1 passaggio, ~150-200 parole)",
            variable=self.mode_var,
            value="simple",
        ).grid(row=0, column=2, padx=12, pady=10, sticky="w")

        # --- Riga 2: pulsante avvia ---
        self.run_btn = ctk.CTkButton(
            self,
            text="▶  Avvia recap",
            command=self._start_pipeline,
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.run_btn.grid(row=2, column=0, padx=16, pady=6, sticky="ew")

        # --- Riga 3: barra di avanzamento trascrizione ---
        progress_frame = ctk.CTkFrame(self)
        progress_frame.grid(row=3, column=0, padx=16, pady=(0, 4), sticky="ew")
        progress_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(progress_frame, text="Trascrizione:").grid(
            row=0, column=0, padx=(12, 8), pady=6, sticky="w"
        )
        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=14)
        self.progress_bar.set(0)
        self.progress_bar.grid(row=0, column=1, padx=(0, 8), pady=6, sticky="ew")
        self.progress_label = ctk.CTkLabel(
            progress_frame, text="0%", width=36, anchor="e"
        )
        self.progress_label.grid(row=0, column=2, padx=(0, 12), pady=6, sticky="e")

        # --- Riga 4: log ---
        log_frame = ctk.CTkFrame(self)
        log_frame.grid(row=4, column=0, padx=16, pady=(4, 16), sticky="nsew")
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)

        self.log_box = ctk.CTkTextbox(
            log_frame,
            state="disabled",
            font=ctk.CTkFont(family="Courier New", size=12),
            wrap="word",
        )
        self.log_box.grid(row=0, column=0, padx=4, pady=4, sticky="nsew")

    # -----------------------------------------------------------------------
    # Callback
    # -----------------------------------------------------------------------
    def _pick_file(self):
        path = filedialog.askopenfilename(
            title="Seleziona file audio o video",
            filetypes=[
                ("File audio/video", "*.mp3 *.wav *.m4a *.ogg *.flac *.mp4 *.mkv *.avi *.mov *.webm *.m4v"),
                ("File audio", "*.mp3 *.wav *.m4a *.ogg *.flac"),
                ("File video", "*.mp4 *.mkv *.avi *.mov *.webm *.m4v"),
                ("Tutti i file", "*.*"),
            ],
        )
        if path:
            self._audio_path = path
            self.file_label.configure(text=Path(path).name, text_color="white")

    def _start_pipeline(self):
        if self._running:
            return
        if not self._audio_path:
            messagebox.showwarning("Attenzione", "Seleziona prima un file audio.")
            return
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            messagebox.showerror(
                "API Key mancante",
                "GEMINI_API_KEY non trovata.\n"
                "Crea un file .env nella cartella del programma:\n"
                "GEMINI_API_KEY=AIza...",
            )
            return

        self._running = True
        self.run_btn.configure(state="disabled", text="⏳  Elaborazione in corso...")
        self._clear_log()
        self._set_progress(0)

        threading.Thread(
            target=self._run_pipeline,
            args=(self._audio_path, api_key, self.mode_var.get()),
            daemon=True,
        ).start()

    # -----------------------------------------------------------------------
    # Pipeline (thread background)
    # -----------------------------------------------------------------------
    def _run_pipeline(self, audio_path: str, api_key: str, mode: str):
        start = time.time()
        try:
            self._log("=" * 52)
            self._log("  MEETING RECAP AGENT")
            self._log(f"  Modalità : {'Completo (2 passaggi)' if mode == 'full' else 'Semplice (1 passaggio)'}")
            self._log(f"  File     : {Path(audio_path).name}")
            self._log(f"  Modello  : Whisper {WHISPER_MODEL_DEFAULT} + {GEMINI_MODEL}")
            self._log("=" * 52)

            # 1. Estrazione audio (se video) + trascrizione
            is_video = Path(audio_path).suffix.lower() in VIDEO_EXTENSIONS
            if is_video:
                self._log("\n[1/3] Estrazione audio dal video (ffmpeg)...")
            else:
                self._log("\n[1/3] Caricamento Whisper e trascrizione audio...")

            audio_for_whisper, is_temp = prepare_audio(audio_path)
            if is_video:
                self._log("      Audio estratto. Avvio trascrizione...")

            try:
                transcript = transcribe(
                    audio_for_whisper,
                    WHISPER_MODEL_DEFAULT,
                    progress_callback=self._set_progress,
                )
            finally:
                if is_temp:
                    Path(audio_for_whisper).unlink(missing_ok=True)

            self._set_progress(1.0)
            self._log(f"      Completata — {len(transcript)} caratteri trascritti")

            # 2. Gemini
            client = genai.Client(api_key=api_key)
            meeting_date = datetime.now().strftime("%d/%m/%Y")

            if mode == "full":
                self._log("\n[2/3] Generazione recap completo...")
                self._log("      Passaggio 1/2 — Prima bozza...")
                final, draft1, draft2 = generate_recap(transcript, meeting_date, client)
                self._log("      Passaggio 2/2 — Verifica e formattazione email... ✓")
            else:
                self._log("\n[2/3] Generazione recap semplice...")
                final = generate_simple_recap(transcript, client)
                draft1, draft2 = "", ""
                self._log("      Completato ✓")

            # 3. Salvataggio
            stem = Path(audio_path).stem
            output_path = str(get_output_dir(audio_path) / f"{stem}_recap.docx")
            self._log(f"\n[3/3] Salvataggio: {Path(output_path).name}")
            save_docx(
                content=final,
                transcript=transcript,
                output_path=output_path,
                audio_path=audio_path,
                mode=mode,
                draft1=draft1,
                draft2=draft2,
            )

            self._log("\n" + "=" * 52)
            self._log(f"  ✓ COMPLETATO")
            self._log(f"  {output_path}")
            self._log("=" * 52)

        except Exception as exc:
            self._log(f"\n[ERRORE] {type(exc).__name__}: {exc}")
            self.after(0, lambda: messagebox.showerror(
                "Errore", f"Elaborazione fallita:\n{exc}"
            ))
        finally:
            self._running = False
            self.after(0, self._reset_button)
        self._log(f"\nTempo totale: {int(time.time() - start)} secondi")

    # -----------------------------------------------------------------------
    # Log (thread-safe)
    # -----------------------------------------------------------------------
    def _log(self, message: str):
        self.log_box.after(0, self._append_log, message)

    def _append_log(self, message: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _set_progress(self, value: float):
        """Thread-safe: aggiorna la progress bar (value: 0.0–1.0)."""
        self.progress_bar.after(0, self._update_progress, value)

    def _update_progress(self, value: float):
        self.progress_bar.set(value)
        self.progress_label.configure(text=f"{int(value * 100)}%")

    def _reset_button(self):
        self.run_btn.configure(state="normal", text="▶  Avvia recap")


if __name__ == "__main__":
    app = App()
    app.mainloop()
