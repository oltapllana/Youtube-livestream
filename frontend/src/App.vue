<template>
  <div>
    <TopBar :clock-label="clockLabel" @open-prefs="showPrefs = true" />

    <PreferencesPanel
      v-model:open="showPrefs"
      :prefs="prefs"
      @save="onSavePrefs"
      @save-and-generate="onSaveAndGenerate"
    />

    <main class="main">
      <div class="content-container">
        <section class="player-section">
          <VideoPlayer
            :program="currentProg"
            :next-program="nextProg"
            :loading="loader.open"
            :loading-msg="loader.message"
            :has-schedule="schedule.length > 0"
          />
          <NowPlaying :program="currentProg" :next-program="nextProg" />
        </section>

        <aside class="schedule-sidebar">
          <div class="sidebar-header">
            <h3 class="section-title">Up Next</h3>
            <span v-if="schedule.length" class="schedule-stats">
              {{ futureCount }} programs remaining
            </span>
          </div>
          <ScheduleList :schedule="schedule" :now="adjustedNow" :loading="loader.open" />
        </aside>
      </div>
    </main>

    <LoadingOverlay :open="loader.open" :title="loader.title" :message="loader.message" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from "vue";
import {
  minsToTime,
  timeToMins,
  getNowMins,
  cleanTitle,
  fetchPreferences,
  savePreferences as apiSavePrefs,
  generateSchedule as apiGenerate,
} from "./api.js";

import TopBar from "./components/TopBar.vue";
import PreferencesPanel from "./components/PreferencesPanel.vue";
import VideoPlayer from "./components/VideoPlayer.vue";
import NowPlaying from "./components/NowPlaying.vue";
import ScheduleList from "./components/ScheduleList.vue";
import LoadingOverlay from "./components/LoadingOverlay.vue";
import { useLoading, withLoader } from "./loading.js";

const ALL_CATEGORIES = ["science", "technology", "climate"];

function normalizeCategories(categories = []) {
  if (!Array.isArray(categories)) return [];
  return [...new Set(categories.map((c) => String(c).toLowerCase()))];
}

function hasAllCategories(categories = []) {
  const selected = new Set(normalizeCategories(categories));
  return ALL_CATEGORIES.every((cat) => selected.has(cat));
}

// ── State ────────────────────────────────────────────────────
const loader = useLoading();
const showPrefs = ref(false);

const schedule = ref([]);
const clockNow = ref(getNowMins());
const scheduleEndAt = ref(null); // Absolute timestamp (ms) when current schedule ends

const prefs = ref({
  openTime: minsToTime(getNowMins()),
  closeTime: "23:00",
  minDurationPct: 100,
  channelsCount: 10,
  switchPenaltyPct: 10,
  terminationPenalty: 20,
  maxConsecutiveGenre: 2,
  bonusPct: 5,
  categoryFilter: [...ALL_CATEGORIES],
  selectedChannelIds: [],
});

let clockTimer = null;
let expirationTimer = null; // 1-second timer for precise schedule expiration
let isRegenerating = false; // guard against double-triggering autoRegenerate

/** Calculate ms until closing_time from right now (second-precise). */
function msUntilClosing(closingTimeMinutes, openingTimeMinutes) {
  const now = new Date();
  const nowMs = now.getTime();

  // Build a Date for closingTime today
  const closingH = Math.floor(closingTimeMinutes / 60);
  const closingM = closingTimeMinutes % 60;

  if (closingTimeMinutes > 1440) {
    // Cross-midnight: closing is tomorrow
    const closeDate = new Date(now);
    const adjMin = closingTimeMinutes - 1440;
    closeDate.setHours(Math.floor(adjMin / 60), adjMin % 60, 0, 0);
    // If we're before midnight (still in "today" part of the schedule)
    if (now.getHours() * 60 + now.getMinutes() >= openingTimeMinutes) {
      closeDate.setDate(closeDate.getDate() + 1);
    }
    const diff = closeDate.getTime() - nowMs;
    return diff > 0 ? diff : 0;
  }

  const closeDate = new Date(now);
  closeDate.setHours(closingH, closingM, 0, 0);
  const diff = closeDate.getTime() - nowMs;
  return diff > 0 ? diff : 0;
}

