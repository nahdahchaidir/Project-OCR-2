const API_BASE = "api";
const LOGIN_PAGE = "6 - Fix - Login.html";

function token() {
  return localStorage.getItem("pln_token") || "";
}

function hardLogout() {
  localStorage.removeItem("pln_token");
  localStorage.removeItem("pln_user");
  window.location.href = LOGIN_PAGE;
}

function injectTopbar(username) {
  const bar = document.createElement("div");
  bar.style.position = "fixed";
  bar.style.top = "14px";
  bar.style.right = "14px";
  bar.style.zIndex = "9999";
  bar.style.display = "flex";
  bar.style.gap = "10px";
  bar.style.alignItems = "center";
  bar.style.padding = "10px 12px";
  bar.style.borderRadius = "14px";
  bar.style.background = "rgba(255,255,255,.86)";
  bar.style.border = "1px solid rgba(15,23,42,.12)";
  bar.style.boxShadow = "0 16px 40px rgba(0,0,0,.18)";
  bar.innerHTML = `
    <span style="font-family:system-ui;font-size:13px;color:rgba(15,23,42,.85)">
      Login: <strong>@${username}</strong>
    </span>
    <button id="plnLogoutBtn" style="
      height:34px;padding:0 12px;border-radius:12px;cursor:pointer;
      border:1px solid rgba(15,23,42,.18);background:transparent;font-weight:700;
    ">Logout</button>
  `;
  document.body.appendChild(bar);

  document.getElementById("plnLogoutBtn").addEventListener("click", async () => {
    try {
      await fetch(`${API_BASE}/logout.php`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token()}` }
      });
    } catch {}
    hardLogout();
  });
}

(async function () {
  if (!token()) return hardLogout();

  try {
    const res = await fetch(`${API_BASE}/me.php`, {
      headers: { Authorization: `Bearer ${token()}` },
    });
    const data = await res.json();

    if (!res.ok || !data.ok) return hardLogout();

    injectTopbar(data.user.username);
  } catch {
    // kalau server down, tetap kunci halaman
    hardLogout();
  }
})();
