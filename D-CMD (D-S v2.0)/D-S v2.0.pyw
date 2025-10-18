import customtkinter as ctk
import psutil
import time
import threading
import os
import subprocess
from datetime import datetime
from tkinter import END

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

class DeltaDOSApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DELTA DOS - Neon Terminal")
        self.geometry("1000x600")
        self.configure(fg_color="#000000")
        self.iconbitmap(r'icon.ico')

        # current working directory
        self.cwd = os.getcwd()

        # Title
        self.title_label = ctk.CTkLabel(
            self, text="Δ DELTA DOS SYSTEM v2.0",
            font=("Consolas", 28, "bold"), text_color="#00FF00"
        )
        self.title_label.pack(pady=15)

        # Output box
        self.output_box = ctk.CTkTextbox(
            self, width=900, height=400, corner_radius=10,
            font=("Consolas", 16), fg_color="#000000", text_color="#00FF00"
        )
        self.output_box.pack(pady=10)
        self.output_box.insert("end", "Booting DELTA DOS...\n")
        self.output_box.configure(state="disabled")

        # Command frame
        self.command_frame = ctk.CTkFrame(self, fg_color="#000000")
        self.command_frame.pack(pady=10)

        self.prompt_label = ctk.CTkLabel(
            self.command_frame, text=f"{self.cwd}>",
            font=("Consolas", 18, "bold"), text_color="#00FF00"
        )
        self.prompt_label.pack(side="left", padx=5)

        self.command_entry = ctk.CTkEntry(
            self.command_frame, width=700, corner_radius=10,
            font=("Consolas", 18), fg_color="#001100", text_color="#00FF00",
            border_width=2, border_color="#00FF00"
        )
        self.command_entry.pack(side="left", padx=5)
        self.command_entry.bind("<Return>", self.process_command)

        self.cursor_label = ctk.CTkLabel(
            self.command_frame, text="_",
            font=("Consolas", 18, "bold"), text_color="#00FF00"
        )
        self.cursor_label.pack(side="left")
        self._blink_cursor()

        # System info
        self.info_frame = ctk.CTkFrame(self, fg_color="#000000")
        self.info_frame.pack(pady=10)

        self.cpu_label = ctk.CTkLabel(
            self.info_frame, text="CPU: 0%",
            font=("Consolas", 14), text_color="#00FF00"
        )
        self.cpu_label.pack(side="left", padx=20)

        self.ram_label = ctk.CTkLabel(
            self.info_frame, text="RAM: 0%",
            font=("Consolas", 14), text_color="#00FF00"
        )
        self.ram_label.pack(side="left", padx=20)

        self.time_label = ctk.CTkLabel(
            self.info_frame, text="TIME: --:--:--",
            font=("Consolas", 14), text_color="#00FF00"
        )
        self.time_label.pack(side="left", padx=20)

        self.update_system_info()

    # Typing animation
    def _typing_effect(self, text, delay=0.01):
        self.output_box.configure(state="normal")
        for char in text:
            self.output_box.insert(END, char)
            self.output_box.update()
            time.sleep(delay)
        self.output_box.insert(END, "\n")
        self.output_box.configure(state="disabled")
        self.output_box.see("end")

    # Process command
    def process_command(self, event=None):
        cmd = self.command_entry.get().strip()
        self.command_entry.delete(0, END)
        self.output_box.configure(state="normal")
        self.output_box.insert("end", f"{self.cwd}> {cmd}\n")
        self.output_box.configure(state="disabled")

        threading.Thread(target=self.execute_command, args=(cmd,), daemon=True).start()

    def execute_command(self, cmd):
        if not cmd:
            return

        parts = cmd.split()
        main_cmd = parts[0].lower() if parts else ""

        # Basic commands
        if main_cmd == "help":
            help_text = (
                "Available commands:\n"
                "HELP, TIME, DATE, SYSINFO, CLEAR, EXIT\n"
                "CD <dir> - Change directory\n"
                "DIR / LS - List files\n"
                "CMD <command> - Execute raw Windows CMD command\n"
            )
            self._typing_effect(help_text)

        elif main_cmd == "time":
            self._typing_effect(f"Current Time: {datetime.now().strftime('%H:%M:%S')}")

        elif main_cmd == "date":
            self._typing_effect(f"Today’s Date: {datetime.now().strftime('%d-%m-%Y')}")

        elif main_cmd == "sysinfo":
            info = f"CPU: {psutil.cpu_percent()}%, RAM: {psutil.virtual_memory().percent}%"
            self._typing_effect(info)

        elif main_cmd == "clear":
            self.output_box.configure(state="normal")
            self.output_box.delete("1.0", END)
            self.output_box.configure(state="disabled")

        elif main_cmd == "exit":
            self._typing_effect("Shutting down DELTA DOS...")
            time.sleep(1)
            self.destroy()

        # Directory commands
        elif main_cmd == "cd":
            if len(parts) == 1:
                self._typing_effect(self.cwd)
            else:
                path = parts[1]
                try:
                    new_path = os.path.abspath(os.path.join(self.cwd, path))
                    os.chdir(new_path)
                    self.cwd = new_path
                    self.prompt_label.configure(text=f"{self.cwd}>")
                    self._typing_effect(f"Changed directory to {self.cwd}")
                except Exception as e:
                    self._typing_effect(f"Error: {e}")

        elif main_cmd in ["dir", "ls"]:
            try:
                items = os.listdir(self.cwd)
                output = "\n".join(items)
                self._typing_effect(output if output else "(empty directory)")
            except Exception as e:
                self._typing_effect(f"Error listing directory: {e}")

        # Raw CMD execution
        elif main_cmd == "cmd":
            if len(parts) < 2:
                self._typing_effect("Usage: CMD <command>")
            else:
                raw_cmd = " ".join(parts[1:])
                self.run_system_command(raw_cmd)

        else:
            # Fallback: try executing any CMD command directly
            self.run_system_command(cmd)

    # Run actual CMD commands
    def run_system_command(self, command):
        try:
            process = subprocess.Popen(
                command, shell=True, cwd=self.cwd,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            out, err = process.communicate()
            result = out + err if (out or err) else "(no output)"
            self._typing_effect(result)
        except Exception as e:
            self._typing_effect(f"Error executing command: {e}")

    # Blinking cursor
    def _blink_cursor(self):
        def blink():
            while True:
                current = self.cursor_label.cget("text")
                self.cursor_label.configure(text="" if current == "_" else "_")
                time.sleep(0.6)
        threading.Thread(target=blink, daemon=True).start()

    # System info updater
    def update_system_info(self):
        def update():
            while True:
                cpu = psutil.cpu_percent(interval=1)
                mem = psutil.virtual_memory().percent
                now = datetime.now().strftime("%H:%M:%S")
                self.cpu_label.configure(text=f"CPU: {cpu:.0f}%")
                self.ram_label.configure(text=f"RAM: {mem:.0f}%")
                self.time_label.configure(text=f"TIME: {now}")
        threading.Thread(target=update, daemon=True).start()

# Run app
if __name__ == "__main__":
    app = DeltaDOSApp()
    app._typing_effect("DELTA DOS v2.0 | Build 2025-10", delay=0.01)
    app._typing_effect("Initializing core modules...", delay=0.01)
    app._typing_effect("Welcome, Commander. Type HELP to begin.", delay=0.01)
    app.mainloop()