// ── Computed: time-aware program lookup (handles cross-midnight) ──
const adjustedNow = computed(() => {
  const now = clockNow.value;
  if (schedule.value.length === 0) return now;
  const maxEnd = Math.max(...schedule.value.map((p) => p.end));
  // If schedule has cross-midnight times (>1440) and we're in the early hours
  if (maxEnd > 1440 && now < maxEnd - 1440) {
    return now + 1440;
  }
  return now;
});

const currentProg = computed(() => {
  const now = adjustedNow.value;
  // Primary: a program whose timeslot covers right now
  const playing = schedule.value.find((p) => now >= p.start && now < p.end);
  if (playing) return playing;
  // Grace period: show the program that JUST ended (within 2 minutes)
  // so the video stays visible while auto-regeneration is in progress
  const justEnded = [...schedule.value]
    .filter((p) => p.end <= now && now - p.end <= 2)
    .sort((a, b) => b.end - a.end)[0];
  if (justEnded) return justEnded;
  return null;
});

const nextProg = computed(() => {
  const now = adjustedNow.value;
  return schedule.value.find((p) => p.start > now) || null;
});

const futureCount = computed(() => {
  const now = adjustedNow.value;
  return schedule.value.filter((p) => p.start > now).length;
});

const clockLabel = computed(() => {
  if (currentProg.value) {
    const name = currentProg.value.program_name || cleanTitle(currentProg.value.program_id);
    return `Now playing: ${name}`;
  }
  if (nextProg.value) return `Next at ${minsToTime(nextProg.value.start)}`;
  return minsToTime(clockNow.value);
});

// ── Build payload from prefs ─────────────────────────────────
function buildPayload() {
  const categoryFilter = normalizeCategories(prefs.value.categoryFilter);

  return {
    opening_time: getNowMins(),
    closing_time: timeToMins(prefs.value.closeTime),
    min_duration_pct: prefs.value.minDurationPct,
    channels_count: prefs.value.channelsCount,
    switch_penalty_pct: prefs.value.switchPenaltyPct,
    termination_penalty: prefs.value.terminationPenalty,
    max_consecutive_genre: prefs.value.maxConsecutiveGenre,
    bonus_pct: prefs.value.bonusPct,
    category_filter: categoryFilter,
    selected_channel_ids: prefs.value.selectedChannelIds,
  };
}

// ── Build default payload with dynamic time window ───────────
function buildAutoPayload(openTime, closeTime) {
  const categoryFilter = normalizeCategories(prefs.value.categoryFilter);

  return {
    opening_time: openTime,
    closing_time: closeTime,
    min_duration_pct: 100,
    channels_count: 10,
    switch_penalty_pct: 10,
    termination_penalty: 20,
    max_consecutive_genre: prefs.value.maxConsecutiveGenre,
    bonus_pct: prefs.value.bonusPct,
    category_filter: categoryFilter,
    selected_channel_ids: prefs.value.selectedChannelIds,
  };
}

// ── Load prefs from API ──────────────────────────────────────
async function loadPreferences() {
  return withLoader({ title: "Loading", message: "Fetching preferences…" }, async () => {
    const data = await fetchPreferences();
    prefs.value.openTime = minsToTime(getNowMins());
    prefs.value.closeTime = minsToTime(data.closing_time ?? 1380);
    prefs.value.minDurationPct = data.min_duration_pct ?? 100;
    prefs.value.channelsCount = data.channels_count ?? 10;
    prefs.value.switchPenaltyPct = data.switch_penalty_pct ?? 10;
    prefs.value.terminationPenalty = data.termination_penalty ?? 20;
    prefs.value.maxConsecutiveGenre = data.max_consecutive_genre ?? 2;
    prefs.value.bonusPct = data.bonus_pct ?? 5;
    const loadedCategories = normalizeCategories(data.category_filter ?? []);
    prefs.value.categoryFilter = loadedCategories.length
      ? loadedCategories
      : [...ALL_CATEGORIES];
    prefs.value.selectedChannelIds = data.selected_channel_ids ?? [];
  }).catch((e) => console.warn("Could not load preferences:", e));
}

// ── Generate schedule ────────────────────────────────────────
let genCount = 0;

