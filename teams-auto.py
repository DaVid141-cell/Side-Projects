import tkinter as tk
from tkinter import ttk
import threading
import subprocess
import time
import random
import pyautogui
import sys

# CONFIG
WORDS = [
    "just checking on this",
    "working on it now",
    "reviewing the document",
    "updating the report",
    "almost done with this",
    "checking my notes",
    "finishing up a task",
    "looking into this",
    "going through emails",
    "double checking the numbers",
    "wrapping up this section",
    "still on this task",
    "making some edits",
    "going over the details",
    "taking a quick look",
]

TYPING_DURATION = 180 # seconds
PAUSE_DURATION = 180 # secobds
TYPE_INTERVAL = 0.07 # seconds between keystrokes
LINE_PAUSE_MIN = 10 # seconds between lines (MIN)
LINE_PAUSE_MAX = 20 # seconds beteeen lines (MAX)

# HELPERS
def random_line():
    return random.choice(WORDS)

def fmt(seconds):
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"

# WORKERS

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Teams Status Keeper")
        self.resizable(False, False)
        self.configure(bg="#1e1e2e")

        self._running = False
        self._thread = None
        self._stop_evt = threading.Event()

        self._phase = tk.StringVar(value="Offline")
        self._countdown = tk.StringVar(value="--:--")
        self._lines = tk.IntVar(value=0)
        self._log_lines = []

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # UI APP

    def _build_ui(self):
        BG = "#1e1e2e"
        CARD = "#2a2a3e"
        ACC = "#7c6af7"
        GRN  = "#4ade80"
        RED  = "#f87171"
        ORG = "#FBBF77"
        TXT  = "#e2e0ff"
        MUT  = "#9b99c4"
        MONO = ("Consolas", 10)

        pad = dict(padx=20, pady=10)

        # --- header ----
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=20, pady=(18, 0))

        tk.Label(header, text="O", font=("Segoe UI", 22), bg=BG, 
                    fg=ACC).pack(side="left")
        tk.Label(header, text=" Teams Status Keeper", 
                    font=("Segoe UI", 14, "bold"), bg=BG, fg=TXT).pack(side="left")
        
        # --- status card ---
        card = tk.Frame(self, bg=CARD, bd=0, highlightthickness=1, highlightbackground="#3a3a55")
        card.pack(fill="x", padx=20, pady=14)

        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill="x", padx=16, pady=12)

        # phase and countdown row
        row1 = tk.Frame(inner, bg=CARD)
        row1.pack(fill="x")

        self._phase_lbl = tk.Label(row1, textvariable=self._phase, 
                                    font=("Segoe UI", 11, "bold"), bg=CARD, fg=MUT, width=14, anchor="w")
        self._phase_lbl.pack(side="left")

        tk.Label(row1, text="Next in", font=("Segoe UI", 10), bg=CARD, fg=MUT).pack(side="left", padx=(20,4))

        self._cd_lbl = tk.Label(row1, textvariable=self._countdown, font=("Consolas", 13, "bold"), bg=CARD, fg=TXT)
        self._cd_lbl.pack(side="left")

        # lines typed
        row2 = tk.Frame(inner, bg=CARD)
        row2.pack(fill="x", pady=(6, 0))

        tk.Label(row2, text="Lines typed:", font=("Segoe UI", 10), bg=CARD, fg=MUT).pack(side="left")
        tk.Label(row2, textvariable=self._lines, font=("Segoe UI", 10, "bold"), bg=CARD, fg=TXT).pack(side="left", padx=4)

        # -- progress bar --
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("Acc.Horizontal.TProgressbar", troughcolor=BG, background=ACC, 
                            thickness=6, borderwidth=0)
        
        self._progress = ttk.Progressbar(self, orient="horizontal", mode="determinate", style="Acc.Horizontal.TProgressbar")
        self._progress.pack(fill="x", padx=20, pady=(0, 4))

        # -- log box --
        log_frame = tk.Frame(self, bg=BG)
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        tk.Label(log_frame, text="Activity log", font=("Segoe UI", 9), bg=BG, fg=MUT).pack(anchor="w", pady=(0, 4))
        self._log = tk.Text(log_frame, height=10, bg=CARD, fg=TXT, font=MONO, 
                                relief="flat", bd=0, state="disabled", cursor="arrow",
                                insertbackground=TXT, highlightthickness=1, highlightbackground="#3a3a55")
        self._log.pack(fill="both", expand=True)

        # -- buttons UI --
        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(fill="x", padx=20, pady=(0, 10))

        self._start_btn = tk.Button(btn_row, text="▶ Start", font=("Segoe UI", 11, "bold"),
                                        bg=ACC, fg="#fff", relief="flat", bd=0,
                                        activebackground="#6a5ce0", activeforeground="#fff",
                                        cursor="hand2", padx=20, pady=8, command=self._toggle)
        self._start_btn.pack(side="left", expand=True, fill="x", padx=(0, 8))

        tk.Button(
            btn_row, text="Clear log", font=("Segoe UI", 10), 
            bg=CARD, fg=MUT, relief="flat", bd=0, activebackground="#3a3a55",
            activeforeground=TXT, cursor="hand2", padx=14, pady=8,
            command=self._clear_log
        ).pack(side="left")

        # stored colors for dynamic use
        self._GRN, self._RED, self._ACC, self._ORG = GRN, RED, ACC, ORG
        self._MUT, self._TXT, self._CARD = MUT, TXT, CARD

        self.geometry("480x520")

    # -- logging --
    def _log_msg(self, msg, color=None):
        current_time = time.strftime("%H:%M:%S")
        line = f"[{current_time}] {msg}\n"
        self._log.configure(state="normal")
        start = self._log.index("end-1c")
        self._log.insert("end", line)
        if color:
            end = self._log.index("end-1c")
            tag = f"color_{color.replace('#', '')}"
            self._log.tag_configure(tag, foreground=color)
            self._log.tag_add(tag, start, end)
        self._log.see("end")
        self._log.configure(state="disabled")

    def _clear_log(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    # -- toggle start and stop
    def _toggle(self):
        if not self._running:
            self._start()
        else:
            self._stop()

    def _start(self):
        self._running = True
        self._stop_evt.clear()
        self._start_btn.configure(text="■ Stop", bg=self._RED, activebackground="#e05555")
        self._lines.set(0)
        self._log_msg("Started - opening Notepad....")
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _stop(self):
        self._running = False
        self._stop_evt.set()
        self._start_btn.configure(text="▶  Start", bg=self._ACC, activebackground="#6a5ce0")
        self._phase.set("Idle")
        self._countdown.set("--:--")
        self._progress["value"] = 0
        self._phase_lbl.configure(fg=self._MUT)
        self._log_msg("Stopped.", self._RED)

    # --- worker thread ---
    def _worker(self):
        # opens notepad
        subprocess.Popen(["notepad.exe"])
        time.sleep(2)

        while not self._stop_evt.is_set():

            # typing phase
            self._set_phase("Online", self._GRN)
            self._log_msg("Typing Script has started...", self._GRN)
            deadline = time.time() + TYPING_DURATION

            while time.time() < deadline and not self._stop_evt.is_set():
                remaining = deadline - time.time()
                self._update_progress(remaining, TYPING_DURATION)

                # line type
                line = random_line()
                pyautogui.typewrite(line, interval=TYPE_INTERVAL)
                pyautogui.press("enter")
                self._lines.set(self._lines.get() + 1)
                self._log_msg(f'Typed: "{line}"')

                # wait between lines
                pause = random.randint(LINE_PAUSE_MIN, LINE_PAUSE_MAX)

                self._stop_evt.wait(pause)
            
            if self._stop_evt.is_set():
                break

            # -- pause phase --
            self._set_phase("Idle", self._ORG)
            self._log_msg("Typing has Stop (3mins)", self._ORG)
            deadline = time.time() + PAUSE_DURATION

            while time.time() < deadline and not self._stop_evt.is_set():
                remaining= deadline - time.time()
                self._update_progress(remaining, PAUSE_DURATION)
                self._stop_evt.wait(1)
        
        self.after(0, self._stop)

    # UI update helpers
    def _set_phase(self, text, color):
        self.after(0, lambda: self._phase.set(text))
        self.after(0, lambda: self._phase_lbl.configure(fg=color))

    def _update_progress(self, remaining, total):
        pct = max(0, (remaining / total) * 100)
        cd = fmt(remaining)
        self.after(0, lambda: self._progress.configure(value=pct))
        self.after(0, lambda: self._countdown.set(cd))
    
    # -- close --
    def _on_close(self):
        self._stop_evt.set()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()

