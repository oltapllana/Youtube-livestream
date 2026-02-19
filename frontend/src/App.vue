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
      <section class="player-section">
        <VideoPlayer
          :program="currentProg"
          :next-program="nextProg"
          :loading="loader.open"
          :loading-msg="loader.message"
          :has-schedule="schedule.length > 0"
        />
        <NowPlaying
          :program="currentProg"
          :next-program="nextProg"
        />
      </section>

      <section class="schedule-section">
        <h3 class="section-title">Schedule</h3>
        <ScheduleList
          :schedule="schedule"
          :now="clockNow"
          :loading="loader.open"
        />
      </section>
    </main>

 <LoadingOverlay
  :open="loader.open"
  :title="loader.title"
  :message="loader.message"
/>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import {
  minsToTime,
  timeToMins,
  getNowMins,
  cleanTitle,
  fetchPreferences,
  savePreferences as apiSavePrefs,
  generateSchedule as apiGenerate,
} from './api.js'

import TopBar from './components/TopBar.vue'
import PreferencesPanel from './components/PreferencesPanel.vue'
import VideoPlayer from './components/VideoPlayer.vue'
import NowPlaying from './components/NowPlaying.vue'
import ScheduleList from './components/ScheduleList.vue'
import LoadingOverlay from './components/LoadingOverlay.vue'
import { useLoading, withLoader } from './loading.js'

// ── State ────────────────────────────────────────────────────
const loader = useLoading()
const showPrefs  = ref(false)

const schedule   = ref([])
const clockNow   = ref(getNowMins())
const scheduleClosingTime = ref(null) // Track when current schedule ends

const prefs = ref({
  openTime: '08:00',
  closeTime: '23:00',
  minDurationPct: 100,
  channelsCount: 10,
  switchPenaltyPct: 10,
  terminationPenalty: 20,
  maxConsecutiveGenre: 2,
  bonusPct: 5,
  categoryFilter: [],
  selectedChannelIds: [],
})

let clockTimer = null

// ── Computed: time-aware program lookup ──────────────────────
const currentProg = computed(() => {
  const now = clockNow.value
  return schedule.value.find((p) => now >= p.start && now < p.end) || null
})

const nextProg = computed(() => {
  const now = clockNow.value
  return schedule.value.find((p) => p.start > now) || null
})

const clockLabel = computed(() => {
  if (currentProg.value) return `Now playing: ${cleanTitle(currentProg.value.program_id)}`
  if (nextProg.value) return `Next at ${minsToTime(nextProg.value.start)}`
  return minsToTime(clockNow.value)
})

// ── Build payload from prefs ─────────────────────────────────
function buildPayload() {
  return {
    opening_time: timeToMins(prefs.value.openTime),
    closing_time: timeToMins(prefs.value.closeTime),
    min_duration_pct: prefs.value.minDurationPct,
    channels_count: prefs.value.channelsCount,
    switch_penalty_pct: prefs.value.switchPenaltyPct,
    termination_penalty: prefs.value.terminationPenalty,
    max_consecutive_genre: prefs.value.maxConsecutiveGenre,
    time_preferences: [],
    bonus_pct: prefs.value.bonusPct,
    category_filter: prefs.value.categoryFilter,
    selected_channel_ids: prefs.value.selectedChannelIds,
  }
}

// ── Build default payload with dynamic time window ───────────
function buildAutoPayload(openTime, closeTime) {
  return {
    opening_time: openTime,
    closing_time: closeTime,
    min_duration_pct: 100,
    channels_count: 10,
    switch_penalty_pct: 10,
    termination_penalty: 20,
    max_consecutive_genre: 2,
    time_preferences: [],
    bonus_pct: 5,
    category_filter: prefs.value.categoryFilter,
    selected_channel_ids: prefs.value.selectedChannelIds,
  }
}

