import { initHeader } from "/assets/js/header.js";
import { setupHeaderAndProfile, loadProfileWeather } from "/assets/js/mypage_common.js";
import { goLoginWithReturn } from "./mypage_common.js";

const API_BASE = "";

function handleUnauthorized(res) {
  if (res.status === 401) {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");

    if (window.location.pathname !== "/") {
      window.location.href = "/";
    } else {
      window.location.reload();
    }
    return true; // 여기서 끝내야 할 때
  }
  return false;
}

async function loadProfile(token) {
  const res = await fetch(API_BASE + "/user/profile", {
    headers: { "Authorization": "Bearer " + token }
  });
  if (!res.ok) return;
  const data = await res.json();

  const baseName = data.nickname || data.userid || "사용자";

  // 상단/사이드바 (굳이 중복이지만 문제는 없음)
  const navNick = document.getElementById("header-nickname");
  if (navNick) navNick.textContent = data.nickname || baseName;
  const sideNick = document.getElementById("side-nickname");
  const sideEmail = document.getElementById("side-email");
  const sideInit  = document.getElementById("side-initial");
  if (sideNick) sideNick.textContent = baseName;
  if (sideEmail) sideEmail.textContent = data.email || "";
  if (sideInit)  sideInit.textContent  = baseName[0];

  // ★ 내 정보 폼
  document.getElementById("userid").value   = data.userid   || "";
  document.getElementById("email").value    = data.email    || "";
  document.getElementById("nickname").value = data.nickname || "";
  document.getElementById("phonenum").value = data.phonenum || "";
  if (data.birthday) document.getElementById("birthday").value = data.birthday;
  if (data.gender)   document.getElementById("gender").value   = data.gender;

  document.getElementById("edit-region-label").value = data.region_name || "";
  document.getElementById("edit-region-id").value    = data.region_id   || "";
}

// access_token 없으면 로그인으로 돌리고, 있으면 전체 초기화
export async function initProfilePage() {
  const token = localStorage.getItem("access_token");
  if (!token) {
    alert("로그인이 필요합니다.");
    goLoginWithReturn();
    return;
  }

  await initHeader();            // 헤더 골격
  await setupHeaderAndProfile(); // 로그인 사용자 + 왼쪽 박스
  await loadProfileWeather();    // 날씨 6일치
  await loadNotifications();     // 알림 뱃지/목록
  await loadSidos();             // 시/군/동 리스트 준비
  await loadProfile(token);      // ★ 내 정보 폼 채우기

  // 이벤트 바인딩 (지금 코드 그대로)
  document.getElementById("region-apply-btn").onclick = applyRegionSelection;

  // 프로필 저장
  const profileForm = document.getElementById("profile-form");
  profileForm.addEventListener("submit", (e) => onSubmitProfile(e, token));

  // 비밀번호 보기/숨기기 토글
  const newPwInput = document.getElementById("new_password");
  const newPwConfirmInput = document.getElementById("new_password_confirm");

  document.getElementById("toggle_new_pw").addEventListener("click", () => {
  const isHidden = newPwInput.type === "password";
  newPwInput.type = isHidden ? "text" : "password";
  });

  document.getElementById("toggle_new_pw2").addEventListener("click", () => {
  const isHidden = newPwConfirmInput.type === "password";
  newPwConfirmInput.type = isHidden ? "text" : "password";
  });

  // 비밀번호 변경 submit
  const pwForm = document.getElementById("pw-form");
  pwForm.addEventListener("submit", (e) => onSubmitPassword(e, token));


  document.getElementById("logout-btn").addEventListener("click", () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    window.location.href = "/";
  });
  document.getElementById("delete-btn").addEventListener("click", onDeleteAccount);

  // 닉네임 중복 체크
  const nickInput = document.getElementById("nickname");
  const nickMsg = document.getElementById("nickname-msg");
  let nickTimer = null;
  nickInput.addEventListener("input", function() {
    clearTimeout(nickTimer);
    const val = nickInput.value.trim();
    if (val.length < 2) {
      nickMsg.textContent = "닉네임을 2자 이상 입력하세요.";
      nickMsg.className = "small text-danger mt-1";
      return;
    }
    nickTimer = setTimeout(async () => {
      const res = await fetch(`/auth/check-nickname?nickname=${encodeURIComponent(val)}`);
      const data = await res.json().catch(()=>null);
      if (data && data.result === "dup") {
        nickMsg.textContent = "이미 사용 중인 닉네임입니다.";
        nickMsg.className = "small text-danger mt-1";
      } else {
        nickMsg.textContent = "사용 가능한 닉네임입니다.";
        nickMsg.className = "small text-success mt-1";
      }
    }, 400);
  });

  // 휴대폰 번호 포맷 체크
  const phoneInput = document.getElementById("phonenum");
  const phoneMsg = document.getElementById("phone-msg");
  phoneInput.addEventListener("input", function() {
    let val = phoneInput.value.replace(/\D/g, "");
    phoneInput.value = val;
    if (!val) {
      phoneMsg.textContent = "";
      return;
    }
    if (/^010\d{8}$/.test(val)) {
      phoneMsg.textContent = "사용 가능한 번호입니다.";
      phoneMsg.className = "small text-success mt-1";
    } else {
      phoneMsg.textContent = "010으로 시작하는 11자리 숫자로 입력하세요.";
      phoneMsg.className = "small text-danger mt-1";
    }
  });
}
  
