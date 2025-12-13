import { initHeader } from "./header.js";
import { setupHeaderAndProfile, loadProfileWeather } from "./mypage_common.js";

const API_BASE = "";
let token = null;  // 전역 토큰

// DOM에서 카드/빈 상태 영역 잡기
const gridEl  = document.getElementById("favorites-grid");
const emptyEl = document.getElementById("favorites-empty");

// 좋아요 목록 불러오기
async function loadFavorites() {
  if (!gridEl || !emptyEl) return;

  try {
    const res = await fetch(API_BASE + "/favorites/places", {
      headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error("failed");
    const items = await res.json();

    if (!items.length) {
      emptyEl.classList.remove("d-none");
      gridEl.innerHTML = "";
      return;
    }

    emptyEl.classList.add("d-none");
    gridEl.innerHTML = "";

    items.forEach(p => {
      const col = document.createElement("div");
      col.className = "favorite-card";

      col.innerHTML = `
        <a href="/places/detail/${p.id}" class="text-decoration-none text-reset">
          <div class="card border-0">
            <div class="position-relative">
              <img src="${p.firstimage || '/static/no_image.jpg'}"
                   alt="${p.title}">
              <button type="button"
                      class="btn btn-light btn-sm position-absolute top-0 end-0 m-2 rounded-circle like-btn"
                      data-place-id="${p.id}"
                      style="box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                <span class="text-danger">♥</span>
              </button>
            </div>
            <div class="mt-2">
              <div class="fw-semibold text-truncate" title="${p.title}">${p.title}</div>
              <div class="text-muted small text-truncate" title="${p.addr1 || ''}">
                ${p.addr1 || ""}
              </div>
            </div>
          </div>
        </a>
      `;
      gridEl.appendChild(col);
    });
  } catch (e) {
    console.error(e);
    alert("좋아요 목록을 불러오지 못했습니다.");
  }
}

// 하트 클릭 시 해제 + 새로고침
document.addEventListener("click", async (e) => {
  const btn = e.target.closest(".like-btn");
  if (!btn) return;

  if (!token) {
    alert("로그인이 필요합니다.");
    window.location.href = "/login";
    return;
  }

  e.preventDefault();   // 카드 링크 클릭 막기
  e.stopPropagation();

  const placeId = btn.dataset.placeId;
  try {
    const res = await fetch(API_BASE + `/favorites/places/${placeId}`, {
      method: "POST",
      headers: { "Authorization": "Bearer " + token }
    });
    if (!res.ok) throw new Error();
    const data = await res.json();
    if (!data.liked) {
      await loadFavorites();   // 해제되면 목록 갱신
    }
  } catch (e2) {
    console.error(e2);
    alert("좋아요 해제에 실패했습니다.");
  }
});

// 페이지 진입 시 한 번만 초기화
document.addEventListener("DOMContentLoaded", async () => {
  token = localStorage.getItem("access_token");
  if (!token) {
    alert("로그인이 필요합니다.");
    window.location.href = "/login";
    return;
  }

  await initHeader();
  await setupHeaderAndProfile();
  await loadProfileWeather();

  await loadFavorites();
});
