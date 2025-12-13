import { loadProfileWeather } from "./mypage_common.js";
import { requireLoginForMypage, requireCompletedProfile } from "/assets/js/mypage_common.js";

const API_BASE = "";

let currentYear, currentMonth;
let eventsCache = {};
let userBaseAddress = null;
let userCalendarId = null;
let debugPlaceWeatherMap = {};
let debugUserWeatherMap = {};
let festivalMap = {};

function getToken() { return localStorage.getItem("access_token"); }


async function apiFetch(url, options = {}) {
  const res = await fetch(url, options);
  if (res.status === 401) {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    alert("로그아웃되었습니다. 다시 로그인해 주세요.");
    window.location.href = "/";
    return null;
  }
  return res;
}

async function initCalendar() { 
    console.log("initCalendar called");
    const today = new Date();
    const body = {
      user_id: 0,                 // 백엔드에서 current_user.id로 덮어쓰기 때문에 안 보내도 되게 스키마 수정하는 게 좋음
      place_id: null,
      event_date: today.toISOString().slice(0, 10),
      start_time: null,
      end_time: null,
      memo: "내 캘린더"
    };
    currentYear = today.getFullYear();
    currentMonth = today.getMonth();
    document.getElementById("prev-month").onclick = () => changeMonth(-1);
    document.getElementById("next-month").onclick = () => changeMonth(1);
    renderCalendar();
 }
async function loadCalendars() { 
    const res = await apiFetch(API_BASE + "/calendar/", {
      headers: { "Authorization": "Bearer " + getToken() }
    });
    if (!res) return;       
    const list = res.ok ? await res.json() : [];

    const ul = document.getElementById("my-cal-list");
    ul.innerHTML = "";
    list.forEach(c => {
      const li = document.createElement("li");
      li.className = "list-group-item d-flex justify-content-between align-items-center";
      li.textContent = c.memo || c.title || "내 캘린더";
      ul.appendChild(li);
    });
 }
async function ensureUserCalendarId() {
  const token = getToken();
  if (userCalendarId) return userCalendarId;

  // 1) 내 캘린더 목록 조회
  const res = await fetch(API_BASE + "/calendar/", {
    headers: { "Authorization": "Bearer " + token }
  });

  if (!res.ok) {
    alert("캘린더 조회에 실패했습니다.");
    return null;
  }

  const list = await res.json(); 

  // 2) 없으면 자동으로 하나 생성
  if (!list || list.length === 0) {
    const createRes = await fetch(API_BASE + "/calendar/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
      },
      body: JSON.stringify({})  
    });

    if (!createRes.ok) {
      alert("기본 캘린더 생성에 실패했습니다.");
      return null;
    }

    const cal = await createRes.json();
    userCalendarId = cal.id;
    return userCalendarId;
  }

  // 3) 이미 있는 경우 첫 번째 사용
  userCalendarId = list[0].id;
  return userCalendarId;
}

async function fetchWeatherRecommendations(events) {
  if (!events.length) return {};

  const token = getToken();
  if (!token) return {};

  try {
    const res = await fetch(API_BASE + "/calendar/weather/recommend", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
      },
      body: JSON.stringify(events)
    });
    
    if (!res.ok) {
      console.warn("weather recommend failed", res.status);
      return {};
    }

    const data = await res.json();   // { results: [...] }

    const map = {};
    (data.results || []).forEach(r => {
      const key = `${r.date}|${r.address}`;
      map[key] = r;                  // { is_good, weather, ... }
    });
    return map;
  } catch (e) {
    console.error("weather recommend error", e);
    return {};
  }
}