async function runGenerate(customPayload = null) {
  return withLoader(
    { title: "Generating", message: "Discovering live streams and building schedule…" },
    async () => {
      const payload = customPayload || buildPayload();
      const data = await apiGenerate(payload);

      schedule.value = data.scheduled_programs || [];

      // Track absolute end timestamp (second-precise)
      const msLeft = msUntilClosing(payload.closing_time, payload.opening_time);
      scheduleEndAt.value = Date.now() + msLeft;

      // Start 1-second expiration timer
      startExpirationTimer();

      // Update prefs UI (shfaq kohë normale)
      prefs.value.openTime = minsToTime(payload.opening_time % 1440);
      prefs.value.closeTime = minsToTime(payload.closing_time % 1440);
    }
  ).catch((err) => {
    console.error("Schedule generation failed:", err);
    alert("Error: " + err.message);
  });
}

// ── Auto-regenerate when schedule expires ────────────────────
function startExpirationTimer() {
  if (expirationTimer) clearInterval(expirationTimer);
  expirationTimer = setInterval(() => {
    if (
      scheduleEndAt.value !== null &&
      Date.now() >= scheduleEndAt.value &&
      !isRegenerating
    ) {
      console.log("[EXPIRATION] Schedule end reached, triggering auto-regenerate…");
      clearInterval(expirationTimer);
      expirationTimer = null;
      autoRegenerate();
    }
  }, 1000); // check every 1 second
}

async function autoRegenerate() {
  if (isRegenerating) return;
  isRegenerating = true;
  try {
    const now = getNowMins();
    const openTime = now;
    const closeTime = now + 720; // 12 hours later

    console.log(
      `[AUTO-REGENERATE] Starting new 12-hour window: ${minsToTime(
        openTime
      )} → ${minsToTime(closeTime)}`
    );

    await runGenerate(buildAutoPayload(openTime, closeTime));
  } finally {
    isRegenerating = false;
  }
}

// ── Panel actions ────────────────────────────────────────────
async function onSavePrefs() {
  return withLoader({ title: "Saving", message: "Saving preferences…" }, () =>
    apiSavePrefs(buildPayload())
  );
}

async function onSaveAndGenerate() {
  return withLoader({ title: "Saving", message: "Saving & generating…" }, async () => {
    await apiSavePrefs(buildPayload());
    showPrefs.value = false;
    await runGenerate();
  });
}

// ── Lifecycle ────────────────────────────────────────────────
onMounted(async () => {
  // 1. Load saved preferences
  await loadPreferences();

  // 2. Check if current time is within the saved schedule window
  const now = getNowMins();
  const openMins = timeToMins(prefs.value.openTime);
  const closeMins = timeToMins(prefs.value.closeTime);

  if (now < openMins || now >= closeMins) {
    // Current time is outside the schedule window → auto-regenerate
    // with start = now, end = now + 12 hours
    console.log(
      `[MOUNT] Current time ${minsToTime(now)} is outside [${prefs.value.openTime}, ${
        prefs.value.closeTime
      }]. Auto-regenerating…`
    );
    await autoRegenerate();
  } else {
    await runGenerate();
  }

  // 3. Clock tick every 1 second for responsive time-aware sync
  clockTimer = setInterval(() => {
    clockNow.value = getNowMins();
  }, 1000);

  document.addEventListener("keydown", onKeydown);
});

// ── Watch for schedule expiration (backup — main check is the 1s timer) ──
watch(clockNow, () => {
  if (
    scheduleEndAt.value !== null &&
    Date.now() >= scheduleEndAt.value &&
    !isRegenerating
  ) {
    autoRegenerate();
  }
});

onUnmounted(() => {
  if (clockTimer) clearInterval(clockTimer);
  if (expirationTimer) clearInterval(expirationTimer);
  document.removeEventListener("keydown", onKeydown);
});

function onKeydown(e) {
  if (e.key === "Escape") {
    if (showPrefs.value) showPrefs.value = false;
    if (document.fullscreenElement) document.exitFullscreen();
  }
  if (e.key === "f" && !e.ctrlKey && !e.metaKey) {
    const tag = document.activeElement.tagName;
    if (tag !== "INPUT" && tag !== "TEXTAREA") {
      const wrap = document.querySelector(".player-wrap");
      if (!document.fullscreenElement) {
        wrap?.requestFullscreen().catch(() => wrap?.classList.toggle("is-fullscreen"));
      } else {
        document.exitFullscreen();
      }
    }
  }
}
</script>
