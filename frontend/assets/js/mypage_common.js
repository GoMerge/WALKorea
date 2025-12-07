export let userBaseAddress = null;

// 토큰 헬퍼 (캘린더에서 이미 쓰는 getToken 그대로 사용)
function getToken() {
  return localStorage.getItem("access_token");
}

window.goLoginWithReturn = function() {
  const currentUrl = window.location.href;
  localStorage.setItem("postLoginRedirect", currentUrl);
  window.location.href = "/login";
};

// 현재 페이지 주소를 저장하고 로그인 페이지로 이동
export function goLoginWithReturn() {
  const currentUrl = window.location.href;
  localStorage.setItem("postLoginRedirect", currentUrl);
  window.location.href = "/login";
}

// 마이페이지 진입 전에 로그인 검사
export function requireLoginForMypage() {
  const token = localStorage.getItem("access_token");
  if (!token) {
    alert("로그인이 필요합니다.");
    goLoginWithReturn();
    return false;
  }
  return true;
}


// 공통: 헤더/사이드바 프로필 세팅
export async function setupHeaderAndProfile() {
  const token = getToken();
  const nav = document.querySelector(".navbar-nav");
  const loginLi = document.getElementById("nav-login");
  const signupLi = document.getElementById("nav-signup");

  if (token && nav) {
    if (loginLi) loginLi.remove();
    if (signupLi) signupLi.remove();
    const logoutLi = document.createElement("li");
    logoutLi.className = "nav-item";
    logoutLi.innerHTML = `<a class="btn btn-outline-danger" href="#">로그아웃</a>`;
    logoutLi.querySelector("a").onclick = (e) => {
      e.preventDefault();
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      window.location.href = "/";
    };
    nav.appendChild(logoutLi);
  }
  if (!token) return;

  const res = await fetch("http://127.0.0.1:8000/user/profile", {
    headers: { "Authorization": "Bearer " + token }
  });
  if (!res.ok) return;
  const user = await res.json();

  const nick = user.nickname || user.userid || user.username || "사용자";
  const email = user.email || user.user_email || "";

  const sideNick = document.getElementById("side-nickname");
  const profNick = document.getElementById("profile-nickname");
  if (sideNick) sideNick.textContent = nick;
  if (profNick) profNick.textContent = nick;

  const sideEmail = document.getElementById("side-email");
  const profEmail = document.getElementById("profile-email");
  if (sideEmail) sideEmail.textContent = email;
  if (profEmail) profEmail.textContent = email;

  const sideInit = document.getElementById("side-initial");
  const profInit = document.getElementById("profile-initial");
  if (sideInit) sideInit.textContent = nick[0];
  if (profInit) profInit.textContent = nick[0];

  const regionMsg = document.getElementById("profile-region-msg");
  const weatherTitle = document.getElementById("region-weather-title");
  const weatherDesc  = document.getElementById("region-weather-desc");
  if (!user.region_id) {
    if (regionMsg)    regionMsg.textContent = "";
    if (weatherTitle) weatherTitle.textContent = "동네를 선택해 주세요";
    if (weatherDesc)  weatherDesc.textContent  =
      "프로필에서 거주 지역을 설정하면, 이곳에 6일간의 날씨를 보여줄게요.";
    userBaseAddress = null;
  } else {
    const base = user.region_full_name || user.region_name;
    if (regionMsg)    regionMsg.textContent = "";
    if (weatherTitle) weatherTitle.textContent = `${base}의 날씨`;
    if (weatherDesc)  weatherDesc.textContent  =
      "오늘을 포함한 6일치 동네 날씨예요.";
    userBaseAddress = base;
  }
}

// 요일/아이콘 유틸
function formatKoreanWeekday(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  const names = ["일", "월", "화", "수", "목", "금", "토"];
  return names[d.getDay()];
}
function mapIconToEmoji(icon) {
  switch (icon) {
    case "rain": return "🌧️";
    case "snow": return "❄️";
    case "fog": return "🌫️";
    case "wind": return "💨";
    case "cloudy": return "☁️";
    case "partly-cloudy-day": return "⛅";
    case "partly-cloudy-night": return "☁️";
    case "clear-day": return "☀️";
    case "clear-night": return "🌙";
    default: return "🌤️";
  }
}

// 공통: 6일치 날씨 박스 채우기
export async function loadProfileWeather() {
  const token = getToken();
  if (!token) return;

  try {
    const res = await fetch("http://127.0.0.1:8000/weather/profile/current", {
      headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) return;
    const data = await res.json(); // { region_name, days: [...] }
    console.log("profile weather data:", data);
    console.log(data.days[0])

    const boxTitle = document.getElementById("region-weather-title");
    const boxDesc  = document.getElementById("region-weather-desc");
    const listBox  = document.getElementById("region-weather-list");
    if (!data.days || !boxTitle || !boxDesc || !listBox) return;

    boxTitle.textContent = `${data.region_name}의 날씨`;
    boxDesc.textContent  = "오늘을 포함한 6일치 동네 날씨예요.";

    listBox.innerHTML = "";
    data.days.forEach((d, idx) => {
        const div = document.createElement("div");
        // 줄 자체를 카드 가운데로
        div.className = "d-flex justify-content-center align-items-center small mb-1";

        const weekday = formatKoreanWeekday(d.date);
        const label = idx === 0 ? "오늘" : weekday;

        const tmax = d.temp_max;
        const tmin = d.temp_min;
        const tempPart = (tmax != null && tmin != null)
            ? `${tmax.toFixed(0)}° / ${tmin.toFixed(0)}°`
            : "-°";

        const iconEmoji = mapIconToEmoji(d.icon);

        div.innerHTML = `
            <span style="flex:1; text-align:center;" class="text-muted">
            ${label}
            </span>
            <span style="flex:1; text-align:center;">
            ${iconEmoji}
            </span>
            <span style="flex:1; text-align:center;" class="fw-semibold">
            ${tempPart}
            </span>
        `;
        listBox.appendChild(div);
    });
    } catch (e) {
        console.error("profile weather error", e);
    }
}

// 모든 로그인 버튼 자동화
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("a[href='/login']").forEach(btn => {
    btn.href = "#";
    btn.onclick = (e) => {
      e.preventDefault();
      goLoginWithReturn();
    };
  });
});


window.checkAutoReturn = function() {
  const returnUrl = localStorage.getItem("postLoginRedirect");
  if (returnUrl) {
    localStorage.removeItem("postLoginRedirect");
    window.location.href = returnUrl;
  }
};