async function loadEventsToCalendar(calId) { 
    const token = getToken();
    const res = await fetch( API_BASE + `/calendar/${calId}/events`, {
      headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) return;
    const events = await res.json();
    console.log("events from API:", events);

    // 1) 현재 달 기준으로 먼저 필터링
    const filtered = events.filter(ev => {
      const iso = ev.start_datetime || ev.start_date;
      if (!iso) return false;
      const d = new Date(iso);
      return d.getFullYear() === currentYear && d.getMonth() === currentMonth;
    });

    // 2) 날씨 추천 payload (현재 달 이벤트만)
    const placeWeatherPayload = filtered
      .filter(ev => ev.location && (ev.start_datetime || ev.start_date))
      .map(ev => ({
        address: ev.location,
        date: (ev.start_datetime || ev.start_date).slice(0,10)
      }));
    const placeWeatherMap = await fetchWeatherRecommendations(placeWeatherPayload);
    debugPlaceWeatherMap = placeWeatherMap;

    // 2-1) 한 달 전체 날짜에 대해 사용자 위치 기준 날씨 요청 (따봉용)
    let userWeatherMap = {};
    if (userBaseAddress) {
      const monthDaysPayload = [];

      const firstDay = new Date(currentYear, currentMonth, 1);
      const lastDay  = new Date(currentYear, currentMonth + 1, 0);
      const total    = lastDay.getDate();

      for (let d = 1; d <= total; d++) {
        const dateStr = `${currentYear}-${String(currentMonth+1).padStart(2,"0")}-${String(d).padStart(2,"0")}`;
        monthDaysPayload.push({
          address: userBaseAddress,    // ★ 항상 사용자 위치
          date: dateStr                // ★ 그 달의 모든 날짜
        });
      }

      userWeatherMap = await fetchWeatherRecommendations(monthDaysPayload);
      debugUserWeatherMap = userWeatherMap;
    }

    const cells = document.querySelectorAll(".calendar-day");
    const map = {};
    eventsCache = {};

    // 3) 내 일정 목록: 현재 달만
    const ul = document.getElementById("my-cal-list");
    ul.innerHTML = "";

    const sorted = [...filtered].sort((a, b) => {
      const sa = (a.start_datetime || a.start_date);
      const sb = (b.start_datetime || b.start_date);
      return sa.localeCompare(sb);
    });

    sorted.forEach(ev => {
      const iso = (ev.start_datetime || ev.start_date);
      const d = new Date(iso);
      const month = d.getMonth() + 1;
      const day = d.getDate();
      const time = iso.slice(11, 16);
      const keyForEvent = `${iso.slice(0,10)}|${ev.location || ""}`;

      const w = placeWeatherMap[keyForEvent];
      console.log("event item:", keyForEvent, ev);
      console.log("weather for event:", ev.title, keyForEvent, w);

      const li = document.createElement("li");
      li.className = "list-group-item d-flex justify-content-between align-items-center";

      if (ev.is_shared === 1) {
        li.classList.add("shared-event-list-item");
      } else if (ev.from_place) {
        li.classList.add("from-place-highlight-list");
      }

      let emoji = "";
      let wText = "날씨 정보 없음";

      if (ev.location) {
        const key = `${iso.slice(0,10)}|${ev.location}`;
        const w = placeWeatherMap[key];
        console.log("weather for event:", ev.title, key, w);

        emoji = weatherEmojiFromResult(w);

        if (w && w.weather && w.weather.avg_weather) {
          const aw = w.weather.avg_weather;
          const tRaw = aw["기온(℃)"];
          const pRaw = aw["강수량(mm)"];

          const parts = [];
          if (tRaw != null) parts.push(`평균 ${Number(tRaw).toFixed(1)}°C`);
          if (pRaw != null) parts.push(`강수 ${Number(pRaw).toFixed(1)}mm`);

          if (parts.length > 0) {
            wText = parts.join(", ");
          }
        }
      }

      li.innerHTML = `
        <div class="me-2 flex-grow-1">
          <div class="fw-semibold">${emoji ? emoji + " " : ""}${ev.title}</div>
          <div class="text-muted small">
            ${month}/${day} ${time} · ${wText}
          </div>
        </div>
        <div class="d-flex gap-1">
          <button class="btn btn-sm btn-outline-primary btn-share-event">공유하기</button>
          <button class="btn btn-sm btn-outline-secondary btn-edit-event">수정</button>
          <button class="btn btn-sm btn-outline-danger btn-delete-event">삭제</button>
        </div>
      `;

      const shareBtn = li.querySelector(".btn-share-event");
      shareBtn.onclick = async (e) => {
        e.stopPropagation();
        await openShareModal(ev);
      };

      const editBtn = li.querySelector(".btn-edit-event");
      editBtn.onclick = (e) => {
        e.stopPropagation();
        openEventModalForEdit(ev);   // 수정 모드로 모달 열기
      };

      const deleteBtn = li.querySelector(".btn-delete-event");
      deleteBtn.onclick = async (e) => {
        e.stopPropagation();
        await deleteEvent(ev);
      };

      li.onclick = () => openEventDetail(ev);
      ul.appendChild(li);
    });



    // 4) 날짜별 이벤트/캐시 구성
    filtered.forEach(ev => {
      const src = ev.start_datetime || ev.start_date;
      if (!src) return;
      const d = src.slice(0, 10);   // "YYYY-MM-DD"
      if (!map[d]) map[d] = [];
      map[d].push(ev.title);
      if (!eventsCache[d]) eventsCache[d] = [];
      eventsCache[d].push(ev);
    });
    console.log("eventsByDate map:", map);

    festivalMap = {};
    try {
      const token = getToken();      
      if (!token) return;      

      const resFest = await fetch(
         API_BASE + `/calendar/festivals?year=${currentYear}&month=${currentMonth+1}`,
        {
          headers: { "Authorization": "Bearer " + token }  
        }
      );
      if (resFest.ok) {
        const fests = await resFest.json(); 
        fests.forEach(f => {
          const d = f.date; 
          if (!festivalMap[d]) festivalMap[d] = [];
          festivalMap[d].push(f);
        });
      }
    } catch (e) {
      console.error("festival load error", e);
    }

    // 5) 셀 렌더링 + 따봉/이모지
    cells.forEach(cell => {
      const date = cell.dataset.date;           // "YYYY-MM-DD"
      const label = cell.querySelector(".event-list");
      const dateEl = cell.querySelector(".date-num");
      if (!label || !dateEl) return;

      const cellEvents = eventsCache[date] || [];

      // 1) 사용자 위치 기준 "좋은 날"인지 먼저 판별
      let dayIsGood = false;
      let wForDay = null;

      if (userBaseAddress) {
        const key = `${date}|${userBaseAddress}`;
        wForDay = userWeatherMap[key];
        if (wForDay && (wForDay.is_good === true || wForDay.quality === "good")) {
          dayIsGood = true;
        }
      }

      // 2) 기존 배지 제거 후, good 이면 새 배지 추가
      const oldBadge = dateEl.querySelector(".day-good-badge");
      if (oldBadge) oldBadge.remove();

      if (dayIsGood) {
        const badge = document.createElement("span");
        badge.textContent = "👍";
        badge.className = "day-good-badge ms-1";
        dateEl.appendChild(badge);
      }

      // 3) 이하 일정/표정 이모티콘 로직은 그대로
      if (cellEvents.length > 0) {
        label.innerHTML = "";
        cellEvents.slice(0, 3).forEach(ev => {
          const chip = document.createElement("div");
          chip.className = "event-chip";

          if (ev.is_shared === 1) {
            chip.classList.add("shared-event-chip");
          } else {
            chip.classList.add("place-event-chip");
            if (ev.from_place) {
              chip.classList.add("from-place-highlight");  // 관광지 상세에서 저장한 일정
            }
          }

          let emoji = "";
          if (ev.location) {
            const key = `${date}|${ev.location}`;
            const w = placeWeatherMap[key];
            emoji = weatherEmojiFromResult(w);
          }

          chip.textContent = `${emoji ? emoji + " " : ""}${ev.title}`;
          label.appendChild(chip);
        });

        if (cellEvents.length > 3) {
          const more = document.createElement("div");
          more.className = "text-muted small";
          more.textContent = `+${cellEvents.length - 3}개 더보기`;
          label.appendChild(more);
        }
      }
      const fests = festivalMap[date] || [];
      fests.forEach(f => {
        const festChip = document.createElement("div");
        festChip.className = "event-chip festival-chip";   // 별도 클래스
        festChip.textContent = `${f.title} · ${f.location}`;
        festChip.onclick = (e) => {
          e.stopPropagation();
          if (f.detail_url) {
            window.location.href = f.detail_url;
          }
        };
        label.appendChild(festChip);
      });

      if (!cellEvents.length && !fests.length) {
        label.textContent = "일정 없음";
      }
    });
}

async function setupUserRegion() {
  const user = window.__userProfile;   // 헤더에서 이미 받아둔 프로필

  if (!user) {
    userBaseAddress = null;
    return;
  }

  if (!user.region_id) {
    userBaseAddress = null;
  } else {
    userBaseAddress = user.region_full_name || user.region_name;
  }
}


async function checkIncomingShares() {
    const token = getToken();
    if (!token) return;

    const res = await fetch(API_BASE + "/calendar/share/incoming", {
      headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) return;
    const requests = await res.json();   // [{id, from_user_id, event_id, status, ...}]

    for (const req of requests) {
      await showShareConfirmDialog(req);
    }
}
async function fetchRegionSuggestions(q) {
    const res = await fetch( API_BASE + `/address/search?q=${encodeURIComponent(q)}`);
    if (!res.ok) {
      suggestBox.style.display = "none";
      suggestBox.innerHTML = "";
      return;
    }
    const items = await res.json();  // [{id, code, full_name}, ...]

    if (!items.length) {
      suggestBox.style.display = "none";
      suggestBox.innerHTML = "";
      return;
    }

    suggestBox.innerHTML = "";
    items.forEach(item => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "list-group-item list-group-item-action small text-start";
      btn.textContent = item.full_name;
      btn.dataset.regionId = item.id;
      btn.dataset.regionCode = item.code;
      btn.onclick = () => selectRegionSuggestion(item);
      suggestBox.appendChild(btn);
    });
    suggestBox.style.display = "block";
}
function openEventModal(defaultDate = null) {
  const formEl      = document.getElementById("event-form");
  const startInput  = document.getElementById("ev-start");
  const endInput    = document.getElementById("ev-end");
  const titleInput  = document.getElementById("ev-title");
  const memoInput   = document.getElementById("ev-memo");
  const remindSel   = document.getElementById("ev-remind");
  const placeInput  = document.getElementById("ev-place");
  const suggestBox  = document.getElementById("place-suggestions");
  const preview     = document.getElementById("place-preview");

  // 1) 폼 전체 리셋 + 수정 모드 플래그 제거
  if (formEl) {
    formEl.reset();
    delete formEl.dataset.editEventId;
  }
  if (placeInput) {
    placeInput.value = "";
    placeInput.dataset.regionId = "";
    placeInput.dataset.regionCode = "";
    placeInput.dataset.fullName = "";
  }
  if (suggestBox) {
    suggestBox.style.display = "none";
    suggestBox.innerHTML = "";
  }
  if (preview) preview.textContent = "";

  // 2) 기본 날짜/시간 세팅 (선택한 날짜 기준)
  const baseDate = defaultDate ? new Date(defaultDate) : new Date();
  const base = new Date(
    baseDate.getFullYear(),
    baseDate.getMonth(),
    baseDate.getDate(),
    9, 0
  );
  const end  = new Date(base.getTime() + 60 * 60 * 1000);

  const toLocal = d => {
    const off = d.getTimezoneOffset();
    const local = new Date(d.getTime() - off * 60000);
    return local.toISOString().slice(0, 16);
  };

  if (startInput) startInput.value = toLocal(base);
  if (endInput)   endInput.value   = toLocal(end);
  if (remindSel)  remindSel.value  = "0";

  // 3) 모달 표시
  const modalEl = document.getElementById("eventModal");
  const modal = new bootstrap.Modal(modalEl);
  modal.show();
}

function openDayEventModal(dateStr) {
    const listEl = document.getElementById("day-event-list");
    const titleEl = document.getElementById("day-modal-title");
    const addBtn = document.getElementById("btn-add-on-day");

    // 제목: "2025년 12월 8일" 형태
    const d = new Date(dateStr);
    titleEl.textContent = `${d.getFullYear()}년 ${d.getMonth()+1}월 ${d.getDate()}일 일정`;

    listEl.innerHTML = "";
    const events = eventsCache[dateStr] || [];

    if (events.length === 0) {
      const li = document.createElement("li");
      li.className = "list-group-item text-muted small";
      li.textContent = "등록된 일정이 없습니다.";
      listEl.appendChild(li);
    } else {
      events.forEach(ev => {
        const li = document.createElement("li");
        li.className = "list-group-item d-flex justify-content-between align-items-center";

        let emoji = "";
        let wText = "날씨 정보 없음";

        if (ev.location) {
          const key = `${dateStr}|${ev.location}`;
          const w = debugPlaceWeatherMap[key];
          console.log("day modal weather:", ev.title, key, w);

          emoji = weatherEmojiFromResult(w);

          if (w) {
            const parts = [];
            if (w.avg_temp != null)  parts.push(`평균 ${Number(w.avg_temp).toFixed(1)}°C`);
            if (w.precip_mm != null) parts.push(`강수 ${Number(w.precip_mm).toFixed(1)}mm`);
            if (parts.length > 0) wText = parts.join(", ");
          }
        }

        li.innerHTML = `
          <div class="me-2 flex-grow-1">
            <div class="fw-semibold">${emoji ? emoji + " " : ""}${ev.title}</div>
            <div class="text-muted small">
              ${(ev.start_datetime || ev.start_date).slice(11,16)}
              ~ ${(ev.end_datetime || ev.end_date).slice(11,16)}
              · ${wText}
            </div>
          </div>
          <div class="d-flex gap-1">
            <button class="btn btn-sm btn-outline-primary btn-share-event">공유</button>
            <button class="btn btn-sm btn-outline-secondary btn-edit-event">수정</button>
            <button class="btn btn-sm btn-outline-danger btn-delete-event">삭제</button>
          </div>
        `;

        const shareBtn = li.querySelector(".btn-share-event");
        shareBtn.onclick = async (e) => {
          e.stopPropagation();
          await openShareModal(ev);
        };

        const editBtn = li.querySelector(".btn-edit-event");
        editBtn.onclick = (e) => {
          e.stopPropagation();
          // 날짜별 모달 닫고 수정 모달 오픈
          bootstrap.Modal.getInstance(document.getElementById("dayEventModal")).hide();
          openEventModalForEdit(ev);
        };

        const deleteBtn = li.querySelector(".btn-delete-event");
        deleteBtn.onclick = async (e) => {
          e.stopPropagation();
          await deleteEvent(ev);
        };

        // 리스트 전체 클릭 시 상세 정보만 보고 싶으면 유지
        li.onclick = () => openEventDetail(ev);

        listEl.appendChild(li);
      });
    }

    addBtn.onclick = () => {
      const modal = bootstrap.Modal.getInstance(document.getElementById("dayEventModal"));
      modal.hide();
      openEventModal(dateStr);   // ★ 이 날짜로 일정 추가 모달 오픈
    };

    const modal = new bootstrap.Modal(document.getElementById("dayEventModal"));
    modal.show();
}

function formatKoreanWeekday(dateStr) {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    const names = ["일", "월", "화", "수", "목", "금", "토"];
    return names[d.getDay()];
}

function mapIconToEmoji(icon) {
    // Visual Crossing icon 값 간단 매핑
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

  function weatherEmojiFromResult(w) {
    if (!w) return "";                 // 정보 없으면 이모지 없음
    if (w.is_good === true) return "😊";   // 좋음
    if (w.is_good === false) return "😡";  // 나쁨
    return "😐";                        // 나쁘지도, 좋지도 않을 때
  }

  function weatherTextFromResult(w) {
    if (!w) return "";                 // 정보 없으면 텍스트도 없음
    return w.is_good ? "날씨 좋음" : "날씨 나쁨";
  }


function renderCalendar() {
  const title = document.getElementById("month-title");
  title.textContent = `${currentYear}년 ${currentMonth+1}월`;

  const body = document.getElementById("calendar-body");
  body.innerHTML = "";

  const first = new Date(currentYear, currentMonth, 1);
  const last  = new Date(currentYear, currentMonth+1, 0);
  const startDay = first.getDay();
  const total = last.getDate();

  const today = new Date();
  const isThisMonth = (today.getFullYear() === currentYear && today.getMonth() === currentMonth);

  for (let i=0;i<startDay;i++) body.appendChild(document.createElement("div"));

  for (let d=1; d<=total; d++) {
    const div = document.createElement("div");
    div.className = "calendar-day";
    const dateStr = `${currentYear}-${String(currentMonth+1).padStart(2,"0")}-${String(d).padStart(2,"0")}`;
    if (isThisMonth && d === today.getDate()) div.classList.add("today");
    div.dataset.date = dateStr;
    div.innerHTML = `
      <div class="date-num">${d}</div>
      <div class="small text-muted event-list">일정 없음</div>
    `;
    body.appendChild(div);
  }
}

async function changeMonth(delta) {
  currentMonth += delta;
  if (currentMonth < 0) { currentMonth = 11; currentYear--; }
  else if (currentMonth > 11) { currentMonth = 0; currentYear++; }
  renderCalendar();

  const calId = await ensureUserCalendarId();
  if (calId) {
    await loadEventsToCalendar(calId);
  }
}

document.getElementById("event-form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const formEl = document.getElementById("event-form");
  const editingId = formEl.dataset.editEventId || null;

  const calId = await ensureUserCalendarId();
  if (!calId) return;

  const title = document.getElementById("ev-title").value.trim();
  const start = document.getElementById("ev-start").value;
  const end   = document.getElementById("ev-end").value;
  const memo  = document.getElementById("ev-memo").value.trim();
  const remindMinutes = parseInt(document.getElementById("ev-remind").value, 10);
  const placeInputEl = document.getElementById("ev-place");
  const placeText = placeInputEl.value.trim();
  const placeFull = placeInputEl.dataset.fullName || placeText;

  if (!title || !start || !end) {
    alert("제목과 시간은 필수입니다.");
    return;
  }

  const startDate = new Date(start + ':00').toISOString();
  const endDate   = new Date(end + ':00').toISOString();

  const payload = {
    title,
    start_date: startDate,
    end_date: endDate,
    description: memo || null,
    location: placeFull || null,
    remind_minutes: isNaN(remindMinutes) ? null : remindMinutes
  };

  const token = getToken();
  let url, method;
  if (editingId) {
    url = API_BASE + `/calendar/events/${editingId}`;
    method = "PUT";
  } else {
    url = API_BASE + `/calendar/${calId}/events`;
    method = "POST";
  }

  const res = await fetch(url, {
    method,
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + token
    },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    const err = await res.json().catch(()=>null);
    alert((err && err.detail) || "일정 저장에 실패했습니다.");
    return;
  }

  delete formEl.dataset.editEventId;

  const modalEl = document.getElementById("eventModal");
  const modal = bootstrap.Modal.getInstance(modalEl);
  modal.hide();

  await loadCalendars();
  const calIdAfter = await ensureUserCalendarId();
  if (calIdAfter) {
    await loadEventsToCalendar(calIdAfter);
  }
});

function openEventModalForEdit(ev) {
    const startInput = document.getElementById("ev-start");
    const endInput   = document.getElementById("ev-end");
    const titleInput = document.getElementById("ev-title");
    const memoInput  = document.getElementById("ev-memo");
    const remindSel  = document.getElementById("ev-remind");
    const placeInputEl = document.getElementById("ev-place");

    // 시작/종료 시간을 로컬 포맷으로 변환
    const toLocal = iso => {
      const d = new Date(iso);
      const off = d.getTimezoneOffset();
      const local = new Date(d.getTime() - off*60000);
      return local.toISOString().slice(0,16);
    };

    titleInput.value = ev.title || "";
    memoInput.value  = ev.memo || ev.description || "";
    placeInputEl.value = ev.location || "";
    remindSel.value = ev.remind_minutes != null ? String(ev.remind_minutes) : "0";

    startInput.value = toLocal(ev.start_datetime || ev.start_date);
    endInput.value   = toLocal(ev.end_datetime || ev.end_date);

    // 수정 모드 표시용
    document.getElementById("event-form").dataset.editEventId = ev.id;

    const modal = new bootstrap.Modal(document.getElementById("eventModal"));
    modal.show();
}

async function deleteEvent(ev) {
    if (!confirm(`'${ev.title}' 일정을 삭제할까요?`)) return;

    const token = getToken();
    const res = await fetch(API_BASE + `/calendar/events/${ev.id}`, {
      method: "DELETE",
      headers: { "Authorization": "Bearer " + token }
    });

    if (!res.ok) {
      const err = await res.json().catch(()=>null);
      alert((err && err.detail) || "일정 삭제에 실패했습니다.");
      return;
    }

    alert("일정을 삭제했습니다.");

    await loadCalendars();
    const calId = await ensureUserCalendarId();
    if (calId) {
      await loadEventsToCalendar(calId);
    }
}

function openEventDetail(ev) {
    const isShared = ev.is_shared === 1;

    const title = ev.title;
    const start = (ev.start_datetime || ev.start_date);
    const end   = (ev.end_datetime || ev.end_date);
    const place = ev.location || "-";
    const memo  = ev.memo || ev.description || "-";

    let msg =
      `제목: ${title}\n` +
      `시간: ${start} ~ ${end}\n` +
      `장소: ${place}\n` +
      `메모: ${memo}\n`;

    if (isShared) {
      msg += `\n※ 공유로 받은 일정입니다.`;
    }

    alert(msg);
}

let shareTargetFollowing = [];
let shareSourceEvent = null;

async function loadFollowingForShare() {
    const token = getToken();
    if (!token) return;
    const res = await fetch(API_BASE + "/follow/following", {
      headers: { "Authorization": "Bearer " + token }
    });
    shareTargetFollowing = res.ok ? await res.json() : [];
  }

  

async function openShareModal(ev) {
    shareSourceEvent = ev;

    // 팔로잉 목록 없으면 로딩
    if (!shareTargetFollowing.length) {
      await loadFollowingForShare();
    }

    const titleEl = document.getElementById("share-event-title");
    const select  = document.getElementById("share-target-select");
    titleEl.textContent = `공유할 일정: ${ev.title}`;

    select.innerHTML = "";

    if (!shareTargetFollowing.length) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "먼저 친구를 팔로우해 주세요.";
      select.appendChild(opt);
      select.disabled = true;
    } else {
      select.disabled = false;
      shareTargetFollowing.forEach(f => {
        const opt = document.createElement("option");
        opt.value = f.following_id;
        opt.textContent = f.following_nickname || `사용자 #${f.following_id}`;
        select.appendChild(opt);
      });
    }

    const modal = new bootstrap.Modal(document.getElementById("shareEventModal"));
    modal.show();
}

