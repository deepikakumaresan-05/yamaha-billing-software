import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from db import get_db, fmt_currency
YAMAHA_BLUE="#003087";YAMAHA_RED="#E60026";BG="#f4f6fb";WHITE="#ffffff";TEXT="#1a1a2e";MUTED="#6b7280";BORDER="#e5e7eb"
MONTHS=["January","February","March","April","May","June","July","August","September","October","November","December"]
class ReportsFrame(tk.Frame):
    def __init__(self,parent,db_path,refresh_cb):
        super().__init__(parent,bg=BG);self.db_path=db_path;self.refresh_cb=refresh_cb;self._build()
    def _build(self):
        top=tk.Frame(self,bg=BG);top.pack(fill="x",pady=(0,12))
        tk.Label(top,text="Monthly Reports",font=("Segoe UI",13,"bold"),bg=BG,fg=YAMAHA_BLUE).pack(side="left")
        tk.Button(top,text="🔄 Generate",font=("Segue UI",10,"bold"),bg=YAMAHA_RED,fg=WHITE,relief="flat",padx=14,pady=6,cursor="hand2",command=self.refresh).pack(side="right")
        ff=tk.Frame(self,bg=WHITE,highlightbackground=BORDER,highlightthickness=1,padx=16,pady=12);ff.pack(fill="x",pady=(0,12))
        tk.Label(ff,text="Month:",font=("Segui UI",10),bg=WHITE,fg=MUTED).pack(side="left")
        self.month_var=tk.StringVar(value=MONTHS[date.today().month-1])
        ttk.Combobox(ff,textvariable=self.month_var,values=MONTHS,width=14,state="readonly").pack(side="left",padx=8)
        tk.Label(ff,text="Year:",font=("Segoe UI",10),bg=WHITE,fg=MUTED).pack(side="left",padx=(10,0))
        self.year_var=tk.StringVar(value=str(date.today().year))
        ttk.Combobox(ff,textvariable=self.year_var,values=[str(y) for y in range(2023,date.today().year+2)],width=8,state="readonly").pack(side="left",padx=8)
        sf=tk.Frame(self,bg=BG);sf.pack(fill="x",pady=(0,12));self.stat_vars={}
        for key,label,color in [("bike_count","Bikes Sold",YAMAHA_RED),("bike_rev","Bike Revenue",YAMAHA_BLUE),("acc_count","Acc Bills","#7c3aed"),("acc_rev","Acc Revenue","#7c3aed"),("svc_count","Services","#16a34a"),("svc_rev","Svc Revenue","#16a34a"),("total_rev","Total Revenue",YAMAHA_BLUE),("total_gst","GST Collected","#b45309")]:
            f=tk.Frame(sf,bg=WHITE,highlightbackground=BORDER,highlightthickness=1);f.pack(side="left",expand=True,fill="x",padx=(0,8))
            tk.Label(f,text=label,font=("Segoe UI",8,"bold"),bg=WHITE,fg=MUTED).pack(anchor="w",padx=10,pady=(8,0))
            var=tk.StringVar(value="0");self.stat_vars[key]=var
            tk.Label(f,textvariable=var,font=("Segoe UI",14,"bold"),bg=WHITE,fg=color).pack(anchor="w",padx=10,pady=(2,8))
        nb=ttk.Notebook(self);nb.pack(fill="both",expand=True)
        inv_f=tk.Frame(nb,bg=WHITE);nb.add(inv_f,text="  All Invoices  ")
        ic=("Invoice No","Type","Customer","Date","Amount","GST","Payment")
        self.inv_tree=ttk.Treeview(inv_f,columns=ic,show="headings",height=14)
        for c,w in zip(ic,[110,80,160,100,110,100,100]): self.inv_tree.heading(c,text=c);self.inv_tree.column(c,width=w)
        sb=ttk.Scrollbar(inv_f,orient="vertical",command=self.inv_tree.yview);self.inv_tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right",fill="y");self.inv_tree.pack(fill="both",expand=True)
        exp_f=tk.Frame(nb,bg=WHITE);nb.add(exp_f,text="  Expenses  ");self._build_expenses(exp_f)
        bal_f=tk.Frame(nb,bg=WHITE);nb.add(bal_f,text="  Balance Sheet  ")
        self.bal_inner=tk.Frame(bal_f,bg=WHITE,padx=30,pady=20);self.bal_inner.pack(fill="both",expand=True)
        self.refresh()
    def _build_expenses(self,parent):
        top=tk.Frame(parent,bg=WHITE,pady=10,padx=14);top.pack(fill="x")
        tk.Button(top,text="+ Add Expense",font=("Segoe UI",10,"bold"),bg=YAMAHA_RED,fg=WHITE,relief="flat",padx=12,pady=5,cursor="hand2",command=self._add_expense).pack(side="right")
        ec=("Date","Category","Description","Amount","Payment")
        self.exp_tree=ttk.Treeview(parent,columns=ec,show="headings",height=12)
        for c,w in zip(ec,[100,120,220,110,100]): self.exp_tree.heading(c,text=c);self.exp_tree.column(c,width=w)
        esb=ttk.Scrollbar(parent,orient="vertical",command=self.exp_tree.yview);self.exp_tree.configure(yscrollcommand=esb.set)
        esb.pack(side="right",fill="y");self.exp_tree.pack(fill="both",expand=True,padx=8,pady=8)
        self.exp_total=tk.StringVar(value="Total Expenses: ₹0.00")
        tk.Label(parent,textvariable=self.exp_total,font=("Segoe UI",11,"bold"),bg=WHITE,fg=YAMAHA_RED).pack(anchor="e",padx=16,pady=6)
    def _add_expense(self):
        dlg=tk.Toplevel(self);dlg.title("Add Expense");dlg.geometry("400x360");dlg.configure(bg=WHITE);dlg.grab_set()
        f=tk.Frame(dlg,bg=WHITE,padx=24,pady=16);f.pack(fill="both",expand=True)
        tk.Label(f,text="Add Expense",font=("Segoe UI",13,"bold"),bg=WHITE,fg=YAMAHA_BLUE).pack(anchor="w",pady=(0,16))
        cats=["Rent","Salary","Electricity","Maintenance","Marketing","Fuel","Other"];fields={}
        def row(label,widget_fn):
            tk.Label(f,text=label,font=("Segoe UI",8,"bold"),bg=WHITE,fg=MUTED).pack(anchor="w",pady=(6,0))
            var=tk.StringVar();widget_fn(var);fields[label]=var
        row("Date",lambda v:(tk.Entry(f,textvariable=v,font=("Segoe UI",11),relief="flat",bg="#f3f4f6",highlightbackground=BORDER,highlightthickness=1).pack(fill="x",ipady=5) or v.set(str(date.today()))))
        row("Category",lambda v:(ttk.Combobox(f,textvariable=v,values=cats,state="readonly",font=("Segoe UI",11)).pack(fill="x") or v.set(cats[0])))
        row("Description",lambda v:tk.Entry(f,textvariable=v,font=("Segoe UI",11),relief="flat",bg="#f3f4f6",highlightbackground=BORDER,highlightthickness=1).pack(fill="x",ipady=5))
        row("Amount (₹)",lambda v:(tk.Entry(f,textvariable=v,font=("Segoe UI",11),relief="flat",bg="#f3f4f6",highlightbackground=BORDER,highlightthickness=1).pack(fill="x",ipady=5) or v.set("0")))
        row("Payment Mode",lambda v:(ttk.Combobox(f,textvariable=v,values=["Cash","UPI","Card","Bank Transfer"],state="readonly").pack(fill="x") or v.set("Cash")))
        def save():
            try: amt=float(fields["Amount (₹)"].get() or 0)
            except: messagebox.showerror("Error","Enter valid amount!",parent=dlg);return
            with get_db(self.db_path) as conn:
                conn.execute("INSERT INTO expenses(expense_date,category,description,amount,payment_mode) VALUES(?,?,?,?,?)",
                             (fields["Date"].get(),fields["Category"].get(),fields["Description"].get(),amt,fields["Payment Mode"].get()))
            dlg.destroy();self.refresh()
        tk.Button(dlg,text="💾 Save",font=("Segoe UI",11,"bold"),bg=YAMAHA_RED,fg=WHITE,relief="flat",padx=16,pady=8,cursor="hand2",command=save).pack(anchor="w",padx=24)
    def refresh(self):
        mn=MONTHS.index(self.month_var.get())+1;yr=self.year_var.get();prefix=f"{yr}-{str(mn).zfill(2)}"
        with get_db(self.db_path) as conn:
            invs=conn.execute("SELECT * FROM invoices WHERE invoice_date LIKE ? ORDER BY invoice_date DESC",(f"{prefix}%",)).fetchall()
            exps=conn.execute("SELECT * FROM expenses WHERE expense_date LIKE ? ORDER BY expense_date DESC",(f"{prefix}%",)).fetchall()
        bikes=[i for i in invs if i["type"]=="bike"];accs=[i for i in invs if i["type"]=="acc"];svcs=[i for i in invs if i["type"]=="svc"]
        total_rev=sum(float(i["grand_total"]) for i in invs);total_gst=sum(float(i["gst_amt"]) for i in invs);total_exp=sum(float(e["amount"]) for e in exps)
        self.stat_vars["bike_count"].set(str(len(bikes)));self.stat_vars["bike_rev"].set(fmt_currency(sum(float(i["grand_total"]) for i in bikes)))
        self.stat_vars["acc_count"].set(str(len(accs)));self.stat_vars["acc_rev"].set(fmt_currency(sum(float(i["grand_total"]) for i in accs)))
        self.stat_vars["svc_count"].set(str(len(svcs)));self.stat_vars["svc_rev"].set(fmt_currency(sum(float(i["grand_total"]) for i in svcs)))
        self.stat_vars["total_rev"].set(fmt_currency(total_rev));self.stat_vars["total_gst"].set(fmt_currency(total_gst))
        for row in self.inv_tree.get_children(): self.inv_tree.delete(row)
        tm={"bike":"Bike Sale","acc":"Accessories","svc":"Service"}
        for inv in invs: self.inv_tree.insert("","end",values=(inv["invoice_no"],tm.get(inv["type"],inv["type"]),inv["customer_name"],inv["invoice_date"],fmt_currency(inv["grand_total"]),fmt_currency(inv["gst_amt"]),inv["payment_mode"] or ""))
        for row in self.exp_tree.get_children(): self.exp_tree.delete(row)
        for exp in exps: self.exp_tree.insert("","end",values=(exp["expense_date"],exp["category"],exp["description"],fmt_currency(exp["amount"]),exp["payment_mode"]))
        self.exp_total.set(f"Total Expenses: {fmt_currency(total_exp)}")
        for w in self.bal_inner.winfo_children(): w.destroy()
        profit=total_rev-total_exp
        tk.Label(self.bal_inner,text=f"Balance Sheet — {self.month_var.get()} {yr}",font=("Segoe UI",13,"bold"),bg=WHITE,fg=YAMAHA_BLUE).pack(anchor="w",pady=(0,16))
        for label,value,color in [("INCOME",None,None),("Bike Sales Revenue",fmt_currency(sum(float(i["grand_total"]) for i in bikes)),"#16a34a"),("Accessories Revenue",fmt_currency(sum(float(i["grand_total"]) for i in accs)),"#16a34a"),("Service Revenue",fmt_currency(sum(float(i["grand_total"]) for i in svcs)),"#16a34a"),("GST Collected",fmt_currency(total_gst),"#b45309"),("TOTAL INCOME",fmt_currency(total_rev),"#16a34a"),("","",None),("EXPENSES",None,None),("Total Expenses",fmt_currency(total_exp),YAMAHA_RED),("","",None),("NET PROFIT / LOSS",fmt_currency(profit),"#16a34a" if profit>=0 else YAMAHA_RED)]:
            if label in("INCOME","EXPENSES"):
                tk.Label(self.bal_inner,text=label,font=("Segoe UI",10,"bold"),bg=WHITE,fg=MUTED).pack(anchor="w",pady=(12,2))
                tk.Frame(self.bal_inner,bg=BORDER,height=1).pack(fill="x")
            elif label=="":
                pass
            else:
                rf=tk.Frame(self.bal_inner,bg=WHITE);rf.pack(fill="x",pady=3)
                bold="bold" if label in("TOTAL INCOME","NET PROFIT / LOSS") else "normal"
                size=12 if label in("TOTAL INCOME","NET PROFIT / LOSS") else 11
                tk.Label(rf,text=label,font=("Segoe UI",size,bold),bg=WHITE,fg=TEXT).pack(side="left")
                tk.Label(rf,text=value,font=("Segoe UI",size,"bold"),bg=WHITE,fg=color).pack(side="right")
                if label=="TOTAL INCOME": tk.Frame(self.bal_inner,bg=YAMAHA_BLUE,height=2).pack(fill="x",pady=4)
