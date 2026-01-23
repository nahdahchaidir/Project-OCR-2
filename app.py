import os
import subprocess
import json
import threading
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ============================================
# KONFIGURASI SCRIPT
# ============================================

SCRIPT_MAPPING = {
    'data_cust_new': '0 - Fix - Data Cust ACMT DLPD - UX - New.py',
    'split_idpel': '1 - Fix - Split Idpel.py', 
    'download_foto': '2 - Fix - Download Foto ACMT.py',
    'verifikasi_kwh': '3 - Fix - Verifikasi Fisik kWh Meter - TFLITE.py',
    'filter_output_scan': '4 - Fix - Filter Output Scan.py'
}

# ============================================
# FUNGSI UNTUK MENJALANKAN SCRIPT DENGAN GUI
# ============================================

def run_script_with_gui(script_path):
    """
    Menjalankan script Python yang menggunakan tkinter GUI
    dengan environment variable khusus untuk headless mode
    """
    env = os.environ.copy()
    env['DISPLAY'] = ':0'  # Untuk Linux/Mac dengan X11
    env['PYTHONUNBUFFERED'] = '1'
    
    # Untuk MacOS, coba beberapa opsi
    if sys.platform == 'darwin':  # MacOS
        env['TK_SILENCE_DEPRECATION'] = '1'
    
    try:
        # Jalankan script
        result = subprocess.run(
            ['python3', script_path],
            capture_output=True,
            text=True,
            env=env,
            timeout=30  # Timeout 30 detik untuk GUI
        )
        
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            'stdout': '',
            'stderr': 'Timeout: Script GUI membutuhkan interaksi user',
            'returncode': 1
        }
    except Exception as e:
        return {
            'stdout': '',
            'stderr': f'Error: {str(e)}',
            'returncode': 1
        }

def run_non_gui_script(script_path):
    """Menjalankan script non-GUI"""
    try:
        result = subprocess.run(
            ['python3', script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 menit
        )
        
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            'stdout': '',
            'stderr': 'Timeout: Script terlalu lama',
            'returncode': 1
        }
    except Exception as e:
        return {
            'stdout': '',
            'stderr': f'Error: {str(e)}',
            'returncode': 1
        }

# ============================================
# ENDPOINT API
# ============================================

@app.route('/api/run/<script_name>', methods=['POST', 'GET'])  # Terima POST dan GET
def run_script(script_name):
    """Endpoint untuk menjalankan script Python"""
    
    # Log request
    print(f"📦 Request menjalankan script: {script_name}")
    print(f"📋 Method: {request.method}")
    
    # Cek apakah script ada di mapping
    if script_name not in SCRIPT_MAPPING:
        return jsonify({
            'error': f'Script "{script_name}" tidak ditemukan',
            'available_scripts': list(SCRIPT_MAPPING.keys())
        }), 404
    
    script_file = SCRIPT_MAPPING[script_name]
    
    # Cek apakah file script ada
    if not os.path.exists(script_file):
        return jsonify({
            'error': f'File "{script_file}" tidak ditemukan',
            'current_dir': os.getcwd(),
            'files': os.listdir('.')
        }), 404
    
    print(f"🚀 Menjalankan: {script_file}")
    
    # Tentukan jenis script (GUI atau non-GUI)
    is_gui_script = script_name in ['data_cust_new', 'download_foto']
    
    try:
        if is_gui_script:
            print("⚠️  Script GUI - mungkin perlu interaksi user")
            result = run_script_with_gui(script_file)
        else:
            result = run_non_gui_script(script_file)
        
        print(f"✅ Selesai dengan return code: {result['returncode']}")
        
        return jsonify({
            'stdout': result['stdout'],
            'stderr': result['stderr'],
            'returncode': result['returncode'],
            'script': script_name,
            'file': script_file,
            'is_gui': is_gui_script,
            'success': result['returncode'] == 0
        })
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({
            'error': f'Error menjalankan script: {str(e)}',
            'script': script_name,
            'file': script_file
        }), 500

# ============================================
# ENDPOINT UTAMA
# ============================================

@app.route('/')
def index():
    """Serve halaman web utama"""
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>PLN Tools Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; padding: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .error { color: #d00; background: #fee; padding: 20px; border-radius: 5px; }
                .success { color: #090; background: #efe; padding: 20px; border-radius: 5px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔧 PLN Tools Dashboard</h1>
                <div class="error">
                    <h2>File index.html tidak ditemukan</h2>
                    <p>Pastikan file HTML ada di direktori yang sama dengan app.py</p>
                    <p>Direktori saat ini: <code>""" + os.getcwd() + """</code></p>
                    <p>File yang ada:</p>
                    <ul>
        """ + "\n".join([f"<li>{f}</li>" for f in os.listdir('.') if f.endswith('.html') or f.endswith('.py')]) + """
                    </ul>
                </div>
                <div class="success">
                    <h3>✅ Flask API berjalan dengan baik</h3>
                    <p>Endpoint yang tersedia:</p>
                    <ul>
                        <li><a href="/api/run/split_idpel">/api/run/split_idpel</a> (GET/POST)</li>
                        <li><a href="/api/run/filter_output_scan">/api/run/filter_output_scan</a></li>
                        <li><a href="/api/run/verifikasi_kwh">/api/run/verifikasi_kwh</a></li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        """

@app.route('/api/scripts')
def list_scripts():
    """Endpoint untuk melihat daftar script yang tersedia"""
    scripts_info = []
    
    for name, filename in SCRIPT_MAPPING.items():
        exists = os.path.exists(filename)
        scripts_info.append({
            'name': name,
            'filename': filename,
            'exists': exists,
            'is_gui': name in ['data_cust_new', 'download_foto']
        })
    
    return jsonify({
        'scripts': scripts_info,
        'total': len(scripts_info),
        'current_directory': os.getcwd()
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'pln-tools-api',
        'endpoints': {
            '/': 'Web interface',
            '/api/run/<script>': 'Run Python script',
            '/api/scripts': 'List available scripts',
            '/health': 'Health check'
        }
    })

# ============================================
# RUN SERVER
# ============================================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 PLN Tools API Server")
    print("=" * 60)
    print(f"📁 Direktori: {os.getcwd()}")
    print(f"🐍 Python: {sys.version}")
    print("=" * 60)
    
    # Cek file yang ada
    print("📋 File Python yang ditemukan:")
    for f in os.listdir('.'):
        if f.endswith('.py'):
            print(f"  • {f}")
    
    print("=" * 60)
    print("🔌 Endpoint yang tersedia:")
    print("  • GET  /              → Web Interface")
    print("  • POST /api/run/<name> → Jalankan script")
    print("  • GET  /api/scripts   → Daftar script")
    print("  • GET  /health        → Health check")
    print("=" * 60)
    print("📡 Server berjalan di: http://localhost:5000")
    print("=" * 60)
    
    app.run(debug=True, port=5000, threaded=True)