document.getElementById("btn-share-confirm").onclick = async () => {
    const select = document.getElementById("share-target-select");
    const targetId = parseInt(select.value, 10);
    if (!targetId || !shareSourceEvent) return;

    const token = getToken();
    const res = await fetch(API_BASE + "/calendar/share/request", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
      },
      body: JSON.stringify({
        event_id: shareSourceEvent.id,
        target_user_id: targetId
      })
    });
    
    if (!res.ok) {
      const err = await res.json().catch(() => null);
      alert((err && err.detail) || "일정 공유에 실패했습니다.");
      return;
    }

    alert("일정 공유 요청을 보냈습니다.");
    bootstrap.Modal.getInstance(document.getElementById("shareEventModal")).hide();
};

async function respondShare(requestId, accept) {
    const token = getToken();
    const res = await fetch(API_BASE + `/calendar/share/${requestId}/respond`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
      },
      body: JSON.stringify({ accept })
    });
    return res.ok;
}

async function showShareConfirmDialog(req) {
    const textEl = document.getElementById("share-confirm-text");
    const name = req.from_user_nickname || `사용자 #${req.from_user_id}`;

    let datePart = "";
    if (req.date) {
      const d = new Date(req.date);
      const y = d.getFullYear();
      const m = d.getMonth() + 1;
      const day = d.getDate();
      datePart = `${y}.${String(m).padStart(2,"0")}.${String(day).padStart(2,"0")}`;
    }

    const title = req.title || "제목 없음";
    const location = req.location || "-";

    textEl.textContent =
      `${name} 님이 '${title}' (${datePart || "날짜 미정"}, ${location}) 일정을 공유했습니다. ` +
      `캘린더에 추가하시겠습니까?`;

    return new Promise(resolve => {
      const modalEl = document.getElementById("shareConfirmModal");
      const modal = new bootstrap.Modal(modalEl);

      const acceptBtn = document.getElementById("btn-share-accept");
      const rejectBtn = document.getElementById("btn-share-reject");

      const cleanup = async (reload) => {
        acceptBtn.onclick = null;
        rejectBtn.onclick = null;
        modal.hide();
        if (reload) {
          const calId = await ensureUserCalendarId();
          if (calId) await loadEventsToCalendar(calId);
        }
        resolve();
      };

      acceptBtn.onclick = async () => {
        const ok = await respondShare(req.id, true);
        if (!ok) alert("공유 일정 수락에 실패했습니다.");
        await cleanup(true);
      };

      rejectBtn.onclick = async () => {
        const ok = await respondShare(req.id, false);
        if (!ok) alert("공유 일정 거절에 실패했습니다.");
        await cleanup(false);
      };

      modal.show();
    });
}

