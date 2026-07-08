import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from db import get_db, next_invoice_no, fmt_currency, upsert_customer
from widgets import card, labeled_entry, labeled_combo, primary_button, outline_button
from print_invoice import print_invoice
from stock_management import init_service_stock_table, deduct_stock

YAMAHA_BLUE="#003087"; YAMAHA_RED="#E60026"; BG="#f4f6fb"; WHITE="#ffffff"; MUTED="#6b7280"; BORDER="#e5e7eb"
GST_RATES=["18","12","5","0"]; PAYMENT_MODES=["Cash","UPI","Card","Online Transfer","Cheque"]

class ServiceBillingFrame(tk.Frame):
    def __init__(self,parent,db_path,refresh_cb):
        super().__init__(parent,bg=BG)
        self.db_path=db_path; self.refresh_cb=refresh_cb
        self.last_invoice=None; self.part_rows=[]; self.svc_rows=[]
        init_service_stock_table(self.db_path); self._build()

    def _build(self):
        c1=card(self,"Customer & Vehicle Info","🔧"); g=tk.Frame(c1,bg=WHITE); g.pack(fill="x")
        self.cname,_=labeled_entry(g,"Customer Name *",0,0,width=26)
        self.mobile,_=labeled_entry(g,"Mobile",0,1,width=20)
        self.vehno,_=labeled_entry(g,"Vehicle Number",0,2,width=20)
        self.model,_=labeled_entry(g,"Vehicle Model",1,0,width=26)
        self.km,_=labeled_entry(g,"KM Reading",1,1,width=14)
        self.jobno,_=labeled_entry(g,"Job Card No.",1,2,width=16)
        self.inv_date,_=labeled_entry(g,"Invoice Date",2,0,default=str(date.today()),width=18)
        self.advisor,_=labeled_entry(g,"Service Advisor",2,1,width=20)

        # ── Spare Parts ──────────────────────────────────────────────
        c_parts=card(self,"Spare Parts Used","📦")

        # Single grid frame for BOTH header and data rows
        self.parts_grid=tk.Frame(c_parts,bg=WHITE)
        self.parts_grid.pack(fill="x")

        # Column config — all weights 0 so no stretching
        col_conf = [("no",30),("name",230),("hsn",80),("qty",55),("rate",80),("amt",80),("del",30)]
        for i,(_,w) in enumerate(col_conf):
            self.parts_grid.grid_columnconfigure(i, minsize=w, weight=0)

        # Header row = row 0
        for i,(txt,_) in enumerate(col_conf[:-1]):
            labels = ["#","Part Name","HSN","Qty","Rate ₹","Amount"]
            tk.Label(self.parts_grid, text=labels[i],
                     font=("Segoe UI",8,"bold"), bg="#eef2ff", fg=YAMAHA_BLUE,
                     anchor="w").grid(row=0, column=i, sticky="nsew", padx=4, pady=4)
        tk.Label(self.parts_grid, text="", bg="#eef2ff").grid(row=0, column=6, sticky="nsew")
        self.parts_grid.grid_rowconfigure(0, minsize=28)

        tk.Button(c_parts,text="+ Add Part",font=("Segoe UI",10),bg="#eef2ff",fg=YAMAHA_BLUE,
                  relief="flat",padx=12,pady=5,cursor="hand2",command=self._add_part_row).pack(anchor="w",pady=(4,0))

        # ── Services ─────────────────────────────────────────────────
        c_svc=card(self,"Services (Labour)","⚙️")

        self.svc_grid=tk.Frame(c_svc,bg=WHITE)
        self.svc_grid.pack(fill="x")

        svc_col_conf = [("no",30),("desc",230),("type",80),("qty",55),("rate",80),("amt",80),("del",30)]
        for i,(_,w) in enumerate(svc_col_conf):
            self.svc_grid.grid_columnconfigure(i, minsize=w, weight=0)

        svc_labels = ["#","Description","Type","Qty","Rate ₹","Amount"]
        for i,lbl in enumerate(svc_labels):
            tk.Label(self.svc_grid, text=lbl,
                     font=("Segoe UI",8,"bold"), bg="#eef2ff", fg=YAMAHA_BLUE,
                     anchor="w").grid(row=0, column=i, sticky="nsew", padx=4, pady=4)
        tk.Label(self.svc_grid, text="", bg="#eef2ff").grid(row=0, column=6, sticky="nsew")
        self.svc_grid.grid_rowconfigure(0, minsize=28)

        tk.Button(c_svc,text="+ Add Service",font=("Segoe UI",10),bg="#eef2ff",fg=YAMAHA_BLUE,
                  relief="flat",padx=12,pady=5,cursor="hand2",command=self._add_svc_row).pack(anchor="w",pady=(4,0))

        # Summary
        c4=card(self,"Summary","₹"); g4=tk.Frame(c4,bg=WHITE); g4.pack(fill="x")
        self.discount,_=labeled_entry(g4,"Discount (₹)",0,0,default="0",width=16)
        self.gst_rate,_=labeled_combo(g4,"GST Rate",0,1,GST_RATES,default="18",width=14)
        self.paymode,_=labeled_combo(g4,"Payment Mode",0,2,PAYMENT_MODES,width=18)
        self.discount.trace_add("write",lambda *a:self._calc())
        self.gst_rate.trace_add("write",lambda *a:self._calc())
        tf=tk.Frame(c4,bg="#f8faff",highlightbackground="#dde3f0",highlightthickness=1)
        tf.pack(fill="x",pady=(12,0)); self.t_vars={}
        for label,key,color in [("Spare Parts Total","parts","#1a1a2e"),("Labour Charges","lab","#1a1a2e"),
            ("Discount","disc","#16a34a"),("CGST + SGST","gst","#b45309"),("Grand Total","grand","#003087")]:
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
        self._add_part_row(); self._add_svc_row()

    def _get_stock_map(self):
        with get_db(self.db_path) as conn:
            rows=conn.execute("SELECT * FROM service_stock ORDER BY item_name").fetchall()
        sm={}
        for r in rows:
            qty=float(r["quantity"] or 0)
            label=f"{r['item_name']}  [Stock: {qty} {r['unit'] or ''}]"
            sm[label]=r
        return sm

    def _add_part_row(self):
        sm=self._get_stock_map(); labels=["-- Select from Stock --"]+list(sm.keys())
        row_num = len(self.part_rows) + 1  # +1 because row 0 is header

        tk.Label(self.parts_grid, text=str(row_num), bg=WHITE, fg=MUTED,
                 font=("Segoe UI",9)).grid(row=row_num, column=0, padx=4, pady=3, sticky="w")

        sel_var=tk.StringVar(value=labels[0])
        sel_cb=ttk.Combobox(self.parts_grid, textvariable=sel_var, values=labels, state="normal")
        sel_cb.grid(row=row_num, column=1, padx=3, pady=3, sticky="w")

        hsn_var=tk.StringVar()
        hsn_e=tk.Entry(self.parts_grid, textvariable=hsn_var, width=9, relief="flat",
                       bg="#f3f4f6", highlightbackground=BORDER, highlightthickness=1)
        hsn_e.grid(row=row_num, column=2, padx=3, pady=3, sticky="w")

        qty_var=tk.StringVar(value="1")
        qty_e=tk.Entry(self.parts_grid, textvariable=qty_var, width=5, relief="flat",
                       bg="#f3f4f6", highlightbackground=BORDER, highlightthickness=1)
        qty_e.grid(row=row_num, column=3, padx=3, pady=3, sticky="w")

        rate_var=tk.StringVar(value="0")
        rate_e=tk.Entry(self.parts_grid, textvariable=rate_var, width=8, relief="flat",
                        bg="#f3f4f6", highlightbackground=BORDER, highlightthickness=1)
        rate_e.grid(row=row_num, column=4, padx=3, pady=3, sticky="w")

        amt_var=tk.StringVar(value="₹0.00")
        amt_lbl=tk.Label(self.parts_grid, textvariable=amt_var, bg=WHITE, fg=YAMAHA_BLUE,
                 font=("Segoe UI",9,"bold"), anchor="e")
        amt_lbl.grid(row=row_num, column=5, padx=4, pady=3, sticky="w")

        rd={"row":row_num,"sel":sel_var,"hsn":hsn_var,"qty":qty_var,"rate":rate_var,
            "amt":amt_var,"stock_map":sm,"stock_id":None,
            "widgets":[sel_cb, hsn_e, qty_e, rate_e, amt_lbl]}

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
            self.part_rows.remove(r); self._calc()

        del_btn=tk.Button(self.parts_grid, text="✕", bg=WHITE, fg="#ccc", relief="flat",
                          font=("Segoe UI",9), cursor="hand2", command=del_row)
        del_btn.grid(row=row_num, column=6, padx=2, pady=3, sticky="w")
        rd["widgets"].append(del_btn)
        self.part_rows.append(rd); self._calc()

    def _add_svc_row(self):
        row_num = len(self.svc_rows) + 1

        tk.Label(self.svc_grid, text=str(row_num), bg=WHITE, fg=MUTED,
                 font=("Segoe UI",9)).grid(row=row_num, column=0, padx=4, pady=3, sticky="w")

        desc_var=tk.StringVar()
        desc_e=tk.Entry(self.svc_grid, textvariable=desc_var, width=22, relief="flat",
                        bg="#f3f4f6", highlightbackground=BORDER, highlightthickness=1)
        desc_e.grid(row=row_num, column=1, padx=3, pady=3, sticky="w")

        type_var=tk.StringVar()
        type_e=tk.Entry(self.svc_grid, textvariable=type_var, width=9, relief="flat",
                        bg="#f3f4f6", highlightbackground=BORDER, highlightthickness=1)
        type_e.grid(row=row_num, column=2, padx=3, pady=3, sticky="w")

        qty_var=tk.StringVar(value="1")
        qty_e=tk.Entry(self.svc_grid, textvariable=qty_var, width=5, relief="flat",
                       bg="#f3f4f6", highlightbackground=BORDER, highlightthickness=1)
        qty_e.grid(row=row_num, column=3, padx=3, pady=3, sticky="w")

        rate_var=tk.StringVar(value="0")
        rate_e=tk.Entry(self.svc_grid, textvariable=rate_var, width=8, relief="flat",
                        bg="#f3f4f6", highlightbackground=BORDER, highlightthickness=1)
        rate_e.grid(row=row_num, column=4, padx=3, pady=3, sticky="w")

        amt_var=tk.StringVar(value="₹0.00")
        amt_lbl=tk.Label(self.svc_grid, textvariable=amt_var, bg=WHITE, fg=YAMAHA_BLUE,
                 font=("Segoe UI",9,"bold"), anchor="e")
        amt_lbl.grid(row=row_num, column=5, padx=4, pady=3, sticky="w")

        rd={"row":row_num,"desc":desc_var,"type":type_var,"qty":qty_var,"rate":rate_var,
            "amt":amt_var,"widgets":[desc_e,type_e,qty_e,rate_e,amt_lbl]}
        qty_var.trace_add("write",lambda *a:self._calc())
        rate_var.trace_add("write",lambda *a:self._calc())

        def del_row(r=rd):
            for w in r["widgets"]: w.grid_forget()
            self.svc_rows.remove(r); self._calc()

        del_btn=tk.Button(self.svc_grid, text="✕", bg=WHITE, fg="#ccc", relief="flat",
                          font=("Segoe UI",9), cursor="hand2", command=del_row)
        del_btn.grid(row=row_num, column=6, padx=2, pady=3, sticky="w")
        rd["widgets"].append(del_btn)
        self.svc_rows.append(rd); self._calc()

    def _calc(self):
        parts_total=0.0
        for rd in self.part_rows:
            try: q=float(rd["qty"].get() or 1)
            except: q=1.0
            try: r=float(rd["rate"].get() or 0)
            except: r=0.0
            amt=q*r; rd["amt"].set(f"₹{amt:,.2f}"); parts_total+=amt
        lab_total=0.0
        for rd in self.svc_rows:
            try: q=float(rd["qty"].get() or 1)
            except: q=1.0
            try: r=float(rd["rate"].get() or 0)
            except: r=0.0
            amt=q*r; rd["amt"].set(f"₹{amt:,.2f}"); lab_total+=amt
        sub=parts_total+lab_total
        try: disc=float(self.discount.get() or 0)
        except: disc=0.0
        try: gst_pct=float(self.gst_rate.get() or 0)
        except: gst_pct=0.0
        after_disc=sub-disc; gst_amt=after_disc*gst_pct/100; grand=after_disc+gst_amt
        self.t_vars["parts"].set(fmt_currency(parts_total))
        self.t_vars["lab"].set(fmt_currency(lab_total))
        self.t_vars["disc"].set(f"-{fmt_currency(disc)}")
        self.t_vars["gst"].set(f"{fmt_currency(gst_amt)} ({gst_pct/2}%+{gst_pct/2}%)")
        self.t_vars["grand"].set(fmt_currency(grand))
        self._last={"parts":parts_total,"lab":lab_total,"disc":disc,
                    "gst_pct":gst_pct,"gst_amt":gst_amt,"grand":grand}

    def _generate(self):
        name=self.cname.get().strip()
        if not name: messagebox.showerror("Error","Customer name required!"); return
        if not self.part_rows and not self.svc_rows:
            messagebox.showerror("Error","Add at least one part or service!"); return
        warnings=[]
        for rd in self.part_rows:
            label=rd["sel"].get()
            if label=="-- Select from Stock --": continue
            sid=rd.get("stock_id")
            if not sid: continue
            try: qu=float(rd["qty"].get() or 1)
            except: qu=1.0
            with get_db(self.db_path) as conn:
                row=conn.execute("SELECT item_name,quantity FROM service_stock WHERE id=?",(sid,)).fetchone()
            if row and qu>float(row["quantity"] or 0):
                warnings.append(f"'{row['item_name']}': Need {qu}, Available {row['quantity']}")
        if warnings:
            if not messagebox.askyesno("Stock Warning ⚠️","Insufficient:\n"+"\n".join(warnings)+"\n\nStill generate?"): return
        self._calc(); t=self._last; inv_no=next_invoice_no(self.db_path,"svc")
        with get_db(self.db_path) as conn:
            conn.execute("""INSERT INTO invoices
                (invoice_no,type,customer_name,mobile,vehicle_no,model,invoice_date,
                 payment_mode,subtotal,discount,gst_pct,gst_amt,grand_total)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (inv_no,"svc",name,self.mobile.get(),self.vehno.get(),self.model.get(),
                 self.inv_date.get(),self.paymode.get(),
                 t["parts"]+t["lab"],t["disc"],t["gst_pct"],t["gst_amt"],t["grand"]))
            conn.execute("""INSERT INTO service_jobs
                (invoice_no,job_card_no,km_reading,advisor,labour_total,parts_total)
                VALUES(?,?,?,?,?,?)""",
                (inv_no,self.jobno.get(),self.km.get(),self.advisor.get(),t["lab"],t["parts"]))
            for rd in self.part_rows:
                label=rd["sel"].get()
                if label=="-- Select from Stock --": continue
                try: q=float(rd["qty"].get() or 1)
                except: q=1.0
                try: r=float(rd["rate"].get() or 0)
                except: r=0.0
                part_name=label.split("  [Stock:")[0]
                conn.execute("""INSERT INTO invoice_items
                    (invoice_no,item_type,description,part_no,quantity,rate,amount)
                    VALUES(?,?,?,?,?,?,?)""",
                    (inv_no,"part",part_name,rd["hsn"].get(),q,r,round(q*r,2)))
            for rd in self.svc_rows:
                if not rd["desc"].get().strip(): continue
                try: q=float(rd["qty"].get() or 1)
                except: q=1.0
                try: r=float(rd["rate"].get() or 0)
                except: r=0.0
                conn.execute("""INSERT INTO invoice_items
                    (invoice_no,item_type,description,part_no,quantity,rate,amount)
                    VALUES(?,?,?,?,?,?,?)""",
                    (inv_no,"service",rd["desc"].get(),rd["type"].get(),q,r,round(q*r,2)))
        deducted=[]
        for rd in self.part_rows:
            sid=rd.get("stock_id")
            if not sid: continue
            label=rd["sel"].get()
            if label=="-- Select from Stock --": continue
            try: qu=float(rd["qty"].get() or 1)
            except: qu=1.0
            ok,remaining=deduct_stock(self.db_path,sid,qu)
            nm=label.split("  [Stock:")[0]
            deducted.append(f"{'✅' if ok else '⚠️'} {nm}: {remaining} left")
        upsert_customer(self.db_path,name,self.mobile.get(),vehicle_no=self.vehno.get(),model=self.model.get())
        self.last_invoice=inv_no; self.refresh_cb()
        msg=f"Customer: {name}\nTotal: {fmt_currency(t['grand'])}\nPayment: {self.paymode.get()}"
        if deducted: msg+="\n\nStock Updated:\n"+"\n".join(deducted)
        messagebox.showinfo("Bill Generated ✅",msg)

    def _print(self):
        if not self.last_invoice: messagebox.showinfo("Info","Generate an invoice first!"); return
        print_invoice(self.db_path,self.last_invoice)

    def _clear(self):
        for var in [self.cname,self.mobile,self.vehno,self.model,self.km,self.jobno,self.advisor]: var.set("")
        self.discount.set("0"); self.inv_date.set(str(date.today()))
        for rd in self.part_rows:
            for w in rd["widgets"]: w.grid_forget()
        for rd in self.svc_rows:
            for w in rd["widgets"]: w.grid_forget()
        self.part_rows.clear(); self.svc_rows.clear()
        self._add_part_row(); self._add_svc_row(); self._calc()

    def refresh(self):
        sm=self._get_stock_map()
        labels=["-- Select from Stock --"]+list(sm.keys())
        for rd in self.part_rows:
            rd["stock_map"]=sm
            rd["widgets"][0]["values"]=labels
            if rd["sel"].get() not in labels:
                rd["sel"].set("-- Select from Stock --")