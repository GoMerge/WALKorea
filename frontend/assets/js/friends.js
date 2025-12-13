import { initHeader } from "/assets/js/header.js";
import { setupHeaderAndProfile, loadProfileWeather, requireLoginForMypage } from "/assets/js/mypage_common.js";
import { loadNotifications } from "/assets/js/notifications.js";

const API_BASE = "";

let currentUserId = null;
let followingIdSet = new Set();
const token = localStorage.getItem("access_token");

// --- 친구 검색/팔로우/언팔 ---

async function searchFriendsByNickname(query) {
  console.log("searchFriendsByNickname 호출:", query);

  const ul = document.getElementById("friend-search-result");
  if (!ul) return;

  ul.innerHTML = "";
  if (!res.ok) {
    const li = document.createElement("li");
    li.className = "list-group-item text-muted small";
    li.textContent = "검색 결과가 없습니다.";
    ul.appendChild(li);
    return;
  }
 

  const res = await fetch(
    API_BASE + `/follow/search-by-nickname/?nickname=${encodeURIComponent(query)}`,
    { headers: { "Authorization": "Bearer " + token } }
  );
  if (!res.ok) {
    alert("친구 검색에 실패했습니다.");
    return;
  }

  const users = await res.json();

  const filtered = users.filter(u => {
    const uid = u.user_id;
    if (currentUserId && uid === currentUserId) return false;
    if (followingIdSet.has(uid)) return false;
    return true;
  });

  if (!filtered.length) {
    const li = document.createElement("li");
    li.className = "list-group-item text-muted small";
    li.textContent = "검색 결과가 없습니다.";
    ul.appendChild(li);
    return;
  }

  filtered.forEach(user => {
    const li = document.createElement("li");
    li.className = "list-group-item d-flex justify-content-between align-items-center";

    li.innerHTML = `
      <div>
        <div class="fw-semibold">${user.nickname || "(이름 없음)"}</div>
      </div>
      <button class="btn btn-sm btn-outline-success">팔로우</button>
    `;

    const btn = li.querySelector("button");
    btn.onclick = async () => {
      await followUser(user.user_id);
      btn.textContent = "팔로잉";
      btn.classList.remove("btn-outline-success");
      btn.classList.add("btn-secondary");
      btn.disabled = true;
    };

    ul.appendChild(li);
  });
}

async function followUser(targetUserId) {
  if (!token) return;

  const res = await fetch(API_BASE + "/follow/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": "Bearer " + token,
    },
    body: JSON.stringify({ following_id: targetUserId }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => null);
    alert((err && err.detail) || "팔로우 신청에 실패했습니다.");
    return;
  }

  alert("팔로우 신청이 완료되었습니다.");
  await loadFollowLists();
}

async function unfollowUser(followingId, name) {
  if (!token) return;
  if (!confirm(`'${name}' 팔로우를 취소할까요?`)) return;

  const res = await fetch(API_BASE + `/follow/${followingId}`, {
    method: "DELETE",
    headers: { "Authorization": "Bearer " + token },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => null);
    alert((err && err.detail) || "팔로우 취소에 실패했습니다.");
    return;
  }

  alert("팔로우를 취소했습니다.");
  await loadFollowLists();
}

async function loadFollowLists() {
  if (!token) return;

  const [followingRes, followerRes] = await Promise.all([
    fetch(API_BASE + "/follow/following", {
      headers: { "Authorization": "Bearer " + token },
    }),
    fetch(API_BASE + "/follow/followers", {
      headers: { "Authorization": "Bearer " + token },
    }),
  ]);

  const following = followingRes.ok ? await followingRes.json() : [];
  const followers = followerRes.ok ? await followerRes.json() : [];

  const fList = document.getElementById("following-list");
  const rList = document.getElementById("follower-list");
  if (!fList || !rList) return;
  fList.innerHTML = "";
  rList.innerHTML = "";

  const followingCountEl = document.getElementById("following-count");
  const followerCountEl = document.getElementById("follower-count");
  if (followingCountEl) followingCountEl.textContent = `(${following.length})`;
  if (followerCountEl) followerCountEl.textContent = `(${followers.length})`;

  followingIdSet = new Set(following.map(f => f.following_id));

  following.forEach(f => {
    const name = f.following_nickname || `사용자 #${f.following_id}`;

    const li = document.createElement("li");
    li.className = "list-group-item d-flex justify-content-between align-items-center";

    li.innerHTML = `
        <span class="follow-name" title="${name}">${name}</span>
        <button class="btn btn-sm btn-outline-danger">취소</button>
    `;

    const btn = li.querySelector("button");
    btn.onclick = async () => {
      if (!confirm(`'${name}' 팔로우를 취소할까요?`)) return;
      await unfollowUser(f.following_id, name);
    };

    fList.appendChild(li);
  });

  followers.forEach(f => {
    const name = f.follower_nickname || `사용자 #${f.follower_id}`;

    const li = document.createElement("li");
    li.className = "list-group-item d-flex justify-content-between align-items-center";

    li.innerHTML = `
        <span class="follow-name" title="${name}">${name}</span>
    `;

    rList.appendChild(li);
  });
}

// --- 페이지 초기화 ---

export async function initFriendsPage() {
  if (!requireLoginForMypage()) return;

  const token = localStorage.getItem("access_token");
  if (!token) {
    alert("로그인이 필요합니다.");
    window.location.href = "/login";
    return;
  }

  await initHeader();
  await setupHeaderAndProfile();
  await loadProfileWeather();

  const meRes = await fetch(API_BASE + "/user/profile", {
    headers: { Authorization: "Bearer " + token },
  });
  if (meRes.ok) {
    const me = await meRes.json();
    currentUserId = me.id;
  }

  await loadFollowLists();
  await loadNotifications();

  const input = document.getElementById("friend-search-input");
  const btn = document.getElementById("friend-search-btn");
  if (btn && input) {
    btn.addEventListener("click", () => {
      searchFriendsByNickname(input.value);
    });
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        searchFriendsByNickname(input.value);
      }
    });
  }
}
