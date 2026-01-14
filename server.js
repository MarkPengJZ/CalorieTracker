import express from "express";
import { DateTime } from "luxon";
import { promises as fs } from "fs";
import path from "path";
import { fileURLToPath } from "url";
import crypto from "crypto";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const DATA_DIR = path.join(__dirname, "data");
const DATA_FILE = path.join(DATA_DIR, "store.json");
const DEFAULT_TIMEZONE = "UTC";
const SUCCESS_DEFINITION = {
  minMeals: 1,
  minCalories: 500,
  logic: "meals>=1 || calories>=500"
};
const BADGE_MILESTONES = [
  { id: "streak-3", label: "3-Day Streak", threshold: 3 },
  { id: "streak-7", label: "7-Day Streak", threshold: 7 },
  { id: "streak-14", label: "14-Day Streak", threshold: 14 },
  { id: "streak-30", label: "30-Day Streak", threshold: 30 }
];

async function ensureDataFile() {
  await fs.mkdir(DATA_DIR, { recursive: true });
  try {
    await fs.access(DATA_FILE);
  } catch {
    const initial = { meals: [], checkins: [] };
    await fs.writeFile(DATA_FILE, JSON.stringify(initial, null, 2));
  }
}

async function loadStore() {
  await ensureDataFile();
  const raw = await fs.readFile(DATA_FILE, "utf-8");
  return JSON.parse(raw);
}

async function saveStore(store) {
  await fs.writeFile(DATA_FILE, JSON.stringify(store, null, 2));
}

function getNowIso() {
  return DateTime.utc().toISO();
}

function normalizeTimezone(timezone) {
  if (!timezone) {
    return DEFAULT_TIMEZONE;
  }
  const zone = DateTime.local().setZone(timezone).zoneName;
  return zone || DEFAULT_TIMEZONE;
}

function toDayKey(iso, timezone) {
  return DateTime.fromISO(iso, { zone: "utc" }).setZone(timezone).toISODate();
}

function buildDailySummaries(store, timezone) {
  const summaries = new Map();

  store.meals.forEach((meal) => {
    const dayKey = toDayKey(meal.timestamp, timezone);
    const summary = summaries.get(dayKey) || {
      date: dayKey,
      meals: 0,
      calories: 0,
      checkIn: false
    };
    summary.meals += 1;
    summary.calories += meal.calories;
    summaries.set(dayKey, summary);
  });

  store.checkins.forEach((checkin) => {
    const dayKey = toDayKey(checkin.timestamp, timezone);
    const summary = summaries.get(dayKey) || {
      date: dayKey,
      meals: 0,
      calories: 0,
      checkIn: false
    };
    summary.checkIn = true;
    summaries.set(dayKey, summary);
  });

  return summaries;
}

function isSuccessful(summary) {
  return summary.meals >= SUCCESS_DEFINITION.minMeals || summary.calories >= SUCCESS_DEFINITION.minCalories;
}

function buildDateRange(start, end) {
  const dates = [];
  let cursor = DateTime.fromISO(start);
  const last = DateTime.fromISO(end);

  while (cursor <= last) {
    dates.push(cursor.toISODate());
    cursor = cursor.plus({ days: 1 });
  }

  return dates;
}

function calculateStreaks(summaries, timezone) {
  const today = DateTime.utc().setZone(timezone).toISODate();
  const summaryValues = Array.from(summaries.values());
  const successfulDays = summaryValues
    .filter((summary) => isSuccessful(summary))
    .map((summary) => summary.date)
    .sort();

  const earliestDate = successfulDays[0] || today;
  const dateRange = buildDateRange(earliestDate, today);

  let currentStreak = 0;
  for (let i = dateRange.length - 1; i >= 0; i -= 1) {
    const date = dateRange[i];
    const summary = summaries.get(date);
    if (summary && isSuccessful(summary)) {
      currentStreak += 1;
    } else {
      break;
    }
  }

  let longestStreak = 0;
  let runningStreak = 0;
  const badgeDates = new Map();
  dateRange.forEach((date) => {
    const summary = summaries.get(date);
    if (summary && isSuccessful(summary)) {
      runningStreak += 1;
      longestStreak = Math.max(longestStreak, runningStreak);
      BADGE_MILESTONES.forEach((badge) => {
        if (runningStreak === badge.threshold) {
          badgeDates.set(badge.id, date);
        }
      });
    } else {
      runningStreak = 0;
    }
  });

  const lastSuccessDate = successfulDays[successfulDays.length - 1] || null;

  return {
    currentStreak,
    longestStreak,
    lastSuccessDate,
    badgeDates,
    today
  };
}

function buildBadges(longestStreak, badgeDates) {
  return BADGE_MILESTONES.map((badge) => ({
    ...badge,
    achieved: longestStreak >= badge.threshold,
    achievedOn: badgeDates.get(badge.id) || null
  }));
}

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

app.get("/api/streak/status", async (req, res) => {
  const timezone = normalizeTimezone(req.query.timezone);
  const store = await loadStore();
  const summaries = buildDailySummaries(store, timezone);
  const streaks = calculateStreaks(summaries, timezone);
  const todaySummary = summaries.get(streaks.today) || {
    date: streaks.today,
    meals: 0,
    calories: 0,
    checkIn: false
  };

  res.json({
    timezone,
    successDefinition: SUCCESS_DEFINITION,
    currentStreak: streaks.currentStreak,
    longestStreak: streaks.longestStreak,
    lastSuccessDate: streaks.lastSuccessDate,
    badges: buildBadges(streaks.longestStreak, streaks.badgeDates),
    today: {
      ...todaySummary,
      success: isSuccessful(todaySummary)
    }
  });
});

app.get("/api/streak/history", async (req, res) => {
  const timezone = normalizeTimezone(req.query.timezone);
  const days = Number.parseInt(req.query.days, 10) || 30;
  const store = await loadStore();
  const summaries = buildDailySummaries(store, timezone);

  const today = DateTime.utc().setZone(timezone).toISODate();
  const start = DateTime.fromISO(today).minus({ days: days - 1 }).toISODate();
  const dateRange = buildDateRange(start, today);

  const history = dateRange.map((date) => {
    const summary = summaries.get(date) || {
      date,
      meals: 0,
      calories: 0,
      checkIn: false
    };
    return {
      ...summary,
      success: isSuccessful(summary)
    };
  });

  res.json({
    timezone,
    range: { start, end: today },
    history
  });
});

app.post("/api/meals", async (req, res) => {
  const { calories, description, timestamp } = req.body;
  const parsedCalories = Number.parseInt(calories, 10);

  if (!Number.isFinite(parsedCalories) || parsedCalories <= 0) {
    res.status(400).json({ error: "Calories must be a positive number." });
    return;
  }

  const store = await loadStore();
  const meal = {
    id: crypto.randomUUID(),
    calories: parsedCalories,
    description: description || "",
    timestamp: timestamp || getNowIso()
  };

  store.meals.push(meal);
  await saveStore(store);

  res.status(201).json(meal);
});

app.post("/api/checkins", async (req, res) => {
  const { timestamp, note } = req.body;
  const store = await loadStore();

  const checkin = {
    id: crypto.randomUUID(),
    note: note || "",
    timestamp: timestamp || getNowIso()
  };

  store.checkins.push(checkin);
  await saveStore(store);

  res.status(201).json(checkin);
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  // eslint-disable-next-line no-console
  console.log(`Server listening on port ${port}`);
});
