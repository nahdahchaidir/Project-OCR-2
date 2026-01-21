from flask import Flask, jsonify
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Sesuaikan nama HTML kamu kalau filenya "5 - Fix - Visualisasi_data.html"
HTML_FILE = "5 - Fix - Visualisasi_data.html"  # atau "Visualisasi_data.html"

SCRIPTS = {
    "data_cust_edit": "0 - Fix - Data Cust ACMT DLPD - UX - Edit.py",
    "data_cust_new": "0 - Fix - Data Cust ACMT DLPD - UX - New.py",
    "split_idpel": "1 - Fix - Split Idpel.py",
    "download_foto": "2 - Fix - Download Foto ACMT.py",
    "verifikasi_kwh": "3 - Fix - Verifikasi Fisik kWh Meter - TFLITE.py",
    "filter_output_scan": "4 - Fix - Filter Output Scan.py",
}

# static_folder="." supaya folder gambar/output kamu bisa diakses relatif (mis. 3_scan_output/idpel.jpg)
app = Flask(__name__, static_folder=".", static_url_path="")

@app.get("/")
def index():
    # Serve HTML utama
    return app.send_static_file(HTML_FILE)

@app.post("/api/run/<tool>")
def run_tool(tool: str):
    if tool not in SCRIPTS:
        return jsonify(error="Tool tidak dikenal"), 404

    script_path = BASE_DIR / SCRIPTS[tool]
    if not script_path.exists():
        return jsonify(error=f"File tidak ditemukan: {script_path.name}"), 404

    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=60 * 60,  # 1 jam
        )
        return jsonify(
            stdout=proc.stdout,
            stderr=proc.stderr,
            returncode=proc.returncode,
        )
    except subprocess.TimeoutExpired:
        return jsonify(error="Timeout (script terlalu lama)"), 408
    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
