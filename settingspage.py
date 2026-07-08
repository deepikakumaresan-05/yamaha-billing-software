import tkinter as tk
from tkinter import messagebox
from db import get_db, get_setting, set_setting, hash_password
YAMAHA_BLUE="#003087";YAMAHA_RED="#E60026";BG="#f4f6fb";WHITE="#ffffff";TEXT="#1a1a2e";MUTED="#6b7280";BORDER="#e5e7eb"
class SettingsFrame(tk.Frame):
    def __init__(self,parent,db_path,refresh_cb):
        super().__init__(parent,bg=BG);self.db_path=db_path;self.refresh_cb=refresh_cb;self._build()
    def _build(self):
        tk.Label(self,text="Settings",font=("Segoe UI",13,"bold"),bg=BG,fg=YAMAHA_BLUE).pack(anchor="w",pady=(0,14))
        sc=tk.Frame(self,bg=WHITE,highlightbackground=BORDER,highlightthickness=1,padx=24,pady=18);sc.pack(fill="x",pady=(0,14))
        tk.Label(sc,text="🏪  Showroom Details",font=("Segoe UI",11,"bold"),bg=WHITE,fg=YAMAHA_BLUE).pack(anchor="w",pady=(0,12))
        self.fields={}
        fd=[("shop_name","Showroom Name"),("dealer_code","Dealer Code"),("address","Address"),("phone1","Phone 1"),("phone2","Phone 2"),("email","Email"),("gstin","GSTIN"),("state","State Code")]
        grid=tk.Frame(sc,bg=WHITE);grid.pack(fill="x")
        for i,(key,label) in enumerate(fd):
            r,c=divmod(i,2)
            tk.Label(grid,text=label,font=("Segoe UI",8,"bold"),bg=WHITE,fg=MUTED).grid(row=r*2,column=c,sticky="w",padx=(0,20),pady=(8,0))
            var=tk.StringVar(value=get_setting(self.db_path,key,""));self.fields[key]=var
            tk.Entry(grid,textvariable=var,font=("Segoe UI",11),width=34,relief="flat",bg="#f3f4f6",highlightbackground=BORDER,highlightthickness=1).grid(row=r*2+1,column=c,sticky="w",padx=(0,20),ipady=6)
        tk.Button(sc,text="💾  Save Shop Details",font=("Segoe UI",11,"bold"),bg=YAMAHA_RED,fg=WHITE,relief="flat",padx=18,pady=8,cursor="hand2",command=self._save_shop).pack(anchor="w",pady=(16,0))
        pc=tk.Frame(self,bg=WHITE,highlightbackground=BORDER,highlightthickness=1,padx=24,pady=18);pc.pack(fill="x",pady=(0,14))
        tk.Label(pc,text="🔐  Change Password",font=("Segoe UI",11,"bold"),bg=WHITE,fg=YAMAHA_BLUE).pack(anchor="w",pady=(0,12))
        pg=tk.Frame(pc,bg=WHITE);pg.pack(fill="x");self.pw_fields={}
        for i,(key,label) in enumerate([("current","Current Password"),("new","New Password"),("confirm","Confirm New Password")]):
            tk.Label(pg,text=label,font=("Segoe UI",8,"bold"),bg=WHITE,fg=MUTED).grid(row=0,column=i,sticky="w",padx=(0,20))
            var=tk.StringVar();self.pw_fields[key]=var
            tk.Entry(pg,textvariable=var,show="●",font=("Segoe UI",11),width=22,relief="flat",bg="#f3f4f6",highlightbackground=BORDER,highlightthickness=1).grid(row=1,column=i,sticky="w",padx=(0,20),ipady=6)
        tk.Button(pc,text="🔑  Update Password",font=("Segoe UI",11,"bold"),bg=YAMAHA_BLUE,fg=WHITE,relief="flat",padx=18,pady=8,cursor="hand2",command=self._change_password).pack(anchor="w",pady=(14,0))
        ic=tk.Frame(self,bg="#f0f7ff",highlightbackground="#bfdbfe",highlightthickness=1,padx=24,pady=16);ic.pack(fill="x")
        tk.Label(ic,text="ℹ️  Application Info",font=("Segoe UI",11,"bold"),bg="#f0f7ff",fg=YAMAHA_BLUE).pack(anchor="w",pady=(0,8))
        for line in ["Software: Yamaha Showroom Billing System","Version: 2.0","Database: SQLite (yamaha_showroom.db)","Default Login: admin / admin123","Built with: Python + Tkinter"]:
            tk.Label(ic,text=line,font=("Segoe UI",10),bg="#f0f7ff",fg="#1e3a8a").pack(anchor="w",pady=1)
    def _save_shop(self):
        for key,var in self.fields.items(): set_setting(self.db_path,key,var.get())
        messagebox.showinfo("Saved","✅ Shop details saved successfully!")
    def _change_password(self):
        current=self.pw_fields["current"].get(); new=self.pw_fields["new"].get(); confirm=self.pw_fields["confirm"].get()
        if not current or not new: messagebox.showerror("Error","Fill all password fields!"); return
        if new!=confirm: messagebox.showerror("Error","New passwords don't match!"); return
        if len(new)<6: messagebox.showerror("Error","Password must be at least 6 characters!"); return
        with get_db(self.db_path) as conn:
            row=conn.execute("SELECT password_hash FROM users WHERE username='admin'").fetchone()
            if not row or row["password_hash"]!=hash_password(current): messagebox.showerror("Error","Current password is wrong!"); return
            conn.execute("UPDATE users SET password_hash=? WHERE username='admin'",(hash_password(new),))
        for var in self.pw_fields.values(): var.set("")
        messagebox.showinfo("Success","✅ Password changed successfully!")
    def refresh(self):
        for key,var in self.fields.items(): var.set(get_setting(self.db_path,key,""))