export async function initCalendarPage() {
  if (!requireLoginForMypage()) {
    return;  // 로그인 안 되어 있으면 아래 로직 실행 안 함
  }
  if (!(await requireCompletedProfile())) {
    return;
  }

  const placeInput = document.getElementById("ev-place");
  const suggestBox = document.getElementById("place-suggestions");
  const btnNew     = document.getElementById("btn-new-calendar");
  const calBody    = document.getElementById("calendar-body");

  if (placeInput && suggestBox) {
    let placeTimer = null;
    placeInput.addEventListener("input", () => {
      const q = placeInput.value.trim();
      if (placeTimer) clearTimeout(placeTimer);
      if (!q) {
        suggestBox.style.display = "none";
        suggestBox.innerHTML = "";
        return;
      }
      placeTimer = setTimeout(() => fetchRegionSuggestions(q), 300);
    });
  }

  if (btnNew) {
    btnNew.addEventListener("click", () => openEventModal());
  }
  if (calBody) {
    calBody.addEventListener("dblclick", (e) => {
      const cell = e.target.closest(".calendar-day");
      if (!cell) return;
      const dateStr = cell.dataset.date;
      openDayEventModal(dateStr);
    });
  }

  // 실제 캘린더 채우기
  await setupUserRegion();  
  await initCalendar();
  await loadCalendars();
  const calId = await ensureUserCalendarId();
  if (calId) {
    await loadEventsToCalendar(calId);
  }
  await checkIncomingShares();
}

