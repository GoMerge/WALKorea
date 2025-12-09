let notifCount = 0;
let ws = null;
let currentToken = null;

const API_BASE = "";

// 🔥 1. 배지 업데이트 함수 개선 (핵심!)
function updateBadge(count = notifCount) {
  const badge = document.getElementById("notif-badge");
  if (!badge) return;
  
  notifCount = count;
  badge.textContent = count;
  badge.classList.toggle("d-none", count === 0);
  console.log('📊 배지 업데이트:', count);
}

// ✅ 2. loadNotifications 완전 개선 (배지 즉시 업데이트)
export async function loadNotifications() {
  console.log("🔔 loadNotifications 호출됨");
  
  const token = localStorage.getItem("access_token");
  if (!token) {
    console.log('❌ 토큰 없음');
    currentToken = null;
    updateBadge(0);
    return [];
  }
  
  currentToken = token;
  
  try {
    const res = await fetch(API_BASE + "/notifications/", {
      headers: { "Authorization": `Bearer ${token}` }
    });
    
    if (!res.ok) {
      console.error('알림 API 에러:', res.status);
      return [];
    }
    
    const items = await res.json();
    console.log("✅ 알림 데이터:", items.length, '개');
    
    // 🔥 배지 즉시 업데이트 (가장 중요!)
    updateBadge(items.length);
    
    // 리스트 렌더링
    const listEl = document.getElementById("notif-list");
    const emptyEl = document.getElementById("notif-empty-text");
    
    if (!listEl) {
      console.error('❌ notif-list 요소 없음');
      return items;
    }
    
    listEl.innerHTML = "";
    
    if (!items.length && emptyEl) {
      emptyEl.style.display = "block";
      emptyEl.textContent = "아직 알림이 없습니다.";
    } else if (emptyEl) {
      emptyEl.style.display = "none";
    }
    
    // 각 알림 렌더링
    items.forEach(n => renderNotificationItem(listEl, n));
    
    return items;
    
  } catch (e) {
    console.error('알림 로드 실패:', e);
    updateBadge(0);
    return [];
  }
}

// ✅ 3. 초기화 함수 추가 (header.js에서 호출)
export async function initNotifications() {
  console.log('🔔 notifications 초기화');
  await loadNotifications(); // 배지 + 리스트 초기화
  
  // 드롭다운 클릭 이벤트 설정
  setupDropdownEvents();
}

// ✅ 4. 드롭다운 이벤트 설정
function setupDropdownEvents() {
  const dropdownBtn = document.getElementById('notifDropdown');
  if (dropdownBtn) {
    // Bootstrap 드롭다운 + 알림 새로고침
    dropdownBtn.addEventListener('click', async () => {
      console.log('🔔 드롭다운 클릭');
      await loadNotifications(); // 클릭시 최신화
    });
  }
  
  // 전체삭제 버튼
  const clearBtn = document.getElementById('notif-clear-all');
  if (clearBtn) {
    clearBtn.onclick = deleteAllNotifications;
  }
}

// ✅ 기존 renderNotificationItem 유지 (완벽함)
export function renderNotificationItem(container, n) {
  const li = document.createElement("li");
  li.className = "notif-item d-flex justify-content-between align-items-start py-1";

  const left = document.createElement("div");
  left.className = "d-flex align-items-start gap-2";

  const avatar = document.createElement("div");
  avatar.className = "notif-avatar";

  if (n.type === "followed" || n.type === "follow") {
    avatar.textContent = "👤";
  } else if (n.type === "calendar_share") {
    avatar.textContent = "📅";
  } else {
    avatar.textContent = "🔔";
  }

  const textBox = document.createElement("div");
  const msgDiv = document.createElement("div");
  msgDiv.className = "small mb-0";
  msgDiv.textContent = n.message;

  textBox.appendChild(msgDiv);
  left.appendChild(avatar);
  left.appendChild(textBox);

  const delBtn = document.createElement("button");
  delBtn.type = "button";
  delBtn.className = "notif-close-btn";
  delBtn.innerHTML = "×";

  delBtn.onclick = async () => {
    if (!currentToken) return;
    const res = await fetch(`${API_BASE}/notifications/${n.id}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    if (res.ok) {
      li.remove();
      updateBadge(notifCount - 1);
      
      const listEl = document.getElementById("notif-list");
      const emptyEl = document.getElementById("notif-empty-text");
      if (listEl.children.length === 0 && emptyEl) {
        emptyEl.style.display = "block";
        emptyEl.textContent = "아직 알림이 없습니다.";
      }
    }
  };

  li.appendChild(left);
  li.appendChild(delBtn);
  container.appendChild(li);
}

// ✅ 기존 deleteAllNotifications 유지
export async function deleteAllNotifications() {
  if (!currentToken) return;
  
  if (!confirm('모든 알림을 삭제하시겠습니까?')) return;
  
  const res = await fetch(API_BASE + "/notifications/", {
    method: "DELETE",
    headers: { "Authorization": `Bearer ${currentToken}` }
  });
  
  if (res.ok) {
    const listEl = document.getElementById("notif-list");
    if (listEl) listEl.innerHTML = "";
    updateBadge(0);
  }
}

// ✅ 기존 WebSocket 유지
export function initWebsocket(userId) {
  if (!userId) return;
  if (ws) ws.close();

  ws = new WebSocket(`ws://localhost:8000/ws/notify/${userId}`);

  ws.onopen = () => console.log("✅ WebSocket 연결됨");
  ws.onmessage = async (e) => {
    console.log("🔔 WebSocket 메시지:", e.data);
    try {
      const payload = JSON.parse(e.data);
      const ul = document.getElementById("notif-list");
      if (!ul) return;

      const n = {
        id: payload.notification_id,
        message: payload.message,
        type: payload.event,
      };
      renderNotificationItem(ul, n);
      updateBadge(notifCount + 1);
    } catch (err) {
      console.error("WebSocket 파싱 에러:", err);
    }
  };

  ws.onclose = () => console.log("❌ WebSocket 연결 종료");
  ws.onerror = (e) => console.error("WebSocket 에러:", e);
}

// 디버그용
window.debugLoadNotifications = loadNotifications;
