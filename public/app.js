const timezoneInput = document.getElementById("timezone");
const refreshButton = document.getElementById("refresh");
const currentStreakEl = document.getElementById("current-streak");
const longestStreakEl = document.getElementById("longest-streak");
const lastSuccessEl = document.getElementById("last-success");
const todaySummaryEl = document.getElementById("today-summary");
const badgesEl = document.getElementById("badges");
const historyEl = document.getElementById("history");
const mealForm = document.getElementById("meal-form");
const checkinForm = document.getElementById("checkin-form");

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
    li.textContent = badge.achieved
      ? `🏅 ${badge.label} (earned ${badge.achievedOn})`
      : `⬜ ${badge.label}`;
    badgesEl.appendChild(li);
  });
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
});

refreshButton.addEventListener("click", refresh);

refresh();
