import os
import re
import pandas as pd
import sys

# Paksa encoding output UTF-8 (agar tidak error di Windows cp1252)
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# ==================================================
# 1 KONFIGURASI
# ==================================================
FOLDER_SCAN = "3_scan_output"
EXCEL_INPUT = "DLPD_ACMT_32AMS_202601.xlsx"

# ==================================================
# 2 AMBIL IDPEL DARI NAMA FILE SCAN
# ==================================================
def ambil_idpel_dari_filename(folder):
    idpel_set = set()

    for file in os.listdir(folder):
        nama_file, _ = os.path.splitext(file)
        match = re.search(r"\d+", nama_file)  # ambil angka IDPEL

        if match:
            idpel_set.add(match.group())

    return idpel_set


# ==================================================
# 3 DETEKSI KOLOM IDPEL DI EXCEL (CASE-INSENSITIVE)
# ==================================================
def cari_kolom_idpel(df):
    for col in df.columns:
        if "idpel" in col.lower():
            return col
    raise Exception("Kolom IDPEL tidak ditemukan di file Excel!")


# ==================================================
# 4 MAIN PROCESS
# ==================================================
def main():
    print("Mengambil IDPEL dari folder scan...")
    idpel_folder = ambil_idpel_dari_filename(FOLDER_SCAN)

    if not idpel_folder:
        raise Exception("IDPEL dari folder scan tidak ditemukan!")

    print(f"Total IDPEL ditemukan: {len(idpel_folder)}")

    print("Membaca file Excel input...")
    df = pd.read_excel(EXCEL_INPUT, dtype=str)

    kolom_idpel = cari_kolom_idpel(df)
    print(f"Kolom IDPEL terdeteksi: {kolom_idpel}")

    print("Melakukan filter data Excel...")
    df_filtered = df[df[kolom_idpel].isin(idpel_folder)]
    print(f"Total data setelah filter: {len(df_filtered)} baris")

    # ==================================================
    # 5 NAMA FILE OUTPUT OTOMATIS
    # ==================================================
    nama_awal = os.path.splitext(os.path.basename(EXCEL_INPUT))[0]
    excel_output = f"Output_Scan_{nama_awal}.xlsx"

    print("Menyimpan hasil ke Excel...")
    df_filtered.to_excel(excel_output, index=False)

    print(f"SELESAI -> {excel_output}")


# ==================================================
# 6 EXECUTE
# ==================================================
if __name__ == "__main__":
    main()
