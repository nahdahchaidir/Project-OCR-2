#!/usr/bin/env python3
# ==========================================================
# DOWNLOAD PLN → XLSX → GABUNG SEMUA SHEET → OUTPUT 1 XLSX
# DENGAN PILIHAN SERVER (INTRANET / INTERNET)
# + DROPDOWN "UNIT DATA" (SEMUA / 1 UNIT) DI BAWAH UNITAP
# ==========================================================

import os
import time
import tempfile
import threading
import urllib3
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from urllib3.exceptions import InsecureRequestWarning

# ===================== KONFIG =====================
MAX_RETRY = 3
RETRY_DELAY = 5

UNITAP_DICT = {
    "32AMU": ["32010", "32020", "32030", "32040"],
    "32AMS": ["32111", "32121", "32131", "32141", "32151", "32161"],
    "32CWP": ["32210", "32240", "32250", "32260", "32270", "32280"],
    "32CKD": ["32320", "32330", "32340", "32350", "32360", "32370", "32380"],
    "32CPG": ["32410", "32420", "32430", "32440", "32450"],
    "32CPR": ["32510", "32520", "32530", "32540", "32550", "32560", "32570"],
    "32CPL": ["32610", "32620", "32630", "32640", "32650", "32660", "32680"],
    "32CBK": ["32710", "32720", "32730", "32740", "32750", "32760", "32770"],
    "32CBB": ["32810", "32820", "32830", "32840", "32850"],
    "32CMJ": ["32910", "32920", "32930", "32940", "32950", "32960"],
}

urllib3.disable_warnings(InsecureRequestWarning)

URL_TEMPLATE = (
    "{base}/birt-acmt/run?"
    "__report=rpt_icmo_DataDetail.rptdesign"
    "&up={up}&blth={blth}"
    "&rbm=TOTAL&jns=FG_DLPD_JAMNYALA"
    "&tglbaca=&jnf=0&jnt=99999999999"
    "&kdbaca=&kdklpk=&dlpd=4&ptgs="
    "&__format=xlsx"
)

# ===================== GUI =====================
root = tk.Tk()
root.title("Downloader PLN - XLSX Merge Sheets")
root.geometry("760x650")

