import tempfile, webbrowser
from db import get_db, get_setting, fmt_currency

def num_to_words(n):
    ones=["","One","Two","Three","Four","Five","Six","Seven","Eight","Nine","Ten",
          "Eleven","Twelve","Thirteen","Fourteen","Fifteen","Sixteen","Seventeen","Eighteen","Nineteen"]
    tens=["","","Twenty","Thirty","Forty","Fifty","Sixty","Seventy","Eighty","Ninety"]
    def h(n):
        if n<20: return ones[n]
        elif n<100: return tens[n//10]+(" "+ones[n%10] if n%10 else "")
        elif n<1000: return ones[n//100]+" Hundred"+(" "+h(n%100) if n%100 else "")
        elif n<100000: return h(n//1000)+" Thousand"+(" "+h(n%1000) if n%1000 else "")
        elif n<10000000: return h(n//100000)+" Lakh"+(" "+h(n%100000) if n%100000 else "")
        else: return h(n//10000000)+" Crore"+(" "+h(n%10000000) if n%10000000 else "")
    try: n=int(round(float(n))); return (h(n)+" Rupees") if n else "Zero Rupees"
    except: return ""

def print_invoice(db_path, invoice_no):
    with get_db(db_path) as conn:
        inv   = conn.execute("SELECT * FROM invoices WHERE invoice_no=?", (invoice_no,)).fetchone()
        items = conn.execute("SELECT * FROM invoice_items WHERE invoice_no=?", (invoice_no,)).fetchall()
        bike  = conn.execute("SELECT * FROM bike_sales WHERE invoice_no=?", (invoice_no,)).fetchone()
        svc   = conn.execute("SELECT * FROM service_jobs WHERE invoice_no=?", (invoice_no,)).fetchone()
    if not inv: return
    shop = {k: get_setting(db_path, k, "") for k in
            ["shop_name","dealer_code","address","phone1","phone2","email","gstin","state"]}
    shop["name"] = shop.pop("shop_name") or "Sri Yamaha Motors"
    gst_pct = float(inv["gst_pct"] or 18)
    cgst = float(inv["gst_amt"] or 0)/2; sgst = cgst
    grand = float(inv["grand_total"] or 0)
    inv_label = {"bike":"SALES INVOICE","acc":"TAX INVOICE","svc":"SERVICE INVOICE"}.get(inv["type"],"TAX INVOICE")

    if inv["type"]=="bike" and bike:
        body = f"""
        <div class="btobox">
          <div><div class="bttl">BILL TO</div><div class="bnm">{inv['customer_name'] or ''}</div>
          <div>Mobile: {inv['mobile'] or ''}</div></div>
          <div style="text-align:right"><div class="bttl">VEHICLE</div>
          <div><b>{bike['colour'] or ''} {inv['model'] or ''}</b></div>
          <div>Engine No: {bike['engine_no'] or ''}</div>
          <div>Chassis No: {bike.get('frame_no') or ''}</div></div>
        </div>
        <table><thead><tr><th>DESCRIPTION</th><th class="r">AMOUNT</th></tr></thead><tbody>
        <tr><td>Ex-Showroom Price</td><td class="r">{fmt_currency(bike['ex_showroom'])}</td></tr>
        <tr><td>RTO / Registration</td><td class="r">{fmt_currency(bike['rto_charge'])}</td></tr>
        <tr><td>Insurance</td><td class="r">{fmt_currency(bike['insurance'])}</td></tr>
        <tr><td>Accessories Add-on</td><td class="r">{fmt_currency(bike['accessories'])}</td></tr>
        <tr><td>Discount</td><td class="r" style="color:green">-{fmt_currency(inv['discount'])}</td></tr>
        <tr><td>CGST @{gst_pct/2}%</td><td class="r">{fmt_currency(cgst)}</td></tr>
        <tr><td>SGST @{gst_pct/2}%</td><td class="r">{fmt_currency(sgst)}</td></tr>
        </tbody></table>
        <div class="tbox">
          <div class="tr"><span>Taxable Amount</span><span>{fmt_currency(float(inv['subtotal'] or 0)-float(inv['discount'] or 0))}</span></div>
          <div class="tr"><span>CGST @{gst_pct/2}%</span><span>{fmt_currency(cgst)}</span></div>
          <div class="tr"><span>SGST @{gst_pct/2}%</span><span>{fmt_currency(sgst)}</span></div>
          <div class="tr grd"><span>Total Amount</span><span>{fmt_currency(grand)}</span></div>
          <div class="tr"><span>Amount Received</span><span>{fmt_currency(bike['amount_received'])}</span></div>
          <div class="tr" style="color:#E60026"><span>Balance Due</span><span>{fmt_currency(bike['balance'])}</span></div>
        </div>"""
    else:
        part_items=[i for i in items if i["item_type"]=="part"]
        svc_items =[i for i in items if i["item_type"]=="service"]
        all_items =part_items+svc_items
        body = f"""
        <div class="btobox">
          <div><div class="bttl">BILL TO</div><div class="bnm">{inv['customer_name'] or ''}</div>
          <div>Mobile: {inv['mobile'] or ''}</div>"""
        if inv["type"]=="svc" and svc:
            body+=f"<div>Job Card: {svc['job_card_no'] or ''} | KM: {svc['km_reading'] or ''}</div>"
        body+=f"""</div>
          <div style="text-align:right"><div class="bttl">VEHICLE NO.</div>
          <div class="bnm">{inv['vehicle_no'] or ''}</div>
          <div>{inv['model'] or ''}</div></div>
        </div>"""
        tot_qty=tot_tax=tot_amt=taxable_sum=0
        rows_html=""
        for item in all_items:
            qty=float(item["quantity"] or 1); rate=float(item["rate"] or 0)
            amt=float(item["amount"] or qty*rate)
            taxable=round(amt/(1+gst_pct/100),2); tax_amt=round(amt-taxable,2)
            tot_qty+=qty; tot_tax+=tax_amt; tot_amt+=amt; taxable_sum+=taxable
            rows_html+=f"""<tr>
              <td>{item['description'] or ''}</td>
              <td class="c">{item['part_no'] or ''}</td>
              <td class="c">{int(qty)} PCS</td>
              <td class="r">{rate:,.2f}</td>
              <td class="r">{tax_amt:,.2f}<br><small>({int(gst_pct)}%)</small></td>
              <td class="r">{int(round(amt))}</td></tr>"""
        body+=f"""
        <table>
          <thead><tr><th style="width:30%">ITEMS</th><th class="c" style="width:12%">HSN</th>
          <th class="c" style="width:10%">QTY.</th><th class="r" style="width:13%">RATE</th>
          <th class="r" style="width:13%">TAX</th><th class="r" style="width:12%">AMOUNT</th></tr></thead>
          <tbody>{rows_html}</tbody>
          <tfoot><tr style="font-weight:700;background:#f1f5ff">
          <td>SUBTOTAL</td><td></td><td class="c">{int(tot_qty)}</td><td></td>
          <td class="r">₹{tot_tax:,.2f}</td><td class="r">₹{int(round(tot_amt)):,}</td></tr></tfoot>
        </table>
        <div style="display:flex;justify-content:space-between;margin-top:16px">
          <div class="terms">
            <b>TERMS AND CONDITIONS</b><br>
            1. Goods once sold will not be taken back or exchanged<br>
            2. All disputes are subject to local jurisdiction only<br>
            3. Warranty subject to manufacturer terms<br>
            4. Payment once made will not be refunded
          </div>
          <div class="tbox">
            <div class="tr"><span>Taxable Amount</span><span>₹{taxable_sum:,.2f}</span></div>
            <div class="tr"><span>CGST @{gst_pct/2}%</span><span>₹{cgst:,.2f}</span></div>
            <div class="tr"><span>SGST @{gst_pct/2}%</span><span>₹{sgst:,.2f}</span></div>
            <div class="tr grd"><span>Total Amount</span><span>₹{int(round(grand)):,}</span></div>
            <div class="tr"><span>Received Amount</span><span>₹ 0</span></div>
          </div>
        </div>
        <div style="margin-top:10px;font-size:12px">
          <b>Total Amount (in words)</b><br>{num_to_words(grand)}
        </div>"""

    html=f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
    <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'Segoe UI',Arial,sans-serif;font-size:13px;color:#1a1a2e;padding:30px}}
    .header{{display:flex;justify-content:space-between;border-bottom:3px solid #003087;padding-bottom:14px;margin-bottom:14px}}
    .sname{{font-size:22px;font-weight:800;color:#003087;margin-bottom:4px}}
    .shop p{{font-size:12px;color:#555;margin:2px 0}}
    .imeta{{text-align:right;font-size:12px}}
    .itag{{display:inline-block;border:2px solid #003087;color:#003087;font-weight:700;
           font-size:11px;padding:2px 10px;letter-spacing:1px;margin-bottom:8px}}
    .imeta table td{{padding:2px 6px;border:none;font-size:12px}}
    .btobox{{display:flex;justify-content:space-between;background:#f8f9fa;
             border-radius:6px;padding:12px 16px;margin-bottom:14px}}
    .bttl{{font-size:10px;font-weight:700;color:#003087;text-transform:uppercase;margin-bottom:4px}}
    .bnm{{font-size:15px;font-weight:700;margin-bottom:2px}}
    table{{width:100%;border-collapse:collapse;margin-bottom:0}}
    th{{background:#003087;color:#fff;padding:9px 10px;font-size:11px;text-transform:uppercase}}
    td{{padding:8px 10px;border-bottom:1px solid #e5e7eb;font-size:13px}}
    tfoot td{{border-top:2px solid #003087;border-bottom:none}}
    .c{{text-align:center}}.r{{text-align:right}}
    small{{color:#888;font-size:10px}}
    .tbox{{min-width:250px;border:1px solid #003087;border-radius:6px;padding:12px 16px}}
    .tr{{display:flex;justify-content:space-between;padding:4px 0;font-size:13px}}
    .grd{{font-weight:700;font-size:15px;color:#003087;border-top:1px solid #003087;margin-top:8px;padding-top:8px}}
    .terms{{font-size:11px;color:#444;max-width:52%;line-height:1.9}}
    .sign{{display:flex;justify-content:flex-end;margin-top:30px}}
    .sign-in{{text-align:center;border-top:1px solid #003087;padding-top:8px;min-width:200px;font-size:12px;font-weight:700;color:#003087}}
    @media print{{body{{padding:15px}}}}
    </style>
    <script>window.onload=function(){{window.print()}}</script>
    </head><body>
    <div class="header">
      <div class="shop">
        <div class="sname">{shop['name']}</div>
        <p>{shop['address']}</p>
        <p>Mobile: {shop['phone1']}{"  |  "+shop['phone2'] if shop['phone2'] else ""}</p>
        <p>Email: {shop['email']}</p>
        {"<p>GSTIN: "+shop['gstin']+"</p>" if shop['gstin'] else ""}
      </div>
      <div class="imeta">
        <div class="itag">{inv_label} &nbsp; ORIGINAL FOR RECIPIENT</div>
        <table>
          <tr><td><b>Invoice Date:</b></td><td>{inv['invoice_date'] or ''}</td></tr>
          <tr><td><b>Payment:</b></td><td>{inv['payment_mode'] or ''}</td></tr>
        </table>
      </div>
    </div>
    {body}
    <div class="sign"><div class="sign-in">AUTHORISED SIGNATORY FOR<br>{shop['name']}</div></div>
    </body></html>"""

    tmp=tempfile.NamedTemporaryFile(delete=False,suffix=".html",mode="w",encoding="utf-8")
    tmp.write(html); tmp.close()
    webbrowser.open(f"file://{tmp.name}")
