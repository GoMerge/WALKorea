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

  // 헤더 요소가 아예 없는 페이지면 그냥 종료
  if (!headerNickname || !headerInitial) return;

  // 비로그인 상태
  if (!token) {
    navGuest && navGuest.classList.remove("d-none");
    navUser  && navUser.classList.add("d-none");
    headerNickname.textContent = "";
    headerInitial.textContent  = "";
    return;
  }

  // 로그인 사용자 프로필 조회
  const res = await fetch(API_BASE + "/user/profile", {
    headers: { Authorization: "Bearer " + token },
  });
  if (!res.ok) {
    // 토큰 이상 등 → 비로그인으로 처리
    navGuest && navGuest.classList.remove("d-none");
    navUser  && navUser.classList.add("d-none");
    headerNickname.textContent = "";
    headerInitial.textContent  = "";
    return;
  }

  const user = await res.json();

  const needProfile = !user.nickname;  // 닉네임 없으면 프로필 미완성

  if (needProfile) {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    navGuest && navGuest.classList.remove("d-none");
    navUser  && navUser.classList.add("d-none");
    headerNickname.textContent = "";
    headerInitial.textContent  = "";
    return;
  }

  // 닉네임 있는 정상 로그인 상태
  navGuest && navGuest.classList.add("d-none");
  navUser  && navUser.classList.remove("d-none");

  const baseName = user.nickname || user.userid || "사용자";
  headerNickname.textContent = baseName;
  headerInitial.textContent  = baseName[0];
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
