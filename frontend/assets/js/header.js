import { initNotifications, initWebsocket } from './notifications.js';

function getToken() {
  return localStorage.getItem("access_token");
}

export async function initHeader() {
  console.log('🚀 initHeader 시작!');
  const token = getToken();
  console.log('🔑 토큰:', token ? '있음' : '없음');

  const navGuest = document.getElementById("nav-guest");
  const navUser = document.getElementById("nav-user");
  const logoutBtn = document.getElementById("nav-logout");
  const nickSpan = document.getElementById("header-nickname");  
  const initialDiv = document.getElementById("header-initial");

  if (!token) {
    if (navGuest) navGuest.classList.remove("d-none");
    if (navUser) navUser.classList.add("d-none");
    return;
  }

  if (navGuest) navGuest.classList.add("d-none");
  if (navUser) navUser.classList.remove("d-none");

  try {
    const res = await fetch("http://127.0.0.1:8000/user/profile", {
      headers: { Authorization: "Bearer " + token },
    });
    if (!res.ok) return;

    const profile = await res.json();
    console.log("👤 프로필:", profile);

    const nick = profile.nickname || profile.name || "사용자";
    if (nickSpan) nickSpan.textContent = nick;
    if (initialDiv) initialDiv.textContent = nick[0];

    if (profile.id) {
      await initNotifications();
      initWebsocket(profile.id);
    }
  } catch (e) {
    console.error("header profile load error", e);
  }

  if (logoutBtn) {
    logoutBtn.addEventListener("click", (e) => {
      e.preventDefault();
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = "/";
    });
  }

   document.querySelectorAll("a[href='/login']").forEach(btn => {
    btn.onclick = (e) => {
      e.preventDefault();
      window.goLoginWithReturn();
    };
  });
}

function requireLoginForMypage() {
  const token = localStorage.getItem("access_token");
  if (!token) {
    alert("로그인이 필요합니다.");
    goLoginWithReturn();  // ← 여기서 현재 URL 저장 후 로그인 화면으로
    return false;
  }
  return true;
}
