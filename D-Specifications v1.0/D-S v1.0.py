"""
Delta DOS-Style Device Info & Booster (single-file)
Requirements: psutil, customtkinter
pip install psutil customtkinter

Features:
- Retro DOS-styled GUI with modern widgets (customtkinter)
- Device specs (CPU, cores, memory, OS)
- Real-time CPU% and RAM% gauges
- FPS demo (animated canvas) and measured FPS
- CPS (clicks-per-second) tester (click the button to measure)
- Safe "Run Speed Boost" actions: clear %TEMP% files, flush DNS
- Change mouse pointer speed (Windows) with Apply effect
- Change app cursor (custom .cur/.ani)
- Animated typing output (retro)
- Colorful neon styling
"""

import os
import platform
import psutil
import threading
import time
import subprocess
import sys
import ctypes
from datetime import datetime
from collections import deque

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog

# -------------------------
# Config & helper
# -------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

MONO_FONT = ("Consolas", 12)
TITLE_FONT = ("Consolas", 16, "bold")
ACCENT = "#00ff99"  # neon green accent for retro DOS feel

IS_WINDOWS = sys.platform.startswith("win")

def safe_run(cmd, shell=False):
    try:
        return subprocess.check_output(cmd, shell=shell, stderr=subprocess.STDOUT, universal_newlines=True)
    except Exception as e:
        return f"Error: {e}"

def human_bytes(n):
    for unit in ['B','KB','MB','GB','TB']:
        if n < 1024:
            return f"{n:.2f} {unit}"
        n /= 1024
    return f"{n:.2f} PB"

# -------------------------
# System functions
# -------------------------
def get_system_specs():
    uname = platform.uname()
    cpu = psutil.cpu_freq()
    mem = psutil.virtual_memory()
    specs = {
        "System": f"{uname.system} {uname.release} ({uname.version})",
        "Node": uname.node,
        "Machine": uname.machine,
        "Processor": uname.processor or "Unknown",
        "CPU Cores (logical/physical)": f"{psutil.cpu_count(logical=True)}/{psutil.cpu_count(logical=False) or 'N/A'}",
        "CPU Max (MHz)": f"{cpu.max:.0f}" if cpu and cpu.max else "N/A",
        "Total RAM": human_bytes(mem.total),
        "Boot Time": datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"),
    }
    return specs

def clear_temp_files(typing_callback=None):
    if IS_WINDOWS:
        temp = os.environ.get("TEMP", os.environ.get("TMP", None))
    else:
        temp = "/tmp"
    if not temp or not os.path.isdir(temp):
        return f"Temp directory not found: {temp}"
    removed = 0
    removed_size = 0
    errors = 0
    for root, dirs, files in os.walk(temp):
        for f in files:
            try:
                fp = os.path.join(root, f)
                size = os.path.getsize(fp)
                os.remove(fp)
                removed += 1
                removed_size += size
            except Exception:
                errors += 1
    summary = f"Cleared {removed} files ({human_bytes(removed_size)}) from {temp}. Errors: {errors}"
    if typing_callback:
        typing_callback(summary + "\n")
    return summary

def flush_dns(typing_callback=None):
    if not IS_WINDOWS:
        return "DNS flush not supported on this OS."
    out = safe_run(["ipconfig", "/flushdns"])
    if typing_callback:
        typing_callback(out + "\n")
    return out

def set_mouse_speed(speed):
    """Set Windows mouse speed (1-20)."""
    if not IS_WINDOWS:
        return False, "Not Windows"
    try:
        speed_i = int(max(1, min(20, speed)))
        res = ctypes.windll.user32.SystemParametersInfoW(113, 0, speed_i, 2)  # SPI_SETMOUSESPEED
        return bool(res), f"Set speed to {speed_i}" if res else "Failed (SystemParametersInfoW returned 0)"
    except Exception as e:
            return False, str(e)

