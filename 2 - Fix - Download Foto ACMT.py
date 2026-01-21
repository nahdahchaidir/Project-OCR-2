# pip install requests urllib3

import os
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import threading
import urllib3

# Matikan peringatan SSL insecure
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# =================== KONFIGURASI DEFAULT =================== #
DEFAULT_RETRIES = 1     # default maksimal dicoba ulang
RETRY_DELAY = 1         # detik jeda tiap gagal


# Fungsi untuk membuat folder jika belum ada
def create_folder(folder):
    try:
        os.makedirs(folder, exist_ok=True)
        print(f"[INFO] Folder {folder} siap digunakan.")
    except Exception as e:
        print(f"[ERROR] Gagal membuat folder {folder}: {e}")


# Fungsi download dengan retry
def download_image(image_id, blth, output_folder, session, base_url, failed_ids, max_retries):
    url = f"https://{base_url}/acmt/DisplayBlobServlet1?idpel={image_id}&blth={blth}&unitup="
    file_name = f"{image_id}.jpg"
    file_path = os.path.join(output_folder, file_name)

    for attempt in range(1, max_retries + 1):
        try:
            response = session.get(url, timeout=15, verify=False)
            response.raise_for_status()

            if len(response.content) == 0:
                raise Exception("Isi file kosong (0 KB).")

            with open(file_path, "wb") as file:
                file.write(response.content)

            print(f"[SUCCESS] ID {image_id} berhasil diunduh.")
            return True

        except Exception as e:
            print(f"[RETRY {attempt}/{max_retries}] ID {image_id}: {e}")
            if attempt < max_retries:
                time.sleep(RETRY_DELAY)
            else:
                print(f"[FAILED] Gagal permanen ID {image_id}.")
                failed_ids.append(image_id)
                return False


# Fungsi paralel download dengan progress
def download_images_with_progress(ids, blth, output_folder, session, base_url, progress_var, label_var, failed_ids, max_retries, max_threads=10):
    total = len(ids)
    done = 0

    with ThreadPoolExecutor(max_threads) as executor:
        futures = {
            executor.submit(download_image, image_id, blth, output_folder, session, base_url, failed_ids, max_retries): image_id
            for image_id in ids
        }

        for future in as_completed(futures):
            done += 1
            percent = int((done / total) * 100)
            progress_var.set(percent)
            label_var.set(f"Progress: {percent}% ({done}/{total})")


# Fungsi utama
def main(thbl, cookie, input_file, base_url, progress_var, label_var, root, max_retries):
    failed_ids = []
    try:
        with open(input_file, "r") as file:
            ids = [line.strip() for line in file if line.strip()]

        output_folder = "2_images"
        create_folder(output_folder)

        # folder log gagal unduh
        log_folder = "4_log_gagal_unduh_foto"
        create_folder(log_folder)

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Connection": "keep-alive",
            "Referer": f"https://{base_url}/acmt/Main.html",
            "Cookie": cookie,
        }

        session = requests.Session()
        session.headers.update(headers)

        download_images_with_progress(ids, thbl, output_folder, session, base_url, progress_var, label_var, failed_ids, max_retries, max_threads=10)

        if failed_ids:
            # nama file gagal = failed_ids_<nama_input>.txt di dalam folder log
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            failed_file = os.path.join(log_folder, f"failed_ids_{base_name}.txt")

            with open(failed_file, "w") as f:
                for fid in failed_ids:
                    f.write(f"{fid}\n")

            messagebox.showwarning("Selesai", f"Ada {len(failed_ids)} ID gagal.\nLihat di folder:\n{failed_file}")
        else:
            messagebox.showinfo("Selesai", "Semua gambar berhasil diunduh!")

    except FileNotFoundError:
        messagebox.showerror("Error", f"File {input_file} tidak ditemukan.")
    except Exception as e:
        messagebox.showerror("Error", f"Terjadi kesalahan: {e}")


# GUI Tkinter
def run_gui():
    def browse_file():
        filename = filedialog.askopenfilename(
            title="Pilih file idpel.txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filename:
            entry_file.delete(0, tk.END)
            entry_file.insert(0, filename)

    def start_download():
        thbl = entry_thbl.get().strip()
        cookie = entry_cookie.get().strip()
        input_file = entry_file.get().strip()
        base_url = combo_server.get()
        max_retries = int(spin_retry.get())

        if not thbl or not cookie or not input_file or not base_url:
            messagebox.showerror("Input Error", "THBL, Cookie, File IDPEL, Server, dan Retry harus diisi!")
            return

        threading.Thread(
            target=main,
            args=(thbl, cookie, input_file, base_url, progress_var, label_var, root, max_retries),
            daemon=True
        ).start()

    root = tk.Tk()
    root.title("Downloader Foto ACMT")

    tk.Label(root, text="THBL (misal 202510):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
    entry_thbl = tk.Entry(root, width=50)
    entry_thbl.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(root, text="Cookie:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
    entry_cookie = tk.Entry(root, width=50)
    entry_cookie.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(root, text="File IDPEL:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
    entry_file = tk.Entry(root, width=50)
    entry_file.grid(row=2, column=1, padx=5, pady=5)
    tk.Button(root, text="Browse", command=browse_file).grid(row=2, column=2, padx=5, pady=5)

    tk.Label(root, text="Server:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
    combo_server = ttk.Combobox(root, values=["portalapp.iconpln.co.id", "ap2t.pln.co.id"], width=47)
    combo_server.grid(row=3, column=1, padx=5, pady=5)
    combo_server.current(0)

    tk.Label(root, text="Retry (default 1):").grid(row=4, column=0, sticky="w", padx=5, pady=5)
    spin_retry = tk.Spinbox(root, from_=1, to=20, width=5)
    spin_retry.delete(0, tk.END)
    spin_retry.insert(0, str(DEFAULT_RETRIES))
    spin_retry.grid(row=4, column=1, sticky="w", padx=5, pady=5)

    progress_var = tk.IntVar()
    label_var = tk.StringVar(value="Progress: 0%")

    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=400)
    progress_bar.grid(row=5, column=0, columnspan=3, padx=5, pady=10)

    progress_label = tk.Label(root, textvariable=label_var)
    progress_label.grid(row=6, column=0, columnspan=3)

    btn_start = tk.Button(root, text="Mulai Download", command=start_download)
    btn_start.grid(row=7, column=0, columnspan=3, pady=10)

    tk.Label(root, text="Created by MONEVMU").grid(row=8, column=0, sticky="w", padx=5, pady=5)

    root.mainloop()


if __name__ == "__main__":
    run_gui()
