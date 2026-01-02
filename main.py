import tkinter as tk
from tkinter import messagebox
import pymem
import pymem.process
import threading
import time
import struct
import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class LeakedTrainer:
    def __init__(self, master):
        self.master = master
        master.title("LeakedTrainer [v2.0] - GTAIV")
        master.geometry("400x350") 
        master.configure(bg='#0a0a0a')

        self.icon_file = resource_path("icon.ico")
        if os.path.exists(self.icon_file):
            try:
               
                master.iconbitmap(self.icon_file)
            except tk.TclError:
                pass

        self.label = tk.Label(master, text="LeakedTrainer GTA IV", fg="#ff3333", bg="#0a0a0a", font=("Consolas", 14, "bold"))
        self.label.pack(pady=15)

        self.status_label = tk.Label(master, text="STATUS: STANDBY", fg="#555555", bg="#0a0a0a", font=("Consolas", 9))
        self.status_label.pack(pady=5)

        # Ammo Toggle
        self.ammo_button = tk.Button(
            master, 
            text="LOCK AMMO (99,999,999)", 
            command=self.toggle_ammo, 
            bg="#1a1a1a", 
            fg="#eee", 
            width=25,
            font=("Consolas", 10),
            relief="flat"
        )
        self.ammo_button.pack(pady=10)

        # God Mode Toggle
        self.god_button = tk.Button(
            master, 
            text="ENABLE GOD MODE", 
            command=self.toggle_god_mode, 
            bg="#1a1a1a", 
            fg="#eee", 
            width=25,
            font=("Consolas", 10),
            relief="flat"
        )
        self.god_button.pack(pady=10)

        self.pm = None
        self.ammo_enabled = False
        self.god_enabled = False

    def get_pm(self):
        if not self.pm:
            try:
                self.pm = pymem.Pymem("GTAIV.exe")
                self.status_label.config(text="STATUS: ATTACHED TO GTAIV.EXE", fg="#00ff00")
            except Exception:
                messagebox.showerror("Error", "GTAIV.exe not found!")
                return False
        return True

    def toggle_ammo(self):
        if not self.get_pm(): return
        self.ammo_enabled = not self.ammo_enabled
        if self.ammo_enabled:
            self.ammo_button.config(text="AMMO LOCKED", bg="#330000", fg="#ff3333")
            threading.Thread(target=self.inject_ammo, daemon=True).start()
        else:
            self.ammo_button.config(text="LOCK AMMO (99,999,999)", bg="#1a1a1a", fg="#eee")

    def toggle_god_mode(self):
        if not self.get_pm(): return
        self.god_enabled = not self.god_enabled
        if self.god_enabled:
            self.god_button.config(text="GOD MODE ACTIVE", bg="#003300", fg="#00ff00")
            threading.Thread(target=self.inject_god_mode, daemon=True).start()
        else:
            self.god_button.config(text="ENABLE GOD MODE", bg="#1a1a1a", fg="#eee")

    def inject_ammo(self):
        # AOB Scan for ammo instruction
        pattern = b"\x0F\xB7\x4B\x04\x8B\xF1"
        try:
            addr = self.pm.pattern_scan_all(pattern)
            if addr:
                new_mem = self.pm.allocate(128)
                # shellcode to move 99mil into [ebx+04]
                shellcode = bytearray([
                    0xC7, 0x43, 0x04, 0xFF, 0xE0, 0xF5, 0x05, 
                    0x0F, 0xB7, 0x4B, 0x04, 0x8B, 0xF1
                ])
                # Jump logic back to original code
                return_addr = addr + 6
                jmp_back = (return_addr - (new_mem + len(shellcode) + 5))
                shellcode.extend(b"\xE9" + jmp_back.to_bytes(4, 'little', signed=True))
                
                self.pm.write_bytes(new_mem, bytes(shellcode), len(shellcode))
                
                jmp_to = (new_mem - (addr + 5))
                inject = b"\xE9" + jmp_to.to_bytes(4, 'little', signed=True) + b"\x90"
                
                orig = self.pm.read_bytes(addr, 6)
                self.pm.write_bytes(addr, inject, len(inject))
                
                while self.ammo_enabled: time.sleep(1)
                
                self.pm.write_bytes(addr, orig, len(orig))
                self.pm.free(new_mem)
        except Exception as e:
            print(f"Ammo Err: {e}")

    def inject_god_mode(self):
        # Scan for the health instruction: fld dword ptr [ecx+00000E9C]
        pattern = b"\xD9\x81\x9C\x0E\x00\x00"
        try:
            addr = self.pm.pattern_scan_all(pattern)
            if addr:
                new_mem = self.pm.allocate(256)
                full_health_hex = struct.pack('f', 200.0) 
                
                shellcode = bytearray([
                    0xC7, 0x81, 0x9C, 0x0E, 0x00, 0x00, 
                ])
                shellcode.extend(full_health_hex)
                shellcode.extend([0xD9, 0x81, 0x9C, 0x0E, 0x00, 0x00])
                
                return_addr = addr + 6
                jmp_back = (return_addr - (new_mem + len(shellcode) + 5))
                shellcode.extend(b"\xE9" + jmp_back.to_bytes(4, 'little', signed=True))
                
                self.pm.write_bytes(new_mem, bytes(shellcode), len(shellcode))
                
                jmp_to = (new_mem - (addr + 5))
                inject = b"\xE9" + jmp_to.to_bytes(4, 'little', signed=True) + b"\x90"
                
                orig = self.pm.read_bytes(addr, 6)
                self.pm.write_bytes(addr, inject, len(inject))
                
                while self.god_enabled: time.sleep(1)
                
                self.pm.write_bytes(addr, orig, len(orig))
                self.pm.free(new_mem)
        except Exception as e:
            print(f"GodMode Err: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LeakedTrainer(root)
    root.mainloop()