async function onSubmitProfile(e, token) {
  e.preventDefault();

  const payload = {
    nickname: document.getElementById("nickname").value.trim(),
    phonenum: document.getElementById("phonenum").value.trim(),
    birthday: document.getElementById("birthday").value || null,
    gender: document.getElementById("gender").value || null,
    region_id: document.getElementById("edit-region-id").value || null,
  };

  const res = await fetch(API_BASE + "/user/profile", {
    method: "PUT",  
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + token,
    },
    body: JSON.stringify(payload),
  });

  if (res.ok) {
    alert("프로필을 저장했습니다.");
    await loadProfileWeather();
  } else {
    const err = await res.json().catch(() => null);
    alert((err && err.detail) || "프로필 저장에 실패했습니다.");
  }
}

function validatePasswordRule(pw) {
  // 예시 규칙: 8~20자, 영문/숫자/특수문자 중 2종류 이상
  if (pw.length < 8 || pw.length > 20) return "비밀번호는 8~20자여야 합니다.";

  const hasLetter = /[A-Za-z]/.test(pw);
  const hasNumber = /[0-9]/.test(pw);
  const hasSpecial = /[!@#$%^&*()\-_+=\[{\]}\\|;:'",.<>/?]/.test(pw);

  const kinds = [hasLetter, hasNumber, hasSpecial].filter(Boolean).length;
  if (kinds < 2) {
    return "영문, 숫자, 특수문자 중 두 가지 이상을 포함해야 합니다.";
  }
  return "";
}

function getPasswordErrors(pw) {
  const errors = [];

  if (pw.length < 8 || pw.length > 20) {
    errors.push("8~20자 사이여야 합니다.");
  }
  if (!/[A-Z]/.test(pw)) {
    errors.push("영어 대문자를 최소 1개 포함해야 합니다.");
  }
  if (!/[a-z]/.test(pw)) {
    errors.push("영어 소문자를 최소 1개 포함해야 합니다.");
  }
  if (!/[0-9]/.test(pw)) {
    errors.push("숫자를 최소 1개 포함해야 합니다.");
  }
  if (!/[!@#$%^&*()\-_+=\[{\]}\\|;:'\",.<>/?]/.test(pw)) {
    errors.push("특수문자를 최소 1개 포함해야 합니다.");
  }
  return errors;
}

async function onSubmitPassword(e, token) {
  e.preventDefault();

  const current = document.getElementById("current_password").value;
  const next = document.getElementById("new_password").value;
  const confirm = document.getElementById("new_password_confirm").value;
  const pwMsg = document.getElementById("pw-msg");

  pwMsg.textContent = "";
  pwMsg.className = "small mt-1";

  if (!current || !next || !confirm) {
    pwMsg.textContent = "모든 비밀번호 필드를 입력해주세요.";
    pwMsg.classList.add("text-danger");
    return;
  }

  if (next !== confirm) {
    pwMsg.textContent = "새 비밀번호가 서로 다릅니다.";
    pwMsg.classList.add("text-danger");
    return;
  }

  const errors = getPasswordErrors(next);
  if (errors.length > 0) {
    pwMsg.innerHTML = errors.map(e => `• ${e}`).join("<br>");
    pwMsg.classList.add("text-danger");
    return;
  }

  const res = await fetch(`${API_BASE}/user/change-pw`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + token,
    },
    body: JSON.stringify({
      current_password: current,
      new_password: next,
    }),
  });

  if (res.ok) {
    pwMsg.textContent = "비밀번호가 변경되었습니다. 다시 로그인해 주세요.";
    pwMsg.classList.remove("text-danger");
    pwMsg.classList.add("text-success");
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setTimeout(() => {
      window.location.href = "/login";
    }, 1000);
  } else {
    let detail = "비밀번호 변경에 실패했습니다.";
    try {
      const err = await res.json();
      if (err && err.detail) detail = err.detail;
    } catch {}
    pwMsg.textContent = detail;
    pwMsg.classList.add("text-danger");
  }
}

