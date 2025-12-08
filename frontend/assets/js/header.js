import { initNotifications, initWebsocket } from './notifications.js';

function getToken() {
  return localStorage.getItem("access_token");
}

export async function initHeader() {
  const token = localStorage.getItem("access_token");

  const navGuest = document.getElementById("nav-guest");
  const navUser  = document.getElementById("nav-user");
  const headerNickname = document.getElementById("header-nickname");
  if (headerNickname) {
    headerNickname.textContent = nickname ?? "";
  }
  const headerInitial  = document.getElementById("header-initial");

  if (!headerNickname || !headerInitial) return;

  if (!token) {
    if (navGuest) navGuest.classList.remove("d-none");
    if (navUser)  navUser.classList.add("d-none");
    return;
  }

  const res = await fetch("http://127.0.0.1:8000/user/profile", {
    headers: { Authorization: "Bearer " + token },
  });
  if (!res.ok) return;
  const user = await res.json();

  const needProfile = !user.nickname;   // 닉네임만 필수

  if (needProfile) {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    if (navGuest) navGuest.classList.remove("d-none");
    if (navUser)  navUser.classList.add("d-none");
    return;
  }

  // 닉네임 있는 로그인 사용자
  if (navGuest) navGuest.classList.add("d-none");
  if (navUser)  navUser.classList.remove("d-none");
  headerNickname.textContent = user.nickname;
  headerInitial.textContent  = user.nickname[0];
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
