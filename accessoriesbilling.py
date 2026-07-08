import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from db import get_db, next_invoice_no, fmt_currency, upsert_customer
from widgets import card, labeled_entry, labeled_combo, primary_button, outline_button
from print_invoice import print_invoice
from stock_management import init_service_stock_table, deduct_stock

YAMAHA_BLUE="#003087"; YAMAHA_RED="#E60026"; BG="#f4f6fb"; WHITE="#ffffff"; MUTED="#6b7280"; BORDER="#e5e7eb"
GST_RATES=["18","12","28","5","0"]
PAYMENT_MODES=["Cash","UPI","Card","Online Transfer","Cheque"]

class AccessoriesBillingFrame(tk.Frame):
    def __init__(self, parent, db_path, refresh_cb):
        super().__init__(parent,bg=BG)
        self.db_path=db_path; self.refresh_cb=refresh_cb
        self.last_invoice=None; self.item_rows=[]
        init_service_stock_table(self.db_path); self._build()

    def _build(self):
        c1=card(self,"Customer Details","👤"); g=tk.Frame(c1,bg=WHITE); g.pack(fill="x")
        self.cname,_=labeled_entry(g,"Customer Name *",0,0,width=28)
        self.mobile,_=labeled_entry(g,"Mobile",0,1,width=22)
        self.vehno,_=labeled_entry(g,"Vehicle Number",0,2,width=22)
        self.inv_date,_=labeled_entry(g,"Invoice Date",1,0,default=str(date.today()),width=18)
        self.paymode,_=labeled_combo(g,"Payment Mode",1,1,PAYMENT_MODES,width=20)
        self.gst_rate,_=labeled_combo(g,"GST Rate",1,2,GST_RATES,default="18",width=14)
        self.gst_rate.trace_add("write",lambda *a:self._calc())

        c2=card(self,"Accessories / Parts List","🧰")

        # Single grid frame for header + data rows
        self.items_grid=tk.Frame(c2,bg=WHITE)
        self.items_grid.pack(fill="x")

        col_conf=[("no",30),("name",230),("hsn",80),("qty",55),("rate",80),("tax",65),("amt",80),("del",30)]
        for i,(_,w) in enumerate(col_conf):
            self.items_grid.grid_columnconfigure(i,minsize=w,weight=0)

        # Header row = row 0
        hdr_labels=["#","Item Name","HSN Code","Qty","Rate ₹","Tax","Amount",""]
        for i,lbl in enumerate(hdr_labels):
            tk.Label(self.items_grid,text=lbl,font=("Segoe UI",8,"bold"),
                     bg="#eef2ff",fg=YAMAHA_BLUE,anchor="w").grid(
                         row=0,column=i,sticky="nsew",padx=4,pady=5)
        self.items_grid.grid_rowconfigure(0,minsize=28)

        tk.Button(c2,text="+ Add Item",font=("Segoe UI",10),
                  bg="#eef2ff",fg=YAMAHA_BLUE,relief="flat",padx=12,pady=5,
                  cursor="hand2",command=self._add_item_row).pack(anchor="w",pady=(4,0))

        c3=card(self,"Summary","₹"); g3=tk.Frame(c3,bg=WHITE); g3.pack(fill="x")
        self.discount,_=labeled_entry(g3,"Discount (₹)",0,0,default="0",width=18)
        self.discount.trace_add("write",lambda *a:self._calc())
        tf=tk.Frame(c3,bg="#f8faff",highlightbackground="#dde3f0",highlightthickness=1)
        tf.pack(fill="x",pady=(10,0)); self.t_vars={}
        for label,key,color in [("Subtotal","sub","#1a1a2e"),("Discount","disc","#16a34a"),
            ("CGST","cgst","#b45309"),("SGST","sgst","#b45309"),("Grand Total","grand","#003087")]:
            row=tk.Frame(tf,bg="#f8faff"); row.pack(fill="x",padx=16,pady=3)
            bold="bold" if key=="grand" else "normal"; size=11 if key=="grand" else 10
            tk.Label(row,text=label,font=("Segoe UI",size,bold),bg="#f8faff",fg=MUTED).pack(side="left")
            var=tk.StringVar(value="₹0.00"); self.t_vars[key]=var
            tk.Label(row,textvariable=var,font=("Segoe UI",size,bold),bg="#f8faff",fg=color).pack(side="right")
            if key=="disc": tk.Frame(tf,bg="#dde3f0",height=1).pack(fill="x",padx=8)

        bf=tk.Frame(self,bg=BG); bf.pack(fill="x",pady=8)
        primary_button(bf,"✔  Generate Invoice",self._generate).pack(side="left",padx=(0,8))
        outline_button(bf,"🖨  Print Last Invoice",self._print).pack(side="left",padx=(0,8))
        outline_button(bf,"↺  Clear",self._clear).pack(side="left")
        self._add_item_row()

    def _get_stock_map(self):
        with get_db(self.db_path) as conn:
            rows=conn.execute("SELECT * FROM service_stock ORDER BY item_name").fetchall()
        sm={}
        for r in rows:
            qty=float(r["quantity"] or 0)
            label=f"{r['item_name']}  [Stock: {qty} {r['unit'] or ''}]"
            sm[label]=r
        return sm

    def _add_item_row(self):
        sm=self._get_stock_map(); labels=["-- Select Item --"]+list(sm.keys())
        row_num=len(self.item_rows)+1

        tk.Label(self.items_grid,text=str(row_num),bg=WHITE,fg=MUTED,
                 font=("Segoe UI",9)).grid(row=row_num,column=0,padx=4,pady=3,sticky="w")

        sel_var=tk.StringVar(value=labels[0])
        sel_cb=ttk.Combobox(self.items_grid,textvariable=sel_var,values=labels,state="normal")
        sel_cb.grid(row=row_num,column=1,padx=3,pady=3,sticky="w")

        hsn_var=tk.StringVar()
        hsn_e=tk.Entry(self.items_grid,textvariable=hsn_var,width=9,relief="flat",
                       bg="#f3f4f6",highlightbackground=BORDER,highlightthickness=1)
        hsn_e.grid(row=row_num,column=2,padx=3,pady=3,sticky="w")

        qty_var=tk.StringVar(value="1")
        qty_e=tk.Entry(self.items_grid,textvariable=qty_var,width=5,relief="flat",
                       bg="#f3f4f6",highlightbackground=BORDER,highlightthickness=1)
        qty_e.grid(row=row_num,column=3,padx=3,pady=3,sticky="w")

        rate_var=tk.StringVar(value="0")
        rate_e=tk.Entry(self.items_grid,textvariable=rate_var,width=8,relief="flat",
                        bg="#f3f4f6",highlightbackground=BORDER,highlightthickness=1)
        rate_e.grid(row=row_num,column=4,padx=3,pady=3,sticky="w")

        tax_var=tk.StringVar(value="0.00")
        tax_lbl=tk.Label(self.items_grid,textvariable=tax_var,bg=WHITE,fg="#b45309",
                 font=("Segoe UI",9),anchor="e")
        tax_lbl.grid(row=row_num,column=5,padx=3,pady=3,sticky="w")

        amt_var=tk.StringVar(value="₹0.00")
        amt_lbl=tk.Label(self.items_grid,textvariable=amt_var,bg=WHITE,fg=YAMAHA_BLUE,
                 font=("Segoe UI",9,"bold"),anchor="e")
        amt_lbl.grid(row=row_num,column=6,padx=3,pady=3,sticky="w")

        rd={"row":row_num,"sel":sel_var,"hsn":hsn_var,"qty":qty_var,"rate":rate_var,
            "tax":tax_var,"amt":amt_var,"stock_map":sm,"stock_id":None,
            "widgets":[sel_cb,hsn_e,qty_e,rate_e,tax_lbl,amt_lbl]}

        def on_select(*a,r=rd):
            lbl=r["sel"].get(); sm2=r["stock_map"]
            if lbl in sm2:
                item=sm2[lbl]; r["hsn"].set(item["hsn_code"] or "")
                r["rate"].set(str(item["selling_price"] or 0)); r["stock_id"]=item["id"]
            self._calc()
        sel_cb.bind("<<ComboboxSelected>>",on_select)
        qty_var.trace_add("write",lambda *a:self._calc())
        rate_var.trace_add("write",lambda *a:self._calc())

        def del_row(r=rd):
            for w in r["widgets"]: w.grid_forget()
            self.item_rows.remove(r); self._calc()

        del_btn=tk.Button(self.items_grid,text="✕",bg=WHITE,fg="#ccc",relief="flat",
                          font=("Segoe UI",9),cursor="hand2",command=del_row)
        del_btn.grid(row=row_num,column=7,padx=2,pady=3,sticky="w")
        rd["widgets"].append(del_btn)
        self.item_rows.append(rd); self._calc()

    def _calc(self):
        try: gst_pct=float(self.gst_rate.get() or 0)
        except: gst_pct=0.0
        try: disc=float(self.discount.get() or 0)
        except: disc=0.0
        sub=0.0
        for rd in self.item_rows:
            try: q=float(rd["qty"].get() or 1)
            except: q=1.0
            try: r=float(rd["rate"].get() or 0)
            except: r=0.0
            taxable=round(r/(1+gst_pct/100),2) if gst_pct else r
            tax_amt=round(r-taxable,2); amt=round(q*r,2)
            rd["tax"].set(f"{tax_amt*q:,.2f}"); rd["amt"].set(f"₹{amt:,.2f}"); sub+=amt
        after_disc=sub-disc
        cgst=round(after_disc*(gst_pct/2)/(100+gst_pct)*100/100,2) if gst_pct else 0
        self.t_vars["sub"].set(fmt_currency(sub)); self.t_vars["disc"].set(f"-{fmt_currency(disc)}")
        self.t_vars["cgst"].set(f"₹{cgst:,.2f} ({gst_pct/2}%)")
        self.t_vars["sgst"].set(f"₹{cgst:,.2f} ({gst_pct/2}%)")
        self.t_vars["grand"].set(fmt_currency(after_disc))
        self._last={"sub":sub,"disc":disc,"gst_pct":gst_pct,"gst_amt":cgst*2,"grand":after_disc}

    def _generate(self):
        name=self.cname.get().strip()
        if not name: messagebox.showerror("Error","Customer name required!"); return
        valid=[rd for rd in self.item_rows if rd["sel"].get()!="-- Select Item --"]
        if not valid: messagebox.showerror("Error","Select at least one item!"); return
        warnings=[]
        for rd in valid:
            sid=rd.get("stock_id")
            if not sid: continue
            try: qu=float(rd["qty"].get() or 1)
            except: qu=1.0
            with get_db(self.db_path) as conn:
                row=conn.execute("SELECT item_name,quantity FROM service_stock WHERE id=?",(sid,)).fetchone()
            if row and qu>float(row["quantity"] or 0):
                warnings.append(f"'{row['item_name']}': Need {qu}, Available {row['quantity']}")
        if warnings:
            if not messagebox.askyesno("Stock Warning ⚠️","Insufficient stock:\n"+"\n".join(warnings)+"\n\nStill generate?"): return
        self._calc(); t=self._last; inv_no=next_invoice_no(self.db_path,"acc")
        with get_db(self.db_path) as conn:
            conn.execute("""INSERT INTO invoices
                (invoice_no,type,customer_name,mobile,vehicle_no,model,invoice_date,
                 payment_mode,subtotal,discount,gst_pct,gst_amt,grand_total)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (inv_no,"acc",name,self.mobile.get(),self.vehno.get(),"",
                 self.inv_date.get(),self.paymode.get(),
                 t["sub"],t["disc"],t["gst_pct"],t["gst_amt"],t["grand"]))
            for rd in valid:
                try: q=float(rd["qty"].get() or 1)
                except: q=1.0
                try: r=float(rd["rate"].get() or 0)
                except: r=0.0
                item_name=rd["sel"].get().split("  [Stock:")[0]
                conn.execute("""INSERT INTO invoice_items
                    (invoice_no,item_type,description,part_no,quantity,rate,amount)
                    VALUES(?,?,?,?,?,?,?)""",
                    (inv_no,"part",item_name,rd["hsn"].get(),q,r,round(q*r,2)))
        deducted=[]
        for rd in valid:
            sid=rd.get("stock_id")
            if not sid: continue
            try: qu=float(rd["qty"].get() or 1)
            except: qu=1.0
            ok,remaining=deduct_stock(self.db_path,sid,qu)
            nm=rd["sel"].get().split("  [Stock:")[0]
            deducted.append(f"{'✅' if ok else '⚠️'} {nm}: {remaining} left")
        upsert_customer(self.db_path,name,self.mobile.get(),vehicle_no=self.vehno.get())
        self.last_invoice=inv_no; self.refresh_cb()
        msg=f"Customer: {name}\nTotal: {fmt_currency(t['grand'])}\nPayment: {self.paymode.get()}"
        if deducted: msg+="\n\nStock Updated:\n"+"\n".join(deducted)
        messagebox.showinfo("Bill Generated ✅",msg)

    def _print(self):
        if not self.last_invoice: messagebox.showinfo("Info","Generate an invoice first!"); return
        print_invoice(self.db_path,self.last_invoice)

    def _clear(self):
        for var in [self.cname,self.mobile,self.vehno]: var.set("")
        self.discount.set("0"); self.inv_date.set(str(date.today()))
        for rd in self.item_rows:
            for w in rd["widgets"]: w.grid_forget()
        self.item_rows.clear(); self._add_item_row(); self._calc()

    def refresh(self):
        sm=self._get_stock_map()
        labels=["-- Select Item --"]+list(sm.keys())
        for rd in self.item_rows:
            rd["stock_map"]=sm
            rd["widgets"][0]["values"]=labels
            if rd["sel"].get() not in labels:
                rd["sel"].set("-- Select Item --")