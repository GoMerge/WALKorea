import { initNotifications, initWebsocket } from "./notifications.js";
import { goLoginWithReturn } from "./mypage_common.js";

const API_BASE = "";

function getToken() {
  return localStorage.getItem("access_token");
}

export async function initHeader() {
  const token = getToken();

  const navGuest = document.getElementById("nav-guest");
  const navUser  = document.getElementById("nav-user");
  const headerNickname = document.getElementById("header-nickname");
  const headerInitial  = document.getElementById("header-initial");

  if (!headerNickname || !headerInitial) return;

  // 비로그인 상태
  if (!token) {
    navGuest && navGuest.classList.remove("d-none");
    navUser  && navUser.classList.add("d-none");
    headerNickname.textContent = "";
    headerInitial.textContent  = "";
    return;
  }

  // 🔥 프로필 조회 (한 번만!)
  const res = await fetch(API_BASE + "/user/profile", {
    headers: { Authorization: `Bearer ${token}` },  // 백틱 통일
  });
  
  if (!res.ok) {
    navGuest && navGuest.classList.remove("d-none");
    navUser  && navUser.classList.add("d-none");
    return;
  }

  const user = await res.json();
  const needProfile = !user.nickname;

  if (needProfile) {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    navGuest && navGuest.classList.remove("d-none");
    navUser  && navUser.classList.add("d-none");
    return;
  }

  // 정상 로그인 UI
  navGuest && navGuest.classList.add("d-none");
  navUser  && navUser.classList.remove("d-none");
  const baseName = user.nickname || user.userid || "사용자";
  headerNickname.textContent = baseName;
  headerInitial.textContent  = baseName[0];

  // 🔥 알림 + WebSocket 초기화 (한 번만!)
  try {
    await initNotifications();  // 배지 즉시 업데이트
    if (user.id) {
      initWebsocket(user.id);   // 실시간 알림
    }
  } catch (e) {
    console.error('알림 초기화 에러:', e);
  }
}

// 이 함수는 다른 파일에서 export 해서 쓰는 게 맞으면 export 붙이기
export function requireLoginForMypage() {
  const token = getToken();
  if (!token) {
    alert("로그인이 필요합니다.");
    goLoginWithReturn();
    return false;
  }
  return true;
  }


  // 로그아웃 버튼 전역 처리
document.addEventListener("click", (e) => {
  const logoutBtn = e.target.closest("#nav-logout");
  if (!logoutBtn) return;

  e.preventDefault();
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  window.location.href = "/login";
});


// 페이지 로드 완료시 헤더 + 알림 자동 초기화
document.addEventListener('DOMContentLoaded', async () => {
  await initHeader();  // 헤더 + 알림 모두 초기화
});