# -------- SERVER --------
tk.Label(root, text="Server", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
server_var = tk.StringVar(value="INTRANET")

frame_server = tk.Frame(root)
frame_server.pack(anchor="w", padx=20)

tk.Radiobutton(frame_server, text="INTRANET (ap2t.pln.co.id)",
               variable=server_var, value="INTRANET").pack(anchor="w")

tk.Radiobutton(frame_server, text="INTERNET (portalapp.iconpln.co.id)",
               variable=server_var, value="INTERNET").pack(anchor="w")

# -------- INPUT --------
frame_input = tk.Frame(root)
frame_input.pack(fill="x", padx=10, pady=10)

tk.Label(frame_input, text="BLTH (YYYYMM)").grid(row=0, column=0, sticky="w")
blth_entry = ttk.Entry(frame_input, width=12)
blth_entry.grid(row=0, column=1, padx=5)
blth_entry.insert(0, "202512")

tk.Label(frame_input, text="UNITAP").grid(row=1, column=0, sticky="w")
unitap_var = tk.StringVar()
unitap_combo = ttk.Combobox(
    frame_input,
    textvariable=unitap_var,
    values=list(UNITAP_DICT.keys()),
    state="readonly",
    width=15
)
unitap_combo.grid(row=1, column=1, padx=5)
unitap_combo.current(0)

# -------- DROPDOWN UNIT DATA (DI BAWAH UNITAP) --------
tk.Label(frame_input, text="UNITUP").grid(row=2, column=0, sticky="w")
unitdata_var = tk.StringVar()

unitdata_combo = ttk.Combobox(
    frame_input,
    textvariable=unitdata_var,
    state="readonly",
    width=15
)
unitdata_combo.grid(row=2, column=1, padx=5)

def refresh_unitdata_options(*args):
    unitap = unitap_var.get().strip()
    units = UNITAP_DICT.get(unitap, [])
    unitdata_combo["values"] = ["SEMUA"] + units
    unitdata_combo.current(0)  # default SEMUA

unitap_combo.bind("<<ComboboxSelected>>", refresh_unitdata_options)
refresh_unitdata_options()

# -------- LOG --------
tk.Label(root, text="Log Proses", font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10)
log_box = tk.Text(root, height=20)
log_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

def log(msg: str):
    log_box.insert(tk.END, msg + "\n")
    log_box.see(tk.END)
    root.update_idletasks()

# ===================== CORE =====================
def proses_download():
    log_box.delete("1.0", tk.END)

    blth = blth_entry.get().strip()
    unitap = unitap_var.get().strip()

    units_all = UNITAP_DICT.get(unitap, [])
    unit_selected = unitdata_var.get().strip()

    # ---- TENTUKAN LIST UNIT YANG DIPROSES ----
    if not units_all:
        messagebox.showerror("Error", f"Daftar UNIT untuk UNITAP {unitap} kosong / tidak ditemukan.")
        return

    if unit_selected and unit_selected != "SEMUA":
        ups = [unit_selected]   # hanya 1 unit
        output_file = f"DLPD_ACMT_{unitap}_{blth}_{unit_selected}.xlsx"
    else:
        ups = units_all         # semua unit
        output_file = f"DLPD_ACMT_{unitap}_{blth}_ALL.xlsx"

    base_url = (
        "https://ap2t.pln.co.id"
        if server_var.get() == "INTRANET"
        else "https://portalapp.iconpln.co.id"
    )

    if not base_url.startswith("https://"):
        messagebox.showerror("Error", "Base URL HARUS https://")
        return

    log(f"SERVER    : {server_var.get()}")
    log(f"UNITAP    : {unitap}")
    log(f"UNITUP    : {unit_selected if unit_selected else 'SEMUA'}")
    log(f"PROSES    : {', '.join(ups)}")   # <- ini yang memastikan SEMUA akan diproses
    log(f"OUTPUT    : {output_file}")
    log("=" * 60)

    http = urllib3.PoolManager(
        cert_reqs="CERT_NONE",
        timeout=urllib3.Timeout(connect=10, read=120),
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
    )

    dfs_final = []

    for up in ups:
        log(f"\nUNIT {up}")

        for attempt in range(1, MAX_RETRY + 1):
            log(f"  Attempt {attempt}")
            tmp_path = None

            try:
                fd, tmp_path = tempfile.mkstemp(suffix=".xlsx")
                os.close(fd)

                url = URL_TEMPLATE.format(base=base_url, up=up, blth=blth)
                resp = http.request("GET", url, preload_content=False)

                if resp.status != 200:
                    raise Exception(f"HTTP {resp.status}")

                ctype = resp.headers.get("Content-Type", "").lower()
                if "excel" not in ctype and "spreadsheetml" not in ctype:
                    raise Exception(f"Bukan XLSX (Content-Type: {ctype})")

                with open(tmp_path, "wb") as f:
                    for chunk in resp.stream(1024 * 64):
                        if not chunk:
                            break
                        f.write(chunk)

                resp.release_conn()

                sheets = pd.read_excel(tmp_path, sheet_name=None)

                total_rows = 0
                for df in sheets.values():
                    df["UNITAP"] = unitap
                    df["UP"] = up
                    dfs_final.append(df)
                    total_rows += len(df)

                log(f"  ✔ {len(sheets)} sheet | {total_rows:,} baris")
                break

            except Exception as e:
                log(f"  ✖ {e}")
                time.sleep(RETRY_DELAY)

            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)

    if not dfs_final:
        messagebox.showerror("Gagal", "Tidak ada data berhasil diunduh")
        return

    final_df = pd.concat(dfs_final, ignore_index=True)
    final_df.to_excel(output_file, index=False)

    log("\n" + "=" * 60)
    log(f"SELESAI ✅ TOTAL BARIS: {len(final_df):,}")
    messagebox.showinfo("Selesai", output_file)

# -------- BUTTON --------
ttk.Button(
    root,
    text="▶ MULAI PROSES",
    command=lambda: threading.Thread(target=proses_download, daemon=True).start()
).pack(pady=10)

root.mainloop()