// ── Load prefs from API ──────────────────────────────────────
async function loadPreferences() {
  return withLoader(
    { title: 'Loading', message: 'Fetching preferences…' },
    async () => {
      const data = await fetchPreferences()
      prefs.value.openTime = minsToTime(data.opening_time ?? 480)
      prefs.value.closeTime = minsToTime(data.closing_time ?? 1380)
      prefs.value.minDurationPct = data.min_duration_pct ?? 100
      prefs.value.channelsCount = data.channels_count ?? 10
      prefs.value.switchPenaltyPct = data.switch_penalty_pct ?? 10
      prefs.value.terminationPenalty = data.termination_penalty ?? 20
      prefs.value.maxConsecutiveGenre = data.max_consecutive_genre ?? 2
      prefs.value.bonusPct = data.bonus_pct ?? 5
      prefs.value.categoryFilter = data.category_filter ?? []
      prefs.value.selectedChannelIds = data.selected_channel_ids ?? []
    }
  ).catch((e) => console.warn('Could not load preferences:', e))
}

// ── Generate schedule ────────────────────────────────────────
let genCount = 0

async function runGenerate(customPayload = null) {
  const id = ++genCount
  console.log(`[GEN ${id}] start`, new Date().toISOString())

  const t0 = performance.now()
  try {
    return await withLoader(
      { title: 'Generating', message: 'Building schedule…' },
      async () => {
        const payload = customPayload || buildPayload()
        const data = await apiGenerate(payload)
        console.log(`[GEN ${id}] api ms`, Math.round(performance.now() - t0))
        schedule.value = data.scheduled_programs || []
        scheduleClosingTime.value = payload.closing_time
      }
    )
  } finally {
    console.log(`[GEN ${id}] end`)
  }
}


// ── Auto-regenerate when schedule expires ────────────────────
async function autoRegenerate() {
  const now = getNowMins()
  const openTime = now
  const closeTime = now + 720 // 12 hours later
  
  console.log(`[AUTO-REGENERATE] Schedule ended. Starting new 12-hour window: ${minsToTime(openTime)} → ${minsToTime(closeTime)}`)
  
  await runGenerate(buildAutoPayload(openTime, closeTime))
}

// ── Panel actions ────────────────────────────────────────────
async function onSavePrefs() {
  return withLoader(
    { title: 'Saving', message: 'Saving preferences…' },
    () => apiSavePrefs(buildPayload())
  )
}

async function onSaveAndGenerate() {
  return withLoader(
    { title: 'Saving', message: 'Saving & generating…' },
    async () => {
      await apiSavePrefs(buildPayload())
      showPrefs.value = false
      await runGenerate()
    }
  )
}

// ── Lifecycle ────────────────────────────────────────────────
onMounted(async () => {
  // 1. Load saved preferences
  await loadPreferences()
  // 2. Generate schedule immediately using those prefs
  await runGenerate()
  // 3. Clock tick every 5 seconds for time-aware sync
  clockTimer = setInterval(() => {
    clockNow.value = getNowMins()
  }, 5000)

  document.addEventListener('keydown', onKeydown)
})

// ── Watch for schedule expiration ────────────────────────────
const regenerating = ref(false)

watch(clockNow, async (now) => {
  if (scheduleClosingTime.value !== null && now >= scheduleClosingTime.value && !regenerating.value) {
    regenerating.value = true
    try { await autoRegenerate() } finally { regenerating.value = false }
  }
})


onUnmounted(() => {
  if (clockTimer) clearInterval(clockTimer)
  document.removeEventListener('keydown', onKeydown)
})

function onKeydown(e) {
  if (e.key === 'Escape') {
    if (showPrefs.value) showPrefs.value = false
    if (document.fullscreenElement) document.exitFullscreen()
  }
  if (e.key === 'f' && !e.ctrlKey && !e.metaKey) {
    const tag = document.activeElement.tagName
    if (tag !== 'INPUT' && tag !== 'TEXTAREA') {
      const wrap = document.querySelector('.player-wrap')
      if (!document.fullscreenElement) {
        wrap?.requestFullscreen().catch(() => wrap?.classList.toggle('is-fullscreen'))
      } else {
        document.exitFullscreen()
      }
    }
  }
}
</script>
