import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from db import get_db, fmt_currency

YAMAHA_BLUE = "#003087"
YAMAHA_RED  = "#E60026"
BG    = "#f4f6fb"
WHITE = "#ffffff"
TEXT  = "#1a1a2e"
MUTED = "#6b7280"
BORDER= "#e5e7eb"

CATEGORIES = ["Spare Part","Accessory","Oil & Lubricant","Tyre & Tube",
              "Battery","Electrical","Brake","Filter","Other"]
UNITS = ["Nos","Litre","ml","Kg","g","Set","Pair","Box","Metre"]

def init_service_stock_table(db_path):
    with get_db(db_path) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS service_stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            part_no TEXT DEFAULT '',
            item_name TEXT NOT NULL,
            hsn_code TEXT DEFAULT '',
            category TEXT DEFAULT 'Spare Part',
            quantity REAL DEFAULT 0,
            unit TEXT DEFAULT 'Nos',
            purchase_price REAL DEFAULT 0,
            selling_price REAL DEFAULT 0,
            low_stock_alert INTEGER DEFAULT 5,
            added_date TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        try:
            conn.execute("ALTER TABLE service_stock ADD COLUMN part_no TEXT DEFAULT ''")
        except: pass

def deduct_stock(db_path, stock_id, qty_used):
    with get_db(db_path) as conn:
        row = conn.execute("SELECT quantity FROM service_stock WHERE id=?", (stock_id,)).fetchone()
        if not row: return False, 0
        remaining = float(row["quantity"]) - float(qty_used)
        if remaining < 0: return False, float(row["quantity"])
        conn.execute("UPDATE service_stock SET quantity=? WHERE id=?", (remaining, stock_id))
    return True, remaining

