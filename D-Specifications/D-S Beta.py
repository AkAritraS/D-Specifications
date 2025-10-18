import customtkinter as ctk
import tkinter as tk
import psutil
import platform
import time
import ctypes
import threading
from datetime import datetime

# ========== CONFIG ==========
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DOS_FONT = ("Consolas", 14)
MONO_FONT = ("Consolas", 12)

# ========== UTILS ==========
def typewrite(widget, text, delay=0.01, color="white"):
    """Typing effect inside textbox widget"""
    widget.configure(state="normal")
    for char in text + "\n":
        widget.insert("end", char, (color,))
        widget.see("end")
        widget.update()
        time.sleep(delay)
    widget.configure(state="disabled")

def set_mouse_speed(speed: int):
    """Set Windows mouse pointer speed (1–20)"""
    SPI_SETMOUSESPEED = 0x0071
    res = ctypes.windll.user32.SystemParametersInfoW(SPI_SETMOUSESPEED, 0, speed, 0)
    if not res:
        return False, ctypes.WinError()
    return True, None

def get_system_specs():
    """Return string with system specs"""
    uname = platform.uname()
    cpu = platform.processor()
    ram = round(psutil.virtual_memory().total / (1024**3), 2)
    return (
        f"System: {uname.system} {uname.release} ({uname.version})\n"
        f"Machine: {uname.machine}\n"
        f"CPU: {cpu}\n"
        f"RAM: {ram} GB\n"
    )

# ========== MAIN APP ==========
class DOSApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Delta DOS Utility")
        self.geometry("850x600")
        self.iconbitmap(r'icon.ico') 

        self._create_layout()
        self._update_stats()
        self._update_datetime()

    def _create_layout(self):
        # -------- Left Panel --------
        left_frame = ctk.CTkFrame(self)
        left_frame.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(left_frame, text="⚙ Device Stats", font=MONO_FONT).pack(pady=6)

        self.cpu_label = ctk.CTkLabel(left_frame, text="CPU: --%", font=MONO_FONT)
        self.cpu_label.pack(pady=2)
        self.ram_label = ctk.CTkLabel(left_frame, text="RAM: --%", font=MONO_FONT)
        self.ram_label.pack(pady=2)

        # Date/Time
        self.datetime_label = ctk.CTkLabel(left_frame, text="Date & Time: --", font=MONO_FONT)
        self.datetime_label.pack(pady=(20, 2))

        # Pointer Controls
        pointer_frame = ctk.CTkFrame(left_frame)
        pointer_frame.pack(pady=20, fill="x")

        ctk.CTkLabel(pointer_frame, text="🖱 Pointer Controls", font=MONO_FONT).pack(pady=6)

        self.speed_var = ctk.CTkSlider(pointer_frame, from_=1, to=20, number_of_steps=19, command=self._update_speed_label)
        self.speed_var.set(10)
        self.speed_var.pack(fill="x", padx=8, pady=6)

        self.speed_label = ctk.CTkLabel(pointer_frame, text="Pointer speed (preview): 10", font=MONO_FONT)
        self.speed_label.pack(padx=8, pady=(0, 4))

        self.apply_speed_btn = ctk.CTkButton(pointer_frame, text="Apply Speed", command=self._apply_pointer_speed)
        self.apply_speed_btn.pack(fill="x", padx=8, pady=(0, 6))

        self.reset_speed_btn = ctk.CTkButton(pointer_frame, text="Reset Default", fg_color="red", command=self._reset_pointer_speed)
        self.reset_speed_btn.pack(fill="x", padx=8, pady=(0, 6))

        # -------- Right Panel (DOS) --------
        right_frame = ctk.CTkFrame(self)
        right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.console = tk.Text(right_frame, bg="black", fg="white", insertbackground="white", font=DOS_FONT, wrap="word", state="disabled")
        self.console.pack(fill="both", expand=True)

        # Color tags
        self.console.tag_config("white", foreground="white")
        self.console.tag_config("cyan", foreground="cyan")
        self.console.tag_config("green", foreground="lightgreen")
        self.console.tag_config("yellow", foreground="yellow")

        # Input bar
        input_frame = ctk.CTkFrame(right_frame)
        input_frame.pack(fill="x")
        ctk.CTkLabel(input_frame, text=">", font=MONO_FONT).pack(side="left", padx=4)
        self.command_entry = ctk.CTkEntry(input_frame, placeholder_text="Enter command...")
        self.command_entry.pack(side="left", fill="x", expand=True, padx=4, pady=4)
        self.command_entry.bind("<Return>", self._process_command)

        # Welcome text
        threading.Thread(target=lambda: typewrite(self.console, "Welcome to Delta DOS Utility!", color="cyan"), daemon=True).start()

    # ----- Stats -----
    def _update_stats(self):
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory().percent
        self.cpu_label.configure(text=f"CPU: {cpu}%")
        self.ram_label.configure(text=f"RAM: {ram}%")
        self.after(1000, self._update_stats)

    def _update_datetime(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.datetime_label.configure(text=f"Date & Time: {now}")
        self.after(1000, self._update_datetime)

    # ----- Pointer -----
    def _update_speed_label(self, val):
        val_i = int(float(val))
        self.speed_label.configure(text=f"Pointer speed (preview): {val_i}")

    def _apply_pointer_speed(self):
        val_i = int(float(self.speed_var.get()))
        success, msg = set_mouse_speed(val_i)
        if success:
            threading.Thread(target=lambda: typewrite(self.console, f"Mouse speed applied: {val_i}", color="green"), daemon=True).start()
        else:
            threading.Thread(target=lambda: typewrite(self.console, f"Failed to set mouse speed: {msg}", color="yellow"), daemon=True).start()

    def _reset_pointer_speed(self):
        self.speed_var.set(10)
        self._apply_pointer_speed()

    # ----- Commands -----
    def _process_command(self, event):
        cmd = self.command_entry.get().strip()
        self.command_entry.delete(0, "end")
        if not cmd:
            return
        threading.Thread(target=lambda: self._execute_command(cmd), daemon=True).start()

    def _execute_command(self, cmd):
        typewrite(self.console, f"> {cmd}", color="cyan")
        if cmd == "/spec":
            specs = get_system_specs()
            typewrite(self.console, specs, color="green")
        elif cmd == "/cls":
            self.console.configure(state="normal")
            self.console.delete("1.0", "end")
            self.console.configure(state="disabled")
        else:
            typewrite(self.console, f"Unknown command: {cmd}", color="yellow")

# ========== RUN ==========
if __name__ == "__main__":
    app = DOSApp()
    app.mainloop()
