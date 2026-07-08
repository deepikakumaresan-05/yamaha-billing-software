import tkinter as tk
from tkinter import ttk

YAMAHA_BLUE="#003087"; YAMAHA_RED="#E60026"
BG="#f4f6fb"; WHITE="#ffffff"; TEXT="#1a1a2e"; MUTED="#6b7280"; BORDER="#e5e7eb"

def card(parent, title=None, icon=""):
    outer=tk.Frame(parent,bg=WHITE,highlightbackground=BORDER,highlightthickness=1)
    outer.pack(fill="x",pady=(0,14))
    if title:
        hdr=tk.Frame(outer,bg=WHITE); hdr.pack(fill="x",padx=16,pady=(12,0))
        tk.Label(hdr,text=f"{icon}  {title}" if icon else title,
                 font=("Segoe UI",10,"bold"),bg=WHITE,fg=MUTED).pack(anchor="w")
        tk.Frame(outer,bg=BORDER,height=1).pack(fill="x",padx=16,pady=(8,0))
    inner=tk.Frame(outer,bg=WHITE,padx=16,pady=12); inner.pack(fill="x")
    return inner

def labeled_entry(parent, label, row, col, colspan=1, default="", width=22, readonly=False):
    frame=tk.Frame(parent,bg=WHITE)
    frame.grid(row=row,column=col,columnspan=colspan,sticky="w",padx=(0,16),pady=5)
    tk.Label(frame,text=label,font=("Segoe UI",8,"bold"),bg=WHITE,fg=MUTED).pack(anchor="w")
    var=tk.StringVar(value=default)
    e=ttk.Entry(frame,textvariable=var,width=width,state="readonly" if readonly else "normal")
    e.pack(anchor="w")
    return var, e

def labeled_combo(parent, label, row, col, values, default=None, width=22):
    frame=tk.Frame(parent,bg=WHITE)
    frame.grid(row=row,column=col,sticky="w",padx=(0,16),pady=5)
    tk.Label(frame,text=label,font=("Segoe UI",8,"bold"),bg=WHITE,fg=MUTED).pack(anchor="w")
    var=tk.StringVar(value=default or (values[0] if values else ""))
    cb=ttk.Combobox(frame,textvariable=var,values=values,width=width-2,state="readonly")
    cb.pack(anchor="w")
    return var, cb

def primary_button(parent, text, command, color=YAMAHA_RED):
    return tk.Button(parent,text=text,font=("Segoe UI",11,"bold"),
                     bg=color,fg=WHITE,relief="flat",padx=18,pady=8,
                     cursor="hand2",command=command,
                     activebackground=YAMAHA_BLUE,activeforeground=WHITE)

def outline_button(parent, text, command):
    return tk.Button(parent,text=text,font=("Segoe UI",10),
                     bg=WHITE,fg=TEXT,relief="flat",padx=14,pady=7,
                     cursor="hand2",command=command,
                     highlightbackground=BORDER,highlightthickness=1)

class ItemTable(tk.Frame):
    def __init__(self, parent, columns, on_change=None, bg=WHITE):
        super().__init__(parent,bg=bg)
        self.columns=columns; self.on_change=on_change
        self.rows=[]; self._row_seq=0; self._build_header()

    def _build_header(self):
        hdr=tk.Frame(self,bg="#eef2ff"); hdr.pack(fill="x")
        tk.Label(hdr,text="#",width=3,font=("Segoe UI",8,"bold"),
                 bg="#eef2ff",fg=YAMAHA_BLUE,anchor="w").grid(row=0,column=0,padx=4,pady=4)
        for i,(h,w,_) in enumerate(self.columns):
            tk.Label(hdr,text=h,width=w,font=("Segoe UI",8,"bold"),
                     bg="#eef2ff",fg=YAMAHA_BLUE,anchor="w").grid(row=0,column=i+1,padx=4,pady=4)
        tk.Label(hdr,text="Amount",width=10,font=("Segoe UI",8,"bold"),
                 bg="#eef2ff",fg=YAMAHA_BLUE,anchor="e").grid(row=0,column=len(self.columns)+1,padx=4)
        tk.Label(hdr,text="",width=3,bg="#eef2ff").grid(row=0,column=len(self.columns)+2)
        self.body=tk.Frame(self,bg=WHITE); self.body.pack(fill="x")

    def add_row(self, defaults=None):
        self._row_seq+=1
        rf=tk.Frame(self.body,bg=WHITE,highlightbackground=BORDER,highlightthickness=1)
        rf.pack(fill="x",pady=1)
        tk.Label(rf,text=str(len(self.rows)+1),width=3,bg=WHITE,fg=MUTED,
                 font=("Segoe UI",9)).grid(row=0,column=0,padx=4,pady=3)
        row_vars=[]; amt_var=tk.StringVar(value="\u20b90.00")
        for i,(_, w, typ) in enumerate(self.columns):
            init=(defaults[i] if defaults and i<len(defaults) else
                  "1" if typ=="qty" else ("0" if typ=="number" else ""))
            var=tk.StringVar(value=init); row_vars.append(var)
            e=ttk.Entry(rf,textvariable=var,width=w)
            e.grid(row=0,column=i+1,padx=3,pady=3)
            if typ in ("qty","number"):
                var.trace_add("write",lambda *a,rv=row_vars,av=amt_var: self._recalc(rv,av))
        tk.Label(rf,textvariable=amt_var,width=10,bg=WHITE,fg=YAMAHA_BLUE,
                 font=("Segoe UI",9,"bold"),anchor="e").grid(row=0,column=len(self.columns)+1,padx=4)
        def _del(frame=rf,entry=(rf,row_vars+[amt_var])):
            frame.destroy()
            self.rows=[r for r in self.rows if r[0] is not frame]
            if self.on_change: self.on_change()
        tk.Button(rf,text="✕",bg=WHITE,fg="#ccc",relief="flat",font=("Segoe UI",9),
                  cursor="hand2",command=_del).grid(row=0,column=len(self.columns)+2,padx=2)
        self.rows.append((rf,row_vars+[amt_var]))
        self._recalc(row_vars,amt_var)

    def _recalc(self, row_vars, amt_var):
        qty=rate=0.0
        for i,(_,_,typ) in enumerate(self.columns):
            try:
                if typ=="qty":    qty =float(row_vars[i].get() or 1)
                if typ=="number": rate=float(row_vars[i].get() or 0)
            except ValueError: pass
        amt_var.set(f"\u20b9{qty*rate:,.2f}")
        if self.on_change: self.on_change()

    def get_items(self):
        items=[]
        for _,rvs in self.rows:
            vals=[v.get() for v in rvs[:-1]]
            qty=rate=0.0
            for i,(_,_,typ) in enumerate(self.columns):
                try:
                    if typ=="qty":    qty =float(vals[i] or 1)
                    if typ=="number": rate=float(vals[i] or 0)
                except ValueError: pass
            items.append({"vals":vals,"qty":qty,"rate":rate,"amount":qty*rate})
        return items

    def get_total(self):
        return sum(it["amount"] for it in self.get_items())

    def clear(self):
        for rf,_ in self.rows: rf.destroy()
        self.rows=[]; self._row_seq=0
        if self.on_change: self.on_change()
