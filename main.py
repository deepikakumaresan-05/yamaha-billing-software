import tkinter as tk
from tkinter import ttk
import os
from datetime import date
from db import init_db, get_db, fmt_currency
from login import LoginWindow

import sys
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "yamaha_showroom.db")
YAMAHA_BLUE="#003087";YAMAHA_RED="#E60026";BG="#f4f6fb";WHITE="#ffffff";TEXT="#1a1a2e";MUTED="#6b7280";BORDER="#e5e7eb"

class InvoicesFrame(tk.Frame):
    def __init__(self,parent,db_path,refresh_cb):
        super().__init__(parent,bg=BG);self.db_path=db_path;self.refresh_cb=refresh_cb;self._build()
    def _build(self):
        tk.Label(self,text="All Invoices",font=("Segoe UI",13,"bold"),bg=BG,fg=YAMAHA_BLUE).pack(anchor="w",pady=(0,10))
        sf=tk.Frame(self,bg=BG);sf.pack(fill="x",pady=(0,12));self.sum_vars={}
        for key,label,color in [("total","Total Bills",TEXT),("bike","Bike Sales",YAMAHA_RED),("acc","Accessories",YAMAHA_BLUE),("svc","Services","#16a34a"),("revenue","Total Revenue",YAMAHA_BLUE)]:
            f=tk.Frame(sf,bg=WHITE,highlightbackground=BORDER,highlightthickness=1);f.pack(side="left",expand=True,fill="x",padx=(0,8))
            tk.Label(f,text=label,font=("Segoe UI",8,"bold"),bg=WHITE,fg=MUTED).pack(anchor="w",padx=10,pady=(8,0))
            var=tk.StringVar(value="0");self.sum_vars[key]=var
            tk.Label(f,textvariable=var,font=("Segoe UI",16,"bold"),bg=WHITE,fg=color).pack(anchor="w",padx=10,pady=(2,8))
        sb=tk.Frame(self,bg=BG);sb.pack(fill="x",pady=(0,8))
        tk.Label(sb,text="🔍",font=("Segoe UI",12),bg=BG).pack(side="left")
        self.search_var=tk.StringVar();self.search_var.trace_add("write",lambda *a:self.refresh())
        tk.Entry(sb,textvariable=self.search_var,font=("Segoe UI",11),width=30,relief="flat",bg=WHITE,highlightbackground=BORDER,highlightthickness=1).pack(side="left",padx=8,ipady=5)
        cols=("Invoice No","Type","Customer","Mobile","Date","Amount","Payment")
        self.tree=ttk.Treeview(self,columns=cols,show="headings",height=18)
        for c,w in zip(cols,[110,100,160,120,100,110,110]): self.tree.heading(c,text=c);self.tree.column(c,width=w)
        self.tree.tag_configure("bike",background="#fff5f5");self.tree.tag_configure("acc",background="#f0f7ff");self.tree.tag_configure("svc",background="#f0fff4")
        self.tree.bind("<Double-1>", self._open_invoice)
        vsb=ttk.Scrollbar(self,orient="vertical",command=self.tree.yview);self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right",fill="y");self.tree.pack(fill="both",expand=True);self.refresh()
    def refresh(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        search=self.search_var.get().lower()
        with get_db(self.db_path) as conn:
            rows=conn.execute("SELECT * FROM invoices ORDER BY created_at DESC").fetchall()
        tm={"bike":"🏍 Bike","acc":"🧰 Accessories","svc":"🔧 Service"}
        total=bike=acc=svc=0;rev=0.0
        for r in rows:
            if search and search not in (r["customer_name"] or "").lower() and search not in (r["invoice_no"] or "").lower() and search not in (r["mobile"] or "").lower(): continue
            self.tree.insert("","end",tags=(r["type"],),values=(r["invoice_no"],tm.get(r["type"],r["type"]),r["customer_name"] or "",r["mobile"] or "",r["invoice_date"] or "",fmt_currency(r["grand_total"]),r["payment_mode"] or ""))
            total+=1;rev+=float(r["grand_total"] or 0)
            if r["type"]=="bike": bike+=1
            elif r["type"]=="acc": acc+=1
            elif r["type"]=="svc": svc+=1
        self.sum_vars["total"].set(str(total));self.sum_vars["bike"].set(str(bike));self.sum_vars["acc"].set(str(acc));self.sum_vars["svc"].set(str(svc));self.sum_vars["revenue"].set(fmt_currency(rev))
    def _open_invoice(self, event):
        selected = self.tree.focus()
        if not selected:
            return
        values = self.tree.item(selected, "values")
        if not values:
            return
        invoice_no = values[0]
        from print_invoice import print_invoice
        print_invoice(self.db_path, invoice_no)

class DashboardFrame(tk.Frame):
    def __init__(self,parent,db_path,refresh_cb):
        super().__init__(parent,bg=BG);self.db_path=db_path;self.refresh_cb=refresh_cb;self._build()
    def _build(self):
        tk.Label(self,text="Dashboard",font=("Segoe UI",13,"bold"),bg=BG,fg=YAMAHA_BLUE).pack(anchor="w",pady=(0,12))
        sf=tk.Frame(self,bg=BG);sf.pack(fill="x",pady=(0,16));self.stat_vars={}
        for key,label,color in [("bills","Total Bills",YAMAHA_BLUE),("revenue","Total Revenue","#16a34a"),("gst","GST Collected","#b45309"),("avg","Avg Bill Value",YAMAHA_BLUE),("stock","Stock Items",TEXT),("customers","Customers",YAMAHA_RED)]:
            f=tk.Frame(sf,bg=WHITE,highlightbackground=BORDER,highlightthickness=1);f.pack(side="left",expand=True,fill="x",padx=(0,10))
            tk.Label(f,text=label,font=("Segoe UI",9,"bold"),bg=WHITE,fg=MUTED).pack(anchor="w",padx=14,pady=(12,0))
            var=tk.StringVar(value="0");self.stat_vars[key]=var
            tk.Label(f,textvariable=var,font=("Segoe UI",20,"bold"),bg=WHITE,fg=color).pack(anchor="w",padx=14,pady=(2,12))
        rc=tk.Frame(self,bg=WHITE,highlightbackground=BORDER,highlightthickness=1);rc.pack(fill="both",expand=True)
        tk.Label(rc,text="Recent Transactions",font=("Segoe UI",11,"bold"),bg=WHITE,fg=YAMAHA_BLUE).pack(anchor="w",padx=16,pady=(12,8))
        tk.Frame(rc,bg=BORDER,height=1).pack(fill="x",padx=16)
        self.recent_frame=tk.Frame(rc,bg=WHITE);self.recent_frame.pack(fill="both",expand=True,padx=16,pady=8)
        self.refresh()
    def refresh(self):
        with get_db(self.db_path) as conn:
            invs=conn.execute("SELECT * FROM invoices").fetchall()
            stock_count=conn.execute("SELECT COUNT(*) FROM service_stock").fetchone()[0]
            cust_count=conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
            recent=conn.execute("SELECT * FROM invoices ORDER BY created_at DESC LIMIT 10").fetchall()
        total=len(invs);rev=sum(float(i["grand_total"]) for i in invs)
        gst=sum(float(i["gst_amt"]) for i in invs);avg=rev/total if total else 0
        self.stat_vars["bills"].set(str(total));self.stat_vars["revenue"].set(fmt_currency(rev))
        self.stat_vars["gst"].set(fmt_currency(gst));self.stat_vars["avg"].set(fmt_currency(avg))
        self.stat_vars["stock"].set(str(stock_count));self.stat_vars["customers"].set(str(cust_count))
        for w in self.recent_frame.winfo_children(): w.destroy()
        tm={"bike":"🏍 Bike","acc":"🧰 Acc","svc":"🔧 Service"}
        for inv in recent:
            row=tk.Frame(self.recent_frame,bg=WHITE);row.pack(fill="x",pady=3)
            tk.Label(row,text=inv["invoice_no"],font=("Segoe UI",11,"bold"),bg=WHITE,fg=TEXT,width=12,anchor="w").pack(side="left")
            tk.Label(row,text=tm.get(inv["type"],""),font=("Segoe UI",10),bg=WHITE,fg=MUTED,width=14,anchor="w").pack(side="left")
            tk.Label(row,text=inv["customer_name"] or "",font=("Segoe UI",10),bg=WHITE,fg=TEXT,width=22,anchor="w").pack(side="left")
            tk.Label(row,text=fmt_currency(inv["grand_total"]),font=("Segoe UI",11,"bold"),bg=WHITE,fg=YAMAHA_BLUE).pack(side="right")
            tk.Label(row,text=inv["invoice_date"] or "",font=("Segoe UI",9),bg=WHITE,fg=MUTED,width=12,anchor="e").pack(side="right")
            tk.Frame(self.recent_frame,bg=BORDER,height=1).pack(fill="x")

class YamahaApp(tk.Tk):
    def __init__(self,role="admin"):
        super().__init__();self.role=role
        self.title("Yamaha Showroom Billing System")
        self.geometry("1280x720");self.minsize(1100,640);self.configure(bg=BG)
        self.db_path=DB_PATH;self._build_ui();self.show_frame("bike")

    def _build_ui(self):
        from bike_billing import BikeBillingFrame
        from accessories_billing import AccessoriesBillingFrame
        from service_billing import ServiceBillingFrame
        from stock_management import StockFrame
        from customer_history import CustomerHistoryFrame
        from reports import ReportsFrame
        from backup import BackupFrame
        from settings_page import SettingsFrame

        self.sidebar=tk.Frame(self,bg=YAMAHA_BLUE,width=220);self.sidebar.pack(side="left",fill="y");self.sidebar.pack_propagate(False)
        logo=tk.Frame(self.sidebar,bg=YAMAHA_BLUE,pady=18);logo.pack(fill="x")
        tk.Label(logo,text="🏍",font=("Segoe UI",30),bg=YAMAHA_BLUE,fg=WHITE).pack()
        tk.Label(logo,text="Y A M A H A",font=("Segoe UI",13,"bold"),bg=YAMAHA_BLUE,fg=WHITE).pack()
        tk.Label(logo,text="Showroom Billing",font=("Segoe UI",9),bg=YAMAHA_BLUE,fg="#8ba3d4").pack()
        tk.Frame(self.sidebar,bg="#1a4a9e",height=1).pack(fill="x",padx=16)
        nav=tk.Frame(self.sidebar,bg=YAMAHA_BLUE);nav.pack(fill="both",expand=True,pady=8)
        self.nav_btns={}

        def slbl(t): tk.Label(nav,text=t,font=("Segoe UI",8,"bold"),bg=YAMAHA_BLUE,fg="#6b85b8").pack(anchor="w",padx=18,pady=(12,2))
        def nbtn(key,icon,label):
            btn=tk.Button(nav,text=f"{icon}  {label}",font=("Segoe UI",11),bg=YAMAHA_BLUE,fg="#c8d4ea",bd=0,relief="flat",anchor="w",padx=18,pady=9,cursor="hand2",activebackground=YAMAHA_RED,activeforeground=WHITE,command=lambda k=key:self.show_frame(k))
            btn.pack(fill="x",padx=6,pady=1);self.nav_btns[key]=btn

        slbl("BILLING")
        nbtn("bike","🏍","New Bike Sale");nbtn("accessories","🧰","Accessories");nbtn("service","🔧","Service Billing")
        slbl("RECORDS")
        nbtn("stock","📦","Stock Management");nbtn("customers","👥","Customer History");nbtn("invoices","📄","All Invoices");nbtn("reports","📊","Monthly Reports")
        slbl("SYSTEM")
        nbtn("backup","💾","Backup & Restore");nbtn("settings","⚙️","Settings")

        footer=tk.Frame(self.sidebar,bg=YAMAHA_BLUE);footer.pack(side="bottom",fill="x",pady=10)
        tk.Frame(footer,bg="#1a4a9e",height=1).pack(fill="x",padx=16,pady=(0,8))
        self.inv_count_var=tk.StringVar(value="Total Bills: 0")
        tk.Label(footer,textvariable=self.inv_count_var,font=("Segoe UI",9),bg=YAMAHA_BLUE,fg="#6b85b8").pack(padx=18,anchor="w")

        self.main=tk.Frame(self,bg=BG);self.main.pack(side="left",fill="both",expand=True)
        topbar=tk.Frame(self.main,bg=WHITE,height=58);topbar.pack(fill="x");topbar.pack_propagate(False)
        self.topbar_title=tk.Label(topbar,text="",font=("Segoe UI",14,"bold"),bg=WHITE,fg=TEXT)
        self.topbar_title.pack(side="left",padx=24,pady=14)
        tk.Label(topbar,text=f"📅 {date.today().strftime('%d %b %Y, %A')}",font=("Segoe UI",10),bg=WHITE,fg=MUTED).pack(side="right",padx=20)
        tk.Frame(self.main,bg=BORDER,height=1).pack(fill="x")

        outer=tk.Frame(self.main,bg=BG);outer.pack(fill="both",expand=True)
        self.canvas=tk.Canvas(outer,bg=BG,highlightthickness=0)
        vsb=ttk.Scrollbar(outer,orient="vertical",command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set);vsb.pack(side="right",fill="y");self.canvas.pack(side="left",fill="both",expand=True)
        self.scroll_frame=tk.Frame(self.canvas,bg=BG)
        self._cw=self.canvas.create_window((0,0),window=self.scroll_frame,anchor="nw")
        self.scroll_frame.bind("<Configure>",lambda e:self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",lambda e:self.canvas.itemconfig(self._cw,width=e.width))
        self.canvas.bind_all("<MouseWheel>",lambda e:self.canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

        titles={"bike":"New Bike Sale","accessories":"Accessories Billing","service":"Service Billing",
                "stock":"Stock Management","customers":"Customer History","invoices":"All Invoices",
                "reports":"Monthly Reports","backup":"Backup & Restore","settings":"Settings"}
        self.titles=titles
        frame_map={"bike":BikeBillingFrame,"accessories":AccessoriesBillingFrame,"service":ServiceBillingFrame,
                   "stock":StockFrame,"customers":CustomerHistoryFrame,"invoices":InvoicesFrame,
                   "reports":ReportsFrame,"backup":BackupFrame,"settings":SettingsFrame}
        self.frames={}
        for key,cls in frame_map.items():
            try: f=cls(self.scroll_frame,self.db_path,self.refresh_count)
            except Exception as e:
                f=tk.Frame(self.scroll_frame,bg=BG)
                tk.Label(f,text=f"Error loading {key}: {e}",bg=BG,fg="red").pack(padx=20,pady=20)
            f.grid(row=0,column=0,sticky="nsew",padx=20,pady=16);f.grid_remove();self.frames[key]=f
        self.scroll_frame.grid_rowconfigure(0,weight=1);self.scroll_frame.grid_columnconfigure(0,weight=1)
        self.current=None;self.refresh_count()

    def show_frame(self,key):
        if self.current:
            self.frames[self.current].grid_remove()
            b=self.nav_btns.get(self.current)
            if b: b.config(bg=YAMAHA_BLUE,fg="#c8d4ea")
        self.frames[key].grid()
        if hasattr(self.frames[key],"refresh"): self.frames[key].refresh()
        self.current=key;self.topbar_title.config(text=self.titles.get(key,key))
        b=self.nav_btns.get(key)
        if b: b.config(bg=YAMAHA_RED,fg=WHITE)
        self.canvas.yview_moveto(0)

    def refresh_count(self):
        try:
            with get_db(self.db_path) as conn:
                c=conn.execute("SELECT COUNT(*) FROM invoices").fetchone()[0]
            self.inv_count_var.set(f"Total Bills: {c}")
        except: pass

if __name__=="__main__":
    init_db(DB_PATH)
    login=LoginWindow(DB_PATH);login.mainloop()
    if not login.logged_in: exit()
    app=YamahaApp(role=login.role);app.mainloop()