class StockFrame(tk.Frame):
    def __init__(self, parent, db_path, refresh_cb):
        super().__init__(parent, bg=BG)
        self.db_path = db_path
        self.refresh_cb = refresh_cb
        init_service_stock_table(self.db_path)
        self._build()

    def _build(self):
        # Top bar
        top = tk.Frame(self, bg=BG); top.pack(fill="x", pady=(0,10))
        tk.Label(top, text="Stock Management", font=("Segoe UI",13,"bold"),
                 bg=BG, fg=YAMAHA_BLUE).pack(side="left")
        tk.Button(top, text="+ Add Stock Item", font=("Segoe UI",10,"bold"),
                  bg=YAMAHA_RED, fg=WHITE, relief="flat", padx=14, pady=6,
                  cursor="hand2", command=self._add_dialog).pack(side="right")
        tk.Button(top, text="🔄 Refresh", font=("Segoe UI",10),
                  bg=WHITE, fg=TEXT, relief="flat", padx=10, pady=5,
                  cursor="hand2", command=self.refresh).pack(side="right", padx=8)

        # Summary cards
        sf = tk.Frame(self, bg=BG); sf.pack(fill="x", pady=(0,12))
        self.sum_vars = {}
        for key, label, color in [
            ("total","Total Items",YAMAHA_BLUE),
            ("instock","In Stock","#16a34a"),
            ("low","Low Stock ⚠️","#b45309"),
            ("outstock","Out of Stock",YAMAHA_RED),
            ("value","Stock Value",YAMAHA_BLUE),
        ]:
            f = tk.Frame(sf, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)
            f.pack(side="left", expand=True, fill="x", padx=(0,8))
            tk.Label(f, text=label, font=("Segoe UI",8,"bold"),
                     bg=WHITE, fg=MUTED).pack(anchor="w", padx=12, pady=(10,0))
            var = tk.StringVar(value="0")
            self.sum_vars[key] = var
            tk.Label(f, textvariable=var, font=("Segoe UI",16,"bold"),
                     bg=WHITE, fg=color).pack(anchor="w", padx=12, pady=(2,10))

        # Search
        sb = tk.Frame(self, bg=BG); sb.pack(fill="x", pady=(0,8))
        tk.Label(sb, text="🔍 Search:", font=("Segoe UI",10), bg=BG, fg=MUTED).pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self.refresh())
        tk.Entry(sb, textvariable=self.search_var, font=("Segoe UI",11),
                 width=28, relief="flat", bg=WHITE,
                 highlightbackground=BORDER, highlightthickness=1).pack(
                     side="left", padx=8, ipady=5)

        # Table — S.No | Part No | Item Name | HSN Code | Quantity | Price | Total
        cols = ("S.No","Part No","Item Name","HSN Code","Quantity","Unit","Price (₹)","Total Value","Status")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=18)
        widths = [45,100,200,100,75,60,100,110,90]
        anchors = ["center","center","w","center","center","center","center","center","center"]
        for c, w, a in zip(cols, widths, anchors):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w, minwidth=40, anchor=a)
        self.tree.tag_configure("instock",  background="#f0fff4")
        self.tree.tag_configure("low",      background="#fffbeb")
        self.tree.tag_configure("outstock", background="#fff0f0")
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self._edit_selected())

        tk.Label(self,
                 text="💡 Double-click a row to Edit / Delete  ",
                 font=("Segoe UI",9), bg=BG, fg=MUTED).pack(anchor="w", pady=(6,0))

        self.refresh()

    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        search = self.search_var.get().lower()
        with get_db(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM service_stock ORDER BY item_name").fetchall()
        total = instock = low = outstock = 0
        total_val = 0.0; sno = 0
        for r in rows:
            if search and search not in (r["item_name"] or "").lower() \
                      and search not in (r["part_no"]   or "").lower() \
                      and search not in (r["hsn_code"]  or "").lower():
                continue
            qty   = float(r["quantity"]      or 0)
            price = float(r["selling_price"] or 0)
            alert = int(r["low_stock_alert"] or 5)
            val   = qty * price
            if qty <= 0:       tag="outstock"; status="Out of Stock"
            elif qty <= alert: tag="low";      status="Low Stock ⚠️"
            else:              tag="instock";  status="In Stock"
            sno += 1
            self.tree.insert("", "end", iid=r["id"], tags=(tag,), values=(
                sno, r["part_no"] or "", r["item_name"] or "",
                r["hsn_code"] or "", qty, r["unit"] or "Nos",
                f"₹{price:,.2f}", f"₹{val:,.2f}", status))
            total += 1; total_val += val
            if qty <= 0: outstock += 1
            elif qty <= alert: low += 1
            else: instock += 1
        self.sum_vars["total"].set(str(total))
        self.sum_vars["instock"].set(str(instock))
        self.sum_vars["low"].set(str(low))
        self.sum_vars["outstock"].set(str(outstock))
        self.sum_vars["value"].set(f"₹{total_val:,.2f}")

    def _edit_selected(self):
        sel = self.tree.focus()
        if sel: self._add_dialog(edit_id=int(sel))

    def _add_dialog(self, edit_id=None):
        data = None
        if edit_id:
            with get_db(self.db_path) as conn:
                data = conn.execute("SELECT * FROM service_stock WHERE id=?", (edit_id,)).fetchone()

        dlg = tk.Toplevel(self)
        dlg.title("Edit Stock Item" if edit_id else "Add Stock Item")
        dlg.geometry("520x450")
        dlg.resizable(False, False)
        dlg.configure(bg=WHITE)
        dlg.grab_set()

        hdr = tk.Frame(dlg, bg=YAMAHA_BLUE, height=48)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="✏️  Edit Stock Item" if edit_id else "➕  Add Stock Item",
                 font=("Segoe UI",12,"bold"), bg=YAMAHA_BLUE, fg=WHITE).pack(side="left", padx=18, pady=12)

        f = tk.Frame(dlg, bg=WHITE, padx=24, pady=10); f.pack(fill="both", expand=True)

        def lbl_entry(label, row, col, default="", width=22):
            tk.Label(f, text=label, font=("Segoe UI",8,"bold"),
                     bg=WHITE, fg=MUTED).grid(row=row*2, column=col, sticky="w", padx=(0,16), pady=(8,0))
            var = tk.StringVar(value=str(default))
            tk.Entry(f, textvariable=var, font=("Segoe UI",11), width=width,
                     relief="flat", bg="#f3f4f6",
                     highlightbackground=BORDER, highlightthickness=1).grid(
                         row=row*2+1, column=col, sticky="w", padx=(0,16), ipady=6)
            return var

        def lbl_combo(label, row, col, values, default="", width=20):
            tk.Label(f, text=label, font=("Segoe UI",8,"bold"),
                     bg=WHITE, fg=MUTED).grid(row=row*2, column=col, sticky="w", padx=(0,16), pady=(8,0))
            var = tk.StringVar(value=default or values[0])
            ttk.Combobox(f, textvariable=var, values=values, width=width, state="readonly").grid(
                row=row*2+1, column=col, sticky="w", padx=(0,16))
            return var

        v_partno   = lbl_entry("Part No.",           0, 0, data["part_no"]          if data else "", 18)
        v_name     = lbl_entry("Item Name *",        0, 1, data["item_name"]         if data else "", 24)
        v_hsn      = lbl_entry("HSN Code",           1, 0, data["hsn_code"]          if data else "", 18)
        v_cat      = lbl_combo("Category",           1, 1, CATEGORIES,
                                data["category"]      if data else CATEGORIES[0], 22)
        v_qty      = lbl_entry("Quantity",           2, 0, data["quantity"]          if data else "0", 10)
        v_unit     = lbl_combo("Unit",               2, 1, UNITS,
                                data["unit"]          if data else "Nos", 12)
        v_purchase = lbl_entry("Purchase Price (₹)", 3, 0, data["purchase_price"]   if data else "0", 14)
        v_selling  = lbl_entry("Selling Price (₹)",  3, 1, data["selling_price"]    if data else "0", 14)
        v_alert    = lbl_entry("Low Stock Alert",    4, 0, data["low_stock_alert"]  if data else "5", 10)
        v_date     = lbl_entry("Date Added",         4, 1, data["added_date"]       if data else str(date.today()), 16)

        def save():
            name_val = v_name.get().strip()
            if not name_val:
                messagebox.showerror("Error", "Item name required!", parent=dlg); return
            try:
                q  = float(v_qty.get()      or 0)
                pp = float(v_purchase.get() or 0)
                sp = float(v_selling.get()  or 0)
                al = int(v_alert.get()      or 5)
            except ValueError:
                messagebox.showerror("Error", "Enter valid numbers!", parent=dlg); return
            with get_db(self.db_path) as conn:
                if edit_id:
                    conn.execute("""UPDATE service_stock
                        SET part_no=?,item_name=?,hsn_code=?,category=?,
                            quantity=?,unit=?,purchase_price=?,selling_price=?,
                            low_stock_alert=?,added_date=?,last_updated=CURRENT_TIMESTAMP
                        WHERE id=?""",
                        (v_partno.get(),name_val,v_hsn.get(),v_cat.get(),
                         q,v_unit.get(),pp,sp,al,v_date.get(),edit_id))
                else:
                    conn.execute("""INSERT INTO service_stock
                        (part_no,item_name,hsn_code,category,quantity,unit,
                         purchase_price,selling_price,low_stock_alert,added_date)
                        VALUES(?,?,?,?,?,?,?,?,?,?)""",
                        (v_partno.get(),name_val,v_hsn.get(),v_cat.get(),
                         q,v_unit.get(),pp,sp,al,v_date.get()))
            dlg.destroy(); self.refresh()

        def delete_item():
            if not edit_id: return
            if messagebox.askyesno("Delete Item",
                    f"Delete '{v_name.get()}'?\n\nThis cannot be undone!", parent=dlg):
                with get_db(self.db_path) as conn:
                    conn.execute("DELETE FROM service_stock WHERE id=?", (edit_id,))
                dlg.destroy(); self.refresh()

        bf = tk.Frame(dlg, bg=WHITE, padx=24, pady=14); bf.pack(fill="x")
        tk.Button(bf, text="💾  Save", font=("Segoe UI",11,"bold"),
                  bg=YAMAHA_RED, fg=WHITE, relief="flat", padx=18, pady=8,
                  cursor="hand2", command=save).pack(side="left", padx=(0,10))
        tk.Button(bf, text="Cancel", font=("Segoe UI",10),
                  bg="#f3f4f6", fg=TEXT, relief="flat", padx=12, pady=7,
                  cursor="hand2", command=dlg.destroy).pack(side="left")
        if edit_id:
            tk.Button(bf, text="🗑  Delete Item", font=("Segoe UI",10,"bold"),
                      bg="#fff0f0", fg=YAMAHA_RED, relief="flat", padx=14, pady=7,
                      cursor="hand2", command=delete_item).pack(side="right")
