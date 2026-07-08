import tkinter as tk
from tkinter import ttk
from db import get_db, fmt_currency
YAMAHA_BLUE="#003087";YAMAHA_RED="#E60026";BG="#f4f6fb";WHITE="#ffffff";TEXT="#1a1a2e";MUTED="#6b7280";BORDER="#e5e7eb"
class CustomerHistoryFrame(tk.Frame):
    def __init__(self,parent,db_path,refresh_cb):
        super().__init__(parent,bg=BG);self.db_path=db_path;self.refresh_cb=refresh_cb;self._build()
    def _build(self):
        tk.Label(self,text="Customer History",font=("Segoe UI",13,"bold"),bg=BG,fg=YAMAHA_BLUE).pack(anchor="w",pady=(0,10))
        sf=tk.Frame(self,bg=BG);sf.pack(fill="x",pady=(0,10))
        tk.Label(sf,text="🔍 Search by Name / Mobile:",font=("Segoe UI",10),bg=BG,fg=MUTED).pack(side="left")
        self.search_var=tk.StringVar();self.search_var.trace_add("write",lambda *a:self._search())
        tk.Entry(sf,textvariable=self.search_var,font=("Segoe UI",12),width=32,relief="flat",bg=WHITE,highlightbackground=BORDER,highlightthickness=1).pack(side="left",padx=10,ipady=6)
        pane=tk.PanedWindow(self,orient="horizontal",bg=BG,sashwidth=6);pane.pack(fill="both",expand=True)
        left=tk.Frame(pane,bg=WHITE,highlightbackground=BORDER,highlightthickness=1);pane.add(left,width=320)
        tk.Label(left,text="Customers",font=("Segoe UI",10,"bold"),bg=YAMAHA_BLUE,fg=WHITE).pack(fill="x",ipady=6)
        cc=("Name","Mobile","Vehicle")
        self.cust_tree=ttk.Treeview(left,columns=cc,show="headings",height=20)
        for c,w in zip(cc,[130,110,100]): self.cust_tree.heading(c,text=c);self.cust_tree.column(c,width=w)
        csb=ttk.Scrollbar(left,orient="vertical",command=self.cust_tree.yview);self.cust_tree.configure(yscrollcommand=csb.set)
        csb.pack(side="right",fill="y");self.cust_tree.pack(fill="both",expand=True)
        self.cust_tree.bind("<<TreeviewSelect>>",self._show_history)
        right=tk.Frame(pane,bg=BG);pane.add(right)
        dc=tk.Frame(right,bg=WHITE,highlightbackground=BORDER,highlightthickness=1);dc.pack(fill="x",pady=(0,10))
        dg=tk.Frame(dc,bg=WHITE,padx=16,pady=12);dg.pack(fill="x");self.detail_vars={}
        for i,(key,label) in enumerate([("name","Name"),("mobile","Mobile"),("vehicle_no","Vehicle No"),("vehicle_model","Model"),("email","Email"),("address","Address")]):
            r,c=divmod(i,2)
            tk.Label(dg,text=label,font=("Segoe UI",8,"bold"),bg=WHITE,fg=MUTED).grid(row=r*2,column=c,sticky="w",padx=(0,20),pady=(4,0))
            var=tk.StringVar(value="—");self.detail_vars[key]=var
            tk.Label(dg,textvariable=var,font=("Segoe UI",10),bg=WHITE,fg=TEXT).grid(row=r*2+1,column=c,sticky="w",padx=(0,20))
        tk.Label(right,text="Invoice History",font=("Segoe UI",10,"bold"),bg=BG,fg=YAMAHA_BLUE).pack(anchor="w",pady=(0,4))
        ic=("Invoice No","Type","Date","Vehicle","Total","Payment")
        self.inv_tree=ttk.Treeview(right,columns=ic,show="headings",height=12)
        for c,w in zip(ic,[100,80,100,100,100,90]): self.inv_tree.heading(c,text=c);self.inv_tree.column(c,width=w)
        isb=ttk.Scrollbar(right,orient="vertical",command=self.inv_tree.yview);self.inv_tree.configure(yscrollcommand=isb.set)
        isb.pack(side="right",fill="y");self.inv_tree.pack(fill="both",expand=True)
        self.hist_summary=tk.StringVar(value="Select a customer to view history")
        tk.Label(right,textvariable=self.hist_summary,font=("Segoe UI",10),bg=BG,fg=MUTED).pack(anchor="w",pady=(6,0))
        self._load_customers()
    def _load_customers(self,search=""):
        for row in self.cust_tree.get_children(): self.cust_tree.delete(row)
        with get_db(self.db_path) as conn:
            if search:
                rows=conn.execute("SELECT * FROM customers WHERE name LIKE ? OR mobile LIKE ? ORDER BY name",(f"%{search}%",f"%{search}%")).fetchall()
            else:
                rows=conn.execute("SELECT * FROM customers ORDER BY name").fetchall()
        for r in rows: self.cust_tree.insert("","end",iid=r["id"],values=(r["name"] or "",r["mobile"] or "",r["vehicle_no"] or ""))
    def _search(self): self._load_customers(self.search_var.get())
    def _show_history(self,event):
        sel=self.cust_tree.focus()
        if not sel: return
        with get_db(self.db_path) as conn:
            cust=conn.execute("SELECT * FROM customers WHERE id=?",(sel,)).fetchone()
            invs=conn.execute("SELECT * FROM invoices WHERE mobile=? ORDER BY invoice_date DESC",(cust["mobile"],)).fetchall()
        for key in self.detail_vars: self.detail_vars[key].set(cust[key] or "—")
        for row in self.inv_tree.get_children(): self.inv_tree.delete(row)
        total_spent=0
        tm={"bike":"🏍 Bike","acc":"🧰 Acc","svc":"🔧 Service"}
        for inv in invs:
            self.inv_tree.insert("","end",values=(inv["invoice_no"],tm.get(inv["type"],inv["type"]),inv["invoice_date"],inv["vehicle_no"] or "—",fmt_currency(inv["grand_total"]),inv["payment_mode"] or ""))
            total_spent+=float(inv["grand_total"] or 0)
        self.hist_summary.set(f"Total Visits: {len(invs)}  |  Total Spent: {fmt_currency(total_spent)}")
    def refresh(self): self._load_customers(self.search_var.get())
