import tkinter as tk
from tkinter import messagebox
from datetime import date
from db import get_db, next_invoice_no, fmt_currency, upsert_customer
from widgets import card, labeled_entry, labeled_combo, primary_button, outline_button
from print_invoice import print_invoice

YAMAHA_BLUE="#003087"; YAMAHA_RED="#E60026"; BG="#f4f6fb"; WHITE="#ffffff"; MUTED="#6b7280"
MODELS=["Yamaha FZ-S V3","Yamaha MT-15 V2","Yamaha R15 V4","Yamaha Fascino 125",
        "Yamaha Ray-ZR 125","Yamaha Aerox 155","Yamaha FZX","Other"]
PAYMENT_MODES=["Full Cash","Bank Loan","UPI","Cheque","Exchange"]
GST_RATES=["28","18","12","5","0"]

class BikeBillingFrame(tk.Frame):
    def __init__(self, parent, db_path, refresh_cb):
        super().__init__(parent, bg=BG)
        self.db_path=db_path; self.refresh_cb=refresh_cb
        self.last_invoice=None; self._last={}; self._build()

    def _build(self):
        c1=card(self,"Customer Details","👤"); g=tk.Frame(c1,bg=WHITE); g.pack(fill="x")
        self.cname,_=labeled_entry(g,"Customer Name *",0,0,width=28)
        self.mobile,_=labeled_entry(g,"Mobile *",0,1,width=22)
        self.email,_=labeled_entry(g,"Email",0,2,width=28)
        self.address,_=labeled_entry(g,"Address",1,0,colspan=2,width=52)
        self.idno,_=labeled_entry(g,"Aadhaar / PAN",1,2,width=28)
        g2=tk.Frame(c1,bg=WHITE); g2.pack(fill="x",pady=(6,0))
        self.inv_date,_=labeled_entry(g2,"Invoice Date",0,0,default=str(date.today()),width=18)
        self.exec_name,_=labeled_entry(g2,"Sales Executive",0,1,width=22)

        c2=card(self,"Vehicle Details","🏍"); g3=tk.Frame(c2,bg=WHITE); g3.pack(fill="x")
        self.model,_=labeled_combo(g3,"Model *",0,0,MODELS,width=28)
        self.colour,_=labeled_entry(g3,"Colour",0,1,width=20)
        self.engno,_=labeled_entry(g3,"Engine No.",0,2,width=22)
        self.chassisno,_=labeled_entry(g3,"Chassis No.",1,0,width=22)

        c3=card(self,"Pricing & GST","₹"); g4=tk.Frame(c3,bg=WHITE); g4.pack(fill="x")
        self.exshow,_=labeled_entry(g4,"Ex-Showroom Price (₹) *",0,0,default="0",width=18)
        self.rto,_=labeled_entry(g4,"RTO / Registration (₹)",0,1,default="0",width=18)
        self.insurance,_=labeled_entry(g4,"Insurance (₹)",0,2,default="0",width=18)
        self.accs,_=labeled_entry(g4,"Accessories Add-on (₹)",1,0,default="0",width=18)
        self.discount,_=labeled_entry(g4,"Discount (₹)",1,1,default="0",width=18)
        self.gst_rate,_=labeled_combo(g4,"GST Rate",1,2,GST_RATES,default="18",width=16)
        self.paymode,_=labeled_combo(g4,"Payment Mode",2,0,PAYMENT_MODES,width=22)
        self.bank,_=labeled_entry(g4,"Finance Name",2,1,width=22)
        self.received,_=labeled_entry(g4,"Amount Received (₹)",2,2,default="0",width=18)
        for var in [self.exshow,self.rto,self.insurance,self.accs,self.discount,self.gst_rate,self.received]:
            var.trace_add("write",lambda *a:self._calc())

        c4=card(self,"Bill Summary","📋")
        tf=tk.Frame(c4,bg="#f8faff",highlightbackground="#dde3f0",highlightthickness=1); tf.pack(fill="x",pady=4)
        self.t_vars={}
        for label,key,color in [("Ex-Showroom Price","ex","#1a1a2e"),("RTO / Registration","rto","#1a1a2e"),
            ("Insurance","ins","#1a1a2e"),("Accessories","acc","#1a1a2e"),("Discount","disc","#16a34a"),
            ("CGST + SGST","gst","#b45309"),("Grand Total (On-Road)","grand","#003087"),("Balance Due","bal","#E60026")]:
            r=tk.Frame(tf,bg="#f8faff"); r.pack(fill="x",padx=16,pady=2)
            bold="bold" if key in ("grand","bal") else "normal"
            size=11 if key in ("grand","bal") else 10
            tk.Label(r,text=label,font=("Segoe UI",size,bold),bg="#f8faff",fg=MUTED).pack(side="left")
            var=tk.StringVar(value="₹0.00"); self.t_vars[key]=var
            tk.Label(r,textvariable=var,font=("Segoe UI",size,bold),bg="#f8faff",fg=color).pack(side="right")
            if key in ("grand","disc"): tk.Frame(tf,bg="#dde3f0",height=1).pack(fill="x",padx=8)

        bf=tk.Frame(self,bg=BG); bf.pack(fill="x",pady=8)
        primary_button(bf,"✔  Generate Invoice",self._generate).pack(side="left",padx=(0,8))
        outline_button(bf,"🖨  Print Last Invoice",self._print).pack(side="left",padx=(0,8))
        outline_button(bf,"↺  Clear",self._clear).pack(side="left")
        self._calc()

    def _calc(self):
        def f(v):
            try: return float(v.get() or 0)
            except: return 0.0
        ex=f(self.exshow); rto=f(self.rto); ins=f(self.insurance)
        acc=f(self.accs); disc=f(self.discount)
        try: gst_pct=float(self.gst_rate.get() or 0)
        except: gst_pct=0.0
        received=f(self.received)
        base=ex+rto+ins+acc-disc; gst_amt=base*gst_pct/100
        grand=base+gst_amt; bal=max(0.0,grand-received)
        self.t_vars["ex"].set(fmt_currency(ex)); self.t_vars["rto"].set(fmt_currency(rto))
        self.t_vars["ins"].set(fmt_currency(ins)); self.t_vars["acc"].set(fmt_currency(acc))
        self.t_vars["disc"].set(f"-{fmt_currency(disc)}")
        self.t_vars["gst"].set(f"{fmt_currency(gst_amt)} ({gst_pct/2}%+{gst_pct/2}%)")
        self.t_vars["grand"].set(fmt_currency(grand)); self.t_vars["bal"].set(fmt_currency(bal))
        self._last={"ex":ex,"rto":rto,"ins":ins,"acc":acc,"disc":disc,
                    "gst_pct":gst_pct,"gst_amt":gst_amt,"grand":grand,"bal":bal}

    def _generate(self):
        name=self.cname.get().strip(); mob=self.mobile.get().strip()
        if not name: messagebox.showerror("Error","Customer name required!"); return
        if not mob:  messagebox.showerror("Error","Mobile number required!"); return
        try: ex=float(self.exshow.get() or 0)
        except: ex=0
        if ex<=0: messagebox.showerror("Error","Ex-Showroom price required!"); return
        self._calc(); t=self._last; inv_no=next_invoice_no(self.db_path,"bike")
        with get_db(self.db_path) as conn:
            conn.execute("""INSERT INTO invoices
                (invoice_no,type,customer_name,mobile,vehicle_no,model,invoice_date,
                 payment_mode,subtotal,discount,gst_pct,gst_amt,grand_total)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (inv_no,"bike",name,mob,"",self.model.get(),self.inv_date.get(),
                 self.paymode.get(),t["ex"]+t["rto"]+t["ins"]+t["acc"],
                 t["disc"],t["gst_pct"],t["gst_amt"],t["grand"]))
            conn.execute("""INSERT INTO bike_sales
                (invoice_no,colour,engine_no,frame_no,rto_charge,insurance,accessories,
                 ex_showroom,finance_bank,amount_received,balance,sales_exec,
                 customer_address,customer_email,id_proof)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (inv_no,self.colour.get(),self.engno.get(),self.chassisno.get(),
                 t["rto"],t["ins"],t["acc"],t["ex"],self.bank.get(),
                 float(self.received.get() or 0),t["bal"],self.exec_name.get(),
                 self.address.get(),self.email.get(),self.idno.get()))
        upsert_customer(self.db_path,name,mob,email=self.email.get(),
                        address=self.address.get(),model=self.model.get())
        self.last_invoice=inv_no; self.refresh_cb()
        messagebox.showinfo("Bill Generated ✅",
            f"Customer: {name}\nTotal: {fmt_currency(t['grand'])}\nPayment: {self.paymode.get()}")

    def _print(self):
        if not self.last_invoice: messagebox.showinfo("Info","Generate an invoice first!"); return
        print_invoice(self.db_path,self.last_invoice)

    def _clear(self):
        for var in [self.cname,self.mobile,self.email,self.address,self.idno,
                    self.exec_name,self.colour,self.engno,self.chassisno,self.bank]: var.set("")
        for var in [self.exshow,self.rto,self.insurance,self.accs,self.discount,self.received]: var.set("0")
        self.inv_date.set(str(date.today())); self._calc()

    def refresh(self): pass
