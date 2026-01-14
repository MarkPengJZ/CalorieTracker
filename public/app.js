const timezoneInput = document.getElementById("timezone");
const refreshButton = document.getElementById("refresh");
const currentStreakEl = document.getElementById("current-streak");
const longestStreakEl = document.getElementById("longest-streak");
const lastSuccessEl = document.getElementById("last-success");
const todaySummaryEl = document.getElementById("today-summary");
const badgesEl = document.getElementById("badges");
const historyEl = document.getElementById("history");
const petMoodEl = document.getElementById("pet-mood");
const petMoodDetailEl = document.getElementById("pet-mood-detail");
const petMessageEl = document.getElementById("pet-message");
const avatarButton = document.getElementById("avatar-button");
const avatarFace = document.getElementById("avatar-face");
const avatarMouth = document.getElementById("avatar-mouth");
const avatarBadge = document.getElementById("avatar-badge");
const petFeedButton = document.getElementById("pet-feed");
const petPlayButton = document.getElementById("pet-play");
const petCheerButton = document.getElementById("pet-cheer");
const mealForm = document.getElementById("meal-form");
const checkinForm = document.getElementById("checkin-form");

const petState = {
  mood: "Curious",
  moodDetail: "Log a meal or check in to cheer Sprout up.",
  level: 1,
  energy: 50
};

function getTimezone() {
  return timezoneInput.value || Intl.DateTimeFormat().resolvedOptions().timeZone;
}

async function fetchStatus() {
  const timezone = getTimezone();
  const response = await fetch(`/api/streak/status?timezone=${encodeURIComponent(timezone)}`);
  return response.json();
}

async function fetchHistory() {
  const timezone = getTimezone();
  const response = await fetch(`/api/streak/history?timezone=${encodeURIComponent(timezone)}&days=14`);
  return response.json();
}

function renderStatus(status) {
  currentStreakEl.textContent = `${status.currentStreak} day(s)`;
  longestStreakEl.textContent = `${status.longestStreak} day(s)`;
  lastSuccessEl.textContent = status.lastSuccessDate || "No successes yet";
  todaySummaryEl.textContent = `${status.today.date} · ${status.today.meals} meal(s), ${status.today.calories} calories${status.today.checkIn ? " · checked in" : ""}`;

  badgesEl.innerHTML = "";
  status.badges.forEach((badge) => {
    const li = document.createElement("li");
    li.classList.add("badge-item");
    li.textContent = badge.achieved
      ? `🏅 ${badge.label} (earned ${badge.achievedOn})`
      : `⬜ ${badge.label}`;
    badgesEl.appendChild(li);
  });

  updatePetState(status);
}

function renderHistory(history) {
  historyEl.innerHTML = "";
  history.history
    .slice()
    .reverse()
    .forEach((day) => {
      const li = document.createElement("li");
      li.textContent = `${day.date}: ${day.success ? "✅ success" : "—"} · ${day.meals} meal(s), ${day.calories} calories${day.checkIn ? " · checked in" : ""}`;
      historyEl.appendChild(li);
    });
}

async function refresh() {
  const [status, history] = await Promise.all([fetchStatus(), fetchHistory()]);
  renderStatus(status);
  renderHistory(history);
}

function updatePetState(status) {
  const baseEnergy = status.today.calories >= 500 ? 80 : status.today.meals > 0 ? 65 : 45;
  const streakBoost = Math.min(status.currentStreak * 2, 20);
  petState.energy = Math.min(baseEnergy + streakBoost, 100);
  petState.level = Math.max(1, Math.floor(status.currentStreak / 3) + 1);

  if (status.today.success) {
    petState.mood = "Thriving";
    petState.moodDetail = "Sprout is energized by your successful day!";
  } else if (status.today.meals > 0 || status.today.checkIn) {
    petState.mood = "Encouraged";
    petState.moodDetail = "Nice start! One more win will boost Sprout.";
  } else {
    petState.mood = "Curious";
    petState.moodDetail = "Sprout is waiting for a snack or a check-in.";
  }

  renderPetState();
}

function renderPetState() {
  petMoodEl.textContent = petState.mood;
  petMoodDetailEl.textContent = petState.moodDetail;
  avatarBadge.textContent = `Lv. ${petState.level}`;

  if (petState.mood === "Thriving") {
    avatarFace.dataset.mood = "thriving";
    avatarMouth.style.borderBottomWidth = "6px";
  } else if (petState.mood === "Encouraged") {
    avatarFace.dataset.mood = "encouraged";
    avatarMouth.style.borderBottomWidth = "4px";
  } else {
    avatarFace.dataset.mood = "curious";
    avatarMouth.style.borderBottomWidth = "3px";
  }
}

function animateAvatar(message) {
  avatarButton.animate(
    [
      { transform: "translateY(0) scale(1)" },
      { transform: "translateY(-6px) scale(1.03)" },
      { transform: "translateY(0) scale(1)" }
    ],
    { duration: 360, easing: "ease-out" }
  );
  petMessageEl.textContent = message;
}

function handlePetInteraction(type) {
  if (type === "feed") {
    petState.energy = Math.min(petState.energy + 10, 100);
    animateAvatar("Sprout munches happily. +10 energy!");
  } else if (type === "play") {
    petState.energy = Math.min(petState.energy + 6, 100);
    animateAvatar("Sprout does a happy wiggle!");
  } else if (type === "cheer") {
    animateAvatar("You cheer Sprout on. It feels motivated!");
  } else {
    animateAvatar("Sprout says hi! Tap the buttons to play.");
  }
}

mealForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(mealForm);
  const payload = {
    calories: formData.get("calories"),
    description: formData.get("description")
  };

  await fetch("/api/meals", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  mealForm.reset();
  refresh();
  handlePetInteraction("feed");
});

checkinForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(checkinForm);
  const payload = {
    note: formData.get("note")
  };

  await fetch("/api/checkins", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  checkinForm.reset();
  refresh();
  handlePetInteraction("cheer");
});

refreshButton.addEventListener("click", refresh);
avatarButton.addEventListener("click", () => handlePetInteraction("tap"));
petFeedButton.addEventListener("click", () => handlePetInteraction("feed"));
petPlayButton.addEventListener("click", () => handlePetInteraction("play"));
petCheerButton.addEventListener("click", () => handlePetInteraction("cheer"));

refresh();
