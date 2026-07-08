import tkinter as tk
from tkinter import messagebox
from db import verify_password

YAMAHA_BLUE="#003087"; YAMAHA_RED="#E60026"; WHITE="#ffffff"; BG="#f0f4ff"

class LoginWindow(tk.Tk):
    def __init__(self, db_path):
        super().__init__()
        self.db_path=db_path; self.logged_in=False; self.role=None
        self.title("Yamaha Billing — Login")
        self.geometry("420x480"); self.resizable(False,False)
        self.configure(bg=BG); self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build(self):
        hdr=tk.Frame(self,bg=YAMAHA_BLUE,height=120); hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr,text="🏍",font=("Segoe UI",36),bg=YAMAHA_BLUE,fg=WHITE).pack(pady=(18,0))
        tk.Label(hdr,text="YAMAHA BILLING SYSTEM",font=("Segoe UI",13,"bold"),bg=YAMAHA_BLUE,fg=WHITE).pack()
        card=tk.Frame(self,bg=WHITE,padx=40,pady=30); card.pack(fill="both",expand=True,padx=30,pady=20)
        tk.Label(card,text="Welcome Back!",font=("Segoe UI",14,"bold"),bg=WHITE,fg=YAMAHA_BLUE).pack(anchor="w")
        tk.Label(card,text="Login to continue",font=("Segoe UI",10),bg=WHITE,fg="#6b7280").pack(anchor="w",pady=(2,20))
        tk.Label(card,text="USERNAME",font=("Segoe UI",8,"bold"),bg=WHITE,fg="#6b7280").pack(anchor="w")
        self.user_var=tk.StringVar(value="admin")
        tk.Entry(card,textvariable=self.user_var,font=("Segoe UI",12),relief="flat",
                 bg="#f3f4f6",highlightbackground="#e5e7eb",highlightthickness=1,
                 width=28).pack(anchor="w",pady=(4,14),ipady=8)
        tk.Label(card,text="PASSWORD",font=("Segoe UI",8,"bold"),bg=WHITE,fg="#6b7280").pack(anchor="w")
        self.pw_var=tk.StringVar()
        self.pw_entry=tk.Entry(card,textvariable=self.pw_var,font=("Segoe UI",12),show="●",
                                relief="flat",bg="#f3f4f6",highlightbackground="#e5e7eb",
                                highlightthickness=1,width=28)
        self.pw_entry.pack(anchor="w",pady=(4,20),ipady=8)
        self.pw_entry.bind("<Return>",lambda e:self._login())
        tk.Button(card,text="LOGIN →",font=("Segoe UI",11,"bold"),bg=YAMAHA_RED,fg=WHITE,
                  relief="flat",padx=20,pady=10,cursor="hand2",width=24,command=self._login).pack()
        tk.Label(card,text="Default: admin / admin123",font=("Segoe UI",8),bg=WHITE,fg="#9ca3af").pack(pady=(12,0))

    def _login(self):
        user=self.user_var.get().strip(); pw=self.pw_var.get()
        if not user or not pw: messagebox.showerror("Error","Enter username and password!"); return
        ok,role=verify_password(self.db_path,user,pw)
        if ok: self.logged_in=True; self.role=role; self.destroy()
        else: messagebox.showerror("Login Failed","Wrong username or password!"); self.pw_var.set("")

    def _on_close(self): self.logged_in=False; self.destroy()
