import tkinter as tk
from tkinter import filedialog, messagebox
import shutil, os
from datetime import datetime
YAMAHA_BLUE="#003087";YAMAHA_RED="#E60026";BG="#f4f6fb";WHITE="#ffffff";TEXT="#1a1a2e";MUTED="#6b7280";BORDER="#e5e7eb"
class BackupFrame(tk.Frame):
    def __init__(self,parent,db_path,refresh_cb):
        super().__init__(parent,bg=BG);self.db_path=db_path;self.refresh_cb=refresh_cb;self._build()
    def _build(self):
        tk.Label(self,text="Backup & Restore",font=("Segoe UI",13,"bold"),bg=BG,fg=YAMAHA_BLUE).pack(anchor="w",pady=(0,16))
        bc=tk.Frame(self,bg=WHITE,highlightbackground=BORDER,highlightthickness=1,padx=24,pady=20);bc.pack(fill="x",pady=(0,14))
        tk.Label(bc,text="💾  Backup Data",font=("Segoe UI",12,"bold"),bg=WHITE,fg=YAMAHA_BLUE).pack(anchor="w")
        tk.Label(bc,text="Save a copy of all your billing data to USB / Google Drive / Desktop.",font=("Segoe UI",10),bg=WHITE,fg=MUTED,wraplength=500,justify="left").pack(anchor="w",pady=(6,14))
        tk.Button(bc,text="📁  Choose Location & Backup Now",font=("Segoe UI",11,"bold"),bg=YAMAHA_RED,fg=WHITE,relief="flat",padx=18,pady=10,cursor="hand2",command=self._backup).pack(anchor="w")
        self.last_backup_var=tk.StringVar(value="No backup taken yet")
        tk.Label(bc,textvariable=self.last_backup_var,font=("Segoe UI",9),bg=WHITE,fg=MUTED).pack(anchor="w",pady=(10,0))
        rc=tk.Frame(self,bg=WHITE,highlightbackground=BORDER,highlightthickness=1,padx=24,pady=20);rc.pack(fill="x",pady=(0,14))
        tk.Label(rc,text="🔄  Restore Data",font=("Segoe UI",12,"bold"),bg=WHITE,fg=YAMAHA_BLUE).pack(anchor="w")
        tk.Label(rc,text="⚠️  Warning: Restoring will REPLACE all current data with the backup file.",font=("Segoe UI",10),bg=WHITE,fg="#b45309",wraplength=500,justify="left").pack(anchor="w",pady=(6,14))
        tk.Button(rc,text="📂  Select Backup File & Restore",font=("Segoe UI",11,"bold"),bg=YAMAHA_BLUE,fg=WHITE,relief="flat",padx=18,pady=10,cursor="hand2",command=self._restore).pack(anchor="w")
        tc=tk.Frame(self,bg="#fffbeb",highlightbackground="#fde68a",highlightthickness=1,padx=20,pady=16);tc.pack(fill="x")
        tk.Label(tc,text="💡  Backup Tips",font=("Segoe UI",11,"bold"),bg="#fffbeb",fg="#92400e").pack(anchor="w",pady=(0,8))
        for tip in ["✅ Take backup daily or after every billing session","✅ Keep backup in USB drive AND Google Drive","✅ Backup file name includes date — don't rename it","✅ If PC crashes, install software on new PC and restore backup"]:
            tk.Label(tc,text=tip,font=("Segoe UI",10),bg="#fffbeb",fg="#78350f").pack(anchor="w",pady=1)
    def _backup(self):
        if not os.path.exists(self.db_path): messagebox.showerror("Error","Database file not found!"); return
        ts=datetime.now().strftime("%Y%m%d_%H%M%S")
        dest=filedialog.asksaveasfilename(defaultextension=".db",initialfile=f"yamaha_backup_{ts}.db",filetypes=[("Database Backup","*.db"),("All files","*.*")],title="Save Backup As")
        if not dest: return
        try:
            shutil.copy2(self.db_path,dest)
            self.last_backup_var.set(f"Last backup: {dest}")
            messagebox.showinfo("Backup Success",f"✅ Backup saved!\n\nLocation: {dest}")
        except Exception as e: messagebox.showerror("Backup Failed",f"Error: {e}")
    def _restore(self):
        src=filedialog.askopenfilename(filetypes=[("Database Backup","*.db"),("All files","*.*")],title="Select Backup File")
        if not src: return
        if not messagebox.askyesno("Confirm Restore","⚠️ This will REPLACE all current data!\nAre you sure?"): return
        try:
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path,self.db_path.replace(".db",f"_before_restore_{datetime.now().strftime('%Y%m%d%H%M%S')}.db"))
            shutil.copy2(src,self.db_path)
            messagebox.showinfo("Restore Success","✅ Restored! Please restart the application.")
        except Exception as e: messagebox.showerror("Restore Failed",f"Error: {e}")
    def refresh(self): pass