# -------------------------
# GUI Application
# -------------------------
class DeltaDOSApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DeltaDOS — Device Info & Booster")
        self.iconbitmap(r'icon.ico') 
        self.geometry("980x680")
        self.minsize(900, 620)

        self._create_layout()
        self._start_background_updates()

        # FPS demo state
        self._fps_timestamps = deque(maxlen=60)
        self._animate_canvas()

        # CPS state
        self._click_timestamps = deque()
        self._cps_running = False

        self._typing_lock = threading.Lock()

    def _create_layout(self):
        # Left: Retro console
        left = ctk.CTkFrame(self, corner_radius=8)
        left.pack(side="left", fill="both", expand=True, padx=12, pady=12)

        # Right: Controls
        right = ctk.CTkFrame(self, width=320, corner_radius=8)
        right.pack(side="right", fill="y", padx=(0,12), pady=12)

        title = ctk.CTkLabel(left, text="Delta DOS — DEVICE DASHBOARD", font=TITLE_FONT, anchor="w")
        title.pack(fill="x", padx=8, pady=(8,4))

        console_frame = ctk.CTkFrame(left, corner_radius=6)
        console_frame.pack(fill="both", expand=True, padx=8, pady=8)

        self.console = tk.Text(console_frame, bg="black", fg=ACCENT, insertbackground=ACCENT,
                               font=("Consolas", 12), wrap="word")
        self.console.pack(fill="both", expand=True, padx=6, pady=6)
        self.console.insert("end", "Welcome to DELTA DOS — initialising...\n")
        self.console.config(state="disabled")

        # FPS + CPS
        bottom = ctk.CTkFrame(left, height=110)
        bottom.pack(fill="x", padx=8, pady=(0,8))

        self.anim_canvas = tk.Canvas(bottom, width=300, height=80, bg="black", highlightthickness=0)
        self.anim_canvas.grid(row=0, column=0, padx=8, pady=8)
        self._anim_ball = self.anim_canvas.create_oval(10, 30, 30, 50, outline=ACCENT, fill="")
        self.fps_label = ctk.CTkLabel(bottom, text="FPS: --", font=("Consolas", 11))
        self.fps_label.grid(row=1, column=0, padx=8, pady=2)

        self.cps_btn = ctk.CTkButton(bottom, text="Start CPS Test", command=self._toggle_cps)
        self.cps_btn.grid(row=0, column=1, padx=8, pady=8)
        self.cps_display = ctk.CTkLabel(bottom, text="CPS: --", font=("Consolas", 11))
        self.cps_display.grid(row=1, column=1, padx=8, pady=2)

        # Right side
        self.specs_box = ctk.CTkTextbox(right, height=180, font=MONO_FONT)
        self.specs_box.pack(fill="x", padx=12, pady=(8,8))
        self._update_specs_box()

        self.cpu_label = ctk.CTkLabel(right, text="CPU: -- %", font=MONO_FONT)
        self.cpu_label.pack(fill="x", padx=12, pady=4)
        self.ram_label = ctk.CTkLabel(right, text="RAM: -- %", font=MONO_FONT)
        self.ram_label.pack(fill="x", padx=12, pady=4)

        # Boost
        boost_frame = ctk.CTkFrame(right)
        boost_frame.pack(fill="x", padx=12, pady=8)
        ctk.CTkLabel(boost_frame, text="RUN SPEED BOOST", font=("Consolas", 13, "bold")).pack(pady=6)
        ctk.CTkButton(boost_frame, text="Clear Temp Files", command=self._boost_clear_temp).pack(fill="x", padx=8, pady=4)
        ctk.CTkButton(boost_frame, text="Flush DNS", command=self._boost_flush_dns).pack(fill="x", padx=8, pady=4)

        # Pointer speed (with Apply)
        pointer_frame = ctk.CTkFrame(right)
        pointer_frame.pack(fill="x", padx=12, pady=8)
        ctk.CTkLabel(pointer_frame, text="MOUSE POINTER", font=("Consolas", 13, "bold")).pack(pady=6)
        self.speed_var = ctk.CTkSlider(pointer_frame, from_=1, to=20, number_of_steps=19, command=self._update_speed_label)
        self.speed_var.set(10)
        self.speed_var.pack(fill="x", padx=8, pady=4)
        self.speed_label = ctk.CTkLabel(pointer_frame, text="Pointer speed (preview): 10", font=MONO_FONT)
        self.speed_label.pack(padx=8, pady=2)
        self.apply_speed_btn = ctk.CTkButton(pointer_frame, text="Apply Speed", command=self._apply_pointer_speed)
        self.apply_speed_btn.pack(fill="x", padx=8, pady=4)
        self.reset_speed_btn = ctk.CTkButton(pointer_frame, text="Reset to Default (10)", command=self._reset_pointer_speed)
        self.reset_speed_btn.pack(fill="x", padx=8, pady=4)

        # Cursor change
        cursor_frame = ctk.CTkFrame(right)
        cursor_frame.pack(fill="x", padx=12, pady=8)
        self.cursor_btn = ctk.CTkButton(cursor_frame, text="Choose Cursor (.cur)", command=self._choose_cursor_file)
        self.cursor_btn.pack(fill="x", padx=8, pady=4)
        self.cursor_reset = ctk.CTkButton(cursor_frame, text="Reset App Cursor", command=self._reset_cursor)
        self.cursor_reset.pack(fill="x", padx=8, pady=4)

        # Console actions
        action_frame = ctk.CTkFrame(right)
        action_frame.pack(fill="x", padx=12, pady=8)
        ctk.CTkButton(action_frame, text="Type System Summary", command=self._demo_type_specs).pack(fill="x", padx=8, pady=4)
        ctk.CTkButton(action_frame, text="Clear Console", command=self._clear_console).pack(fill="x", padx=8, pady=4)

        self.bind_all("<Button-1>", self._global_click_handler)

    # -------------------------
    # Console + typing
    # -------------------------
    def _append_console(self, text):
        self.console.config(state="normal")
        self.console.insert("end", text)
        self.console.see("end")
        self.console.config(state="disabled")

    def _typing_effect(self, text, delay=0.01):
        def worker():
            with self._typing_lock:
                self.console.config(state="normal")
                for ch in text:
                    self.console.insert("end", ch)
                    self.console.see("end")
                    self.console.update_idletasks()
                    time.sleep(delay)
                self.console.insert("end", "\n")
                self.console.config(state="disabled")
        threading.Thread(target=worker, daemon=True).start()

    def _demo_type_specs(self):
        specs = get_system_specs()
        header = f"System summary @ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        lines = header + "\n".join([f"{k}: {v}" for k, v in specs.items()])
        self._typing_effect(lines, delay=0.008)

    def _clear_console(self):
        self.console.config(state="normal")
        self.console.delete("1.0", "end")
        self.console.config(state="disabled")

    # -------------------------
    # FPS animation
    # -------------------------
    def _animate_canvas(self):
        x1, y1, x2, y2 = self.anim_canvas.coords(self._anim_ball)
        width = int(self.anim_canvas["width"])
        vx = 3
        if not hasattr(self, "_ball_dir"):
            self._ball_dir = 1
        if x2 >= width - 5:
            self._ball_dir = -1
        if x1 <= 5:
            self._ball_dir = 1
        self.anim_canvas.move(self._anim_ball, vx * self._ball_dir, 0)

        now = time.time()
        self._fps_timestamps.append(now)
        if len(self._fps_timestamps) >= 2:
            dt = self._fps_timestamps[-1] - self._fps_timestamps[0]
            fps = len(self._fps_timestamps) / dt if dt > 0 else 0
        else:
            fps = 0
        self.fps_label.configure(text=f"FPS: {fps:.1f}")

        self.after(16, self._animate_canvas)

    # -------------------------
    # CPS tester
    # -------------------------
    def _toggle_cps(self):
        if not self._cps_running:
            self._cps_running = True
            self.cps_btn.configure(text="Stop CPS Test")
            self._click_timestamps.clear()
            threading.Thread(target=self._cps_monitor, daemon=True).start()
            self._typing_effect("CPS test started. Click anywhere.")
        else:
            self._cps_running = False
            self.cps_btn.configure(text="Start CPS Test")
            self.cps_display.configure(text="CPS: --")
            self._typing_effect("CPS test stopped.")

    def _global_click_handler(self, event):
        if self._cps_running:
            now = time.time()
            self._click_timestamps.append(now)

    def _cps_monitor(self):
        while self._cps_running:
            now = time.time()
            while self._click_timestamps and now - self._click_timestamps[0] > 1.0:
                self._click_timestamps.popleft()
            cps = len(self._click_timestamps)
            self.cps_display.configure(text=f"CPS: {cps}")
            time.sleep(0.08)

    # -------------------------
    # Boost actions
    # -------------------------
    def _boost_clear_temp(self):
        threading.Thread(target=lambda: self._typing_effect(clear_temp_files()), daemon=True).start()

    def _boost_flush_dns(self):
        threading.Thread(target=lambda: self._typing_effect(flush_dns()), daemon=True).start()

    # -------------------------
    # Pointer controls
    # -------------------------
    def _update_speed_label(self, val):
        val_i = int(float(val))
        self.speed_label.configure(text=f"Pointer speed (preview): {val_i}")

    def _apply_pointer_speed(self):
        val_i = int(float(self.speed_var.get()))
        success, msg = set_mouse_speed(val_i)
        if success:
            self._typing_effect(f"Mouse speed applied: {val_i}")
        else:
            self._typing_effect(f"Failed: {msg}")

    def _reset_pointer_speed(self):
        self.speed_var.set(10)
        success, msg = set_mouse_speed(10)
        if success:
            self._typing_effect("Mouse speed reset to default (10).")
        else:
            self._typing_effect(f"Failed: {msg}")

    def _choose_cursor_file(self):
        f = filedialog.askopenfilename(title="Choose .cur file", filetypes=[("Cursor files", "*.cur *.ani *.ico"), ("All files", "*.*")])
        if not f:
            return
        try:
            cursor_name = "@" + f
            self.configure(cursor=cursor_name)
            self._typing_effect(f"App cursor changed to {os.path.basename(f)}")
        except Exception as e:
            self._typing_effect(f"Failed to set cursor: {e}")

    def _reset_cursor(self):
        try:
            self.configure(cursor="")
            self._typing_effect("App cursor reset.")
        except Exception as e:
            self._typing_effect(f"Failed: {e}")

    # -------------------------
    # Background updates
    # -------------------------
    def _update_specs_box(self):
        specs = get_system_specs()
        text = "\n".join([f"{k}: {v}" for k,v in specs.items()])
        self.specs_box.delete("0.0", "end")
        self.specs_box.insert("0.0", text)

    def _start_background_updates(self):
        def updater():
            while True:
                cpu = psutil.cpu_percent(interval=1)
                mem = psutil.virtual_memory().percent
                self.cpu_label.configure(text=f"CPU: {cpu:.0f} %")
                self.ram_label.configure(text=f"RAM: {mem:.0f} %")
        threading.Thread(target=updater, daemon=True).start()

# -------------------------
# Run App
# -------------------------
if __name__ == "__main__":
    app = DeltaDOSApp()
    app._typing_effect("DELTA DOS v1.0 | Build 2025-01.", delay=0.01)
    app._typing_effect("This version of the DELTA-DOS is used by an average user. >Not for Coders< Thank you!", delay = 0.01)
    app.mainloop()