// ---- 회원 탈퇴 ----
async function onDeleteAccount() {
  if (!confirm("정말 탈퇴하시겠습니까? 되돌릴 수 없습니다.")) return;

  const token = localStorage.getItem("access_token");
  if (!token) {
    alert("로그인이 필요합니다.");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/user/delete`, {
      method: "DELETE",
      headers: { Authorization: "Bearer " + token },
    });

    if (res.ok) {
      alert("회원 탈퇴가 완료되었습니다.");
      localStorage.clear();
      window.location.href = "/";
    } else {
      let detail = "회원 탈퇴에 실패했습니다.";
      try {
        const err = await res.json();
        if (err && err.detail) detail = err.detail;
      } catch {}
      alert(detail);
    }
  } catch (e) {
    console.error("delete error", e);
    alert("네트워크 오류로 회원 탈퇴에 실패했습니다.");
  }
}

// ---- 지역 3단계 선택 ----
let selectedSido = null;
let selectedGugun = null;
let selectedDong = null;
let selectedRegionId = null;

async function loadSidos() {
  const res = await fetch(API_BASE + "/regions/sidos");
  if (!res.ok) {
    console.error("sidos load fail", res.status);
    return;
  }
  const list = await res.json();
  const ul = document.getElementById("sido-list");
  ul.innerHTML = "";
  list.forEach(sido => {
    const li = document.createElement("li");
    li.className = "list-group-item list-group-item-action";
    li.textContent = sido.name;
    li.onclick = () => {
      selectedSido = sido;
      selectedGugun = null;
      selectedDong = null;
      loadGuguns(sido.id);
      document.getElementById("sigungu-list").innerHTML = "";
      document.getElementById("dong-list").innerHTML = "";
      updateSelectedText();
    };
    ul.appendChild(li);
  });
}

async function loadGuguns(sidoId) {
  const res = await fetch(API_BASE + `/regions/guguns/${sidoId}`);
  if (!res.ok) return;
  const list = await res.json();
  const ul = document.getElementById("sigungu-list");
  ul.innerHTML = "";
  list.forEach(gu => {
    const li = document.createElement("li");
    li.className = "list-group-item list-group-item-action";
    li.textContent = gu.name;
    li.onclick = () => {
      selectedGugun = gu;
      selectedDong = null;
      loadDongs(gu.id);
      document.getElementById("dong-list").innerHTML = "";
      updateSelectedText();
    };
    ul.appendChild(li);
  });
}

async function loadDongs(gugunId) {
  const res = await fetch(API_BASE + `/regions/dongs/${gugunId}`);
  if (!res.ok) return;
  const list = await res.json();
  const ul = document.getElementById("dong-list");
  ul.innerHTML = "";
  list.forEach(dong => {
    const li = document.createElement("li");
    li.className = "list-group-item list-group-item-action";
    li.textContent = dong.name;
    li.onclick = () => {
      selectedDong = dong;
      selectedRegionId = dong.id;
      updateSelectedText();
    };
    ul.appendChild(li);
  });
}

function updateSelectedText() {
  const text = document.getElementById("region-selected-text");
  if (selectedSido && selectedGugun && selectedDong) {
    text.textContent = `선택된 지역: ${selectedSido.name} ${selectedGugun.name} ${selectedDong.name}`;
  } else if (selectedSido && selectedGugun) {
    text.textContent = `선택된 지역: ${selectedSido.name} ${selectedGugun.name}`;
  } else if (selectedSido) {
    text.textContent = `선택된 지역: ${selectedSido.name}`;
  } else {
    text.textContent = "선택된 지역: 없음";
  }
}

function applyRegionSelection() {
  if (!selectedRegionId) {
    alert("시·도, 시·군·구, 동을 모두 선택해주세요.");
    return;
  }
  const label = `${selectedSido.name} ${selectedGugun.name} ${selectedDong.name}`;
  document.getElementById("edit-region-label").value = label;
  document.getElementById("edit-region-id").value = selectedRegionId;

  const modalEl = document.getElementById("regionModal");
  const modal = bootstrap.Modal.getInstance(modalEl);
  modal.hide();
}
let notifCount = 0;

async function loadNotifications() {
  const token = localStorage.getItem("access_token");
  if (!token) return;

  try {
    const res = await fetch(API_BASE + "/notifications/", {
      headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) return;
    const items = await res.json();   // [{id, type, message, ...}, ...]

    const ul = document.getElementById("notif-list");
    if (!ul) return;
    ul.innerHTML = "";

    items.forEach(n => {
      const li = document.createElement("li");
      li.className = "list-group-item py-2";
      li.textContent = n.message;
      ul.appendChild(li);
    });

    if (items.length > 0) {
      notifCount = items.filter(n => !n.is_read).length || items.length;
      const badge = document.getElementById("notif-badge");
      if (badge) {
        badge.textContent = notifCount;
        badge.classList.toggle("d-none", notifCount === 0);
      }
    }
  } catch (e) {
    console.error("loadNotifications error", e);
  }
}
