import { initHeader } from "/assets/js/header.js";
import {
  setupHeaderAndProfile,
  loadProfileWeather,
} from "/assets/js/mypage_common.js";
import { loadNotifications } from "/assets/js/notifications.js";

const token = localStorage.getItem("access_token");

// --- 취향 불러오기 ---

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

async function loadPreferences() {
  if (!token) return;

  const res = await fetch("http://127.0.0.1:8000/user/profile/preferences", {
    headers: { Authorization: "Bearer " + token }
  });
  if (!res.ok) return;

  const data = await res.json();
  const pref = data.preference;
  if (!pref) return;

  document.getElementById("age_group").value      = pref.age_group      || "";
  document.getElementById("pref_gender").value    = pref.gender         || "";
  document.getElementById("travel_style").value   = pref.travel_style   || "";
  document.getElementById("photo_likes").value    = pref.photo_likes    || "";
  document.getElementById("vibe").value           = pref.vibe           || "";
  document.getElementById("night_activity").value = pref.night_activity || "";
  document.getElementById("budget_level").value   = pref.budget_level   || "";
  document.getElementById("activity_level").value = pref.activity_level || "";
  document.getElementById("crowd_level").value    = pref.crowd_level    || "";

  const travelWith   = pref.travel_with   || [];
  const areaTheme    = pref.area_theme    || [];
  const activityType = pref.activity_type || [];

  document.getElementById("with-alone").checked  = travelWith.includes("혼자");
  document.getElementById("with-friend").checked = travelWith.includes("친구");
  document.getElementById("with-family").checked = travelWith.includes("가족");
  document.getElementById("with-couple").checked = travelWith.includes("커플");

  document.getElementById("theme-sea").checked     = areaTheme.includes("바다");
  document.getElementById("theme-mountain").checked= areaTheme.includes("산");
  document.getElementById("theme-city").checked    = areaTheme.includes("도시");
  document.getElementById("theme-nature").checked  = areaTheme.includes("자연");

  document.getElementById("act-culture").checked = activityType.includes("문화체험");
  document.getElementById("act-food").checked    = activityType.includes("맛집");
  document.getElementById("act-rest").checked    = activityType.includes("휴식");
  document.getElementById("act-spot").checked    = activityType.includes("관광명소");

  document.getElementById("sns_like").checked    = !!pref.sns_like;
  document.getElementById("avoid_crowd").checked = !!pref.avoid_crowd;
}

// --- 취향 저장 ---

async function savePreferences(e) {
  e.preventDefault();
  if (!token) {
    alert("로그인이 필요합니다.");
    window.location.href = "/login";
    return;
  }

  const travelWith = [];
  if (document.getElementById("with-alone").checked)  travelWith.push("혼자");
  if (document.getElementById("with-friend").checked) travelWith.push("친구");
  if (document.getElementById("with-family").checked) travelWith.push("가족");
  if (document.getElementById("with-couple").checked) travelWith.push("커플");

  const areaTheme = [];
  if (document.getElementById("theme-sea").checked)      areaTheme.push("바다");
  if (document.getElementById("theme-mountain").checked) areaTheme.push("산");
  if (document.getElementById("theme-city").checked)     areaTheme.push("도시");
  if (document.getElementById("theme-nature").checked)   areaTheme.push("자연");

  const activityType = [];
  if (document.getElementById("act-culture").checked) activityType.push("문화체험");
  if (document.getElementById("act-food").checked)    activityType.push("맛집");
  if (document.getElementById("act-rest").checked)    activityType.push("휴식");
  if (document.getElementById("act-spot").checked)    activityType.push("관광명소");

  const payload = {
    preference: {
      age_group:      document.getElementById("age_group").value      || "알 수 없음",
      gender:         document.getElementById("pref_gender").value    || "알 수 없음",
      travel_with:    travelWith,
      travel_style:   document.getElementById("travel_style").value   || "계획형",
      activity_level: document.getElementById("activity_level").value || "보통",
      area_theme:     areaTheme,
      activity_type:  activityType,
      photo_likes:    document.getElementById("photo_likes").value    || "보통",
      vibe:           document.getElementById("vibe").value           || "조용한 곳",
      night_activity: document.getElementById("night_activity").value || "낮활동",
      sns_like:       document.getElementById("sns_like").checked,
      avoid_crowd:    document.getElementById("avoid_crowd").checked,
      budget_level:   document.getElementById("budget_level").value   || "mid",
      crowd_level:    document.getElementById("crowd_level").value    || "moderate",
    }
  };

  const res = await fetch("http://127.0.0.1:8000/user/profile/preferences", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + token
    },
    body: JSON.stringify(payload)
  });

    if (res.ok) {
    const summary = document.getElementById("pref-summary");
    if (summary) {
      const age = document.getElementById("age_group").value || "연령 미설정";
      summary.style.display = "block";
      summary.textContent =
        `설정 완료: ${age}, ` +
        `${travelWith.join(", ") || "혼자/동행 미설정"}, ` +
        `${areaTheme.join(", ") || "테마 미설정"} 기준으로 추천해 드릴게요.`;
    }

    // alert 대신 토스트
    const toastEl = document.getElementById("saveToast");
    if (toastEl) {
      const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
      toast.show();
    }
  }
}

// --- 페이지 초기화 ---

export async function initRecommendPage() {
  if (!token) {
    alert("로그인이 필요합니다.");
    window.location.href = "/login";
    return;
  }

  await initHeader();             // header.js: 로그인/게스트 헤더 세팅
  await setupHeaderAndProfile();  // mypage_common.js: 프로필/사이드바 닉네임
  await loadProfileWeather();     // mypage_common.js: 6일 날씨
  await loadPreferences();        // 이 페이지 전용
  await loadNotifications();      // notifications.js: 알림 뱃지/목록

  const form = document.getElementById("pref-form");
  if (form) {
    form.addEventListener("submit", savePreferences);
  }
}
