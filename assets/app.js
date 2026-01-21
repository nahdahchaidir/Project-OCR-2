const API_BASE = "api";
const REDIRECT_OK = "5 - Fix - Visualisasi_data.html";

const form = document.getElementById("loginForm");
const toast = document.getElementById("toast");
const fillDemo = document.getElementById("fillDemo");

function showToast(type, msg) {
  toast.className = `toast ${type}`;
  toast.textContent = msg;
}

function setLoading(isLoading) {
  const btn = form.querySelector('button[type="submit"]');
  btn.disabled = isLoading;
  btn.textContent = isLoading ? "Memproses..." : "Masuk";
}

fillDemo.addEventListener("click", () => {
  document.getElementById("username").value = "operator_pln";
  document.getElementById("password").value = "pln12345";
  showToast("ok", "Demo terisi. Pastikan usernya sudah dibuat via Postman.");
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  showToast("", "");
  setLoading(true);

  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;

  try {
    const res = await fetch(`${API_BASE}/login.php`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    const data = await res.json();

    if (!res.ok || !data.ok) {
      showToast("err", data.message || "Login gagal.");
      return;
    }

    localStorage.setItem("pln_token", data.token);
    localStorage.setItem("pln_user", JSON.stringify(data.user));

    showToast("ok", "Login berhasil. Mengalihkan...");
    setTimeout(() => (window.location.href = REDIRECT_OK), 600);
  } catch {
    showToast("err", "Tidak bisa terhubung ke server. Pastikan Laragon jalan.");
  } finally {
    setLoading(false);
  }
});
